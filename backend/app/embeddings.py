from sentence_transformers import SentenceTransformer

_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class LocalEmbedder:
    """Small CPU-capable model running in-process (per ADR-0003).

    No external call is made at embed time; the model weights are fetched
    once and cached locally. Swapping in a different local model later is a
    drop-in replacement since sync is always a full re-embed (per ADR-0002).
    """

    dimensions = 384

    def __init__(self) -> None:
        self._model = SentenceTransformer(_MODEL_NAME)

    def embed(self, text: str) -> list[float]:
        return self._model.encode(text).tolist()
