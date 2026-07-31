#!/usr/bin/env python3
"""Sequential pipeline: research → write → edit.

Demonstrates the >> operator for chaining agents sequentially.
Each agent's output becomes the next agent's input.

Prerequisites:
  pip install agentspan
  agentspan server start
  export OPENAI_API_KEY=sk-...

Usage:
  python sequential_pipeline.py [topic]
"""

import os
import sys
from agentspan.agents import Agent, AgentRuntime

model = os.environ.get("AGENTSPAN_LLM_MODEL", "openai/gpt-4o-mini")

researcher = Agent(
    name="researcher",
    model=model,
    instructions=(
        "You are a researcher. Given a topic, provide key facts and data points. "
        "Be thorough but concise. Output raw research findings only."
    ),
)

writer = Agent(
    name="writer",
    model=model,
    instructions=(
        "You are a writer. Take research findings and write a clear, engaging "
        "article. Use headers and bullet points where appropriate."
    ),
)

editor = Agent(
    name="editor",
    model=model,
    instructions=(
        "You are an editor. Review the article for clarity, grammar, and tone. "
        "Make improvements and output the final polished version."
    ),
)

# Chain agents sequentially with >>
pipeline = researcher >> writer >> editor

topic = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "The rise of AI coding agents in 2025"

if __name__ == "__main__":
    print(f"Running pipeline on topic: {topic}\n")
    with AgentRuntime() as runtime:
        result = runtime.run(pipeline, topic)
        result.print_result()
