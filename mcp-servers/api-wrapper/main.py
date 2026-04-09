"""
MCP Server Pattern: API Wrapper
================================
Demonstrates wrapping an external REST API as MCP tools.

Pattern: Agent calls MCP tool → tool calls external API → normalizes response → returns to agent.
This decouples the agent from API authentication, pagination, error handling, and response shaping.

Replace the mock API calls with your real external service.
"""

import os
import logging
from datetime import datetime, timezone

import httpx
from fastmcp import FastMCP

logging.basicConfig(level=os.getenv("MCP_LOG_LEVEL", "INFO").upper())
logger = logging.getLogger(__name__)

API_BASE_URL = os.getenv("API_BASE_URL", "https://api.example.com")
API_KEY = os.getenv("API_KEY", "")
PORT = int(os.getenv("PORT", "8002"))

mcp = FastMCP(
    "API Wrapper",
    description="Access external services through normalized MCP tools",
)

# --- Mock data (replace with real API calls) ---

MOCK_WEATHER = {
    "new york": {"temp_c": 18, "condition": "Partly cloudy", "humidity": 65},
    "london": {"temp_c": 12, "condition": "Overcast", "humidity": 80},
    "tokyo": {"temp_c": 22, "condition": "Clear", "humidity": 55},
    "são paulo": {"temp_c": 28, "condition": "Thunderstorms", "humidity": 90},
}

MOCK_EXCHANGE = {
    "USD": 1.0, "EUR": 0.92, "GBP": 0.79, "JPY": 149.5, "BRL": 5.05, "CAD": 1.36,
}


@mcp.tool()
def get_weather(city: str) -> dict:
    """
    Get current weather for a city.

    Args:
        city: City name (e.g., "New York", "London", "Tokyo").

    Returns:
        Temperature, conditions, humidity, and timestamp.
    """
    # --- MOCK: Replace with real API call ---
    # Real implementation:
    # async with httpx.AsyncClient() as client:
    #     resp = await client.get(
    #         f"{API_BASE_URL}/weather",
    #         params={"q": city, "appid": API_KEY},
    #     )
    #     resp.raise_for_status()
    #     data = resp.json()
    #     return {"temp_c": data["main"]["temp"], ...}

    normalized = city.lower().strip()
    if normalized not in MOCK_WEATHER:
        return {
            "error": f"City not found: {city}",
            "available_cities": list(MOCK_WEATHER.keys()),
        }

    data = MOCK_WEATHER[normalized]
    return {
        "city": city,
        "temperature_celsius": data["temp_c"],
        "condition": data["condition"],
        "humidity_percent": data["humidity"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "mock_data",
    }


@mcp.tool()
def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    """
    Convert between currencies using current exchange rates.

    Args:
        amount: Amount to convert.
        from_currency: Source currency code (e.g., "USD", "EUR").
        to_currency: Target currency code (e.g., "BRL", "GBP").

    Returns:
        Converted amount, rate, and timestamp.
    """
    from_code = from_currency.upper().strip()
    to_code = to_currency.upper().strip()

    if from_code not in MOCK_EXCHANGE:
        return {"error": f"Unknown currency: {from_code}", "available": list(MOCK_EXCHANGE.keys())}
    if to_code not in MOCK_EXCHANGE:
        return {"error": f"Unknown currency: {to_code}", "available": list(MOCK_EXCHANGE.keys())}

    rate = MOCK_EXCHANGE[to_code] / MOCK_EXCHANGE[from_code]
    return {
        "from": from_code,
        "to": to_code,
        "amount": amount,
        "converted": round(amount * rate, 2),
        "rate": round(rate, 6),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "mock_data",
    }


@mcp.tool()
def search_external_api(query: str, max_results: int = 5) -> dict:
    """
    Search an external service and return normalized results.
    Demonstrates pagination handling and response normalization.

    Args:
        query: Search query string.
        max_results: Maximum number of results (1-20).

    Returns:
        Normalized search results with title, snippet, and source URL.
    """
    max_results = min(max(max_results, 1), 20)

    # --- MOCK: Replace with real API call ---
    # Real implementation:
    # async with httpx.AsyncClient() as client:
    #     results = []
    #     page = 1
    #     while len(results) < max_results:
    #         resp = await client.get(f"{API_BASE_URL}/search", params={"q": query, "page": page})
    #         data = resp.json()
    #         results.extend(data["items"])
    #         if not data.get("next_page"):
    #             break
    #         page += 1
    #     return {"results": results[:max_results], "total": data["total"]}

    return {
        "query": query,
        "results": [
            {
                "title": f"Result {i+1} for '{query}'",
                "snippet": f"This is a mock result demonstrating the API wrapper pattern.",
                "url": f"https://example.com/results/{i+1}",
                "relevance_score": round(1.0 - (i * 0.15), 2),
            }
            for i in range(max_results)
        ],
        "total_available": 42,
        "source": "mock_data",
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=PORT)
