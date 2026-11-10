import pytest

from app.eval_judge import JUDGE_MODEL, AnthropicJudgeClient, judge_client_from_env


class _StubBlock:
    def __init__(self, text: str) -> None:
        self.text = text


class _StubResponse:
    def __init__(self, text: str) -> None:
        self.content = [_StubBlock(text)]


class _StubMessages:
    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.calls: list[dict] = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return _StubResponse(self.response_text)


class _StubAnthropic:
    def __init__(self, response_text: str) -> None:
        self.messages = _StubMessages(response_text)


def test_judge_parses_a_pass_reply_as_passed_true():
    stub = _StubAnthropic("PASS: the actual answer matches the expected answer.")
    client = AnthropicJudgeClient(stub, model=JUDGE_MODEL)

    verdict = client.judge(
        question="What is the refund window?",
        expected_answer="Refunds are accepted within 30 days.",
        actual_answer="You can get a refund within 30 days.",
    )

    assert verdict.passed is True
    assert verdict.reasoning == "PASS: the actual answer matches the expected answer."


def test_judge_parses_a_fail_reply_as_passed_false():
    stub = _StubAnthropic("FAIL: the actual answer contradicts the expected answer.")
    client = AnthropicJudgeClient(stub, model=JUDGE_MODEL)

    verdict = client.judge(
        question="What is the refund window?",
        expected_answer="Refunds are accepted within 30 days.",
        actual_answer="We do not offer refunds.",
    )

    assert verdict.passed is False
    assert verdict.reasoning == "FAIL: the actual answer contradicts the expected answer."


def test_judge_sends_the_configured_model_name():
    stub = _StubAnthropic("PASS")
    client = AnthropicJudgeClient(stub, model=JUDGE_MODEL)

    client.judge(question="Q?", expected_answer="expected", actual_answer="actual")

    assert stub.messages.calls[0]["model"] == JUDGE_MODEL


def test_judge_client_from_env_uses_judge_model_even_when_llm_model_env_var_set(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "claude-opus-4-8")

    client = judge_client_from_env()

    assert isinstance(client, AnthropicJudgeClient)
    assert client.model == JUDGE_MODEL
    assert client.model != "claude-opus-4-8"
