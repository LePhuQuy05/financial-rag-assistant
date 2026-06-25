"""
Document ingestion pipeline: reads PDF, HTML, and TXT files from data/,
chunks text, and stores embeddings in ChromaDB.

Supports real SEC EDGAR filings (HTML + TXT) and PDF documents.
Handles nested directory structures via recursive scanning.
Uses deterministic chunk IDs so re-ingestion safely upserts.
"""

import os
import chromadb
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from bs4 import BeautifulSoup


CHROMA_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "chroma_db")
COLLECTION_NAME = "financial_docs"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
BATCH_SIZE = 500  # Number of chunks per ChromaDB add batch


# Supported file extensions
PDF_EXTENSIONS = {".pdf"}
HTML_EXTENSIONS = {".htm", ".html"}
TEXT_EXTENSIONS = {".txt"}


# ---------------------------------------------------------------------------
# ChromaDB
# ---------------------------------------------------------------------------
def get_collection():
    """Get or create the ChromaDB collection for financial documents."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    return collection


def get_chunk_count() -> int:
    """Return the number of chunks currently stored in the collection."""
    collection = get_collection()
    return collection.count()


# ---------------------------------------------------------------------------
# Text chunking
# ---------------------------------------------------------------------------
def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Split text into overlapping chunks of approximately chunk_size characters.

    Chunks are split on spaces to avoid breaking words mid-way.
    """
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk_words = words[i : i + chunk_size]
        chunk = " ".join(chunk_words)
        if chunk.strip():
            chunks.append(chunk)
        i += chunk_size - overlap
        if i >= len(words):
            break
    return chunks


# ---------------------------------------------------------------------------
# Text extraction from different formats
# ---------------------------------------------------------------------------
def extract_from_pdf(filepath: str) -> str:
    """Extract all text from a PDF file. Returns empty string on failure."""
    try:
        reader = PdfReader(filepath)
    except (PdfReadError, Exception) as e:
        print(f"    WARNING: Cannot read PDF '{os.path.basename(filepath)}': {e}")
        return ""

    texts = []
    num_pages = len(reader.pages)
    for page_num in range(num_pages):
        try:
            page = reader.pages[page_num]
            text = page.extract_text()
            if text and text.strip():
                texts.append(text)
        except Exception as e:
            print(f"    WARNING: Page {page_num + 1} of '{os.path.basename(filepath)}' failed: {e}")
            continue

    return "\n\n".join(texts)


def extract_from_html(filepath: str) -> str:
    """Extract visible text from an HTML file (SEC filings are .htm files)."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            html = f.read()
    except Exception as e:
        print(f"    WARNING: Cannot read HTML '{os.path.basename(filepath)}': {e}")
        return ""

    try:
        soup = BeautifulSoup(html, "html.parser")
        # Remove script and style elements
        for tag in soup(["script", "style", "meta", "link", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator="\n")
        # Clean up: collapse multiple blank lines
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)
    except Exception as e:
        print(f"    WARNING: Failed to parse HTML '{os.path.basename(filepath)}': {e}")
        return ""


def extract_from_text(filepath: str) -> str:
    """Read plain text from a .txt file."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception as e:
        print(f"    WARNING: Cannot read text file '{os.path.basename(filepath)}': {e}")
        return ""


def extract_text(filepath: str) -> str:
    """Extract text from a file based on its extension."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext in PDF_EXTENSIONS:
        return extract_from_pdf(filepath)
    elif ext in HTML_EXTENSIONS:
        return extract_from_html(filepath)
    elif ext in TEXT_EXTENSIONS:
        return extract_from_text(filepath)
    else:
        return ""


# ---------------------------------------------------------------------------
# Main processing
# ---------------------------------------------------------------------------
def process_documents(data_dir: str):
    """
    Recursively scan data_dir for all supported document files,
    extract text, chunk, and store in ChromaDB.

    Uses deterministic chunk IDs: {relative_path}_c{chunk_index}
    so re-running on the same files simply upserts (no duplicates).
    """
    collection = get_collection()

    # Find all supported files
    all_files = []
    for root, dirs, files in os.walk(data_dir):
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext in PDF_EXTENSIONS | HTML_EXTENSIONS | TEXT_EXTENSIONS:
                all_files.append(os.path.join(root, fname))

    if not all_files:
        print(f"[ingest] No supported files found in {data_dir}.")
        print("[ingest] Run 'python scripts/download_sec_data.py' to download SEC filings,")
        print("[ingest] or 'python scripts/download_samples.py' for sample PDFs.")
        return

    # Count by type
    pdf_count = sum(1 for f in all_files if os.path.splitext(f)[1].lower() in PDF_EXTENSIONS)
    html_count = sum(1 for f in all_files if os.path.splitext(f)[1].lower() in HTML_EXTENSIONS)
    txt_count = sum(1 for f in all_files if os.path.splitext(f)[1].lower() in TEXT_EXTENSIONS)
    print(f"[ingest] Found {len(all_files)} files ({pdf_count} PDF, {html_count} HTML, {txt_count} TXT)")

    total_chunks = 0
    batch_ids = []
    batch_documents = []
    batch_metadatas = []
    skipped_empty = 0

    for filepath in sorted(all_files):
        rel_path = os.path.relpath(filepath, data_dir)
        print(f"[ingest] Processing: {rel_path}")

        text = extract_text(filepath)
        if not text or not text.strip():
            print(f"  Skipped (empty or unreadable)")
            skipped_empty += 1
            continue

        chunks = chunk_text(text)
        if not chunks:
            print(f"  Skipped (no chunks generated)")
            skipped_empty += 1
            continue

        for chunk_idx, chunk in enumerate(chunks):
            chunk_id = f"{rel_path}_c{chunk_idx}"
            # Sanitize ID: ChromaDB IDs must be alphanumeric + some special chars
            chunk_id = chunk_id.replace("\\", "/").replace(" ", "_")

            batch_ids.append(chunk_id)
            batch_documents.append(chunk)
            batch_metadatas.append({
                "source": os.path.basename(filepath),
                "path": rel_path,
                "type": os.path.splitext(filepath)[1].lower(),
            })

            # Flush batch when it reaches BATCH_SIZE
            if len(batch_ids) >= BATCH_SIZE:
                _flush_batch(collection, batch_ids, batch_documents, batch_metadatas)
                total_chunks += len(batch_ids)
                print(f"  [{total_chunks} total chunks so far]")
                batch_ids.clear()
                batch_documents.clear()
                batch_metadatas.clear()

        print(f"  {len(chunks)} chunks")

    # Flush remaining
    if batch_ids:
        _flush_batch(collection, batch_ids, batch_documents, batch_metadatas)
        total_chunks += len(batch_ids)

    print(f"\n[ingest] {'='*50}")
    print(f"[ingest] Ingestion complete!")
    print(f"[ingest]   Total files processed: {len(all_files)}")
    print(f"[ingest]   Skipped (empty):       {skipped_empty}")
    print(f"[ingest]   Total chunks ingested:  {total_chunks}")


def _flush_batch(collection, ids, documents, metadatas):
    """Add a batch of chunks to ChromaDB."""
    try:
        collection.add(ids=ids, documents=documents, metadatas=metadatas)
    except Exception as e:
        print(f"  WARNING: Batch add failed: {e}. Trying one by one...")
        # Fall back to individual adds
        for i in range(len(ids)):
            try:
                collection.add(
                    ids=[ids[i]],
                    documents=[documents[i]],
                    metadatas=[metadatas[i]],
                )
            except Exception as e2:
                print(f"    Skipping chunk {ids[i]}: {e2}")


# Backward compatibility alias
process_pdfs = process_documents


if __name__ == "__main__":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, "data")
    process_documents(data_dir)
