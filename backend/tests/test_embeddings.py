import math

from app.embeddings import LocalEmbedder


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b)


def test_embed_scores_shared_meaning_higher_than_unrelated_text():
    embedder = LocalEmbedder()

    product_text = "Classic Cotton T-Shirt breathable cotton t-shirt sizes S-XL"
    question_embedding = embedder.embed("Tell me about the Classic Cotton T-Shirt")
    matching_embedding = embedder.embed(product_text)
    unrelated_embedding = embedder.embed("Items may be returned within 30 days of delivery for a full refund")

    matching_score = _cosine_similarity(question_embedding, matching_embedding)
    unrelated_score = _cosine_similarity(question_embedding, unrelated_embedding)

    assert matching_score - unrelated_score > 0.2


def test_embed_scores_shared_meaning_higher_than_unrelated_text_for_a_policy_question():
    embedder = LocalEmbedder()

    policy_text = "refund Items may be returned within 30 days of delivery for a full refund"
    question_embedding = embedder.embed("What is the refund policy?")
    matching_embedding = embedder.embed(policy_text)
    unrelated_embedding = embedder.embed("Classic Cotton T-Shirt breathable cotton t-shirt sizes S-XL")

    matching_score = _cosine_similarity(question_embedding, matching_embedding)
    unrelated_score = _cosine_similarity(question_embedding, unrelated_embedding)

    assert matching_score - unrelated_score > 0.2
