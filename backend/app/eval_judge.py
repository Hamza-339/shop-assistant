import os
from dataclasses import dataclass
from typing import Protocol

import anthropic

JUDGE_MODEL = "claude-haiku-4-5-20251001"

_JUDGE_PROMPT = """You are grading a chat assistant's answer against an expected answer.

Question: {question}

Expected answer: {expected_answer}

Actual answer: {actual_answer}

Does the actual answer convey the same information as the expected answer, \
even if worded differently? Reply with PASS or FAIL on the first line, \
followed by a short reason."""


@dataclass(frozen=True)
class JudgeVerdict:
    passed: bool
    reasoning: str


class JudgeClient(Protocol):
    """Grades an answer_question result against a hand-curated expected answer."""

    def judge(self, question: str, expected_answer: str, actual_answer: str) -> JudgeVerdict: ...


class AnthropicJudgeClient:
    """Real JudgeClient backed by Anthropic's Messages API."""

    def __init__(self, client: anthropic.Anthropic, model: str) -> None:
        self._client = client
        self.model = model

    def judge(self, question: str, expected_answer: str, actual_answer: str) -> JudgeVerdict:
        prompt = _JUDGE_PROMPT.format(
            question=question, expected_answer=expected_answer, actual_answer=actual_answer
        )
        response = self._client.messages.create(
            model=self.model,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text
        return JudgeVerdict(passed=text.strip().upper().startswith("PASS"), reasoning=text)


def judge_client_from_env() -> JudgeClient:
    """Builds the AnthropicJudgeClient, always on JUDGE_MODEL (Haiku) regardless of LLM_MODEL."""
    api_key = os.environ["ANTHROPIC_API_KEY"]
    return AnthropicJudgeClient(anthropic.Anthropic(api_key=api_key), JUDGE_MODEL)
