import json
import math

import httpx
import pytest

from app.embeddings import VoyageEmbedder, embedder_from_env
from tests.conftest import requires_voyage_key


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b)


class _StubTransport(httpx.BaseTransport):
    def __init__(self, embedding: list[float]) -> None:
        self.embedding = embedding
        self.requests: list[httpx.Request] = []

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return httpx.Response(200, json={"data": [{"embedding": self.embedding, "index": 0}]})


def test_embed_sends_the_model_and_input_and_returns_the_embedding():
    transport = _StubTransport(embedding=[0.1, 0.2, 0.3])
    client = httpx.Client(base_url="https://api.voyageai.com/v1", transport=transport)
    embedder = VoyageEmbedder(client, model="voyage-4-lite")

    result = embedder.embed("Classic Cotton T-Shirt")

    assert result == [0.1, 0.2, 0.3]
    body = json.loads(transport.requests[0].read())
    assert body["model"] == "voyage-4-lite"
    assert body["input"] == ["Classic Cotton T-Shirt"]


class _FakeClock:
    """Injectable clock/sleep pair: advances monotonic() by exactly however
    long sleep() was told to wait, so pacing logic is testable without
    actually waiting."""

    def __init__(self) -> None:
        self.now = 0.0
        self.slept: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.now += seconds


def test_embed_waits_at_least_the_minimum_interval_between_requests():
    transport = _StubTransport(embedding=[0.1])
    client = httpx.Client(base_url="https://api.voyageai.com/v1", transport=transport)
    clock = _FakeClock()
    embedder = VoyageEmbedder(
        client, model="voyage-4-lite", min_interval_seconds=21.0, clock=clock.monotonic, sleep=clock.sleep
    )

    embedder.embed("first")
    clock.now += 5.0
    embedder.embed("second")

    assert clock.slept == [16.0]


def test_embed_does_not_wait_before_the_first_request():
    transport = _StubTransport(embedding=[0.1])
    client = httpx.Client(base_url="https://api.voyageai.com/v1", transport=transport)
    clock = _FakeClock()
    embedder = VoyageEmbedder(
        client, model="voyage-4-lite", min_interval_seconds=21.0, clock=clock.monotonic, sleep=clock.sleep
    )

    embedder.embed("first")

    assert clock.slept == []


class _FlakyTransport(httpx.BaseTransport):
    """Returns 429 for the first `failures` requests, then 200."""

    def __init__(self, embedding: list[float], failures: int) -> None:
        self.embedding = embedding
        self.failures = failures
        self.requests: list[httpx.Request] = []

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if len(self.requests) <= self.failures:
            return httpx.Response(429, json={"detail": "rate limited"})
        return httpx.Response(200, json={"data": [{"embedding": self.embedding, "index": 0}]})


def test_embed_retries_after_a_429_and_returns_the_embedding():
    transport = _FlakyTransport(embedding=[0.4, 0.5], failures=1)
    client = httpx.Client(base_url="https://api.voyageai.com/v1", transport=transport)
    clock = _FakeClock()
    embedder = VoyageEmbedder(
        client, model="voyage-4-lite", retry_backoff_seconds=65.0, clock=clock.monotonic, sleep=clock.sleep
    )

    result = embedder.embed("rate limited text")

    assert result == [0.4, 0.5]
    assert len(transport.requests) == 2
    assert clock.slept == [65.0]


def test_embed_raises_after_exhausting_retries_on_persistent_429():
    transport = _FlakyTransport(embedding=[0.4], failures=10)
    client = httpx.Client(base_url="https://api.voyageai.com/v1", transport=transport)
    clock = _FakeClock()
    embedder = VoyageEmbedder(
        client,
        model="voyage-4-lite",
        max_retries=3,
        retry_backoff_seconds=1.0,
        clock=clock.monotonic,
        sleep=clock.sleep,
    )

    with pytest.raises(httpx.HTTPStatusError):
        embedder.embed("always rate limited")

    assert len(transport.requests) == 4


def test_embedder_from_env_builds_a_voyage_embedder(monkeypatch):
    monkeypatch.setenv("VOYAGE_API_KEY", "test-key")

    embedder = embedder_from_env()

    assert isinstance(embedder, VoyageEmbedder)


@requires_voyage_key
def test_embed_scores_shared_meaning_higher_than_unrelated_text():
    embedder = embedder_from_env()

    product_text = "Classic Cotton T-Shirt breathable cotton t-shirt sizes S-XL"
    question_embedding = embedder.embed("Tell me about the Classic Cotton T-Shirt")
    matching_embedding = embedder.embed(product_text)
    unrelated_embedding = embedder.embed("Items may be returned within 30 days of delivery for a full refund")

    matching_score = _cosine_similarity(question_embedding, matching_embedding)
    unrelated_score = _cosine_similarity(question_embedding, unrelated_embedding)

    assert matching_score - unrelated_score > 0.2


@requires_voyage_key
def test_embed_scores_shared_meaning_higher_than_unrelated_text_for_a_policy_question():
    embedder = embedder_from_env()

    policy_text = "refund Items may be returned within 30 days of delivery for a full refund"
    question_embedding = embedder.embed("What is the refund policy?")
    matching_embedding = embedder.embed(policy_text)
    unrelated_embedding = embedder.embed("Classic Cotton T-Shirt breathable cotton t-shirt sizes S-XL")

    matching_score = _cosine_similarity(question_embedding, matching_embedding)
    unrelated_score = _cosine_similarity(question_embedding, unrelated_embedding)

    assert matching_score - unrelated_score > 0.2
