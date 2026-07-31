#!/usr/bin/env python3
"""Basic agent with custom @tool functions.

Prerequisites:
  pip install agentspan
  agentspan server start
  export OPENAI_API_KEY=sk-...

Usage:
  python basic_agent_with_tools.py
"""

from agentspan.agents import Agent, AgentRuntime, tool


@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    # Simulated — replace with a real API call
    weather_data = {
        "new york": "72°F, partly cloudy",
        "london": "59°F, rainy",
        "tokyo": "81°F, sunny",
    }
    return weather_data.get(city.lower(), f"No data for {city}")


@tool
def calculate(expression: str) -> str:
    """Evaluate a math expression safely."""
    try:
        # Only allow basic arithmetic for safety
        allowed = set("0123456789+-*/(). ")
        if not all(c in allowed for c in expression):
            return "Error: only basic arithmetic is supported"
        result = eval(expression)  # noqa: S307 — safe due to allowlist above
        return str(result)
    except Exception as e:
        return f"Error: {e}"


@tool(name="search_docs", timeout_seconds=30)
def search_documentation(query: str) -> str:
    """Search product documentation for a query."""
    # Simulated — replace with a real search API
    docs = {
        "pricing": "Our Pro plan is $29/mo. Enterprise is custom pricing.",
        "api": "REST API base URL: https://api.example.com/v1. Auth: Bearer token.",
        "setup": "Quick start: pip install agentspan, then agentspan server start.",
    }
    for keyword, answer in docs.items():
        if keyword in query.lower():
            return answer
    return "No documentation found for that query."


agent = Agent(
    name="helper",
    model="openai/gpt-4o-mini",
    instructions="You are a helpful assistant. Use tools when relevant.",
    tools=[get_weather, calculate, search_documentation],
    max_turns=10,
)


if __name__ == "__main__":
    with AgentRuntime() as runtime:
        result = runtime.run(agent, "What's the weather in Tokyo? Also, what's 15% of 340?")
        result.print_result()
