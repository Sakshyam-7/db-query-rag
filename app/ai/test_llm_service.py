from app.ai.llm import generate_response


prompt = """
Explain what a PostgreSQL database is in two sentences.
"""

response = generate_response(prompt)
print(response)