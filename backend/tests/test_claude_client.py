import pytest

from app.claude_client import DEFAULT_LLM_MODEL, AnthropicClaudeClient, claude_client_from_env
from app.store import StoreEntry


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


def test_generate_answer_returns_the_model_reply_text():
    stub = _StubAnthropic("A breathable cotton t-shirt.")
    client = AnthropicClaudeClient(stub, model="claude-haiku-4-5-20251001")

    answer = client.generate_answer(
        "What is this shirt made of?",
        [StoreEntry(id="gid://shopify/Product/1", kind="product", text="Classic Cotton T-Shirt", embedding=[])],
    )

    assert answer == "A breathable cotton t-shirt."


def test_generate_answer_instructs_the_model_to_confirm_from_whatever_fields_are_present():
    stub = _StubAnthropic("irrelevant")
    client = AnthropicClaudeClient(stub, model="claude-haiku-4-5-20251001")

    client.generate_answer(
        "Is the Draft Snowboard available?",
        [StoreEntry(id="gid://shopify/Product/1", kind="product", text="The Draft Snowboard", embedding=[])],
    )

    prompt = stub.messages.calls[0]["messages"][0]["content"]
    assert "authoritative" in prompt.lower()
    assert "do not" in prompt.lower() or "don't" in prompt.lower()


def test_generate_answer_sends_the_configured_model_name():
    stub = _StubAnthropic("irrelevant")
    client = AnthropicClaudeClient(stub, model="claude-haiku-4-5-20251001")

    client.generate_answer("Question?", [])

    assert stub.messages.calls[0]["model"] == "claude-haiku-4-5-20251001"


def test_claude_client_from_env_defaults_to_anthropic_haiku(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("LLM_MODEL", raising=False)

    client = claude_client_from_env()

    assert isinstance(client, AnthropicClaudeClient)
    assert client.model == DEFAULT_LLM_MODEL


def test_claude_client_from_env_reads_the_model_name_from_env(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "claude-opus-4-8")

    client = claude_client_from_env()

    assert client.model == "claude-opus-4-8"


def test_claude_client_from_env_rejects_an_unsupported_provider(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("LLM_PROVIDER", "openai")

    with pytest.raises(ValueError):
        claude_client_from_env()
