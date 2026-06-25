"""
RAG Engine: queries ChromaDB for relevant chunks and calls DeepSeek LLM.

Retrieves the top 3 most relevant text chunks from the vector store,
constructs a prompt with citations, and returns the LLM's answer.
"""

import os
import json
import requests
import chromadb

from app.ingest import CHROMA_PATH, COLLECTION_NAME

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"
REQUEST_TIMEOUT = 60  # seconds (DeepSeek can be slower)

SYSTEM_PROMPT = """You are a financial assistant. Answer the question based ONLY on the provided context.
If the context does not contain the answer, say so honestly -- do not make up information.
At the end of your answer, cite the source file name and page number(s) you used."""


def get_chromadb_collection():
    """Get the ChromaDB collection (read-only usage)."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client.get_or_create_collection(name=COLLECTION_NAME)


def build_context(chunks_result: dict) -> tuple[str, list[dict]]:
    """
    Build a context string and sources list from ChromaDB query results.

    Returns (context_text, sources_list).
    """
    documents = chunks_result.get("documents", [[]])[0]
    metadatas = chunks_result.get("metadatas", [[]])[0]

    sources = []
    context_parts = []

    for i, (doc, meta) in enumerate(zip(documents, metadatas)):
        source = meta.get("source", "unknown")
        page = meta.get("page", "?")
        sources.append({"source": source, "page": page})
        context_parts.append(f"[Source: {source}, Page {page}]\n{doc}")

    context_text = "\n\n---\n\n".join(context_parts)
    return context_text, sources


def call_llm(context_text: str, question: str) -> str:
    """
    Call the DeepSeek API with the given context and question.

    Returns the LLM's answer text, or an error message on failure.
    """
    api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not api_key or api_key == "your_key_here":
        return (
            "ERROR: DeepSeek API key is not set. Please add your key to the .env file "
            "(DEEPSEEK_API_KEY=your_key) and restart the server."
        )

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {question}"},
        ],
        "temperature": 0.3,
        "max_tokens": 1024,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(DEEPSEEK_URL, json=payload, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        answer = data["choices"][0]["message"]["content"].strip()
        return answer
    except requests.exceptions.Timeout:
        return "ERROR: The LLM request timed out. Please try again."
    except requests.exceptions.HTTPError:
        status = response.status_code
        if status == 401:
            return "ERROR: Invalid DeepSeek API key. Please check your DEEPSEEK_API_KEY in the .env file."
        elif status == 429:
            return "ERROR: DeepSeek rate limit exceeded. Please wait a moment and try again."
        return f"ERROR: DeepSeek API returned an error (HTTP {status})."
    except requests.exceptions.RequestException as e:
        return f"ERROR: Could not reach DeepSeek API: {e}"


def query_rag(question: str) -> dict:
    """
    Full RAG pipeline: retrieve context from ChromaDB, call LLM, return answer + sources.

    Returns a dictionary with 'answer' (str) and 'sources' (list of dicts).
    """
    # Step 1: Retrieve relevant chunks from ChromaDB
    try:
        collection = get_chromadb_collection()
        results = collection.query(query_texts=[question], n_results=3)
    except Exception as e:
        return {
            "answer": f"ERROR: Failed to query the document database: {e}",
            "sources": [],
        }

    # Step 2: Check if we got any results
    documents = results.get("documents", [[]])[0]
    if not documents:
        return {
            "answer": (
                "I could not find any relevant information in the financial documents to answer "
                "your question. The document database may be empty -- please ensure PDFs have been "
                "ingested by checking the server startup logs."
            ),
            "sources": [],
        }

    # Step 3: Build context and call LLM
    context_text, sources = build_context(results)
    answer = call_llm(context_text, question)

    return {"answer": answer, "sources": sources}
