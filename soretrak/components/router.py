"""Router: classifies the message and produces a structured decision.

It uses the history and the previous context to understand follow-up
questions and rewrite them as standalone questions. It does not answer
data questions and runs no SQL.
"""

from soretrak import config, llm
from soretrak.contracts import RouterDecision, TurnContext
from soretrak.prompts import knowledge, render

HISTORY_EXCHANGES = 3   # exchanges = user/assistant pairs, so 6 messages


def build_system_prompt() -> str:
    return render("router.md", perimetre=knowledge("perimetre.md"))


def format_context(contexte: list[TurnContext] | None) -> str:
    """The structured context of the last turns, most recent first."""
    if not contexte:
        return "(aucun)"
    blocks = []
    for i, turn in enumerate(reversed(contexte)):
        label = "Tour précédent" if i == 0 else f"Il y a {i + 1} tours"
        lines = [f"{label} : « {turn['question']} » (résultat : {turn['statut']})"]
        if turn["lieux"]:
            lines.append("  lieux : " + ", ".join(
                f"{l['nom']} ({'ligne' if l['type'] == 'ligne' else 'arrêt'} {l['id']})"
                for l in turn["lieux"]))
        if turn["lignes"]:
            lines.append("  lignes trouvées : " + ", ".join(turn["lignes"]))
        if turn["arrets"]:
            lines.append("  arrêts trouvés : " + ", ".join(turn["arrets"]))
        blocks.append("\n".join(lines))
    return "\n".join(blocks)


def format_pending(en_attente: dict | None) -> str:
    """The question left pending by the Router's clarification request on the previous turn."""
    if not en_attente:
        return ""
    return (f"Question en attente de précision : « {en_attente['question']} »\n"
            f"Tu as demandé : « {en_attente['demande']} »\n"
            "Le dernier message répond probablement à cette demande : combine-les en une "
            "question complète.\n\n")


def format_user_prompt(message: str, history: list[dict] | None = None,
                       contexte: list[TurnContext] | None = None,
                       en_attente: dict | None = None) -> str:
    """`history`: messages {"role": "user"|"assistant", "content": …}, oldest first."""
    recent = (history or [])[-2 * HISTORY_EXCHANGES:]
    lines = [f"{'Utilisateur' if m['role'] == 'user' else 'Assistant'} : {m['content']}"
             for m in recent]
    history_text = "\n".join(lines) if lines else "(début de la conversation)"
    return (
        f"Historique :\n{history_text}\n\n"
        f"Contexte de la conversation (données des tours précédents) :\n{format_context(contexte)}\n\n"
        f"{format_pending(en_attente)}"
        f"Dernier message de l'utilisateur :\n{message}"
    )


def route(message: str, history: list[dict] | None = None,
          contexte: list[TurnContext] | None = None,
          en_attente: dict | None = None) -> RouterDecision:
    return llm.structured(
        build_system_prompt(),
        format_user_prompt(message, history, contexte, en_attente),
        RouterDecision,
        model=config.MODEL_ROUTER,
    )
