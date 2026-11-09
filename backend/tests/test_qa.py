import hashlib

from app.embeddings import LocalEmbedder
from app.models import Citation
from app.qa import DEFLECTION_MESSAGE, NO_GROUNDED_ANSWER, answer_question
from app.store import StoreEntry, VectorStore


STOPWORDS = {
    "a", "an", "the", "is", "are", "do", "you", "your", "what", "how", "many",
    "for", "of", "in", "on", "within", "to", "i", "have", "that", "this",
    "does", "my", "me", "about", "tell",
}


class FakeEmbedder:
    """Bag-of-words hashed embedder: shared meaningful words score similar.
    Used in place of the production LocalEmbedder so most retrieval tests
    don't pay the cost of loading a real model."""

    dimensions = 64

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for word in text.lower().split():
            word = word.strip("?,.")
            if word in STOPWORDS:
                continue
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
    assert result.deflected is False


def test_answer_question_grounds_a_policy_question_with_a_citation():
    embedder = FakeEmbedder()
    store = _seeded_store(embedder)
    claude_client = FakeClaudeClient(response="Refunds are accepted within 30 days.")

    result = answer_question("What is the refund policy?", store, embedder, claude_client)

    assert result.answer == "Refunds are accepted within 30 days."
    assert result.citations == [Citation(id="refund", kind="policy")]
    assert result.deflected is False


def test_answer_question_deflects_an_order_status_question():
    embedder = FakeEmbedder()
    store = _seeded_store(embedder)
    claude_client = FakeClaudeClient(response="should never be returned")

    result = answer_question("Where is my order #1234?", store, embedder, claude_client)

    assert result.answer == DEFLECTION_MESSAGE
    assert result.citations == []
    assert result.deflected is True
    assert claude_client.last_context is None


def test_answer_question_deflects_a_payment_question():
    embedder = FakeEmbedder()
    store = _seeded_store(embedder)
    claude_client = FakeClaudeClient(response="should never be returned")

    result = answer_question("My payment was declined, can you help?", store, embedder, claude_client)

    assert result.answer == DEFLECTION_MESSAGE
    assert result.citations == []
    assert result.deflected is True
    assert claude_client.last_context is None


def test_answer_question_deflects_a_stock_level_question():
    embedder = FakeEmbedder()
    store = _seeded_store(embedder)
    claude_client = FakeClaudeClient(response="should never be returned")

    result = answer_question(
        "Do you have the Classic Cotton T-Shirt in stock?", store, embedder, claude_client
    )

    assert result.answer == DEFLECTION_MESSAGE
    assert result.citations == []
    assert result.deflected is True
    assert claude_client.last_context is None


def test_answer_question_deflects_a_discount_code_question():
    embedder = FakeEmbedder()
    store = _seeded_store(embedder)
    claude_client = FakeClaudeClient(response="should never be returned")

    result = answer_question("Why isn't my discount code working?", store, embedder, claude_client)

    assert result.answer == DEFLECTION_MESSAGE
    assert result.citations == []
    assert result.deflected is True
    assert claude_client.last_context is None


def test_answer_question_deflects_an_order_status_question_using_the_plural_form():
    embedder = FakeEmbedder()
    store = _seeded_store(embedder)
    claude_client = FakeClaudeClient(response="should never be returned")

    result = answer_question("What's the status of my orders?", store, embedder, claude_client)

    assert result.answer == DEFLECTION_MESSAGE
    assert result.citations == []
    assert result.deflected is True
    assert claude_client.last_context is None


def test_answer_question_grounds_a_policy_question_that_mentions_a_deflected_keyword():
    embedder = FakeEmbedder()
    store = _seeded_store(embedder)
    claude_client = FakeClaudeClient(response="Refunds are accepted within 30 days.")

    result = answer_question(
        "What is the refund policy on items that are out of stock?", store, embedder, claude_client
    )

    assert result.answer == "Refunds are accepted within 30 days."
    assert result.citations == [Citation(id="refund", kind="policy")]
    assert result.deflected is False


def test_answer_question_retrieves_the_right_product_against_the_real_embedder():
    embedder = LocalEmbedder()
    store = _seeded_store(embedder)
    claude_client = FakeClaudeClient(response="It's a breathable cotton t-shirt.")

    result = answer_question("Tell me about the Classic Cotton T-Shirt", store, embedder, claude_client)

    assert result.answer == "It's a breathable cotton t-shirt."
    assert result.citations == [Citation(id="gid://shopify/Product/1", kind="product")]
    assert result.deflected is False


def test_answer_question_does_not_fabricate_an_answer_for_a_page_shaped_question():
    embedder = FakeEmbedder()
    store = _seeded_store(embedder)
    claude_client = FakeClaudeClient(response="should never be returned")

    result = answer_question(
        "Do you have a size guide for finding the right fit?", store, embedder, claude_client
    )

    assert result.answer == NO_GROUNDED_ANSWER
    assert result.citations == []
    assert claude_client.last_context is None
