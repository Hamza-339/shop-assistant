import math

from app.claude_client import ClaudeClient
from app.embeddings import LocalEmbedder
from app.models import AnswerResult, Citation
from app.store import StoreEntry, VectorStore

NO_GROUNDED_ANSWER = "I don't have information to answer that."
DEFLECTION_MESSAGE = "I'm not able to help with that here, but our support team can."

# Policies are a small, closed set (refund/privacy/shipping/terms), so a weaker
# cosine score is still trustworthy evidence of the right match - unlike
# products, where a weak score more often means no real match exists (#21).
POLICY_MATCH_THRESHOLD = 0.2

DEFLECTED_KEYWORDS = {"order", "payment", "stock", "inventory", "discount", "coupon", "promo"}
GROUNDED_OVERRIDE_KEYWORDS = {"policy"}


def _singularize(word: str) -> str:
    return word[:-1] if word.endswith("s") and len(word) > 1 else word


def _is_deflected_topic(question: str) -> bool:
    words = {word.strip("?,.#'") for word in question.lower().split()}
    if words & GROUNDED_OVERRIDE_KEYWORDS:
        return False
    stems = {_singularize(word) for word in words}
    return bool(stems & DEFLECTED_KEYWORDS)


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
    if _is_deflected_topic(question):
        return AnswerResult(answer=DEFLECTION_MESSAGE, citations=[], deflected=True)

    entries = store.entries
    question_embedding = embedder.embed(question)

    best_entry: StoreEntry | None = None
    best_score = 0.0
    for entry in entries:
        score = _cosine_similarity(question_embedding, entry.embedding)
        if score > best_score:
            best_score = score
            best_entry = entry

    if best_entry is None:
        return AnswerResult(answer=NO_GROUNDED_ANSWER, citations=[])

    threshold = POLICY_MATCH_THRESHOLD if best_entry.kind == "policy" else embedder.match_threshold
    if best_score < threshold:
        return AnswerResult(answer=NO_GROUNDED_ANSWER, citations=[])

    answer = claude_client.generate_answer(question, [best_entry])
    citation = Citation(id=best_entry.id, kind=best_entry.kind, handle=best_entry.handle)
    return AnswerResult(answer=answer, citations=[citation])
