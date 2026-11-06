import hashlib

from app.models import Citation
from app.qa import answer_question
from app.store import StoreEntry, VectorStore


class FakeEmbedder:
    """Bag-of-words hashed embedder: shared words score similar, unlike the
    production LocalEmbedder's content-blind hash, so retrieval is testable."""

    dimensions = 64

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for word in text.lower().split():
            index = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16) % self.dimensions
            vector[index] += 1.0
        return vector


class FakeClaudeClient:
    def __init__(self, response: str) -> None:
        self.response = response
        self.last_context: list[StoreEntry] | None = None

    def generate_answer(self, question: str, context: list[StoreEntry]) -> str:
        self.last_context = context
        return self.response


def _seeded_store(embedder: FakeEmbedder) -> VectorStore:
    store = VectorStore()
    product_text = "Classic Cotton T-Shirt breathable cotton t-shirt sizes S-XL"
    store.add(
        StoreEntry(
            id="gid://shopify/Product/1",
            kind="product",
            text=product_text,
            embedding=embedder.embed(product_text),
        )
    )
    policy_text = "refund Items may be returned within 30 days of delivery for a full refund"
    store.add(
        StoreEntry(id="refund", kind="policy", text=policy_text, embedding=embedder.embed(policy_text))
    )
    return store


def test_answer_question_grounds_a_product_question_with_a_citation():
    embedder = FakeEmbedder()
    store = _seeded_store(embedder)
    claude_client = FakeClaudeClient(response="It's a breathable cotton t-shirt.")

    result = answer_question("Tell me about the Classic Cotton T-Shirt", store, embedder, claude_client)

    assert result.answer == "It's a breathable cotton t-shirt."
    assert result.citations == [Citation(id="gid://shopify/Product/1", kind="product")]
