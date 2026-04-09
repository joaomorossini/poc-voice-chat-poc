# Pattern: API Wrapper

Wraps external REST APIs as MCP tools, decoupling agents from authentication, pagination, and error handling.

## How It Works

1. Agent calls an MCP tool (e.g., `get_weather("Tokyo")`)
2. Tool handles authentication, makes HTTP request to external API
3. Tool normalizes the response into a consistent structure
4. Agent receives clean data, never sees raw API responses

## When to Use

- Integrating with third-party APIs (weather, payment, CRM, etc.)
- You need to hide API keys from the agent
- External API responses need normalization or pagination handling
- Multiple agents should share the same API access with consistent behavior

## Customization

1. Replace mock functions with real `httpx` calls to your API
2. Set `API_BASE_URL` and `API_KEY` via environment variables
3. Add rate limiting, caching, or circuit breakers as needed

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_BASE_URL` | `https://api.example.com` | Base URL for the external API |
| `API_KEY` | (empty) | API authentication key |
| `PORT` | `8002` | Server port |
| `MCP_LOG_LEVEL` | `INFO` | Logging level |
