import hashlib

from app.eval_judge import JudgeVerdict
from app.eval_runner import EvalPair, EvalResult, run_eval
from app.qa import DEFLECTION_MESSAGE
from app.store import StoreEntry, VectorStore


STOPWORDS = {
    "a", "an", "the", "is", "are", "do", "you", "your", "what", "how", "many",
    "for", "of", "in", "on", "within", "to", "i", "have", "that", "this",
    "does", "my", "me", "about", "tell",
}


class FakeEmbedder:
    dimensions = 64
    match_threshold = 0.3

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
        self.calls: list[str] = []

    def generate_answer(self, question: str, context: list[StoreEntry]) -> str:
        self.calls.append(question)
        return self.response


class FakeJudgeClient:
    def __init__(self, verdict: JudgeVerdict) -> None:
        self.verdict = verdict
        self.calls: list[tuple[str, str, str]] = []

    def judge(self, question: str, expected_answer: str, actual_answer: str) -> JudgeVerdict:
        self.calls.append((question, expected_answer, actual_answer))
        return self.verdict


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
    return store


def test_run_eval_produces_one_result_per_pair_in_order():
    embedder = FakeEmbedder()
    store = _seeded_store(embedder)
    claude_client = FakeClaudeClient(response="It's a breathable cotton t-shirt.")
    judge_client = FakeJudgeClient(verdict=JudgeVerdict(passed=True, reasoning="PASS: close enough."))

    pairs = [
        EvalPair(
            id="p1",
            category="product",
            question="Tell me about the Classic Cotton T-Shirt",
            expected_answer="It's a breathable cotton t-shirt available in sizes S-XL.",
        ),
        EvalPair(
            id="p2",
            category="deflected_orders",
            question="Where is my order #1234?",
            expected_answer=DEFLECTION_MESSAGE,
        ),
    ]

    results = run_eval(pairs, store, embedder, claude_client, judge_client)

    assert results == [
        EvalResult(
            pair_id="p1",
            category="product",
            question="Tell me about the Classic Cotton T-Shirt",
            actual_answer="It's a breathable cotton t-shirt.",
            passed=True,
            reasoning="PASS: close enough.",
        ),
        EvalResult(
            pair_id="p2",
            category="deflected_orders",
            question="Where is my order #1234?",
            actual_answer=DEFLECTION_MESSAGE,
            passed=True,
            reasoning="PASS: close enough.",
        ),
    ]


def test_run_eval_judges_the_actual_answer_not_the_expected_answer():
    embedder = FakeEmbedder()
    store = _seeded_store(embedder)
    claude_client = FakeClaudeClient(response="It's a breathable cotton t-shirt.")
    judge_client = FakeJudgeClient(verdict=JudgeVerdict(passed=True, reasoning="PASS"))

    pairs = [
        EvalPair(
            id="p1",
            category="product",
            question="Tell me about the Classic Cotton T-Shirt",
            expected_answer="It's a breathable cotton t-shirt available in sizes S-XL.",
        ),
    ]

    run_eval(pairs, store, embedder, claude_client, judge_client)

    assert judge_client.calls == [
        (
            "Tell me about the Classic Cotton T-Shirt",
            "It's a breathable cotton t-shirt available in sizes S-XL.",
            "It's a breathable cotton t-shirt.",
        )
    ]


def test_run_eval_does_not_call_claude_client_for_a_deflected_pair():
    embedder = FakeEmbedder()
    store = _seeded_store(embedder)
    claude_client = FakeClaudeClient(response="should never be returned")
    judge_client = FakeJudgeClient(verdict=JudgeVerdict(passed=True, reasoning="PASS"))

    pairs = [
        EvalPair(
            id="p1",
            category="deflected_orders",
            question="Where is my order #1234?",
            expected_answer=DEFLECTION_MESSAGE,
        ),
    ]

    run_eval(pairs, store, embedder, claude_client, judge_client)

    assert claude_client.calls == []
