import os
import pandas as pd
from tqdm import tqdm
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
import os
from dotenv import load_dotenv
from pypdf import PdfReader

# Load .env file
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
MODEL_NAME = os.getenv("EMBEDDING_MODEL")
EMBED_DIM = os.getenv("EMBED_DIM")

if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY not found in .env")

CSV_PATH = "./documents/carc_rarc_codes.csv"
PDF_PATH = "./documents/277_response_understanding.pdf"
BATCH_SIZE = 100

# ---------------- MODEL ----------------
model = SentenceTransformer(MODEL_NAME)
EMBED_DIM = model.get_sentence_embedding_dimension()

# ---------------- PINECONE ----------------
pc = Pinecone(api_key=PINECONE_API_KEY)

if INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(
        name=INDEX_NAME,
        dimension=EMBED_DIM,
        metric="cosine"
    )

index = pc.Index(INDEX_NAME)

# ---------------- CSV INGESTION ----------------
def ingest_csv(csv_path):
    df = pd.read_csv(csv_path)

    # Replace NaN with empty string
    df = df.fillna("")

    vectors = []

    for _, row in tqdm(df.iterrows(), total=len(df)):
        rarc_code = str(row["RARC_Codes"]).strip()
        description = str(row["Description"]).strip()

        # Safety check
        if not rarc_code:
            continue

        text = f"{rarc_code} - {description}" if description else rarc_code

        embedding = model.encode(text).tolist()

        vectors.append({
            "id": f"csv-{rarc_code}",
            "values": embedding,
            "metadata": {
                "source": "csv",
                "rarc_code": rarc_code,
                "description": description,   # always string now
                "text": text
            }
        })

        if len(vectors) >= BATCH_SIZE:
            index.upsert(
                vectors=vectors,
                namespace="denial-codes"
            )
            vectors = []

    if vectors:
        index.upsert(
            vectors=vectors,
            namespace="denial-codes"
        )

# print(index.describe_index_stats())

# ---------------- PDF INGESTION ----------------
def extract_pdf_text(pdf_path):
    reader = PdfReader(pdf_path)
    pages = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            pages.append((i + 1, text))
    return pages


def chunk_text(text, chunk_size=200, overlap=50):
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        start += chunk_size - overlap

    return chunks

def ingest_pdf(pdf_path):
    vectors = []
    doc_id = os.path.basename(pdf_path)
    pages = extract_pdf_text(pdf_path)

    for page_num, text in pages:
        chunks = chunk_text(text)

        for i, chunk in enumerate(chunks):
            embedding = model.encode(chunk).tolist()

            vectors.append({
                "id": f"{doc_id}-p{page_num}-c{i}",
                "values": embedding,
                "metadata": {
                    "source": "pdf",
                    "document": doc_id,
                    "page": page_num,
                    "chunk": i,
                    "text": chunk
                }
            })

            if len(vectors) >= BATCH_SIZE:
                index.upsert(vectors=vectors, namespace="277-responses")
                vectors = []

    if vectors:
        index.upsert(vectors=vectors, namespace="277-responses")


# ---------------- RUN ----------------
if __name__ == "__main__":
    ingest_csv(CSV_PATH)
    ingest_pdf(PDF_PATH)

    print(index.describe_index_stats())