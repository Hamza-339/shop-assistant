from sentence_transformers import SentenceTransformer

_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class LocalEmbedder:
    """Small CPU-capable model running in-process (per ADR-0003).

    No external call is made at embed time; model weights are downloaded
    once on first use and cached on disk, a one-time deviation from
    ADR-0003's "no external dependency" framing that the ADR anticipated
    ("swapping in a higher-quality local model later is a drop-in
    replacement"). Each instantiation still loads those cached weights into
    memory, so construct one LocalEmbedder and reuse it rather than
    constructing it per call. Swapping in a different local model later is a
    drop-in replacement since sync is always a full re-embed (per ADR-0002).
    """

    dimensions = 384
    # Picked from real cosine scores: unrelated text scores up to ~0.39,
    # genuine matches score 0.58+ (per #12).
    match_threshold = 0.45

    def __init__(self) -> None:
        self._model = SentenceTransformer(_MODEL_NAME)

    def embed(self, text: str) -> list[float]:
        return self._model.encode(text).tolist()
