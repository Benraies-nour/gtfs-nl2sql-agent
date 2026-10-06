"""Loading of prompts (soretrak/prompts/) and knowledge files (soretrak/knowledge/).

A prompt contains {{name}} placeholders, filled by render(). A placeholder
left empty is an error: the LLM would receive the text "{{schema}}" instead of the schema.
"""
import re

from soretrak.config import KNOWLEDGE_DIR, PROMPTS_DIR

_PLACEHOLDER = re.compile(r"\{\{(\w+)\}\}")


def knowledge(name: str) -> str:
    """Content of a knowledge file (perimetre.md, schema.md, examples.yaml)."""
    return (KNOWLEDGE_DIR / name).read_text(encoding="utf-8")


def render(name: str, **values: str) -> str:
    """The prompt `name` (e.g. "router.md") with its {{…}} placeholders filled."""
    template = (PROMPTS_DIR / name).read_text(encoding="utf-8")
    missing = set(_PLACEHOLDER.findall(template)) - set(values)
    if missing:
        raise ValueError(f"{name} : emplacement(s) non rempli(s) : {', '.join(sorted(missing))}")
    return _PLACEHOLDER.sub(lambda m: values[m.group(1)], template)
