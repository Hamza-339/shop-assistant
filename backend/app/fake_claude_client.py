from app.store import StoreEntry


class FakeClaudeClient:
    """Stand-in ClaudeClient. Real token-based client comes later."""

    def generate_answer(self, question: str, context: list[StoreEntry]) -> str:
        return context[0].text if context else ""
