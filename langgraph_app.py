from langgraph.graph import StateGraph, END
from typing import TypedDict
from groq import Groq

from rag_retrieval import rag_pipeline, generate_answer   # reuse your code
from sql_agent import run_sql_agent                        # defined below

groq_client = Groq()

# -------- STATE --------
class GraphState(TypedDict):
    question: str
    route: str
    context: str
    answer: str


# -------- ROUTER NODE --------
def route_question(state: GraphState):
    question = state["question"].lower()

    if any(k in question for k in ["claim", "patient", "member", "amount"]):
        return {"route": "sql"}
    else:
        return {"route": "rag"}


# -------- RAG NODE --------
def rag_node(state: GraphState):
    context = rag_pipeline(state["question"])
    answer = generate_answer(state["question"], context)

    return {
        "context": context,
        "answer": answer
    }


# -------- SQL NODE --------
def sql_node(state: GraphState):
    result = run_sql_agent(state["question"])

    return {
        "context": result,
        "answer": result
    }


# -------- GRAPH --------
workflow = StateGraph(GraphState)

workflow.add_node("router", route_question)
workflow.add_node("rag", rag_node)
workflow.add_node("sql", sql_node)

workflow.set_entry_point("router")

workflow.add_conditional_edges(
    "router",
    lambda x: x["route"],
    {
        "rag": "rag",
        "sql": "sql"
    }
)

workflow.add_edge("rag", END)
workflow.add_edge("sql", END)

app = workflow.compile()
