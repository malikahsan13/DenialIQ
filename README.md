# DenialIQ
Smart, short, very strong for AI analytics. See clearly why a claim failed

Below is a clean, production-grade Python ingestion pipeline designed specifically for:

Pinecone

RAG

LangGraph agent usage

Medical billing denial/rejection explanation

High-Level Ingestion Architecture

PDF (277 Guide)      CSV (CARC/RARC)
      │                     │
      ▼                     ▼
 Text Extraction        Row Parsing
      │                     │
 Chunking + Metadata Normalization
      │
 Embeddings (OpenAI / other)
      │
 Pinecone Vector DB

 # Pseudo-flow
User Query
   ↓
Extract Code
   ↓
Retrieve Context (Pinecone)
   ↓
Explain in Plain English
   ↓
Provide Fix Steps


User (Streamlit)
      │
      ▼
 LangGraph Router
      │
 ┌────┴─────┐
 │          │
 ▼          ▼
SQLite   Pinecone
(SQL)     (RAG)
 │          │
 └────┬─────┘
      ▼
     Groq


Sql agent
User Question
   ↓
check_relevance
   ↓
convert_to_sql
   ↓
execute_sql ──(error)──▶ regenerate_query ──▶ execute_sql
   ↓
generate_human_readable_answer
   ↓
END