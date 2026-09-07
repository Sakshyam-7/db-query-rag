"""
Text-to-SQL generation with guardrails, scoped to the current user.

SECURITY NOTES (read before modifying):
- The `users` table is NEVER described to the LLM and NEVER queryable --
  this prevents any possibility of leaking password_hash or other users'
  emails, regardless of what SQL the LLM generates.
- Only `projects` and `tickets` are queryable.
- Non-admin users' queries must be scoped to their own data. We enforce
  this two ways: (1) instructing the LLM in the system prompt with the
  user's actual ID, and (2) checking the generated SQL literally contains
  that ID before executing it, for non-admins. This is a safety net, NOT
  a guarantee -- see the table-allowlist and scoping check below for
  their limitation.
- All queries run through a READ-ONLY database connection (see
  database.py's get_readonly_db) as defense in depth, independent of
  these checks.
"""
import re
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.llm.base import LLMProvider
from app.models.user import UserRole

ALLOWED_TABLES = {"projects", "tickets"}

SCHEMA_DESCRIPTION = """
Tables you may query (nothing else exists as far as you know):

- projects(id, owner_id, name, description, status, created_at, updated_at)
  status is one of: 'active', 'completed', 'on_hold'

- tickets(id, project_id, user_id, title, description, status, priority, created_at, updated_at)
  status is one of: 'open', 'in_progress', 'resolved', 'closed'
  priority is one of: 'low', 'medium', 'high', 'critical'

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


_FORBIDDEN_KEYWORDS = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|grant|revoke|create)\b",
    re.IGNORECASE,
)


def _validate_sql(sql: str, user_id: UUID, role: UserRole) -> str:
    sql = sql.strip().strip(";")

    if not sql.lower().startswith("select"):
        raise UnsafeSQLError("Generated query is not a SELECT statement")

    if _FORBIDDEN_KEYWORDS.search(sql):
        raise UnsafeSQLError("Generated query contains a forbidden keyword")

    if ";" in sql:
        raise UnsafeSQLError("Generated query contains multiple statements")

    # Table allowlist -- reject anything referencing a table we didn't
    # describe (most importantly: the users table must never appear).
    referenced_tables = set(re.findall(r"\bfrom\s+(\w+)|\bjoin\s+(\w+)", sql, re.IGNORECASE))
    referenced_tables = {t for pair in referenced_tables for t in pair if t}
    disallowed = referenced_tables - ALLOWED_TABLES
    if disallowed:
        raise UnsafeSQLError(f"Query references disallowed table(s): {disallowed}")

    # Non-admin scoping check -- crude but meaningful safety net. Not a
    # guarantee: this is a text check, not a real access-control
    # mechanism. See module docstring.
    if role != UserRole.ADMIN and str(user_id) not in sql:
        raise UnsafeSQLError(
            "Generated query does not appear to be scoped to the current user"
        )

    return sql


async def generate_sql(question: str, user_id: UUID, role: UserRole, llm: LLMProvider) -> str:
    system_prompt = _build_system_prompt(user_id, role)
    raw_sql = await llm.generate(prompt=question, system=system_prompt)
    return _validate_sql(raw_sql, user_id, role)


def run_readonly_query(db: Session, sql: str) -> list[dict]:
    """
    Executes on a session bound to the read-only engine (get_readonly_db
    in database.py), which also has a statement timeout set.
    """
    result = db.execute(text(sql))
    columns = result.keys()
    return [dict(zip(columns, row)) for row in result.fetchall()]