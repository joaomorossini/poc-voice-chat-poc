"""
MCP Server Pattern: Knowledge Retrieval
========================================
Demonstrates file-based knowledge search and retrieval via MCP.

Pattern: Agent queries a knowledge base → tool searches indexed documents → returns
relevant excerpts with source citations. Useful as a complement to LibreChat's built-in
RAG when you want tighter control over the search logic, or when documents live outside
LibreChat's file store.

Replace the mock knowledge base with your real documents.
"""

import os
import re
import logging
from pathlib import Path

from fastmcp import FastMCP

logging.basicConfig(level=os.getenv("MCP_LOG_LEVEL", "INFO").upper())
logger = logging.getLogger(__name__)

KNOWLEDGE_DIR = Path(os.getenv("KNOWLEDGE_DIR", str(Path(__file__).parent / "data" / "knowledge")))
PORT = int(os.getenv("PORT", "8003"))
MAX_RESULTS = int(os.getenv("MAX_RESULTS", "5"))
EXCERPT_LENGTH = int(os.getenv("EXCERPT_LENGTH", "500"))

mcp = FastMCP(
    "Knowledge Retrieval",
    description="Search and retrieve from the project knowledge base",
)


def _init_mock_knowledge():
    """Create mock knowledge base documents. Replace with your real content."""
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)

    docs = {
        "onboarding-guide.md": """# Onboarding Guide

## Getting Started
New team members should complete the following steps in their first week:
1. Set up development environment (see Dev Setup Guide)
2. Complete security training module
3. Review architecture documentation
4. Shadow a senior team member for one sprint

## Access Requests
Request access to the following systems via the IT portal:
- GitHub organization (engineering manager approves)
- Cloud provider console (team lead approves)
- Monitoring dashboards (auto-approved for engineering)
- CI/CD pipeline (team lead approves)
""",
        "architecture-overview.md": """# Architecture Overview

## System Design
The platform follows a microservices architecture with the following core services:
- **API Gateway**: Routes requests, handles auth, rate limiting
- **User Service**: Authentication, authorization, profile management
- **Data Service**: CRUD operations, data validation, caching
- **Notification Service**: Email, SMS, push notifications
- **Analytics Service**: Event tracking, reporting, dashboards

## Communication
Services communicate via:
- Synchronous: REST APIs for request/response
- Asynchronous: Message queue (RabbitMQ) for events
- Real-time: WebSocket for live updates

## Data Storage
- PostgreSQL for relational data (users, transactions)
- Redis for caching and session storage
- S3-compatible storage for files and media
""",
        "incident-response.md": """# Incident Response Playbook

## Severity Levels
- **P0 (Critical)**: Service completely down, data loss risk. Response: 15 minutes.
- **P1 (High)**: Major feature broken, significant user impact. Response: 1 hour.
- **P2 (Medium)**: Feature degraded, workaround available. Response: 4 hours.
- **P3 (Low)**: Minor issue, cosmetic, no user impact. Response: next business day.

## Response Procedure
1. Acknowledge the incident in #incidents channel
2. Assign an incident commander
3. Create a war room (video call link in channel topic)
4. Investigate, mitigate, resolve
5. Post-mortem within 48 hours for P0/P1

## Escalation Path
On-call engineer → Team lead → Engineering manager → VP Engineering
""",
        "api-conventions.md": """# API Conventions

## URL Structure
- Use kebab-case for URLs: `/api/user-profiles`
- Version in URL: `/api/v1/resources`
- Plural nouns for collections: `/api/v1/users`
- Nested resources max 2 levels: `/api/v1/users/{id}/orders`

## Response Format
All responses follow this structure:
```json
{
  "data": {},
  "meta": {"page": 1, "total": 100},
  "errors": []
}
```

## Error Codes
- 400: Bad Request (validation error, include field-level details)
- 401: Unauthorized (missing or invalid token)
- 403: Forbidden (valid token, insufficient permissions)
- 404: Not Found
- 429: Rate Limited (include Retry-After header)
- 500: Internal Server Error (log correlation ID, return generic message)
""",
    }

    for filename, content in docs.items():
        filepath = KNOWLEDGE_DIR / filename
        if not filepath.exists():
            filepath.write_text(content)
            logger.info(f"Created mock document: {filename}")


def _search_documents(query: str, max_results: int = MAX_RESULTS) -> list[dict]:
    """Simple keyword search over markdown files. Replace with vector search for production."""
    results = []
    query_terms = set(query.lower().split())

    for filepath in KNOWLEDGE_DIR.glob("**/*.md"):
        content = filepath.read_text()
        content_lower = content.lower()

        # Score by term frequency (naive — replace with embeddings for production)
        score = sum(content_lower.count(term) for term in query_terms)
        if score == 0:
            continue

        # Extract best matching excerpt
        excerpt = _extract_excerpt(content, query_terms)

        results.append({
            "source": str(filepath.relative_to(KNOWLEDGE_DIR)),
            "title": _extract_title(content),
            "score": score,
            "excerpt": excerpt,
        })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:max_results]


def _extract_title(content: str) -> str:
    """Extract the first H1 heading as the document title."""
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    return match.group(1) if match else "Untitled"


def _extract_excerpt(content: str, query_terms: set[str]) -> str:
    """Extract a relevant excerpt around the first matching term."""
    content_lower = content.lower()
    best_pos = len(content)

    for term in query_terms:
        pos = content_lower.find(term)
        if 0 <= pos < best_pos:
            best_pos = pos

    start = max(0, best_pos - EXCERPT_LENGTH // 4)
    end = min(len(content), start + EXCERPT_LENGTH)
    excerpt = content[start:end].strip()

    if start > 0:
        excerpt = "..." + excerpt
    if end < len(content):
        excerpt = excerpt + "..."

    return excerpt


@mcp.tool()
def search_knowledge(query: str, max_results: int = 5) -> dict:
    """
    Search the knowledge base for documents matching a query.

    Args:
        query: Natural language search query.
        max_results: Maximum number of results to return (1-10).

    Returns:
        Matching documents with title, source path, relevance score, and excerpt.
    """
    max_results = min(max(max_results, 1), 10)
    results = _search_documents(query, max_results)

    return {
        "query": query,
        "results": results,
        "total_found": len(results),
        "knowledge_base": str(KNOWLEDGE_DIR),
    }


@mcp.tool()
def get_document(path: str) -> dict:
    """
    Retrieve the full content of a knowledge base document.

    Args:
        path: Relative path to the document (from search results).

    Returns:
        Full document content and metadata.
    """
    filepath = KNOWLEDGE_DIR / path
    if not filepath.exists():
        return {"error": f"Document not found: {path}"}
    if not filepath.resolve().is_relative_to(KNOWLEDGE_DIR.resolve()):
        return {"error": "Access denied — path traversal detected"}

    content = filepath.read_text()
    return {
        "path": path,
        "title": _extract_title(content),
        "content": content,
        "size_bytes": len(content.encode()),
    }


@mcp.tool()
def list_documents() -> dict:
    """
    List all documents in the knowledge base.

    Returns:
        List of available documents with titles and paths.
    """
    docs = []
    for filepath in sorted(KNOWLEDGE_DIR.glob("**/*.md")):
        content = filepath.read_text()
        docs.append({
            "path": str(filepath.relative_to(KNOWLEDGE_DIR)),
            "title": _extract_title(content),
            "size_bytes": len(content.encode()),
        })

    return {"documents": docs, "total": len(docs)}


if __name__ == "__main__":
    _init_mock_knowledge()
    mcp.run(transport="streamable-http", host="0.0.0.0", port=PORT)
