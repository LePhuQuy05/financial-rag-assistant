<div align="center">

# 📊 Financial Document RAG Assistant

**Retrieval-Augmented Generation system for financial documents**

*Ask natural language questions about SEC filings and get AI-powered answers with source citations.*

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.138-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-1.5-FF6B6B.svg)](https://www.trychroma.com/)
[![DeepSeek](https://img.shields.io/badge/LLM-DeepSeek_V3-6366f1.svg)](https://platform.deepseek.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

</div>

---

## 🔍 Overview

A full-stack RAG pipeline that ingests real financial filings from the **SEC EDGAR** database (10-K annual reports from S&P 500 companies), indexes them in a vector database, and uses **DeepSeek-V3** to answer financial questions backed by source citations.

**Why this matters:** Instead of manually searching through hundreds of pages of financial reports, you can ask natural language questions and get instant, cited answers.

### Example

> **Q:** *"What was NVIDIA's total revenue and net income in fiscal 2024?"*
>
> **A:** Based on the provided context, NVIDIA's total revenue for fiscal year 2024 was **$60,922 million** ($60.9 billion), and net income was **$29,760 million** ($29.8 billion).
>
> 📎 *Source: NVIDIA 10-K filing (full-submission.txt)*

---

## 🏗️ Architecture

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────┐
│  SEC EDGAR   │────▶│  app/ingest.py  │────▶│   ChromaDB    │
│  (500 10-Ks) │     │  extract→chunk  │     │  (embeddings) │
└─────────────┘     └─────────────────┘     └──────┬───────┘
                                                   │
┌─────────────┐     ┌─────────────────┐            │
│   DeepSeek   │◀────│ rag_engine.py   │◀───────────┘
│   (LLM)      │     │ prompt→answer   │   top-3 retrieval
└──────┬──────┘     └───────┬─────────┘
       │                    │
       ▼                    ▼
┌─────────────┐     ┌─────────────────┐
│   Answer +   │     │  FastAPI Server │     ┌──────────────┐
│   Citations  │     │  /query /history│────▶│    SQLite     │
└─────────────┘     └─────────────────┘     └──────────────┘
```

**Data Flow:**
1. **Ingestion** — SEC 10-K filings (HTML/TXT) are extracted, cleaned, and chunked (~500 words with 50-word overlap)
2. **Embedding** — `all-MiniLM-L6-v2` converts chunks to vectors stored in ChromaDB
3. **Retrieval** — User question retrieves top-3 most relevant chunks via semantic search
4. **Generation** — DeepSeek-V3 answers the question using ONLY the retrieved context, citing sources

---

## ✨ Features

- **Real Financial Data** — Downloads actual 10-K filings from S&P 500 companies via SEC EDGAR
- **Multi-format Ingestion** — Supports PDF, HTML, and plain text documents
- **Semantic Search** — ChromaDB vector embeddings find relevant content beyond keyword matching
- **Source Citations** — Every answer includes the source document and page reference
- **Query History** — All questions and answers logged in SQLite for auditability
- **Web Chat UI** — Built-in dark-theme web interface for interactive exploration
- **Batch Processing** — Handles 50,000+ text chunks efficiently with batched database writes
- **Smart Re-ingestion** — Deterministic chunk IDs prevent duplicates; skips re-embedding on restart

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|---|---|---|
| **API** | FastAPI + Uvicorn | REST endpoints, async serving |
| **LLM** | DeepSeek-V3 (`deepseek-chat`) | Answer generation from context |
| **Vector DB** | ChromaDB | Semantic document retrieval |
| **Embeddings** | `all-MiniLM-L6-v2` (Sentence Transformers) | Text → vector conversion |
| **Database** | SQLite | Query history logging |
| **PDF Parsing** | pypdf + BeautifulSoup4 | Multi-format text extraction |
| **SEC Data** | `sec-edgar-downloader` | Bulk SEC filing downloads |
| **Frontend** | Vanilla HTML/CSS/JS | Zero-dependency chat UI |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **DeepSeek API key** — [Get one free](https://platform.deepseek.com/api_keys)

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/financial-rag-assistant.git
cd financial-rag-assistant
pip install -r requirements.txt
```

### 2. Set API Key

```bash
# Edit .env and add your DeepSeek key
DEEPSEEK_API_KEY=sk-your-key-here
```

### 3. Get Data

**Option A — Quick test (2 generated PDFs):**
```bash
python scripts/download_samples.py
```

**Option B — Real data (S&P 500 10-K filings):**
```bash
python scripts/download_sec_data.py
# Downloads ~500 real 10-K filings. Takes 10-20 minutes.
# Press Enter at the prompt to begin.
```

### 4. Run

```bash
python -m uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000** in your browser — you'll see the chat interface.

---

## 📡 API Reference

### `GET /` — Web Chat UI
Returns the interactive chat interface.

### `GET /api/health` — Health Check
```json
{"status": "ok", "service": "Financial Document RAG Assistant"}
```

### `POST /query` — Ask a Question

**Request:**
```json
{"question": "What was Apple's net income in Q3 2024?"}
```

**Response:**
```json
{
  "question": "What was Apple's net income in Q3 2024?",
  "answer": "Based on the provided context, Apple's net income in Q3 2024 was $21,448 million...\n\nSource: apple_q3_2024_summary.pdf",
  "sources": [
    {"source": "apple_q3_2024_summary.pdf", "page": 1},
    {"source": "full-submission.txt", "page": "?"}
  ]
}
```

### `GET /history` — Query History

Returns the last 10 questions and answers with timestamps.

---

## 📁 Project Structure

```
financial-rag-assistant/
├── app/
│   ├── main.py              # FastAPI server, endpoints, startup
│   ├── ingest.py            # Multi-format extraction, chunking, ChromaDB storage
│   ├── rag_engine.py        # Retrieval + DeepSeek prompting + response parsing
│   ├── database.py          # SQLite setup, query logging, history retrieval
│   └── templates/
│       └── index.html       # Web chat UI
├── scripts/
│   ├── download_samples.py  # Generate 2 sample financial PDFs
│   └── download_sec_data.py # Download real 10-K filings from SEC EDGAR
├── data/                    # Documents for ingestion (PDF, HTML, TXT)
├── chroma_db/               # ChromaDB persistent storage (auto-created)
├── query_history.db         # SQLite query log (auto-created)
├── .env                     # API key configuration
├── requirements.txt         # Python dependencies
└── plan.md                  # Project planning & design document
```

---

## ⚙️ How It Works

### Ingestion Pipeline (`app/ingest.py`)

1. Recursively scans `data/` for supported files (`.pdf`, `.htm`, `.html`, `.txt`)
2. Extracts text using format-specific parsers (pypdf for PDF, BeautifulSoup for HTML)
3. Splits text into overlapping chunks (500 words, 50-word overlap)
4. Generates deterministic chunk IDs (`relative/path_c0`, `relative/path_c1`, ...)
5. Embeds and stores in ChromaDB in batches of 500

### RAG Engine (`app/rag_engine.py`)

1. Embeds the user's question and queries ChromaDB for top-3 most similar chunks
2. Builds a prompt: *"Answer based ONLY on the context. Cite sources."*
3. Calls DeepSeek-V3 API with the context + question
4. Returns the answer with source metadata

### Smart Restart

On server start, if `chroma_db/` already contains data, ingestion is **skipped**. Delete `chroma_db/` to force a fresh re-ingestion.

---

## 🔧 Configuration

| Variable | Location | Description |
|---|---|---|
| `DEEPSEEK_API_KEY` | `.env` | DeepSeek API key |
| `CHUNK_SIZE` | `app/ingest.py:20` | Words per chunk (default 500) |
| `CHUNK_OVERLAP` | `app/ingest.py:21` | Overlap between chunks (default 50) |
| `BATCH_SIZE` | `app/ingest.py:22` | Chunks per ChromaDB write (default 500) |
| `MODEL` | `app/rag_engine.py:17` | LLM model (default `deepseek-chat`) |

---

## 📝 License

MIT — feel free to use this for your own projects, portfolio, or research.

---

<div align="center">

**Built with Python, FastAPI, ChromaDB, and DeepSeek**

⭐ *If this project helped you, consider giving it a star!*

</div>
