from typing import Protocol

from app.store import StoreEntry


class ClaudeClient(Protocol):
    """Generates a grounded answer from question + retrieved store entries.

    Real token-based client comes later; FakeClaudeClient stands in for tests.
    """

    def generate_answer(self, question: str, context: list[StoreEntry]) -> str: ...
