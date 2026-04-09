# Pattern: Knowledge Retrieval

File-based knowledge search and retrieval via MCP. Complements LibreChat's built-in RAG with tighter control over search logic.

## How It Works

1. Agent calls `list_documents()` or `search_knowledge(query)` to find relevant content
2. Tool searches indexed markdown files using keyword matching (swap for vector search in production)
3. Agent calls `get_document(path)` for full content when needed
4. Results include source citations so the agent can attribute information

## When to Use

- Knowledge lives outside LibreChat's file store (shared docs, wikis, exported content)
- You need custom search logic (domain-specific ranking, filtering by category)
- You want to control what's indexed without using LibreChat's upload flow
- Documents are updated externally and need to be searchable immediately

## When NOT to Use

- LibreChat's built-in RAG (file_search capability) is sufficient
- You need semantic/vector search at scale (use PGVector directly or a dedicated vector DB)

## Customization

1. Replace mock documents in `data/knowledge/` with real content
2. For production: swap keyword search with vector embeddings (e.g., sentence-transformers + FAISS)
3. Mount a volume for the knowledge directory so content persists across rebuilds

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `KNOWLEDGE_DIR` | `data/knowledge` | Path to knowledge base documents |
| `MAX_RESULTS` | `5` | Default max search results |
| `EXCERPT_LENGTH` | `500` | Characters per excerpt |
| `PORT` | `8003` | Server port |
| `MCP_LOG_LEVEL` | `INFO` | Logging level |
