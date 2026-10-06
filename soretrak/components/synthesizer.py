"""Synthesizer: a chain that writes the answer from the real rows of the evidence.

It receives the rows from the query registry, never a summary written by the agent.
"""
import json

from pydantic import BaseModel

from soretrak import config, llm
from soretrak.contracts import AgentResult, QueryRecord
from soretrak.presentation.formatting import clean_rows, clean_text
from soretrak.prompts import render


class Synthese(BaseModel):
    reponse: str


def format_evidence(result: AgentResult, requetes: dict[str, QueryRecord]) -> str:
    blocks = []
    for qid in result.preuves:
        q = requetes[qid]
        header = f"Résultat ({q['row_count']} lignes{', TRONQUÉ' if q['truncated'] else ''})"
        rows = json.dumps(clean_rows(q["rows"]), ensure_ascii=False, default=str)
        blocks.append(f"{header} :\n{rows}")
    return "\n\n".join(blocks) or "(aucun résultat)"


CHART_NOTE = ("Un graphique en barres affiche déjà toutes ces valeurs sous la réponse : "
              "résume en deux phrases au plus (la valeur la plus haute, la plus basse), "
              "sans lister les valeurs une à une.")


def build_user_prompt(question: str, result: AgentResult, requetes: dict[str, QueryRecord],
                      graphique: bool = False) -> str:
    parts = [
        f"Question : {question}",
        f"Statut : {result.statut}",
        f"Note : {clean_text(result.note) if result.note else '(aucune)'}",
        format_evidence(result, requetes),
    ]
    if graphique:
        parts.append(CHART_NOTE)
    return "\n\n".join(parts)


def synthesize(question: str, result: AgentResult, requetes: dict[str, QueryRecord],
               graphique: bool = False) -> str:
    system = render("synthesizer.md")
    synthese = llm.structured(system, build_user_prompt(question, result, requetes, graphique),
                              Synthese, model=config.MODEL_ROUTER)
    return synthese.reponse.strip()
