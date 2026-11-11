from dataclasses import dataclass

from app.claude_client import ClaudeClient
from app.embeddings import Embedder
from app.eval_judge import JudgeClient
from app.qa import answer_question
from app.store import VectorStore


@dataclass(frozen=True)
class EvalPair:
    id: str
    category: str
    question: str
    expected_answer: str


@dataclass(frozen=True)
class EvalResult:
    pair_id: str
    category: str
    question: str
    actual_answer: str
    passed: bool
    reasoning: str


def run_eval(
    pairs: list[EvalPair],
    store: VectorStore,
    embedder: Embedder,
    claude_client: ClaudeClient,
    judge_client: JudgeClient,
) -> list[EvalResult]:
    results = []
    for pair in pairs:
        answer = answer_question(pair.question, store, embedder, claude_client)
        verdict = judge_client.judge(pair.question, pair.expected_answer, answer.answer)
        results.append(
            EvalResult(
                pair_id=pair.id,
                category=pair.category,
                question=pair.question,
                actual_answer=answer.answer,
                passed=verdict.passed,
                reasoning=verdict.reasoning,
            )
        )
    return results
