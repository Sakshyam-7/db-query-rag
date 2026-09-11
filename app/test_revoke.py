"""
Run this on your machine (adjust the connection string to match your
readonly_user credentials) to directly confirm the DB-level permission
backstop works -- independent of any Python validation logic.
"""
import psycopg

# Adjust to match your actual readonly_user / password / db name
conn_string = "postgresql://readonly_user:readonly_pass@localhost:5432/tecky_ai"

with psycopg.connect(conn_string) as conn:
    with conn.cursor() as cur:
        # This should succeed -- readonly_user has SELECT on projects
        try:
            cur.execute("SELECT id, name FROM projects LIMIT 1")
            print("✓ SELECT on 'projects' succeeded (expected)")
        except Exception as e:
            print(f"✗ SELECT on 'projects' FAILED unexpectedly: {e}")

        conn.rollback()  # clear any failed-transaction state before next test

        # This should FAIL with a permission error -- confirms the revoke worked
        try:
            cur.execute("SELECT email, password_hash FROM users LIMIT 1")
            print("✗ SELECT on 'users' SUCCEEDED -- REVOKE did not work, this is a real problem!")
        except Exception as e:
            print(f"✓ SELECT on 'users' correctly BLOCKED: {e}")