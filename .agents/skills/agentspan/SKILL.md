---
name: agentspan
description: Comprehensive Agentspan durable workflow orchestration skill for creating, running, scheduling, monitoring, and debugging AI agent workflows using the Agentspan Python SDK and CLI. Covers agents, tools, multi-agent strategies, guardrails, memory, streaming, human-in-the-loop, testing, and production deployment.
---

# Agentspan: Durable AI Agent Workflow Orchestration

> **Expert AI Agent for Agentspan Workflows**
> Create, run, schedule, monitor, and debug durable AI agent workflows using the Agentspan Python SDK and CLI.

## What I Do

I am an expert Agentspan workflow architect and developer. I help you build reliable, scalable, and fault-tolerant AI agent systems using Agentspan's durable execution runtime.

**Agentspan guarantees your agent workflows complete successfully, even through:**
- Worker process crashes and restarts
- Server failures and deployments
- Long-running operations (hours/days/weeks)
- Human-in-the-loop approval delays
- Network partitions and timeouts

## Core Capabilities

| Capability | Description |
|------------|-------------|
| **Create** | Design and implement agents, tools, multi-agent strategies, guardrails, and memory systems |
| **Run** | Execute agent workflows locally or against a remote server |
| **Schedule** | Set up recurring agent runs and batch processing |
| **Monitor** | Stream events, query status, inspect execution history |
| **Debug** | Troubleshoot failed executions, replay events, analyze errors |
| **Test** | Mock agent behavior, record/replay, pytest integration |

## When to Use Agentspan

| Use Case | Use Agentspan | Use Dagu | Use Temporal |
|----------|---------------|-----------|--------------|
| AI agent orchestration | ✅ Perfect fit | ❌ Not designed for agents | ⚠️ Overkill, no agent primitives |
| Multi-agent pipelines (research→write→edit) | ✅ Built-in strategies | ⚠️ Possible but manual | ⚠️ No agent primitives |
| Human-in-the-loop approval flows | ✅ Built-in HITL | ⚠️ Manual approval gates | ✅ Signals/queries |
| LLM tool-calling workflows | ✅ First-class @tool support | ❌ No LLM integration | ❌ No LLM integration |
| Cron-style task scheduling | ✅ Agent + CLI | ✅ Perfect fit | ✅ Built-in |
| Simple shell script orchestration | ❌ Overkill | ✅ Perfect fit | ❌ Overkill |
| Durable business process (multi-day) | ⚠️ Can work | ❌ Not designed for it | ✅ Designed for it |
| Batch document processing | ✅ Parallel agents | ✅ Sequential steps | ⚠️ Overkill |

## Quick Start

```bash
# Install
pip install agentspan

# Verify setup
agentspan doctor

# Set API key
export OPENAI_API_KEY=sk-...

# Start the server (downloads JAR on first run)
agentspan server start
# UI at http://localhost:6767

# Run your first agent
python hello.py
```

```python
# hello.py
from agentspan.agents import Agent, AgentRuntime, tool

@tool
def get_weather(city: str) -> str:
    """Get current weather for a city."""
    return f"72°F and sunny in {city}"

agent = Agent(name="weatherbot", model="openai/gpt-4o", tools=[get_weather])

with AgentRuntime() as runtime:
    result = runtime.run(agent, "What's the weather in NYC?")
    result.print_result()
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                  Agentspan Server                     │
│         (port 6767, SQLite or PostgreSQL)            │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Workflow  │  │ Task     │  │ Execution History │  │
│  │ Engine    │  │ Queue    │  │ & State Store     │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
│         │             │                │              │
└─────────┼─────────────┼────────────────┼───────────┘
          │             │                │
          ▼             ▼                ▼
┌──────────────────────────────────────────────────────┐
│               Python Worker Process                   │
│                                                       │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐             │
│  │ @tool   │  │ http_   │  │ mcp_    │             │
│  │ Python  │  │ tool()  │  │ tool()  │             │
│  │ funcs   │  │ (server)│  │ (server)│             │
│  └─────────┘  └─────────┘  └─────────┘             │
│                                                       │
│  AgentRuntime manages the worker lifecycle            │
└──────────────────────────────────────────────────────┘
```

**Key principle:** `@tool` functions run in your Python worker process (full access to code, libraries, local state). `http_tool()`, `api_tool()`, `mcp_tool()` run server-side (no code to write).

## CLI Reference

See `references/cli-quick-reference.md` for the full CLI command reference.

```bash
# Server management
agentspan server start          # Start server (downloads JAR on first run)
agentspan server stop           # Stop server
agentspan server logs            # View server logs

# Credentials
agentspan credentials set KEY value    # Store encrypted credential
agentspan credentials list             # List credential keys
agentspan credentials delete KEY       # Delete a credential

# Agent operations
agentspan agent status <exec-id>       # Check execution status
agentspan agent list                    # List registered agents
agentspan agent run --name my_agent "prompt"  # Run and stream
agentspan agent execution --since 1h    # View execution history

# Diagnostics
agentspan doctor                       # Check system dependencies

# Configuration
agentspan configure --url https://server.example.com
```

## Agent Definition

```python
from agentspan.agents import Agent, AgentRuntime

agent = Agent(
    name="my_agent",                    # Unique name (becomes workflow name)
    model="openai/gpt-4o",              # Provider/model format
    instructions="You are helpful.",    # System prompt (str or callable)
    tools=[...],                        # @tool functions or ToolDefs
    agents=[...],                        # Sub-agents for multi-agent
    strategy="handoff",                  # Multi-agent strategy
    router=None,                         # Router agent or function
    output_type=None,                    # Pydantic BaseModel for structured output
    guardrails=[...],                    # Input/output validation
    memory=None,                         # ConversationMemory or SemanticMemory
    dependencies={...},                  # Injected into ToolContext
    max_turns=25,                        # Max agent loop iterations
    max_tokens=None,                     # LLM max tokens
    temperature=None,                    # LLM temperature
    stop_when=None,                      # Early termination condition
    metadata=None,                       # Arbitrary metadata
)
```

## Tools

### @tool — Custom Python Functions

```python
from agentspan.agents import Agent, AgentRuntime, tool

@tool
def get_weather(city: str) -> dict:
    """Get current weather for a city."""
    return {"city": city, "temp": 72, "condition": "Sunny"}

@tool(name="custom_name", approval_required=True, timeout_seconds=60)
def dangerous_action(target: str) -> dict:
    """Do something that requires human approval."""
    return {"done": True}

agent = Agent(name="bot", model="openai/gpt-4o", tools=[get_weather])
```

### ToolContext — Shared State and Dependencies

```python
from agentspan.agents import tool, ToolContext

@tool
def query_database(query: str, context: ToolContext) -> dict:
    """Run a database query."""
    db = context.dependencies["db"]
    user_id = context.dependencies["user_id"]
    return db.execute(query, user=user_id)

agent = Agent(
    name="bot", model="openai/gpt-4o",
    tools=[query_database],
    dependencies={"db": my_database, "user_id": "u-123"},
)
```

### http_tool — HTTP Endpoints (Server-Side)

```python
from agentspan.agents import http_tool

weather = http_tool(
    name="get_weather",
    description="Get weather for a city",
    url="https://api.weather.com/v1/current",
    method="GET",
    headers={"Authorization": "Bearer ${WEATHER_KEY}"},
    input_schema={
        "type": "object",
        "properties": {"city": {"type": "string"}},
        "required": ["city"],
    },
    credentials=["WEATHER_KEY"],
)
```

### api_tool — OpenAPI Auto-Discovery (Server-Side)

```python
from agentspan.agents import api_tool

stripe = api_tool(
    url="https://api.stripe.com/openapi.json",
    headers={"Authorization": "Bearer ${STRIPE_KEY}"},
    credentials=["STRIPE_KEY"],
    max_tools=20,  # LLM auto-filters to most relevant
)
```

### mcp_tool — MCP Servers (Server-Side)

```python
from agentspan.agents import mcp_tool

github = mcp_tool(
    server_url="http://localhost:3001/mcp",
    name="github",
    description="GitHub operations",
)
```

### Credential Management

```bash
# Store credentials (encrypted at rest with AES-256-GCM)
agentspan credentials set GITHUB_TOKEN ghp_xxxxxxxxxxxx
agentspan credentials set STRIPE_API_KEY sk_live_xxxxxxxx
```

```python
# Option A: Isolated subprocess (credentials as env vars)
@tool(credentials=["GITHUB_TOKEN"])
def list_repos(username: str) -> dict:
    import os
    token = os.environ["GITHUB_TOKEN"]  # Auto-injected

# Option B: In-process (use get_credential)
@tool(isolated=False, credentials=["SEARCH_API_KEY"])
def search(query: str) -> dict:
    from agentspan.agents import get_credential
    key = get_credential("SEARCH_API_KEY")
```

## Multi-Agent Strategies

### Sequential Pipeline (a >> b >> c)

```python
researcher = Agent(name="researcher", model="openai/gpt-4o",
                   instructions="Research the topic thoroughly.")
writer = Agent(name="writer", model="openai/gpt-4o",
               instructions="Write an article from the research.")
editor = Agent(name="editor", model="openai/gpt-4o",
               instructions="Polish the article for publication.")

pipeline = researcher >> writer >> editor

with AgentRuntime() as runtime:
    result = runtime.run(pipeline, "AI agents in 2025")
```

### Parallel

```python
market = Agent(name="market", model="openai/gpt-4o",
               instructions="Analyze market size and growth.")
risk = Agent(name="risk", model="openai/gpt-4o",
             instructions="Analyze risks.")
financial = Agent(name="financial", model="openai/gpt-4o",
                  instructions="Analyze financial projections.")

analysis = Agent(
    name="analysis",
    model="openai/gpt-4o",
    agents=[market, risk, financial],
    strategy="parallel",
)

with AgentRuntime() as runtime:
    result = runtime.run(analysis, "Launching an AI healthcare tool")
    print(result.sub_results["market"])
    print(result.sub_results["risk"])
    print(result.sub_results["financial"])
```

### Handoff (Default)

```python
billing = Agent(name="billing", model="openai/gpt-4o",
                instructions="Handle billing inquiries.", tools=[check_balance])
technical = Agent(name="technical", model="openai/gpt-4o",
                  instructions="Handle technical issues.")

support = Agent(
    name="support",
    model="openai/gpt-4o",
    instructions="Route customer requests to the right team.",
    agents=[billing, technical],
    strategy="handoff",
)
```

### Router

```python
# Router agent classifies and dispatches
classifier = Agent(
    name="classifier",
    model="openai/gpt-4o-mini",
    instructions="Classify: billing, technical, or general. Reply with just the category.",
)

support = Agent(
    name="support",
    model="openai/gpt-4o",
    agents=[billing, technical, general],
    strategy="router",
    router=classifier,
)

# Or use a Python function as router
def route(prompt: str) -> str:
    if "bill" in prompt.lower():
        return "billing"
    elif "error" in prompt.lower():
        return "technical"
    return "general"

support = Agent(name="support", agents=[billing, technical, general],
                strategy="router", router=route)
```

### Swarm (Condition-Based Handoffs)

```python
from agentspan.agents import Agent, AgentRuntime, Strategy
from agentspan.agents import TextMentionTermination

triage = Agent(name="triage", model="openai/gpt-4o",
               instructions="Triage requests. Say BILLING or TECH.")
billing = Agent(name="billing", model="openai/gpt-4o",
                instructions="Handle billing.")
technical = Agent(name="technical", model="openai/gpt-4o",
                  instructions="Handle technical issues.")

team = Agent(
    name="support_team",
    model="openai/gpt-4o",
    agents=[triage, billing, technical],
    strategy=Strategy.SWARM,
    handoffs=[
        TextMentionTermination("BILLING", target="billing"),
        TextMentionTermination("TECH", target="technical"),
    ],
)
```

### Strategy Summary

| Strategy | Description | Key Use |
|----------|-------------|---------|
| `handoff` | LLM chooses which sub-agent handles the request | Customer support, routing |
| `sequential` | Sub-agents run in order, output feeds forward | Research→Write→Edit pipelines |
| `parallel` | All sub-agents run concurrently | Multi-perspective analysis |
| `router` | Dedicated classifier selects sub-agent | Cost-optimized routing |
| `swarm` | Condition-based handoffs between agents | Complex multi-step support |
| `round_robin` | Agents take turns in fixed rotation | Debates, discussions |
| `random` | Random sub-agent each turn | Diverse output ensembles |
| `manual` | Human selects which agent runs next | Human-directed workflows |

## Guardrails

```python
from agentspan.agents import (
    Agent, Guardrail, GuardrailResult, guardrail,
    OnFail, Position, RegexGuardrail, LLMGuardrail,
)

# Custom guardrail function
@guardrail
def no_pii(content: str) -> GuardrailResult:
    """Reject responses containing email addresses."""
    import re
    if re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", content):
        return GuardrailResult(passed=False, message="Response contains PII (email). Remove it.")
    return GuardrailResult(passed=True)

# Regex guardrail
no_ssn = RegexGuardrail(
    patterns=[r"\b\d{3}-\d{2}-\d{4}\b"],
    name="no_ssn",
    message="Do not include SSNs.",
)

# LLM-as-judge guardrail
factual_check = LLMGuardrail(
    model="openai/gpt-4o-mini",
    policy="Is this response factually accurate? Reply YES or NO.",
    on_fail=OnFail.RETRY,
    max_retries=2,
)

agent = Agent(
    name="safe_bot",
    model="openai/gpt-4o",
    guardrails=[
        Guardrail(no_pii, on_fail=OnFail.RETRY, max_retries=3),
        no_ssn,
        factual_check,
    ],
)
```

### OnFail Modes

| Mode | Behavior |
|------|----------|
| `OnFail.RETRY` | Append feedback message and re-run the LLM (up to `max_retries`) |
| `OnFail.RAISE` | Fail the execution immediately |
| `OnFail.FIX` | Replace output with `GuardrailResult.fixed_output` |
| `OnFail.HUMAN` | Pause for human review (creates a WaitTask) |

### Input vs Output Guardrails

```python
# Input guardrail — validates user prompt before LLM call
Guardrail(no_jailbreak, position=Position.INPUT, on_fail=OnFail.RAISE)

# Output guardrail — validates LLM response (default)
Guardrail(no_pii, position=Position.OUTPUT, on_fail=OnFail.RETRY)
```

## Memory

### ConversationMemory — Chat History

```python
from agentspan.agents import Agent, AgentRuntime, ConversationMemory

memory = ConversationMemory(max_messages=100)

agent = Agent(name="assistant", model="openai/gpt-4o",
              instructions="You are a helpful assistant.", memory=memory)

with AgentRuntime() as runtime:
    result = runtime.run(agent, "My name is Alice.")
    memory.add_user_message("My name is Alice.")
    memory.add_assistant_message(result.output['result'])

    result2 = runtime.run(agent, "What's my name?")
    # "Your name is Alice."
```

### SemanticMemory — Long-Term Knowledge

```python
from agentspan.agents import Agent, AgentRuntime, tool
from agentspan.agents.semantic_memory import SemanticMemory

memory = SemanticMemory(max_results=3)
memory.add("Customer prefers email communication.")
memory.add("Account is on the Enterprise plan since March 2021.")

@tool
def get_context(query: str) -> str:
    """Retrieve relevant context from memory."""
    return memory.get_context(query)

agent = Agent(name="support", model="openai/gpt-4o",
              tools=[get_context])
```

## Human-in-the-Loop (HITL)

```python
from agentspan.agents import Agent, AgentRuntime, tool

@tool(approval_required=True)
def transfer_funds(from_acct: str, to_acct: str, amount: float) -> dict:
    """Transfer funds. Requires human approval."""
    return process_transfer(from_acct, to_acct, amount)

agent = Agent(name="banker", model="openai/gpt-4o", tools=[transfer_funds])

with AgentRuntime() as runtime:
    handle = runtime.start(agent, "Transfer $5000 from checking to savings")
    for event in handle.stream():
        if event.type == "waiting":
            # Human approves or rejects
            handle.approve()  # or handle.reject("Too risky")
```

CLI approval:
```bash
agentspan agent respond <execution-id> --approve
agentspan agent respond <execution-id> --deny --reason "Amount too large"
```

## Streaming

```python
from agentspan.agents import Agent, AgentRuntime

agent = Agent(name="writer", model="openai/gpt-4o")

with AgentRuntime() as runtime:
    for event in runtime.stream(agent, "Write a haiku about Python"):
        match event.type:
            case "thinking":      print(f"Thinking: {event.content}")
            case "tool_call":     print(f"Calling {event.tool_name}({event.args})")
            case "tool_result":   print(f"Result: {event.result}")
            case "handoff":       print(f"Delegating to {event.target}")
            case "waiting":       print("Waiting for human approval...")
            case "guardrail_pass": print(f"Guardrail passed: {event.guardrail_name}")
            case "guardrail_fail": print(f"Guardrail failed: {event.guardrail_name}")
            case "message":        print(f"Message: {event.content}")
            case "error":          print(f"Error: {event.content}")
            case "done":           print(f"\nFinal: {event.output}")
```

## Testing

```python
from agentspan.agents import Agent, tool
from agentspan.agents.testing import mock_run, MockEvent, expect

@tool
def search_web(query: str) -> str:
    """Search the web."""
    return "results"

agent = Agent(name="research_bot", model="openai/gpt-4o", tools=[search_web])

result = mock_run(
    agent,
    "What is agentspan?",
    events=[
        MockEvent.thinking("I should search for information about agentspan."),
        MockEvent.tool_call("search_web", {"query": "agentspan Python agent runtime"}),
        MockEvent.tool_result("search_web", "Agentspan is an open source Python runtime for AI agents."),
        MockEvent.done("Agentspan is an open source Python runtime for building AI agents."),
    ]
)

expect(result).completed().output_contains("Agentspan").used_tool("search_web")
```

### Record and Replay

```python
from agentspan.agents.testing import record, replay

# Record a real execution (calls LLM)
recording = record(agent, "What's the capital of France?")
recording.save("tests/fixtures/capital_query.json")

# Replay it deterministically (no LLM, no server)
result = replay("tests/fixtures/capital_query.json")
expect(result).completed().output_contains("Paris")
```

## Deployment

### Local Development (SQLite — Zero Setup)

```bash
agentspan server start
# Server at http://localhost:6767
# Data stored in agent-runtime.db
```

### Production (PostgreSQL + Docker Compose)

```bash
cd deployment/docker-compose
cp .env.example .env
# Set OPENAI_API_KEY in .env
docker compose up -d
```

### Kubernetes

```bash
# Helm chart available in deployment/helm/
# K8s manifests in deployment/k8s/
```

### Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVER_PORT` | `6767` | Server port |
| `SPRING_PROFILES_ACTIVE` | `default` (SQLite) | Set to `postgres` for PostgreSQL |
| `SPRING_DATASOURCE_URL` | `jdbc:sqlite:agent-runtime.db` | Database URL |
| `AGENTSPAN_SERVER_URL` | `http://localhost:6767` | Server URL for SDK/workers |
| `AGENTSPAN_AUTH_KEY` | — | Auth key (required for non-localhost) |
| `AGENTSPAN_AUTH_SECRET` | — | Auth secret (required for non-localhost) |

### LLM Providers

Set environment variables for the providers you need:

| Provider | Env Var | Model Prefix |
|----------|--------|-------------|
| OpenAI | `OPENAI_API_KEY` | `openai/` |
| Anthropic | `ANTHROPIC_API_KEY` | `anthropic/` |
| Google Gemini | `GEMINI_API_KEY` + `GOOGLE_CLOUD_PROJECT` | `google_gemini/` |
| Azure OpenAI | `AZURE_OPENAI_API_KEY` + endpoint + deployment | `azure_openai/` |
| AWS Bedrock | `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` | `aws_bedrock/` |
| Mistral | `MISTRAL_API_KEY` | `mistral/` |
| Ollama | `OLLAMA_BASE_URL` | `ollama/` |
| DeepSeek | `DEEPSEEK_API_KEY` | `deepseek/` |
| Grok/xAI | `XAI_API_KEY` | `grok/` |
| Cohere | `COHERE_API_KEY` | `cohere/` |

## Common Patterns

See `references/patterns.md` for detailed pattern examples including:
- Research pipeline (sequential)
- Support ticket triage (handoff/router)
- Batch document processing (parallel)
- Crash and resume (durable execution)
- Human-in-the-loop approval
- Guardrail patterns
- Memory-augmented agents

## Key Differences from Alternatives

| Feature | Agentspan | LangGraph | CrewAI | AutoGen |
|---------|-----------|-----------|--------|---------|
| Durable execution | ✅ Server-managed state | ❌ In-process only | ❌ In-process | ❌ In-process |
| Crash recovery | ✅ Automatic | ❌ Lost on crash | ❌ Lost on crash | ❌ Lost on crash |
| Server UI | ✅ Built-in | ❌ | ❌ | ❌ |
| Human-in-the-loop | ✅ First-class | ⚠️ Manual | ⚠️ Manual | ⚠️ Manual |
| Testing | ✅ mock_run, record/replay | ❌ | ❌ | ❌ |
| Multi-agent strategies | ✅ 8 built-in | ⚠️ Manual graph | ✅ Built-in | ✅ Built-in |
| LLM provider support | ✅ 15+ | ✅ Via LangChain | ✅ | ✅ |
| Code execution | ✅ Docker/Jupyter/Local | ❌ | ❌ | ⚠️ Limited |
| Credential management | ✅ Server-side encrypted | ❌ | ❌ | ❌ |

## Best Practices

1. **Always set `max_turns`** — Prevent runaway agents. Default is 25, lower for simple tasks.
2. **Use guardrails for production** — Input and output validation prevents safety issues.
3. **Store credentials on the server** — Never hardcode API keys. Use `agentspan credentials set`.
4. **Test with `mock_run`** — Write deterministic tests before deploying to production.
5. **Use `AgentRuntime` context manager** — Ensures worker processes are properly cleaned up.
6. **Set `stop_when` for long pipelines** — Custom termination conditions prevent unnecessary LLM calls.
7. **Use `http_tool` and `api_tool` for external APIs** — No worker process needed, runs server-side.
8. **Use SemanticMemory for cross-session context** — Better than stuffing conversation history.
9. **Monitor with `agentspan agent execution`** — Track failed executions in production.
10. **Use `approval_required=True` for destructive tools** — Always require human approval for irreversible actions.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Server won't start | Run `agentspan doctor`. Ensure Java 11+ is installed. |
| Worker can't connect | Check `AGENTSPAN_SERVER_URL`. Default: `http://localhost:6767` |
| LLM API errors | Verify API keys: `agentspan doctor`. Check rate limits. |
| Tool timeout | Increase `timeout_seconds` in `@tool()`. Check network connectivity. |
| Agent runs forever | Set `max_turns` lower. Add `stop_when` condition. |
| Guardrail loops | Set `max_retries` on guardrails. Use `OnFail.RAISE` for critical checks. |
| Worker process dies | Execution continues on server. Reconnect with `AgentHandle(workflow_id=...)`. |
| Port 6767 in use | Set `SERVER_PORT` environment variable or kill existing process. |

## References

- Official Docs: https://agentspan.ai/docs/
- GitHub: https://github.com/agentspan-ai/agentspan
- Examples: https://agentspan.ai/examples/
- PyPI: https://pypi.org/project/agentspan/
- Discord: https://discord.com/invite/ajcA66JcKq

## Using Agentspan from RTerm (the `agentspan-bridge` plugin)

If you run **RTerm / neuralOS** (the AI-native terminal & ops platform), you don't have to drive Agentspan by hand — the **`agentspan-bridge` plugin** (v2.9.9+) wires it into RTerm's agent so any RTerm-managed host can launch durable Agentspan executions.

- **Configure:** RTerm Settings → **AgentSpan** → `agentspan.serverUrl` (default `http://localhost:6767`) + optional `agentspan.authSecretRef` (a vault key holding `AGENTSPAN_AUTH_KEY`/`AGENTSPAN_AUTH_SECRET` — never inline).
- **RTerm agent tools:** `agentspan_health`, `agentspan_run` (an `AgentConfig` or a registered Conductor `workflow` name → `executionId`), `agentspan_status`, `agentspan_approve` (HITL respond), `agentspan_list`, `agentspan_stop`.
- **Trigger + panel:** `agentspan_execution_failed` (fires on FAILED/TERMINATED/TIMED_OUT) and an `agentspan-executions` live dashboard feed.
- **Why pair them:** RTerm gives you the terminal/fleet/governance surface (SSH/WinRM, playbooks, MOP approval, audit, SRE observability); Agentspan gives those operations **durability** (resume-from-step on crash), **plan-execute determinism**, and **Kafka/SQS/AMQP event triggers**. Ask the RTerm agent: "run the disk-cleanup SOP as a durable agent on Agentspan."

See the `rterm-gateway` skill for the RPC surface and the `rterm-backend`/`neuralos` skills for backend setup.
