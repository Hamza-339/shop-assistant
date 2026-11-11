import json
import math
import os

import httpx
import pytest

from app.embeddings import VoyageEmbedder, embedder_from_env

_REQUIRES_VOYAGE_KEY = pytest.mark.skipif(
    not os.environ.get("VOYAGE_API_KEY"),
    reason="needs a real VOYAGE_API_KEY to call the live Voyage API",
)


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


def test_embedder_from_env_builds_a_voyage_embedder(monkeypatch):
    monkeypatch.setenv("VOYAGE_API_KEY", "test-key")

    embedder = embedder_from_env()

    assert isinstance(embedder, VoyageEmbedder)


@_REQUIRES_VOYAGE_KEY
def test_embed_scores_shared_meaning_higher_than_unrelated_text():
    embedder = embedder_from_env()

    product_text = "Classic Cotton T-Shirt breathable cotton t-shirt sizes S-XL"
    question_embedding = embedder.embed("Tell me about the Classic Cotton T-Shirt")
    matching_embedding = embedder.embed(product_text)
    unrelated_embedding = embedder.embed("Items may be returned within 30 days of delivery for a full refund")

    matching_score = _cosine_similarity(question_embedding, matching_embedding)
    unrelated_score = _cosine_similarity(question_embedding, unrelated_embedding)

    assert matching_score - unrelated_score > 0.2


@_REQUIRES_VOYAGE_KEY
def test_embed_scores_shared_meaning_higher_than_unrelated_text_for_a_policy_question():
    embedder = embedder_from_env()

    policy_text = "refund Items may be returned within 30 days of delivery for a full refund"
    question_embedding = embedder.embed("What is the refund policy?")
    matching_embedding = embedder.embed(policy_text)
    unrelated_embedding = embedder.embed("Classic Cotton T-Shirt breathable cotton t-shirt sizes S-XL")

    matching_score = _cosine_similarity(question_embedding, matching_embedding)
    unrelated_score = _cosine_similarity(question_embedding, unrelated_embedding)

    assert matching_score - unrelated_score > 0.2
