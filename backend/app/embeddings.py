import os
from typing import Protocol

import httpx

DEFAULT_VOYAGE_MODEL = "voyage-4-lite"


class Embedder(Protocol):
    """Embeds text into a vector for cosine-similarity retrieval."""

    dimensions: int
    match_threshold: float

    def embed(self, text: str) -> list[float]: ...


class VoyageEmbedder:
    """Embedder backed by Voyage AI's hosted embeddings API (ADR-0005).

    Voyage was picked for its documented free tier (200M tokens/account,
    no monthly call cap), since Vercel's 500MB Python function bundle
    limit rules out shipping the in-process model ADR-0003 used.
    """

    dimensions = 1024
    # Carried over from the local MiniLM model (#12); Voyage's score
    # distribution hasn't been validated against it yet, so this needs
    # re-tuning once eval can run against the real API.
    match_threshold = 0.45

    def __init__(self, client: httpx.Client, model: str) -> None:
        self._client = client
        self.model = model

    def embed(self, text: str) -> list[float]:
        response = self._client.post("/embeddings", json={"model": self.model, "input": [text]})
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]


def embedder_from_env() -> Embedder:
    """Builds a VoyageEmbedder from VOYAGE_API_KEY."""
    api_key = os.environ["VOYAGE_API_KEY"]
    client = httpx.Client(
        base_url="https://api.voyageai.com/v1",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    return VoyageEmbedder(client, model=DEFAULT_VOYAGE_MODEL)
