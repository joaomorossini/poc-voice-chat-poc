"""
MCP Server Pattern: Database Query Tool
========================================
Demonstrates safe, read-only SQL access to a domain database.

Pattern: Agent sends natural language → LLM generates SQL → tool validates and executes.
Safety: SQLite read-only mode, SELECT-only validation, row limits, query timeout.

Replace the mock database with your own schema and data.
"""

import os
import re
import sqlite3
import logging
from pathlib import Path

from fastmcp import FastMCP

logging.basicConfig(level=os.getenv("MCP_LOG_LEVEL", "INFO").upper())
logger = logging.getLogger(__name__)

DB_PATH = os.getenv("DB_PATH", str(Path(__file__).parent / "data" / "example.db"))
ROW_LIMIT = int(os.getenv("ROW_LIMIT", "50"))
QUERY_TIMEOUT = float(os.getenv("QUERY_TIMEOUT", "30"))
PORT = int(os.getenv("PORT", "8001"))

mcp = FastMCP(
    "Database Query Tool",
    description="Execute read-only SQL queries against the domain database",
)


def _init_mock_db():
    """Create a mock database for demonstration. Replace with your real schema."""
    db_path = Path(DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if db_path.exists():
        return

    conn = sqlite3.connect(str(db_path))
    conn.executescript("""
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT,
            plan TEXT DEFAULT 'free',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER REFERENCES customers(id),
            product TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now'))
        );

        INSERT INTO customers (name, email, plan) VALUES
            ('Alice Chen', 'alice@example.com', 'pro'),
            ('Bob Kumar', 'bob@example.com', 'free'),
            ('Carol Díaz', 'carol@example.com', 'enterprise'),
            ('Dave Wilson', 'dave@example.com', 'pro'),
            ('Eva Müller', 'eva@example.com', 'free');

        INSERT INTO orders (customer_id, product, amount, status) VALUES
            (1, 'Widget A', 29.99, 'completed'),
            (1, 'Widget B', 49.99, 'completed'),
            (2, 'Widget A', 29.99, 'pending'),
            (3, 'Enterprise Suite', 999.00, 'completed'),
            (3, 'Support Plan', 199.00, 'active'),
            (4, 'Widget B', 49.99, 'cancelled'),
            (5, 'Widget A', 29.99, 'completed');
    """)
    conn.close()
    logger.info(f"Mock database created at {db_path}")


def _validate_query(sql: str) -> str | None:
    """Returns an error message if the query is unsafe, None if OK."""
    normalized = sql.strip().upper()
    if not normalized.startswith("SELECT"):
        return "Only SELECT queries are allowed"
    dangerous = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "EXEC", "GRANT"]
    for keyword in dangerous:
        if re.search(rf"\b{keyword}\b", normalized):
            return f"Query contains forbidden keyword: {keyword}"
    return None


def _ensure_limit(sql: str) -> str:
    """Append LIMIT if not present."""
    if "LIMIT" not in sql.upper():
        return f"{sql.rstrip(';')} LIMIT {ROW_LIMIT}"
    return sql


@mcp.tool()
def get_database_schema() -> str:
    """
    Returns the database schema — table names, columns, types, and sample data.
    Call this FIRST before writing any SQL queries.
    """
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]

    schema_parts = []
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        col_info = ", ".join(f"{c[1]} ({c[2]})" for c in columns)

        cursor.execute(f"SELECT * FROM {table} LIMIT 3")
        sample = cursor.fetchall()
        col_names = [desc[0] for desc in cursor.description]

        schema_parts.append(
            f"## {table}\n"
            f"Columns: {col_info}\n"
            f"Sample ({len(sample)} rows):\n"
            + "\n".join(
                "  " + " | ".join(str(v) for v in row)
                for row in sample
            )
        )

    conn.close()
    return "\n\n".join(schema_parts)


@mcp.tool()
def execute_sql(sql: str) -> dict:
    """
    Execute a read-only SQL query and return results.

    Args:
        sql: A SELECT query to execute against the database.

    Returns:
        A dict with keys: columns, rows, row_count, truncated.
    """
    error = _validate_query(sql)
    if error:
        return {"error": error, "columns": [], "rows": [], "row_count": 0, "truncated": False}

    sql = _ensure_limit(sql)

    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        conn.execute(f"PRAGMA busy_timeout = {int(QUERY_TIMEOUT * 1000)}")
        cursor = conn.cursor()
        cursor.execute(sql)

        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        truncated = len(rows) >= ROW_LIMIT

        conn.close()
        return {
            "columns": columns,
            "rows": [list(row) for row in rows],
            "row_count": len(rows),
            "truncated": truncated,
        }
    except sqlite3.Error as e:
        return {"error": str(e), "columns": [], "rows": [], "row_count": 0, "truncated": False}


# --- Health endpoint for Docker ---
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

health_app = Starlette(routes=[
    Route("/health", lambda r: JSONResponse({"status": "ok"})),
])

if __name__ == "__main__":
    _init_mock_db()
    mcp.run(transport="streamable-http", host="0.0.0.0", port=PORT)
