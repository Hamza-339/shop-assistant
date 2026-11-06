import math

from app.claude_client import ClaudeClient
from app.embeddings import LocalEmbedder
from app.models import AnswerResult, Citation
from app.store import StoreEntry, VectorStore

NO_GROUNDED_ANSWER = "I don't have information to answer that."
MATCH_THRESHOLD = 0.3


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def answer_question(
    question: str, store: VectorStore, embedder: LocalEmbedder, claude_client: ClaudeClient
) -> AnswerResult:
    entries = store.entries
    question_embedding = embedder.embed(question)

    best_entry: StoreEntry | None = None
    best_score = 0.0
    for entry in entries:
        score = _cosine_similarity(question_embedding, entry.embedding)
        if score > best_score:
            best_score = score
            best_entry = entry

    if best_entry is None or best_score < MATCH_THRESHOLD:
        return AnswerResult(answer=NO_GROUNDED_ANSWER, citations=[])

    answer = claude_client.generate_answer(question, [best_entry])
    return AnswerResult(answer=answer, citations=[Citation(id=best_entry.id, kind=best_entry.kind)])
