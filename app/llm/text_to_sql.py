from uuid import UUID

import sqlglot
from sqlglot import exp
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.llm.base import LLMProvider
from app.models.user import UserRole

ALLOWED_TABLES = {"projects", "tickets"}

SCHEMA_DESCRIPTION = """
Tables you may query (nothing else exists as far as you know):

- projects(id, owner_id, name, description, status, created_at, updated_at)
  status is one of: 'ACTIVE', 'COMPLETED', 'ON_HOLD'

- tickets(id, project_id, user_id, title, description, status, priority, created_at, updated_at)
  status is one of: 'OPEN', 'IN_PROGRESS', 'RESOLVED', 'CLOSED'
  priority is one of: 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'

Rules:
- Only SELECT queries. Never INSERT/UPDATE/DELETE/DROP/ALTER/etc.
- Never reference any table other than projects and tickets.
- Always use explicit column names, never SELECT *.
- Limit results to 50 rows unless the question clearly needs fewer.
- Return ONLY the raw SQL. No explanation, no markdown fences, no
  trailing semicolon, no multiple statements.
"""


class UnsafeSQLError(Exception):
    """Raised when generated SQL fails a safety check and must not run."""
    pass


class SQLExecutionError(Exception):
    """Raised when generated SQL passed validation but Postgres itself
    rejected it at execution time."""
    pass


def _build_system_prompt(user_id: UUID, role: UserRole) -> str:
    if role == UserRole.ADMIN:
        scoping_rule = (
            "This user is an ADMIN. They may query across all projects and "
            "tickets, no ownership filter is required."
        )
    else:
        scoping_rule = (
            f"This user is a regular MEMBER with id '{user_id}'. "
            f"You MUST always filter results to only rows they own: "
            f"for projects, include `owner_id = '{user_id}'`; "
            f"for tickets, include `user_id = '{user_id}'` "
            f"(or filter tickets via a project they own). "
            f"Never return another user's data."
        )
    return f"{SCHEMA_DESCRIPTION}\n{scoping_rule}"


def _validate_sql(sql: str, user_id: UUID, role: UserRole) -> str:
    sql = sql.strip().strip(";")

    try:
        parsed = sqlglot.parse_one(sql, read="postgres")
    except Exception as e:
        raise UnsafeSQLError(f"Generated SQL could not be parsed: {e}")

    if parsed is None:
        raise UnsafeSQLError("Generated SQL is empty or could not be parsed")

    # Must be a SELECT at the top level -- catches INSERT/UPDATE/DELETE/
    # DROP/ALTER/etc. by actual statement TYPE, not by keyword text
    # matching, so it can't be fooled by comments or string literals.
    if not isinstance(parsed, exp.Select):
        raise UnsafeSQLError(
            f"Generated SQL is not a SELECT statement (got {type(parsed).__name__})"
        )

    # Walk the ENTIRE tree (including subqueries, CTEs, joins) for every
    # table reference, and for any disallowed statement type nested
    # anywhere (e.g. a CTE containing something other than SELECT).
    referenced_tables = {
        table.name.lower() for table in parsed.find_all(exp.Table)
    }
    disallowed_tables = referenced_tables - ALLOWED_TABLES
    if disallowed_tables:
        raise UnsafeSQLError(f"Query references disallowed table(s): {disallowed_tables}")

    disallowed_statement_types = (
        exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Alter,
        exp.Create, exp.TruncateTable, exp.Grant,
    )
    for node in parsed.walk():
        if isinstance(node[0], disallowed_statement_types):
            raise UnsafeSQLError(
                f"Query contains a disallowed statement type: {type(node[0]).__name__}"
            )

    rendered_sql = parsed.sql(dialect="postgres")
    if role != UserRole.ADMIN and str(user_id) not in rendered_sql:
        raise UnsafeSQLError(
            "Generated query does not appear to be scoped to the current user"
        )

    return rendered_sql


async def generate_sql(question: str, user_id: UUID, role: UserRole, llm: LLMProvider) -> str:
    system_prompt = _build_system_prompt(user_id, role)
    raw_sql = await llm.generate(prompt=question, system=system_prompt)
    return _validate_sql(raw_sql, user_id, role)


def run_readonly_query(db: Session, sql: str) -> list[dict]:
    try:
        result = db.execute(text(sql))
        columns = result.keys()
        return [dict(zip(columns, row)) for row in result.fetchall()]
    except SQLAlchemyError as e:
        db.rollback()
        raise SQLExecutionError("Generated query failed to execute") from e