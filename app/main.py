"""
FastAPI application: serves /query and /history endpoints.

On startup, automatically ingests all documents (PDF, HTML, TXT) from data/ into ChromaDB.
"""

import os
import sys

from dotenv import load_dotenv

# Load .env before anything else so all modules can access os.getenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field

from app.database import init_db, log_query, get_history
from app.ingest import process_documents, get_chunk_count

# ---------------------------------------------------------------------------
# FastAPI app setup
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Financial Document RAG Assistant",
    description="RAG API for querying financial documents (SEC 10-K filings) with LLM-powered answers and source citations.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request/Response models
# ---------------------------------------------------------------------------
class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="The financial question to ask")


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: list[dict]


class HistoryItem(BaseModel):
    id: int
    question: str
    answer: str
    sources: str
    timestamp: str


# ---------------------------------------------------------------------------
# Startup event
# ---------------------------------------------------------------------------
@app.on_event("startup")
def on_startup():
    """Initialize the database and ingest PDFs on server start."""
    print("[startup] Initializing database...")
    init_db()

    # Determine data directory relative to project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, "data")
    os.makedirs(data_dir, exist_ok=True)

    print("[startup] Ingesting documents from data/ folder...")

    # Check if data already exists to avoid slow re-embedding on restart
    existing_chunks = get_chunk_count()
    if existing_chunks > 0:
        print(f"[startup] Collection already has {existing_chunks} chunks. Skipping ingestion.")
        print("[startup] To force re-ingestion, delete the chroma_db/ folder and restart.")
    else:
        process_documents(data_dir)
    print("[startup] Startup complete. API is ready.")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.get("/favicon.ico")
def favicon():
    """Serve a simple SVG favicon to avoid 404."""
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
        '<rect width="32" height="32" rx="6" fill="#1f6feb"/>'
        '<text x="16" y="23" text-anchor="middle" font-size="20" fill="white">$</text>'
        '</svg>'
    )
    return Response(content=svg, media_type="image/svg+xml")


@app.get("/")
def serve_ui():
    """Serve the chat web UI."""
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>UI template not found</h1>", status_code=500)


@app.get("/api/health")
def health_check():
    """Health check endpoint (JSON)."""
    return {"status": "ok", "service": "Financial Document RAG Assistant"}


@app.post("/query", response_model=QueryResponse)
def query_endpoint(request: QueryRequest):
    """
    Ask a question about the ingested financial documents.

    Returns the LLM's answer with source citations.
    """
    # Import here to avoid circular imports and to let app startup finish first
    from app.rag_engine import query_rag

    try:
        result = query_rag(request.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG pipeline error: {e}")

    # Log the query to SQLite
    sources_str = ", ".join(
        f"{s['source']} (p.{s['page']})" for s in result.get("sources", [])
    )
    try:
        log_query(request.question, result["answer"], sources_str)
    except Exception as e:
        print(f"[main] WARNING: Failed to log query: {e}")

    return QueryResponse(
        question=request.question,
        answer=result["answer"],
        sources=result.get("sources", []),
    )


@app.get("/history", response_model=list[HistoryItem])
def history_endpoint():
    """Return the last 10 queries and answers."""
    try:
        rows = get_history(limit=10)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {e}")
    return rows
