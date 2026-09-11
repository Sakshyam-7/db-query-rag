"""
Chat orchestration service.
"""
import logging

from sqlalchemy.orm import Session

from app.llm.base import LLMProvider
from app.llm.classify import QuestionType
from app.llm.sematic_router import classify_question_hybrid
from app.llm.text_to_sql import SQLExecutionError, UnsafeSQLError, generate_sql, run_readonly_query
from app.models.user import User

logger = logging.getLogger(__name__)

DATA_ANSWER_SYSTEM_PROMPT = """You are a helpful project/ticket tracking assistant.
Answer the user's question using ONLY the data provided below.
The SQL query that was run is shown so you understand exactly what the
results represent -- use it to correctly interpret column names like
generic "count" values.
If the data doesn't contain the answer, say so plainly -- do not guess
or invent facts. Keep the answer concise and in plain language. Never
mention SQL, queries, or databases in your answer -- just answer
naturally, as if you already knew the information.
"""

SMALL_TALK_SYSTEM_PROMPT = """You are a friendly assistant for a project/ticket
tracking application. The user is making small talk (greeting, thanks,
farewell). Respond naturally and warmly, very briefly. You may mention
you're able to answer questions about their projects and tickets, but
don't force it into every response.
"""

OFF_TOPIC_RESPONSE = (
    "I'm only able to help with questions about your projects and "
    "tickets (or a quick hello!) -- I can't help with general "
    "questions, writing, or code outside of that. What would you like "
    "to know about your projects or tickets?"
)


async def answer_chat_message(
    message: str,
    current_user: User,
    readonly_db: Session,
    llm: LLMProvider,
) -> str:
    route = await classify_question_hybrid(message, llm)
    logger.info(f"Classified question as: {route.value}")

    if route == QuestionType.OFF_TOPIC:
        return OFF_TOPIC_RESPONSE

    if route == QuestionType.SMALL_TALK:
        return await llm.generate(prompt=message, system=SMALL_TALK_SYSTEM_PROMPT)

    results = []
    executed_sql = None

    if route in (QuestionType.STRUCTURED, QuestionType.HYBRID):
        try:
            executed_sql = await generate_sql(
                question=message,
                user_id=current_user.id,
                role=current_user.role,
                llm=llm,
            )
            logger.info(f"Generated SQL: {executed_sql}")
            results = run_readonly_query(readonly_db, executed_sql)
            logger.info(f"Query results: {results}")
        except UnsafeSQLError as e:
            logger.warning(f"SQL validation rejected: {e}")
        except SQLExecutionError as e:
            logger.warning(f"SQL execution failed: {e}")

    if route in (QuestionType.SEMANTIC, QuestionType.HYBRID):
        logger.info("Semantic search requested but not yet implemented -- skipping")

    if results and executed_sql:
        context_block = f"SQL query that was run:\n{executed_sql}\n\nQuery results:\n{results}"
    else:
        context_block = "No matching data was found."

    prompt = f"Question: {message}\n\nData:\n{context_block}"

    return await llm.generate(prompt=prompt, system=DATA_ANSWER_SYSTEM_PROMPT)