# SORETRAK Assist

A conversational assistant for the **SORETRAK** bus network in Kairouan, Tunisia. It answers questions written in French, Tunisian Arabic (Latin script or *arabizi*) or Arabic, from the official open GTFS timetables, and replies in French.

It is an NL2SQL system: an LLM agent writes SQL against a read-only SQLite database, and the answer is written only from the rows it returned.

## Features

- Lines serving a stop, stops of a line, timetables, next departures
- Direct rides from A to B, with travel time
- Regional lines from Kairouan (Sousse, Tunis, Mahdia, Monastir…)
- Maps (Leaflet) and bar charts on request
- Honest refusals for what the data does not contain 

## How it works

```
message ─► Router (1 LLM call) ── intent, standalone question, places mentioned
             ├─ conversation · too vague · out of scope · off topic ─► direct reply
             └─ transport
                  ▼
           Place resolution ── stops and lines + facts about them
                  ▼
           SQL agent (ReAct, ≤ 4 tool calls) ── run_sql · resolve_place · finish
                  ├─ answered · no data ─► Synthesizer (1 LLM call) ─► answer
                  └─ ambiguous · impossible · failure ─► fixed message
```

A LangGraph workflow with a single agent. **Code sets the boundaries; the LLM decides within them.**

| Component | Type | Role |
|---|---|---|
| Router | LLM chain | Classifies the message (5 intents), rewrites follow-ups as standalone questions |
| Place resolution | Code | Fuzzy matching over 192 stops and 95 lines; Arabic → Latin, *arabizi*, articles, abbreviations |
| SQL agent | LLM agent | Writes and runs SQL, corrects itself, cites the queries used as evidence |
| Synthesizer | LLM chain | Writes the answer from the evidence rows only |
| Respond | Code | Fixed messages; no technical error ever reaches the user |

Design choices worth noting:

- **Semantic layer in SQL, not in prompts.** Domain rules live in views: `v_trajets` guarantees that A precedes B on the same trip and computes durations from seconds (times are stored as text).
- **Read-only by construction.** `SELECT`/`WITH` shape check, `mode=ro` + `query_only`, an allow-list authorizer, one statement per call, a timeout.
- **Grounded answers.** The synthesizer never sees an agent summary, only the rows returned by the database.
- **Measured, not assumed.** The agent loop was tuned against the evaluation set: one tool call per turn, known facts placed next to the question, a `raison` field that makes each step explicit.

## Results

Measured on a private evaluation set with `gpt-4.1-mini` (OpenAI):

| Set | Checks | Score |
|---|---|---|
| Places | text → expected stop or line (no LLM) | 18/18 |
| Router | message → intent | 31/31 |
| End to end | answer contains the values of a reference SQL query | 29/29 |

Most data questions need 0 or 1 SQL query.

## Quickstart

Python 3.10+ (tested on 3.13).

```bash
pip install -r requirements.txt
python scripts/build_db.py    # once, after adding the GTFS files (see Data)
cp .env.example .env          # set LLM_PROVIDER and the matching API key
streamlit run app.py
```

| Variable | Value |
|---|---|
| `LLM_PROVIDER` | `openai` (recommended) or `groq` |
| `OPENAI_API_KEY` / `GROQ_API_KEY` | key of the active provider |

Command line, with the agent trace:

```bash
python cli.py --trace "quelles lignes passent par bab jdid ?"
```

Add `?debug=1` to the app URL to see the SQL and the agent trace under each answer.

## Data

The data is not included in this repository. Download the SORETRAK GTFS feed from the Tunisian Ministry of Transport's [open-data portal](https://catalogue-data.transport.tn), put the `.txt` files in `data/gtfs/`, then build the SQLite database (`data/soretrak_gtfs.db`):

```bash
python scripts/build_db.py
```



## Project structure

```
app.py, cli.py         Streamlit app, command line
soretrak/
  components/          router, sql_agent, tools, synthesizer, respond
  conversation/        main graph, conversation memory
  places/              normalization, resolution, pre-retrieved facts
  sql/                 shape guard, read-only executor
  presentation/        formatting, map, chart
  prompts/             LLM prompts (French)
  knowledge/           scope, semantic schema, verified examples
data/sql/              schema and views (GTFS files and database not included)
```

---

Independent project, not affiliated with SORETRAK.
