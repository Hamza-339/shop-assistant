import os
import time
from typing import Callable, Protocol

import httpx

DEFAULT_VOYAGE_MODEL = "voyage-4-lite"

# Voyage accounts with no payment method on file get "reduced rate limits of
# 3 RPM and 10K TPM" (from their own 429 body - not documented on their
# pricing page, only discovered by calling the live API). 21s keeps every
# request outside that 3-per-60s window; 65s/3 retries is a safety net for
# when pacing alone isn't enough (e.g. the window hasn't fully reset yet).
DEFAULT_MIN_INTERVAL_SECONDS = 21.0
DEFAULT_RETRY_BACKOFF_SECONDS = 65.0
DEFAULT_MAX_RETRIES = 3


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
    # Voyage's cosine scores run higher than the old local MiniLM model's
    # (#12's 0.45 let an unrelated "size guide" question match a product at
    # 0.56 - a real false-positive caught by
    # test_answer_question_does_not_fabricate_an_answer_for_a_page_shaped_question_against_the_real_embedder).
    # Measured against the real API: genuine matches score ~0.71, that
    # mismatch scored ~0.56, so 0.65 sits safely between them.
    match_threshold = 0.65

    def __init__(
        self,
        client: httpx.Client,
        model: str,
        min_interval_seconds: float = DEFAULT_MIN_INTERVAL_SECONDS,
        retry_backoff_seconds: float = DEFAULT_RETRY_BACKOFF_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._client = client
        self.model = model
        self._min_interval_seconds = min_interval_seconds
        self._retry_backoff_seconds = retry_backoff_seconds
        self._max_retries = max_retries
        self._clock = clock
        self._sleep = sleep
        self._last_request_at: float | None = None

    def embed(self, text: str) -> list[float]:
        self._wait_for_pacing()
        response = self._post_with_retry(text)
        return response.json()["data"][0]["embedding"]

    def _wait_for_pacing(self) -> None:
        if self._last_request_at is not None:
            elapsed = self._clock() - self._last_request_at
            remaining = self._min_interval_seconds - elapsed
            if remaining > 0:
                self._sleep(remaining)
        self._last_request_at = self._clock()

    def _post_with_retry(self, text: str) -> httpx.Response:
        for attempt in range(self._max_retries + 1):
            response = self._client.post("/embeddings", json={"model": self.model, "input": [text]})
            if response.status_code != 429 or attempt == self._max_retries:
                response.raise_for_status()
                return response
            self._sleep(self._retry_backoff_seconds)


def embedder_from_env() -> Embedder:
    """Builds a VoyageEmbedder from VOYAGE_API_KEY."""
    api_key = os.environ["VOYAGE_API_KEY"]
    client = httpx.Client(
        base_url="https://api.voyageai.com/v1",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    return VoyageEmbedder(client, model=DEFAULT_VOYAGE_MODEL)
