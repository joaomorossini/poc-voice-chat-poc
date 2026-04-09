# Pattern: Database Query Tool

Safe, read-only SQL access to a domain database via MCP.

## How It Works

1. Agent calls `get_database_schema()` to understand available tables
2. Agent generates SQL based on user's question + schema context
3. Agent calls `execute_sql(sql)` with a SELECT query
4. Tool validates (SELECT-only, no dangerous keywords), enforces row limit, executes in read-only mode

## When to Use

- Domain data lives in a relational database (SQLite, Postgres, MySQL)
- Users need to query structured data via natural language
- You need safety guarantees (no writes, no schema changes, bounded results)

## Customization

1. Replace `_init_mock_db()` with your real database connection
2. Adjust `DB_PATH`, `ROW_LIMIT`, `QUERY_TIMEOUT` via environment variables
3. For Postgres/MySQL: swap `sqlite3` for `asyncpg`/`aiomysql`, update `_validate_query`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_PATH` | `data/example.db` | Path to SQLite database |
| `ROW_LIMIT` | `50` | Max rows returned per query |
| `QUERY_TIMEOUT` | `30` | Query timeout in seconds |
| `PORT` | `8001` | Server port |
| `MCP_LOG_LEVEL` | `INFO` | Logging level |
