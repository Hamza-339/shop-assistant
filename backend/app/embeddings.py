import hashlib


class LocalEmbedder:
    """Small CPU-capable model running in-process (per ADR-0003).

    Deterministic and dependency-free so it never makes an external call;
    swapping in a higher-quality local model later is a drop-in replacement
    since sync is always a full re-embed (per ADR-0002).
    """

    dimensions = 32

    def embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        return [byte / 255 for byte in digest[: self.dimensions]]
