"""
MCP Server Pattern: Agent Delegation
======================================
Demonstrates hub-and-spoke orchestration by calling other LibreChat agents via the Agents API.

Pattern: Orchestrator agent calls `delegate_to_agent(agent_id, task)` → this tool makes an
HTTP request to LibreChat's OpenAI-compatible Agents API → specialist agent processes the
task → result returned to the orchestrator.

This enables coordination patterns that neither Agent Chain (sequential only) nor Agent
Handoffs (dynamic but conversation-level) support — e.g., parallel fan-out to researchers,
then synthesis by the orchestrator.

Requires: A running LibreChat instance with multiple agents configured.
"""

import os
import logging

import httpx
from fastmcp import FastMCP

logging.basicConfig(level=os.getenv("MCP_LOG_LEVEL", "INFO").upper())
logger = logging.getLogger(__name__)

LIBRECHAT_API_URL = os.getenv("LIBRECHAT_API_URL", "http://api:3080")
LIBRECHAT_API_KEY = os.getenv("LIBRECHAT_API_KEY", "")
PORT = int(os.getenv("PORT", "8004"))
TIMEOUT = float(os.getenv("DELEGATE_TIMEOUT", "120"))

mcp = FastMCP(
    "Agent Delegation",
    description="Delegate tasks to specialist LibreChat agents",
)


@mcp.tool()
async def list_available_agents() -> dict:
    """
    List all agents available for delegation.

    Returns:
        Available agents with their IDs, names, and descriptions.
    """
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{LIBRECHAT_API_URL}/api/agents/v1/models",
                headers={"Authorization": f"Bearer {LIBRECHAT_API_KEY}"},
            )
            resp.raise_for_status()
            data = resp.json()

            agents = []
            for model in data.get("data", []):
                agents.append({
                    "agent_id": model["id"],
                    "name": model.get("name", model["id"]),
                    "description": model.get("description", ""),
                })

            return {"agents": agents, "total": len(agents)}

    except httpx.HTTPError as e:
        logger.error(f"Failed to list agents: {e}")
        return {"error": f"Failed to list agents: {str(e)}", "agents": []}


@mcp.tool()
async def delegate_to_agent(agent_id: str, task: str, context: str = "") -> dict:
    """
    Delegate a task to a specialist agent and return its response.

    The specialist agent runs independently — it has its own tools, system prompt,
    and capabilities. Use this when a task requires expertise that the current agent
    doesn't have.

    Args:
        agent_id: The ID of the specialist agent (from list_available_agents).
        task: Clear description of what the specialist should do.
        context: Optional context to pass to the specialist (data, constraints, prior findings).

    Returns:
        The specialist agent's response text.
    """
    messages = []
    if context:
        messages.append({"role": "user", "content": f"Context:\n{context}"})
        messages.append({"role": "assistant", "content": "Understood. I have the context."})
    messages.append({"role": "user", "content": task})

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(
                f"{LIBRECHAT_API_URL}/api/agents/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {LIBRECHAT_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": agent_id,
                    "messages": messages,
                    "stream": False,
                },
            )
            resp.raise_for_status()
            data = resp.json()

            response_text = data["choices"][0]["message"]["content"]
            return {
                "agent_id": agent_id,
                "task": task,
                "response": response_text,
                "usage": data.get("usage", {}),
            }

    except httpx.HTTPStatusError as e:
        logger.error(f"Agent delegation failed: {e.response.status_code} {e.response.text}")
        return {
            "error": f"Agent returned {e.response.status_code}",
            "agent_id": agent_id,
            "task": task,
        }
    except httpx.HTTPError as e:
        logger.error(f"Agent delegation failed: {e}")
        return {"error": str(e), "agent_id": agent_id, "task": task}


@mcp.tool()
async def delegate_parallel(tasks: list[dict]) -> dict:
    """
    Delegate multiple tasks to specialist agents in parallel.

    Each task in the list should have: agent_id, task, and optional context.
    All tasks run concurrently — use this for fan-out patterns where multiple
    specialists research different aspects of the same question.

    Args:
        tasks: List of dicts, each with 'agent_id' (str), 'task' (str), and optional 'context' (str).

    Returns:
        Results from all specialists, in the same order as the input tasks.
    """
    import asyncio

    if len(tasks) > 10:
        return {"error": "Maximum 10 parallel delegations allowed"}

    async def _run_one(t: dict) -> dict:
        return await delegate_to_agent(
            agent_id=t["agent_id"],
            task=t["task"],
            context=t.get("context", ""),
        )

    results = await asyncio.gather(*[_run_one(t) for t in tasks], return_exceptions=True)

    return {
        "results": [
            r if isinstance(r, dict) else {"error": str(r)}
            for r in results
        ],
        "total": len(results),
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=PORT)
