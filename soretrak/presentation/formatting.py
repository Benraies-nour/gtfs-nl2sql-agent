"""Formatting of results: the rules that make a result row readable.

Used by the Synthesizer (before the LLM), the chart and the interface, so that
a time, a direction or a column name looks the same everywhere.
"""
import re

# Technical columns removed before the LLM: it must not display them.
TECHNICAL_COLUMNS = {"trip_id", "stop_id"}
# The direction is kept but made readable: without it, timetables of both directions mix.
DIRECTION_LABELS = {0: "aller", 1: "retour"}
_SECONDS = re.compile(r"\b(\d{2}:\d{2}):\d{2}\b")
_DIRECTION = re.compile(r"\s*\(?\s*(?:sens\s+(?:direction_id\s*=\s*)?|direction_id\s*=\s*)\d(?:\s*\))?", re.IGNORECASE)


def clean_text(text: str) -> str:
    """Times without seconds, without technical mention of the direction."""
    return _SECONDS.sub(r"\1", _DIRECTION.sub("", text))


def keep_line_breaks(text: str) -> str:
    """Markdown merges a single line break ("ligne 3 ligne 22"): make it explicit,
    except inside tables, which get a blank line around them."""
    lines = text.split("\n")
    out = []
    for i, line in enumerate(lines):
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        in_table, next_table = line.lstrip().startswith("|"), nxt.lstrip().startswith("|")
        if line.strip() and nxt.strip():
            if in_table != next_table:
                line += "\n"          # blank line before and after a table
            elif not in_table:
                line += "  "
        out.append(line)
    return "\n".join(out)


def group_by_line(rows: list[dict]) -> list[dict]:
    """Group the rows of a result by bus line, keeping their internal order:
    otherwise timetables of several lines sorted by time get mixed up when written."""
    if not rows or "route_id" not in rows[0] or len({r.get("route_id") for r in rows}) < 2:
        return rows
    first_seen = {}
    for i, r in enumerate(rows):
        first_seen.setdefault((r.get("route_id"), r.get("direction_id")), i)
    return sorted(rows, key=lambda r: first_seen[(r.get("route_id"), r.get("direction_id"))])


def clean_rows(rows: list[dict]) -> list[dict]:
    rows = group_by_line(rows)
    cleaned = []
    for row in rows:
        out = {}
        for k, v in row.items():
            if k in TECHNICAL_COLUMNS:
                continue
            if k == "direction_id":
                out["sens"] = DIRECTION_LABELS.get(v, v)
            else:
                out[k] = clean_text(v) if isinstance(v, str) else v
        cleaned.append(out)
    return cleaned


_ACCENTS = {"arrets": "arrêts", "departs": "départs", "arret": "arrêt", "depart": "départ"}


def human(column: str) -> str:
    """nb_arrets → "Nombre d'arrêts"; nombre_departs → "Nombre de départs"."""
    words = [_ACCENTS.get(w, w) for w in column.lower().split("_") if w]
    if words and words[0] in ("n", "nb", "nombre", "count", "total"):
        rest = " ".join(words[1:])
        if not rest:
            return "Nombre"
        return f"Nombre d'{rest}" if rest[0] in "aeéiouyh" else f"Nombre de {rest}"
    return " ".join(words).capitalize()


COLUMN_NAMES = {
    "route_id": "Ligne", "route_short_name": "Ligne", "route_long_name": "Nom de la ligne",
    "stop_name": "Arrêt", "departure_time": "Heure", "trip_headsign": "Destination",
    "stop_sequence": "Ordre", "sens": "Sens", "depart_a": "Départ", "arrivee_b": "Arrivée",
    "heure": "Heure",
}


def readable_rows(rows: list[dict]) -> list[dict]:
    """Result rows with column names in plain language."""
    return [{COLUMN_NAMES.get(k, human(k)): v for k, v in row.items()} for row in clean_rows(rows)]
