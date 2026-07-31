#!/usr/bin/env python3
"""Guardrail usage demo.

Demonstrates all 4 OnFail modes and the 3 guardrail types:
  - Custom @guardrail functions
  - RegexGuardrail
  - LLMGuardrail

Prerequisites:
  pip install agentspan
  agentspan server start
  export OPENAI_API_KEY=sk-...

Usage:
  python guardrail_demo.py
"""

import json
import re
from agentspan.agents import (
    Agent, AgentRuntime, Guardrail, GuardrailResult, guardrail,
    OnFail, Position, RegexGuardrail, LLMGuardrail,
)


# ── Custom guardrails ─────────────────────────────────────────────────────────

@guardrail
def word_limit(content: str) -> GuardrailResult:
    """Keep responses under 100 words. RETRY on failure."""
    word_count = len(content.split())
    if word_count > 100:
        return GuardrailResult(
            passed=False,
            message=f"Response is {word_count} words. Keep it under 100 words.",
        )
    return GuardrailResult(passed=True)


@guardrail
def no_jailbreak(content: str) -> GuardrailResult:
    """Block jailbreak attempts. RAISE on failure."""
    red_flags = ["ignore previous instructions", "act as if", "jailbreak", "system prompt"]
    found = [f for f in red_flags if f in content.lower()]
    if found:
        return GuardrailResult(passed=False, message=f"Blocked: detected '{found[0]}'")
    return GuardrailResult(passed=True)


@guardrail
def ensure_json(content: str) -> GuardrailResult:
    """Ensure output is valid JSON. FIX on failure."""
    try:
        json.loads(content)
        return GuardrailResult(passed=True)
    except json.JSONDecodeError:
        return GuardrailResult(
            passed=False,
            message="Output must be valid JSON.",
            fixed_output='{"status": "error", "message": "Could not generate valid JSON"}',
        )


@guardrail
def no_pii(content: str) -> GuardrailResult:
    """Reject responses containing email addresses. RETRY on failure."""
    if re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", content):
        return GuardrailResult(passed=False, message="Response contains PII (email). Remove it.")
    return GuardrailResult(passed=True)


# ── Regex guardrails ──────────────────────────────────────────────────────────

no_ssn = RegexGuardrail(
    patterns=[r"\b\d{3}-\d{2}-\d{4}\b"],
    name="no_ssn",
    message="Do not include Social Security Numbers.",
    on_fail=OnFail.RAISE,
)

no_profanity = RegexGuardrail(
    patterns=r"\b(damn|hell|crap)\b",
    mode="block",
    name="no_profanity",
    on_fail=OnFail.RETRY,
)


# ── LLM guardrail ────────────────────────────────────────────────────────────

factual_check = LLMGuardrail(
    model="openai/gpt-4o-mini",
    policy="Is this response factually accurate and helpful? Reply YES or NO with a brief explanation.",
    on_fail=OnFail.RETRY,
    max_retries=2,
)


# ── Agents with different guardrail configurations ─────────────────────────────

# Agent 1: Input + output guardrails, retry mode
safe_agent = Agent(
    name="safe_bot",
    model="openai/gpt-4o-mini",
    instructions="You are a helpful assistant. Be concise and accurate. Never include personal data.",
    guardrails=[
        Guardrail(no_jailbreak, position=Position.INPUT, on_fail=OnFail.RAISE),
        Guardrail(no_pii, position=Position.OUTPUT, on_fail=OnFail.RETRY, max_retries=3),
        Guardrail(word_limit, on_fail=OnFail.RETRY),
        no_ssn,
    ],
    max_turns=10,
)

# Agent 2: Auto-fix mode for structured output
json_agent = Agent(
    name="json_bot",
    model="openai/gpt-4o-mini",
    instructions="You return data in JSON format. Always respond with valid JSON.",
    guardrails=[
        Guardrail(ensure_json, on_fail=OnFail.FIX),
    ],
    max_turns=5,
)

# Agent 3: LLM-as-judge
review_agent = Agent(
    name="review_bot",
    model="openai/gpt-4o-mini",
    instructions="You provide factual answers about technology topics.",
    guardrails=[
        factual_check,
        no_profanity,
    ],
    max_turns=10,
)


if __name__ == "__main__":
    with AgentRuntime() as runtime:
        print("=== Safe agent (input/output guardrails) ===")
        result = runtime.run(safe_agent, "What are the best practices for API security?")
        result.print_result()

        print("\n=== JSON agent (auto-fix mode) ===")
        result2 = runtime.run(json_agent, "Return a JSON object with the top 3 programming languages and their use cases.")
        result2.print_result()

        print("\n=== Review agent (LLM-as-judge) ===")
        result3 = runtime.run(review_agent, "What is the difference between REST and GraphQL?")
        result3.print_result()
