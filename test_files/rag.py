def retrieve_context(query, top_k=5):
    query_vector = embeddings.embed_query(query)

    res = index.query(
        vector=query_vector,
        top_k=top_k,
        include_metadata=True
    )

    return [
        match["metadata"] for match in res["matches"]
    ]
    
    
    query = "Why was my claim rejected with A7:562 and how do I fix it?"

context = retrieve_context(query)

for c in context:
    print(c)