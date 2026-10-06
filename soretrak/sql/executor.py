"""Read-only SQL execution.

Defense in depth, in order:
1. sql/guard.py: the shape (one SELECT or WITH query);
2. opening with mode=ro and PRAGMA query_only;
3. allow-list authorizer: any non-read action is denied,
   including a write hidden behind a WITH;
4. sqlite3 refuses more than one statement per execute();
5. a timeout through the progress handler.

run_query never raises on an SQL error: it returns a QueryResult with
`error`, a message the SQL Agent can read to correct itself.
"""
import logging
import sqlite3
import time
from pathlib import Path

from soretrak.contracts import QueryResult
from soretrak.sql.guard import clean_sql, validate_sql

logger = logging.getLogger(__name__)

DEFAULT_MAX_ROWS = 50
DEFAULT_TIMEOUT_SECONDS = 5.0
MAX_VALUE_LENGTH = 200

ALLOWED_AUTHORIZER_ACTIONS = {
    sqlite3.SQLITE_SELECT,
    sqlite3.SQLITE_READ,
    sqlite3.SQLITE_FUNCTION,
    sqlite3.SQLITE_RECURSIVE,
}


def _authorizer(action, *args):
    return sqlite3.SQLITE_OK if action in ALLOWED_AUTHORIZER_ACTIONS else sqlite3.SQLITE_DENY


def _open_readonly(db_path: Path, deadline: list[float]) -> sqlite3.Connection:
    uri = db_path.resolve().as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=2)
    conn.execute("PRAGMA query_only = ON")
    conn.set_progress_handler(lambda: 1 if time.monotonic() > deadline[0] else 0, 1000)
    conn.set_authorizer(_authorizer)
    return conn


def _cut(value):
    if isinstance(value, str) and len(value) > MAX_VALUE_LENGTH:
        return value[:MAX_VALUE_LENGTH] + "…"
    if isinstance(value, bytes):
        return f"<{len(value)} octets>"
    return value


def run_query(
    sql: str,
    db_path: str | Path,
    max_rows: int = DEFAULT_MAX_ROWS,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    params: tuple | dict = (),
) -> QueryResult:
    """Run a read query and return at most `max_rows` rows.

    `params`: values for the `?` (or `:name`) markers, never pasted into the SQL text.
    """
    sql = clean_sql(sql)
    form_error = validate_sql(sql)
    if form_error:
        return QueryResult(error=form_error)

    db_path = Path(db_path)
    if not db_path.exists():
        logger.error("Base introuvable : %s", db_path)
        return QueryResult(error=f"Base de données introuvable : {db_path.name}")

    deadline = [time.monotonic() + timeout_seconds]
    conn = None
    try:
        conn = _open_readonly(db_path, deadline)
        deadline[0] = time.monotonic() + timeout_seconds
        cursor = conn.execute(sql, params)
        fetched = cursor.fetchmany(max_rows + 1)
        columns = [d[0] for d in cursor.description or []]
        rows = [{c: _cut(v) for c, v in zip(columns, row)} for row in fetched[:max_rows]]
        return QueryResult(
            columns=columns,
            rows=rows,
            row_count=len(rows),
            truncated=len(fetched) > max_rows,
        )
    except (sqlite3.Error, sqlite3.Warning) as e:
        return QueryResult(error=_explain(e, deadline[0], timeout_seconds))
    finally:
        if conn is not None:
            conn.close()


def _explain(e: Exception, deadline: float, timeout_seconds: float) -> str:
    """Translate an sqlite3 error into a message useful to the agent."""
    text = str(e)
    lowered = text.lower()
    if time.monotonic() > deadline or "interrupted" in lowered:
        return (
            f"Requête interrompue après {timeout_seconds:g} s : "
            "simplifie-la ou ajoute des filtres."
        )
    if "one statement" in lowered:
        return "Une seule instruction par requête : retire le ';' et ce qui suit."
    if "not authorized" in lowered:
        return "Opération refusée : la base est en lecture seule (SELECT uniquement)."
    logger.info("Erreur SQL : %s", text)
    return f"Erreur SQL : {text}"
