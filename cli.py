"""Ask a question or hold a conversation from the terminal.

    py cli.py "quelles lignes passent par bab jdid ?"     one question
    py cli.py                                             conversation (empty line to quit)
    py cli.py --trace ...                                 also prints the agent trace
"""
import json
import logging
import sys
import uuid

from soretrak.conversation.graph import answer


def print_trace(details: dict) -> None:
    decision = details.get("decision") or {}
    print(f"  [router] {decision.get('intent')} → {decision.get('question_autonome') or ''}")
    agent = details.get("agent")
    if not agent:
        return
    for message in agent["trace"]:
        if message.get("role") == "assistant":
            for call in message["tool_calls"]:
                print(f"  → {call['function']['name']} {call['function']['arguments']}")
        elif message.get("role") == "tool":
            print(f"    ← {message['content'][:300]}")
    result = agent["resultat"]
    print(f"  [agent] {result['statut']} preuves={result['preuves']} note={result['note']}")
    for qid in result["preuves"]:
        q = agent["requetes"][qid]
        print(f"  {qid} ({q['row_count']} lignes) : {json.dumps(q['rows'][:5], ensure_ascii=False)}")


def main() -> None:
    args = sys.argv[1:]
    trace = "--trace" in args
    args = [a for a in args if a != "--trace"]
    logging.basicConfig(level=logging.WARNING, format="%(name)s %(message)s")
    thread_id = uuid.uuid4().hex

    questions = [" ".join(args)] if args else None
    while True:
        if questions is not None:
            if not questions:
                break
            message = questions.pop(0)
            print(f"> {message}")
        else:
            try:
                message = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not message:
                break
        response = answer(message, thread_id)
        if trace:
            print_trace(response.details)
        print(f"{response.texte}\n")


if __name__ == "__main__":
    main()
