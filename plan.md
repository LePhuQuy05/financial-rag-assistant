# Project Plan: Financial Document RAG Assistant

## 1. Project Overview
Build a backend RAG (Retrieval-Augmented Generation) system that ingests financial PDF documents, chunks the text, stores embeddings in ChromaDB, and uses an LLM via OpenRouter API to answer questions with source citations. FastAPI will serve the endpoints, and SQLite will log the query history.

## 2. Tech Stack
- **Language:** Python 3.10+
- **Web Framework:** FastAPI, Uvicorn
- **Vector Database:** ChromaDB
- **Relational Database:** SQLite (standard library `sqlite3`)
- **PDF Parsing:** pypdf
- **PDF Generation (sample data):** fpdf2
- **LLM Provider:** DeepSeek API (deepseek-chat / DeepSeek-V3)
- **Embeddings:** ChromaDB default embedding model (all-MiniLM-L6-v2 via sentence-transformers)
- **Environment:** python-dotenv for API key management

## 3. Project Structure
Create the following files and folders:
```text
Financial-RAG-Assistant/
│
├── data/                    # Folder to store PDF files
│   └── .gitkeep
├── scripts/
│   └── download_samples.py  # Generate sample financial PDFs for testing
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application and endpoints
│   ├── ingest.py            # Logic to read PDF, chunk, and store in ChromaDB
│   ├── rag_engine.py        # Logic to query ChromaDB and call OpenRouter LLM
│   └── database.py          # SQLite setup and logging functions
├── .env                     # Environment variables (OPENROUTER_API_KEY)
├── requirements.txt
└── plan.md
```

## 4. Step-by-Step Implementation

### Step 4.1: Environment & Dependencies
Create `requirements.txt` with the following content:
```text
fastapi==0.111.0
uvicorn==0.29.0
chromadb==0.4.24
pypdf==4.2.0
requests==2.31.0
pydantic==2.7.1
sentence-transformers
python-dotenv==1.0.1
fpdf2==2.7.9
```

Create a `.env` file for the DeepSeek API key:
```text
DEEPSEEK_API_KEY=your_key_here
```

*Action: Run `pip install -r requirements.txt`*

### Step 4.2: Data Collection (Generate Sample Financial PDFs)
Since public financial PDF URLs can break, we generate realistic sample PDFs programmatically using `fpdf2`. This ensures the pipeline always works for testing.

Create `scripts/download_samples.py` that generates two PDFs in the `data/` folder:
1. `apple_q3_2024_summary.pdf` — Realistic quarterly financial summary with revenue by segment (iPhone, Services, Mac, iPad, Wearables), net income, gross margin, operating cash flow, and geographic breakdown.
2. `nvidia_2024_annual_summary.pdf` — Realistic annual financial highlights with data center revenue, gaming revenue, gross margin, net income, R&D expenses, and management discussion text.

*Action: Run `python scripts/download_samples.py` to generate the PDFs.*

### Step 4.3: Database Setup (`app/database.py`)
- Create a SQLite database named `query_history.db` in the project root.
- Create a table named `logs` with columns: `id` (INTEGER PRIMARY KEY), `question` (TEXT), `answer` (TEXT), `sources` (TEXT), `timestamp` (DATETIME DEFAULT CURRENT_TIMESTAMP).
- Write a function `log_query(question, answer, sources)` to insert records.
- Write a function `get_history(limit=10)` to retrieve the most recent queries.
- Use a context manager or connection-per-call pattern to ensure thread-safe DB access.

### Step 4.4: Ingestion Pipeline (`app/ingest.py`)
- Initialize a ChromaDB client (persistent client saving to a local folder named `./chroma_db`).
- Use `get_or_create_collection("financial_docs")` so the collection is reused across restarts (avoids crashing if it already exists).
- Write a function `process_pdfs(data_dir: str)`:
  1. Loop through all PDFs in `data_dir`.
  2. Use `pypdf` to extract text page by page. Handle errors gracefully: skip encrypted pages, log warnings, continue to next page/PDF on failure.
  3. Chunk the text into smaller pieces (~500 characters per chunk, with a 50-character overlap to preserve context).
  4. Generate a deterministic unique ID for each chunk (`{doc_name}_p{page}_c{chunk_idx}`).
  5. Add the chunks to the `financial_docs` ChromaDB collection, storing the text and metadata (source file name, page number).
- Log progress: "Processing page X of Y of [filename]...", "Ingested N chunks from [filename]".

### Step 4.5: RAG Engine (`app/rag_engine.py`)
- Load the DeepSeek API key from environment: `os.getenv("DEEPSEEK_API_KEY")`.
- Write a function `query_rag(question: str) -> dict`:
  1. Query the `financial_docs` collection in ChromaDB using the user's `question` to retrieve the top 3 most relevant chunks.
  2. If no relevant chunks are found, return an answer indicating no data is available.
  3. Extract the text of these chunks and their source metadata.
  4. Construct a prompt for the LLM. The prompt MUST enforce answering ONLY based on the context and requiring citation.
     *Prompt Template:*
     ```text
     You are a financial assistant. Answer the question based ONLY on the provided context.
     At the end of your answer, cite the source file name and page number you used.

     Context:
     {context_text}

     Question: {question}
     ```
  5. Make a POST request to OpenRouter API (`https://openrouter.ai/api/v1/chat/completions`).
     - Use a free model: `meta-llama/llama-3-8b-instruct:free`
     - Include the API key in the `Authorization: Bearer` header.
     - Set a reasonable timeout (30s) on the request.
     - Handle errors: auth failure (check API key), rate limits, timeouts.
  6. Parse the LLM response and return a dictionary containing the `answer` and the `sources` list.
  7. If the LLM call fails, return a graceful error message.

### Step 4.6: FastAPI Endpoints (`app/main.py`)
- Load `.env` file at startup using `load_dotenv()`.
- Initialize FastAPI app with title and description.
- Add CORS middleware: `allow_origins=["*"]`, `allow_methods=["*"]`, `allow_headers=["*"]` (for development; restrict in production).
- Create a startup event (`@app.on_event("startup")`) that:
  1. Ensures the `data/` directory exists.
  2. If the `data/` directory is empty (only `.gitkeep`), prints a message telling the user to run `python scripts/download_samples.py` first.
  3. Automatically triggers `process_pdfs("./data")` to ingest all PDFs.
- Create Endpoint 1: `POST /query`
  - Request body: `{"question": "string"}`
  - Validates that `question` is non-empty (returns 400 if missing).
  - Calls `query_rag()`, calls `log_query()` to save to SQLite, and returns the result as JSON.
  - On pipeline errors, returns 500 with error details.
- Create Endpoint 2: `GET /history`
  - Queries the SQLite database via `get_history()` and returns the last 10 queries and answers as JSON.
- Create a simple `GET /` health-check endpoint returning `{"status": "ok"}`.

### Step 4.7: Testing
- Run the server: `uvicorn app.main:app --reload`
- Test the `/query` endpoint:
  ```bash
  curl -X POST "http://127.0.0.1:8000/query" \
       -H "Content-Type: application/json" \
       -d "{\"question\": \"What was the net income reported by Apple?\"}"
  ```
- Test the `/history` endpoint:
  ```bash
  curl "http://127.0.0.1:8000/history"
  ```
- Verify server restart does not crash or create duplicate chunks.

## 5. Important Rules for Claude Code
- Do NOT use any paid APIs without explicitly telling me to set an environment variable first.
- Make sure error handling is implemented for PDF parsing (e.g., skipping encrypted pages, handling corrupt PDFs).
- Keep the code modular and clean.
- Output clear console logs when ingesting PDFs (e.g., "Processing page X of Y...").
- Use `get_or_create_collection` to avoid crashes on server restart.
- Handle the case where no PDFs exist in `data/` — print a helpful message.
- Handle OpenRouter API errors gracefully (auth failures, timeouts, rate limits).
