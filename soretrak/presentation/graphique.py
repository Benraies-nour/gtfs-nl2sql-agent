"""On-demand chart: a bar chart built by the code (no LLM).

It starts from the agent's evidence: the last query with a label column
(line, stop, hour) and a number column, over at least two rows. The values
are the database ones, never rewritten by an LLM.
"""
import re

from soretrak.contracts import AgentRun, ChartData
from soretrak.presentation.formatting import human

MAX_BARS = 40
# Numeric columns that are not measures.
NOT_MEASURES = {"direction_id", "stop_sequence", "stop_lat", "stop_lon", "shape_pt_sequence"}
MEASURE_HINT = re.compile(r"(^n$|^nb|nombre|count|total|somme|^num)", re.IGNORECASE)
HOUR = re.compile(r"^\d{1,2}(:\d{2})?(:\d{2})?$|^\d{1,2}\s?h(\d{2})?$", re.IGNORECASE)


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _pick_columns(rows: list[dict]) -> tuple[str, str] | None:
    """(label, measure) if the query lends itself to a chart, otherwise None."""
    columns = list(rows[0])
    numeric = [c for c in columns if c not in NOT_MEASURES
               and all(_is_number(r.get(c)) for r in rows)]
    labels = [c for c in columns if c not in numeric and c not in NOT_MEASURES]
    if not numeric or not labels:
        return None
    hinted = [c for c in numeric if MEASURE_HINT.search(c)]
    measure = hinted[0] if hinted else numeric[-1]
    label = next((c for c in labels if c in ("route_id", "route_short_name")), labels[0])
    return label, measure


def _label(column: str, value) -> str:
    text = str(value)
    if column in ("route_id", "route_short_name") and not text.lower().startswith("ligne"):
        return f"Ligne {text}"
    if HOUR.match(text) and text.count(":") == 2:
        return text[:5]                     # 08:15:00 → 08:15
    if re.fullmatch(r"\d{1,2}", text) and re.search(r"heure|hour|^h$", column, re.IGNORECASE):
        return f"{int(text):02d}h"          # 6 or 06 → 06h
    return text


def build_chart(question: str, agent: AgentRun | None) -> ChartData | None:
    """Bar chart data, or None if no evidence lends itself to a chart."""
    if not agent:
        return None
    requetes = agent.get("requetes", {})
    preuves = [q for q in agent["resultat"]["preuves"] if q != "q0"]
    for qid in reversed(preuves):
        rows = requetes.get(qid, {}).get("rows") or []
        if len(rows) < 2:
            continue
        picked = _pick_columns(rows)
        if not picked:
            continue
        label_col, measure_col = picked
        data = [{"libelle": _label(label_col, r[label_col]), "valeur": r[measure_col]} for r in rows
                if r.get(label_col) is not None]
        hours = all(HOUR.match(d["libelle"]) for d in data)
        data.sort(key=lambda d: d["libelle"] if hours else -d["valeur"])
        note = None
        if len(data) > MAX_BARS:
            note = f"{MAX_BARS} premières valeurs sur {len(data)}."
            data = data[:MAX_BARS]
        return {
            "titre": question,
            "axe_libelle": "Heure" if hours else ("Ligne" if label_col.startswith("route") else label_col),
            "axe_valeur": human(measure_col),
            "orientation": "verticale" if hours else "horizontale",
            "donnees": data,
            "tronque": bool(requetes[qid].get("truncated")),
            "note": note,
        }
    return None


BAR_COLOR = "#3987e5"   # single series; validated on light and dark backgrounds (contrast ≥ 3:1)
BAR_SIZE = 18           # ≤ 24 px: the bar does not fill its band
LABELS_UP_TO = 20       # beyond that, the value stays in the tooltip


def bar_chart(graphique: ChartData):
    """Altair chart: one series, rounded bar ends, value at the end, tooltip."""
    import altair as alt

    data = graphique["donnees"]
    order = [d["libelle"] for d in data]
    horizontal = graphique["orientation"] == "horizontale"
    label_enc = alt.Y if horizontal else alt.X
    value_enc = alt.X if horizontal else alt.Y
    base = alt.Chart(alt.Data(values=data)).encode(
        label_enc("libelle:N", sort=order, title=graphique["axe_libelle"],
                  axis=alt.Axis(labelLimit=180, ticks=False, domain=False, labelAngle=0)),
        value_enc("valeur:Q", title=graphique["axe_valeur"],
                  axis=alt.Axis(gridOpacity=0.25, domain=False, ticks=False, tickMinStep=1)),
        tooltip=[alt.Tooltip("libelle:N", title=graphique["axe_libelle"]),
                 alt.Tooltip("valeur:Q", title=graphique["axe_valeur"])],
    )
    chart = base.mark_bar(size=BAR_SIZE, color=BAR_COLOR, cornerRadiusEnd=4)
    if len(data) <= LABELS_UP_TO:
        chart += base.mark_text(align="left" if horizontal else "center",
                                baseline="middle" if horizontal else "bottom",
                                dx=4 if horizontal else 0, dy=0 if horizontal else -4
                                ).encode(text="valeur:Q")
    height = max(160, 26 * len(data) + 50) if horizontal else 300
    return chart.properties(height=height)
