from dataclasses import dataclass


@dataclass(frozen=True)
class StoreEntry:
    id: str
    kind: str
    text: str
    embedding: list[float]


class VectorStore:
    """In-process vector store. Sync always wipes before re-embedding (ADR-0002)."""

    def __init__(self) -> None:
        self._entries: list[StoreEntry] = []

    def wipe(self) -> None:
        self._entries = []

    def add(self, entry: StoreEntry) -> None:
        self._entries.append(entry)

    @property
    def entries(self) -> list[StoreEntry]:
        return list(self._entries)
