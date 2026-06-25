"""
SQLite database setup and query history logging.

Creates a query_history.db database with a logs table to store
questions, answers, sources, and timestamps.
"""

import sqlite3
import os
from datetime import datetime

# Database file lives in the project root
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "query_history.db")


def get_connection() -> sqlite3.Connection:
    """Get a connection to the SQLite database (not thread-safe; create per call)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the logs table if it does not exist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            sources TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    print(f"[database] Initialized SQLite database at {DB_PATH}")


def log_query(question: str, answer: str, sources: str):
    """Insert a query and its answer into the logs table."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO logs (question, answer, sources) VALUES (?, ?, ?)",
        (question, answer, sources),
    )
    conn.commit()
    conn.close()


def get_history(limit: int = 10) -> list[dict]:
    """Retrieve the most recent queries from the logs table."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, question, answer, sources, timestamp FROM logs ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
