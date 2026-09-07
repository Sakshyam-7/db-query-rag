import requests


url = "http://localhost:11434/api/generate"

schema = """
Database: PostgreSQL

Table: users
- id: UUID, primary key
- name: VARCHAR
- email: VARCHAR, unique
- password_hash: VARCHAR
- role: ENUM (ADMIN, MEMBER, VIEWER)
- created_at: TIMESTAMP

Table: projects
- id: UUID, primary key
- name: VARCHAR
- description: TEXT
- owner_id: UUID, foreign key → users.id
- status: ENUM (ACTIVE, COMPLETED, ON_HOLD)
- created_at: TIMESTAMP

Table: tickets
- id: UUID, primary key
- title: VARCHAR
- description: TEXT
- project_id: UUID, foreign key → projects.id
- user_id: UUID, foreign key → users.id
- priority: ENUM (LOW, MEDIUM, HIGH)
- status: ENUM (OPEN, IN_PROGRESS, RESOLVED, CLOSED)
- created_at: TIMESTAMP
"""

question = "How many projects are there in the database?"

prompt = f"""
You are a PostgreSQL database assistant.

Here is the database schema:

{schema}

User question:
{question}

Determine which table and columns are needed to answer the question.

Return ONLY the SQL query.
"""

payload = {
    "model": "qwen2.5",
    "prompt": prompt,
    "stream": False,
}

response = requests.post(url, json=payload)

response.raise_for_status()

result = response.json()

print(result["response"])