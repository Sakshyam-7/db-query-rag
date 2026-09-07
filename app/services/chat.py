"""
Chat orchestration service.

Phase 1 (this file, current state): text-to-SQL only. Every question is
treated as a structured-data question and answered via generated SQL
against projects/tickets, scoped to the current user.

Phase 2 (later): add a classify step to route between SQL and pgvector
semantic search, and a "hybrid" path that uses both.
"""
from sqlalchemy.orm import Session

from app.llm.base import LLMProvider
from app.llm.text_to_sql import UnsafeSQLError, generate_sql, run_readonly_query
from app.models.user import User

ANSWER_SYSTEM_PROMPT = """You are a helpful project/ticket tracking assistant.
Answer the user's question using ONLY the data provided below.
If the data doesn't contain the answer, say so plainly -- do not guess
or invent facts. Keep the answer concise and in plain language.
"""


async def answer_chat_message(
    message: str,
    current_user: User,
    readonly_db: Session,
    llm: LLMProvider,
) -> str:
    """
    Orchestrates: generate scoped SQL -> run it read-only -> ask the LLM
    to phrase a plain-language answer from the results.
    """
    try:
        sql = await generate_sql(
            question=message,
            user_id=current_user.id,
            role=current_user.role,
            llm=llm,
        )
        results = run_readonly_query(readonly_db, sql)
    except UnsafeSQLError:
        # Don't fail the whole request -- fall through with no data;
        # the answer prompt below is instructed not to guess when data
        # is missing, so this degrades gracefully instead of leaking
        # anything or crashing.
        results = []

    context_block = f"Query results:\n{results}" if results else "No matching data was found."
    prompt = f"Question: {message}\n\nData:\n{context_block}"

    return await llm.generate(prompt=prompt, system=ANSWER_SYSTEM_PROMPT)