import os
from dotenv import load_dotenv
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from groq import Groq

# ---------------- LOAD ENV ----------------
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
MODEL_NAME = os.getenv("EMBEDDING_MODEL")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-70b-8192")

if not PINECONE_API_KEY:
    raise RuntimeError("Missing PINECONE_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError("Missing GROQ_API_KEY")

# ---------------- MODEL ----------------
model = SentenceTransformer(MODEL_NAME)
EMBED_DIM = model.get_sentence_embedding_dimension()

# ---------------- PINECONE ----------------
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)

# ---------------- GROQ CLIENT ----------------
groq_client = Groq(api_key=GROQ_API_KEY)

# ---------------- RAG RETRIEVER ----------------
def retrieve(query: str, namespace: str, top_k: int = 5):
    """
    Retrieve relevant vectors from Pinecone.
    Always uses a vector; handles specific ID queries or generic queries.
    """
    # Encode the query to get embedding
    query_embedding = model.encode(query).tolist()

    # Pinecone query
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        namespace=namespace,
        include_metadata=True
    )

    matches = []
    for m in results.get("matches", []):
        meta = m.get("metadata", {})
        text = meta.get("text") or meta.get("description") or ""
        matches.append({"metadata": {"text": text}, "score": m.get("score", 0.0)})

    return matches


# ---------------- CONTEXT BUILDER ----------------
def build_context(matches):
    """
    Combine retrieved Pinecone chunks into a single context string.
    """
    context_blocks = []
    for match in matches:
        text = match["metadata"].get("text", "")
        score = round(match.get("score", 0.0), 3)
        context_blocks.append(f"[Score: {score}]\n{text}")
    return "\n\n".join(context_blocks)


# ---------------- RAG PIPELINE ----------------
def rag_pipeline(query: str):
    """
    Retrieve relevant chunks from Pinecone for denial codes and 277 responses.
    """
    code_matches = retrieve(query, namespace="denial-codes", top_k=5)
    response_matches = retrieve(query, namespace="277-responses", top_k=5)

    code_context = build_context(code_matches)
    response_context = build_context(response_matches)

    return f"""
### Denial Code Reference
{code_context}

### 277 Claim Response Explanation
{response_context}
"""


# ---------------- ANSWER GENERATION ----------------
def generate_answer(query: str, context: str):
    """
    Generate concise answer using Groq LLM based on retrieved context.
    """
    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a healthcare claims denial expert. "
                    "Answer using ONLY the provided context. "
                    "Limit your response to 2–3 concise sentences."
                )
            },
            {
                "role": "user",
                "content": f"""
                    Question:
                    {query}

                    Context:
                    {context}
                    """
            }
        ],
        temperature=0.2,
        max_tokens=150
    )

    return response.choices[0].message.content.strip()
