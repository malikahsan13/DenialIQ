import os
import sqlite3
from typing import TypedDict, Optional, List
from dotenv import load_dotenv
from groq import Groq
from langgraph.graph import StateGraph, END

# =====================================================
# ENV
# =====================================================
load_dotenv()

DB_PATH = os.getenv("SQLITE_DB_PATH", "claims.db")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

client = Groq(api_key=GROQ_API_KEY)

# =====================================================
# SCHEMA
# =====================================================
SCHEMA = """
Table: claims
Columns:
- claim_number (TEXT)
- patient_name (TEXT)
- cpt_code (TEXT)
- status (TEXT)
- billed_amount (REAL)
- allowed_amount (REAL)
- denied_amount (REAL)
- denial_code (TEXT)
- adjustment_code (TEXT)
- adjustment_amount (REAL)
- patient_responsibility (REAL)
- payer_name (TEXT)
- service_date (TEXT)
"""

# =====================================================
# STATE
# =====================================================
class SQLState(TypedDict):
    question: str
    sql: Optional[str]
    result: Optional[List]
    answer: Optional[str]
    error: Optional[str]
    attempts: int

# =====================================================
# NODE 1: CHECK RELEVANCE
# =====================================================
def check_relevance(state: SQLState):
    keywords = [
        "claim", "claims", "cpt", "status", "amount", "record", "top", "list",
        "show", "denial", "denied", "denial code", "denial amount",
        "adjustment", "adjustment code", "adjustment amount", "patient responsibility",
        "allowed amount", "payer", "service date"
    ]
    if any(k in state["question"].lower() for k in keywords):
        return state
    return {**state, "answer": "This question is not related to claim data."}

# =====================================================
# NODE 2: NL → SQL
# =====================================================
def nl_to_sql(state: SQLState):
    prompt = f"""
You are a SQLite expert.

Rules:
- Output ONLY a SQLite SELECT query
- NEVER use SELECT *
- Always include these columns if available:
  claim_number, patient_name, cpt_code, status, billed_amount,
  allowed_amount, denied_amount, denial_code, adjustment_code,
  adjustment_amount, patient_responsibility, payer_name, service_date
- Include LIMIT if user asks for "top", "latest", or "recent"
- Filter by specific claim if mentioned (e.g., CLM-3149)
- Ensure columns related to denial or adjustment are included if user mentions them

Schema:
{SCHEMA}

Question:
{state["question"]}

SQL:
"""
    res = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    return {**state, "sql": res.choices[0].message.content.strip()}

# =====================================================
# NODE 3: EXECUTE SQL
# =====================================================
def execute_sql(state: SQLState):
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(state["sql"])
        rows = cur.fetchall()
        conn.close()

        if not rows:
            return {**state, "error": "No results"}

        return {**state, "result": rows, "error": None}

    except Exception as e:
        return {**state, "error": str(e)}

# =====================================================
# NODE 4: RETRY (LIMITED)
# =====================================================
def retry_sql(state: SQLState):
    if state["attempts"] >= 2:
        return {**state, "answer": "Unable to retrieve records.", "error": None}

    repair_prompt = f"""
Fix this SQLite query.

Query:
{state["sql"]}

Error:
{state["error"]}

Schema:
{SCHEMA}

Return ONLY corrected SQL:
"""

    res = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": repair_prompt}],
        temperature=0,
    )

    return {
        **state,
        "sql": res.choices[0].message.content.strip(),
        "attempts": state["attempts"] + 1,
        "error": None,
    }

# =====================================================
# NODE 5: HUMAN ANSWER (PROPER TABLE FORMAT, SAFE)
# =====================================================
def format_answer(state: SQLState):
    rows = state.get("result", [])[:5]

    if not rows:
        return {**state, "answer": "No records found."}

    lines = []

    # Header
    header = (
        "Claim | Patient | CPT | Status | "
        "Billed | Allowed | Denied | Denial Code | Adjustment Code | "
        "Adjustment Amt | Patient Resp"
    )
    lines.append(header)
    lines.append("-" * len(header))

    # Rows
    for r in rows:
        # Safely unpack values with defaults
        claim = r[0] or "-"
        patient = r[1] or "-"
        cpt = r[2] or "-"
        status = r[3] or "-"
        billed = r[4] if r[4] is not None else 0.0
        allowed = r[5] if r[5] is not None else 0.0
        denied = r[6] if r[6] is not None else 0.0
        denial_code = r[7] or "-"
        adjustment_code = r[8] or "-"
        adjustment_amt = r[9] if r[9] is not None else 0.0
        patient_resp = r[10] if r[10] is not None else 0.0

        line = (
            f"{claim} | {patient} | {cpt} | {status} | "
            f"${billed:.2f} | ${allowed:.2f} | ${denied:.2f} | "
            f"{denial_code} | {adjustment_code} | "
            f"${adjustment_amt:.2f} | ${patient_resp:.2f}"
        )
        lines.append(line)

    return {**state, "answer": "\n".join(lines)}


# =====================================================
# NODE 6: FALLBACK
# =====================================================
def fallback(state: SQLState):
    return {**state, "answer": "Unable to process the query."}

# =====================================================
# ROUTING FUNCTIONS
# =====================================================
def route_after_execute(state: SQLState):
    if state.get("error") and state["attempts"] < 2:
        return "retry"
    elif state.get("error"):
        return "fallback"
    return "answer"

def route_after_relevance(state: SQLState):
    if state.get("answer"):
        return "end"
    return "continue"

# =====================================================
# GRAPH DEFINITION
# =====================================================
g = StateGraph(SQLState)

g.add_node("check", check_relevance)
g.add_node("nl_to_sql", nl_to_sql)
g.add_node("execute", execute_sql)
g.add_node("retry", retry_sql)
g.add_node("answer", format_answer)
g.add_node("fallback", fallback)

g.set_entry_point("check")

g.add_conditional_edges(
    "check",
    route_after_relevance,
    {
        "continue": "nl_to_sql",
        "end": END,
    },
)

g.add_edge("nl_to_sql", "execute")

g.add_conditional_edges(
    "execute",
    route_after_execute,
    {
        "retry": "retry",
        "answer": "answer",
        "fallback": "fallback",
    }
)

g.add_edge("retry", "execute")
g.add_edge("answer", END)
g.add_edge("fallback", END)

sql_agent = g.compile()

# =====================================================
# PUBLIC API
# =====================================================
def run_sql_agent(question: str):
    state = {
        "question": question,
        "sql": None,
        "result": None,
        "answer": None,
        "error": None,
        "attempts": 0,
    }
    final = sql_agent.invoke(state, config={"recursion_limit": 15})
    return final.get("answer", "Unable to answer the question.")
