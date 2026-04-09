# Pattern: Agent Delegation

Hub-and-spoke multi-agent orchestration via LibreChat's Agents API.

## How It Works

1. Orchestrator agent needs specialist help (research, review, domain expertise)
2. Calls `delegate_to_agent(agent_id, task, context)` or `delegate_parallel(tasks)`
3. This tool makes an HTTP request to LibreChat's OpenAI-compatible Agents API
4. Specialist agent processes the task with its own tools and system prompt
5. Result returned to the orchestrator for synthesis

## When to Use

- An orchestrator needs to coordinate multiple specialists (researcher, reviewer, writer)
- You want parallel fan-out (ask 3 specialists the same question from different angles)
- Agent Chain (sequential) or Handoffs (conversation-level) don't fit your coordination pattern
- You need an agent to call another agent programmatically, not just hand off the conversation

## Architecture

```
Orchestrator Agent (via LibreChat UI)
  ├─ delegate_to_agent("researcher", "Find pricing data for...") → Researcher Agent
  ├─ delegate_to_agent("analyst", "Compare these two approaches...") → Analyst Agent
  └─ delegate_parallel([...]) → Multiple agents in parallel
```

Each specialist is a full LibreChat agent with its own prompt, tools, and capabilities.
The orchestrator sees only the final response text.

## Caveats

- Each delegation is a full LLM round-trip — latency adds up
- The specialist has no access to the orchestrator's conversation history (only what you pass as context)
- Costs multiply (orchestrator + each specialist)
- Max 10 parallel delegations per call

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LIBRECHAT_API_URL` | `http://api:3080` | LibreChat instance URL |
| `LIBRECHAT_API_KEY` | (empty) | API key for authentication |
| `DELEGATE_TIMEOUT` | `120` | Timeout per delegation in seconds |
| `PORT` | `8004` | Server port |
| `MCP_LOG_LEVEL` | `INFO` | Logging level |
