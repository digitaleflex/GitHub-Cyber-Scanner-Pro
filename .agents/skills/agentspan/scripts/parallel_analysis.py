#!/usr/bin/env python3
"""Parallel analysis: multiple perspectives evaluated concurrently.

Demonstrates the 'parallel' strategy where sub-agents run simultaneously.

Prerequisites:
  pip install agentspan
  agentspan server start
  export OPENAI_API_KEY=sk-...

Usage:
  python parallel_analysis.py [topic]
"""

import os
import sys
from agentspan.agents import Agent, AgentRuntime

model = os.environ.get("AGENTSPAN_LLM_MODEL", "openai/gpt-4o-mini")

market_analyst = Agent(
    name="market_analyst",
    model=model,
    instructions="Analyze the market opportunity: size, growth, competition. Be specific with numbers.",
)

risk_analyst = Agent(
    name="risk_analyst",
    model=model,
    instructions="Analyze the risks: regulatory, technical, market. Rate each risk HIGH/MEDIUM/LOW.",
)

financial_analyst = Agent(
    name="financial_analyst",
    model=model,
    instructions="Analyze the financial projections: revenue, costs, runway, unit economics.",
)

# Parallel strategy runs all sub-agents concurrently
analysis_team = Agent(
    name="analysis_team",
    model=model,
    agents=[market_analyst, risk_analyst, financial_analyst],
    strategy="parallel",
    instructions="Coordinate the analysis. Each analyst works independently.",
)

topic = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Launching an AI-powered code review tool"

if __name__ == "__main__":
    print(f"Running parallel analysis on: {topic}\n")
    with AgentRuntime() as runtime:
        result = runtime.run(analysis_team, topic)
        # Access individual results
        if hasattr(result, "sub_results"):
            print("=== Market Analysis ===")
            print(result.sub_results.get("market_analyst", "N/A"))
            print("\n=== Risk Analysis ===")
            print(result.sub_results.get("risk_analyst", "N/A"))
            print("\n=== Financial Analysis ===")
            print(result.sub_results.get("financial_analyst", "N/A"))
        else:
            result.print_result()
