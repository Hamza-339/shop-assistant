"""Eval Pair regression harness (#8): runs the 30 hand-curated Eval Pairs
through answer_question and grades each with an LLM judge.

Runs independently of the pytest suite: `python -m eval.run_eval` from
backend/. Not collected by pytest (lives outside tests/, no test_*.py name).
"""

import sys

from dotenv import load_dotenv

from app.claude_client import claude_client_from_env
from app.embeddings import LocalEmbedder
from app.eval_judge import judge_client_from_env
from app.eval_runner import run_eval
from eval.pairs import EVAL_PAIRS, build_eval_store


def main() -> int:
    load_dotenv()

    embedder = LocalEmbedder()
    store = build_eval_store(embedder)
    claude_client = claude_client_from_env()
    judge_client = judge_client_from_env()

    results = run_eval(EVAL_PAIRS, store, embedder, claude_client, judge_client)

    failures = 0
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        if not result.passed:
            failures += 1
        print(f"[{status}] {result.pair_id} ({result.category})")
        print(f"  Q: {result.question}")
        print(f"  A: {result.actual_answer}")
        if not result.passed:
            print(f"  judge: {result.reasoning}")

    print(f"\n{len(results) - failures}/{len(results)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
