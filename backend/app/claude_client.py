import os
from typing import Protocol

import anthropic

from app.store import StoreEntry

DEFAULT_LLM_PROVIDER = "anthropic"
DEFAULT_LLM_MODEL = "claude-haiku-4-5-20251001"

_GROUNDED_ANSWER_PROMPT = """Treat the context below as authoritative, current data from our store's \
catalog and policies - not as something you need outside knowledge to supplement. If the context names \
a product, confirm it exists and answer using whatever fields are present (title, price, options, tags) \
even if the description is empty or thin. Do not say you have no information, and do not suggest the \
shopper check elsewhere, as long as the context contains a relevant entry. Do not invent details the \
context doesn't support.

Context:
{context_text}

Question: {question}"""


class ClaudeClient(Protocol):
    """Generates a grounded answer from question + retrieved store entries.

    Real token-based client comes later; FakeClaudeClient stands in for tests.
    """

    def generate_answer(self, question: str, context: list[StoreEntry]) -> str: ...


class AnthropicClaudeClient:
    """Real ClaudeClient backed by Anthropic's Messages API."""

    def __init__(self, client: anthropic.Anthropic, model: str) -> None:
        self._client = client
        self.model = model

    def generate_answer(self, question: str, context: list[StoreEntry]) -> str:
        context_text = "\n\n".join(entry.text for entry in context)
        prompt = _GROUNDED_ANSWER_PROMPT.format(context_text=context_text, question=question)
        response = self._client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text


def claude_client_from_env() -> ClaudeClient:
    """Builds the configured ClaudeClient from LLM_PROVIDER/LLM_MODEL (Anthropic Haiku by default)."""
    provider = os.environ.get("LLM_PROVIDER", DEFAULT_LLM_PROVIDER)
    if provider != "anthropic":
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider!r}")

    model = os.environ.get("LLM_MODEL", DEFAULT_LLM_MODEL)
    api_key = os.environ["ANTHROPIC_API_KEY"]
    return AnthropicClaudeClient(anthropic.Anthropic(api_key=api_key), model)
