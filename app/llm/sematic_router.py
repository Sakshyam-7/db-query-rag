"""
Semantic routing: fast local classification via embedding similarity,
falling back to an LLM call (classify_question) only when the local
match is ambiguous.

Uses sentence-transformers' all-MiniLM-L6-v2 (small, CPU-only) to embed
the incoming question and compare it against example phrases per
category. If the best match is confident enough (score >= threshold),
that category is returned immediately -- no LLM call, no network
request, no load on your GPU. Only genuinely ambiguous questions fall
through to the existing LLM-based classify_question.
"""
import logging

from sentence_transformers import SentenceTransformer, util

from app.llm.base import LLMProvider
from app.llm.classify import QuestionType, classify_question

logger = logging.getLogger(__name__)

_encoder: SentenceTransformer | None = None
_route_embeddings = None

ROUTE_SAMPLES: dict[QuestionType, list[str]] = {
    QuestionType.STRUCTURED: [
        "how many projects do I own",
        "list my open tickets",
        "how many tickets are HIGH priority",
        "show projects with status COMPLETED",
        "count of tickets assigned to me",
        "how many projects are ON_HOLD",
    ],
    QuestionType.SEMANTIC: [
        "which project mentions authentication issues",
        "find tickets about login problems",
        "what project talks about database performance",
        "search descriptions for payment bugs",
    ],
    QuestionType.HYBRID: [
        "which HIGH priority tickets mention a database timeout",
        "find my open tickets about login issues",
        "show COMPLETED projects that mention a redesign",
    ],
    QuestionType.SMALL_TALK: [
        "hello",
        "hi there",
        "how are you",
        "thank you",
        "goodbye",
    ],
    QuestionType.OFF_TOPIC: [
        "what can you do",
        "tell me a joke",
        "who are you",
        "what is AI",
        "explain machine learning",
    ],
}

DEFAULT_THRESHOLD = 0.55


def _get_encoder() -> SentenceTransformer:
    global _encoder
    if _encoder is None:
        logger.info("Loading local embedding model (all-MiniLM-L6-v2)...")
        _encoder = SentenceTransformer("all-MiniLM-L6-v2")
    return _encoder


def _get_route_embeddings():
    global _route_embeddings
    if _route_embeddings is None:
        encoder = _get_encoder()
        _route_embeddings = {
            category: encoder.encode(samples, convert_to_tensor=True)
            for category, samples in ROUTE_SAMPLES.items()
        }
    return _route_embeddings


def _local_classify(question: str, threshold: float) -> tuple[QuestionType | None, float]:
    encoder = _get_encoder()
    route_embeddings = _get_route_embeddings()

    question_vec = encoder.encode(question, convert_to_tensor=True)

    best_category = None
    highest_score = -1.0
    for category, sample_vectors in route_embeddings.items():
        similarities = util.cos_sim(question_vec, sample_vectors)[0]
        max_sim = similarities.max().item()
        if max_sim > highest_score:
            highest_score = max_sim
            best_category = category

    if highest_score >= threshold:
        return best_category, highest_score
    return None, highest_score


async def classify_question_hybrid(
    question: str,
    llm: LLMProvider,
    threshold: float = DEFAULT_THRESHOLD,
) -> QuestionType:
    """
    Stage 1: local embedding similarity (fast, free, CPU-only, no LLM call).
    Stage 2: LLM fallback (classify_question) only if Stage 1 is unsure.
    """
    category, score = _local_classify(question, threshold)

    if category is not None:
        logger.info(f"Semantic router matched '{question}' -> {category.value} (score={score:.2f})")
        return category

    logger.info(f"Semantic router unsure (best score={score:.2f}) -- falling back to LLM classify")
    return await classify_question(question, llm)