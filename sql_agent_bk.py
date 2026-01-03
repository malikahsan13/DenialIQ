import sqlite3

DB_PATH = "claims.db"


def run_sql_agent(question: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    q = question.lower()

    # ---- simple deterministic routing ----
    if "claim" in q or "status" in q:
        cursor.execute("""
            SELECT claim_number, status, amount
            FROM claims
            WHERE cpt_code = '99213'
            LIMIT 1
        """)
        row = cursor.fetchone()
        conn.close()

        if row:
            return (
                f"Claim {row[0]} has status {row[1]} "
                f"with billed amount ${row[2]}."
            )

    conn.close()
    return "No claim information found in the database."
