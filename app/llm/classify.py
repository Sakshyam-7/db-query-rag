"""
Question classification for the chat pipeline.
"""
from enum import Enum

from app.llm.base import LLMProvider

CLASSIFY_SYSTEM_PROMPT = """You classify user messages sent to a project/ticket tracking assistant.

Return ONLY one of these exact words, nothing else -- no explanation,
no punctuation, no extra text:

structured  -- answerable from structured fields: counts, filters, or
               lookups on status, priority, ownership, dates, names.
               e.g. "how many projects do I own", "list my open tickets"

semantic    -- answerable only by understanding free-text content
               (project/ticket descriptions), not by filtering fields.
               e.g. "which project mentions authentication issues"

hybrid      -- needs both a structured filter AND understanding free
               text. e.g. "which HIGH priority tickets mention a
               database timeout"

small_talk  -- greetings, thanks, farewells, or brief pleasantries
               directed at the assistant itself.
               e.g. "hi", "how are you", "thanks", "bye", "who are you"

off_topic   -- ANYTHING else: general knowledge questions, requests for
               code, explanations of concepts, writing tasks, or any
               topic not about the user's own projects/tickets or
               simple pleasantries. e.g. "what is AI", "write me a
               poem", "give me python code", "who is the president",
               "explain machine learning"

If genuinely unsure between structured/semantic/hybrid, default to
structured. If the message is not clearly small_talk, use off_topic.
"""


class QuestionType(str, Enum):
    STRUCTURED = "structured"
    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    SMALL_TALK = "small_talk"
    OFF_TOPIC = "off_topic"


async def classify_question(question: str, llm: LLMProvider) -> QuestionType:
    raw = await llm.generate(prompt=question, system=CLASSIFY_SYSTEM_PROMPT)
    cleaned = raw.strip().lower()

    try:
        return QuestionType(cleaned)
    except ValueError:
        return QuestionType.STRUCTURED