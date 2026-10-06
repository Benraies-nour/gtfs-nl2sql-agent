"""Validation of the shape of an SQL query, before any execution.

The guard only looks at the shape: a single read query starting with
SELECT or WITH. Writes are actually blocked by the authorizer in
sql/executor.py (a CTE can feed a DELETE, which the shape cannot see).

The error messages are read by the SQL Agent: they say what to fix.
"""
import re

_LEADING_COMMENT = re.compile(r"\A\s*(?:--[^\n]*(?:\n|\Z)|/\*.*?\*/)", re.DOTALL)
_FIRST_WORD = re.compile(r"\A([A-Za-z]+)")

ALLOWED_FIRST_WORDS = {"SELECT", "WITH"}


def clean_sql(sql: str) -> str:
    """Strip spaces, leading comments and trailing ';'."""
    text = sql or ""
    while True:
        match = _LEADING_COMMENT.match(text)
        if not match:
            break
        text = text[match.end():]
    return text.strip().rstrip(";").rstrip()


def validate_sql(sql: str) -> str | None:
    """Return None if the shape is acceptable, otherwise an error message."""
    if not sql or not sql.strip():
        return "Requête vide : écris une requête SELECT ou WITH."

    match = _FIRST_WORD.match(sql.lstrip())
    first = match.group(1).upper() if match else ""
    if first in ALLOWED_FIRST_WORDS:
        return None
    if not first:
        return "La requête doit commencer par SELECT ou WITH."
    return (
        f"Instruction {first} refusée : la base est en lecture seule. "
        "Seules les requêtes SELECT ou WITH sont acceptées."
    )
