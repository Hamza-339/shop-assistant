import hashlib

import pytest
from fastapi.testclient import TestClient

from app.main import (
    RATE_LIMIT_WINDOW_SECONDS,
    STOREFRONT_ORIGIN,
    _RATE_LIMIT_HITS,
    app,
    get_claude_client,
    get_embedder,
    get_store,
)
from app.store import StoreEntry, VectorStore

DISALLOWED_ORIGIN = "https://evil.example.com"


class FakeEmbedder:
    dimensions = 8
    match_threshold = 0.3

    def embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        return [byte / 255 for byte in digest[: self.dimensions]]


class FakeClaudeClient:
    def generate_answer(self, question: str, context: list[StoreEntry]) -> str:
        return "It's a breathable cotton t-shirt."


def _seeded_store(embedder: FakeEmbedder) -> VectorStore:
    store = VectorStore()
    text = "Classic Cotton T-Shirt breathable cotton t-shirt sizes S-XL"
    store.add(
        StoreEntry(
            id="gid://shopify/Product/1",
            kind="product",
            handle="classic-cotton-t-shirt",
            text=text,
            embedding=embedder.embed(text),
        )
    )
    return store


@pytest.fixture(autouse=True)
def _reset_state():
    embedder = FakeEmbedder()
    app.dependency_overrides[get_store] = lambda: _seeded_store(embedder)
    app.dependency_overrides[get_embedder] = lambda: embedder
    app.dependency_overrides[get_claude_client] = lambda: FakeClaudeClient()
    _RATE_LIMIT_HITS.clear()
    yield
    app.dependency_overrides.clear()
    _RATE_LIMIT_HITS.clear()


@pytest.fixture
def client():
    return TestClient(app)


def test_api_returns_answer_citations_and_deflected_fields(client):
    response = client.post("/api", json={"question": "Tell me about the Classic Cotton T-Shirt"})

    assert response.status_code == 200
    assert response.json() == {
        "answer": "It's a breathable cotton t-shirt.",
        "citations": [
            {"id": "gid://shopify/Product/1", "kind": "product", "handle": "classic-cotton-t-shirt"}
        ],
        "deflected": False,
    }


def test_api_returns_deflected_shape_for_an_out_of_scope_question(client):
    response = client.post("/api", json={"question": "Where is my order #1234?"})

    assert response.status_code == 200
    body = response.json()
    assert body["deflected"] is True
    assert body["citations"] == []


def test_api_allows_requests_from_the_storefront_origin(client):
    response = client.post(
        "/api",
        json={"question": "Tell me about the Classic Cotton T-Shirt"},
        headers={"Origin": STOREFRONT_ORIGIN},
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == STOREFRONT_ORIGIN


def test_api_rejects_requests_from_a_disallowed_origin(client):
    response = client.post(
        "/api",
        json={"question": "Tell me about the Classic Cotton T-Shirt"},
        headers={"Origin": DISALLOWED_ORIGIN},
    )

    assert "access-control-allow-origin" not in response.headers


def test_api_rejects_preflight_from_a_disallowed_origin(client):
    response = client.options(
        "/api",
        headers={
            "Origin": DISALLOWED_ORIGIN,
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 400


def test_api_rate_limits_after_20_requests_in_a_minute_from_one_ip(client):
    for _ in range(20):
        response = client.post("/api", json={"question": "Tell me about the Classic Cotton T-Shirt"})
        assert response.status_code == 200

    response = client.post("/api", json={"question": "Tell me about the Classic Cotton T-Shirt"})

    assert response.status_code == 429


def test_main_wires_the_real_anthropic_claude_client_as_the_production_default():
    from app.claude_client import AnthropicClaudeClient
    from app.main import _claude_client

    assert isinstance(_claude_client, AnthropicClaudeClient)


def test_api_allows_requests_again_after_the_rate_limit_window_expires(client, monkeypatch):
    fake_now = [0.0]
    monkeypatch.setattr("app.main.time.monotonic", lambda: fake_now[0])

    for _ in range(20):
        response = client.post("/api", json={"question": "Tell me about the Classic Cotton T-Shirt"})
        assert response.status_code == 200

    blocked = client.post("/api", json={"question": "Tell me about the Classic Cotton T-Shirt"})
    assert blocked.status_code == 429

    fake_now[0] += RATE_LIMIT_WINDOW_SECONDS + 1

    response = client.post("/api", json={"question": "Tell me about the Classic Cotton T-Shirt"})

    assert response.status_code == 200
