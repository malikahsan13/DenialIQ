from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

all_docs = pdf_chunks + csv_docs

vectors = []
for i, doc in enumerate(all_docs):
    vectors.append((
        f"doc-{i}",
        embeddings.embed_query(doc.page_content),
        doc.metadata
    ))

index.upsert(vectors=vectors)