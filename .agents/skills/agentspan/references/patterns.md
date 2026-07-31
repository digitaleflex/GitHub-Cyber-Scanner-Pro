# Agentspan Pattern Examples

> Copy-paste-ready pattern examples for common agent workflow scenarios.
> Each pattern is a complete runnable Python script. Start the server with `agentspan server start` before running.

---

## 1. Research Pipeline (Sequential)

Three agents run in sequence: research → write → edit. Each agent's output becomes the next agent's input.

```python
# research_pipeline.py
import os
from agentspan.agents import Agent, AgentRuntime

researcher = Agent(
    name="researcher",
    model=os.environ.get("AGENTSPAN_LLM_MODEL", "openai/gpt-4o-mini"),
    instructions=(
        "You are a researcher. Given a topic, provide key facts and data points. "
        "Be thorough but concise. Output raw research findings."
    ),
)

writer = Agent(
    name="writer",
    model=os.environ.get("AGENTSPAN_LLM_MODEL", "openai/gpt-4o-mini"),
    instructions=(
        "You are a writer. Take research findings and write a clear, engaging "
        "article. Use headers and bullet points where appropriate."
    ),
)

editor = Agent(
    name="editor",
    model=os.environ.get("AGENTSPAN_LLM_MODEL", "openai/gpt-4o-mini"),
    instructions=(
        "You are an editor. Review the article for clarity, grammar, and tone. "
        "Make improvements and output the final polished version."
    ),
)

# Chain with >> operator
pipeline = researcher >> writer >> editor

with AgentRuntime() as runtime:
    result = runtime.run(pipeline, "The impact of AI agents on software development in 2025")
    result.print_result()
```

**Key concepts:**
- `>>` operator chains agents sequentially
- Crash recovery: if the process dies, the server resumes from the current agent
- Swap models per stage: cheaper for research, stronger for editing

---

## 2. Support Ticket Triage (Handoff/Router)

A support agent classifies tickets and routes to specialized sub-agents. Sensitive actions (refunds, suspensions) require human approval.

```python
# support_triage.py
from agentspan.agents import Agent, AgentHandle, AgentRuntime, tool, start
from pydantic import BaseModel
from enum import Enum


# ── Data types ────────────────────────────────────────────────────────────────

class TicketCategory(str, Enum):
    BILLING = "billing"
    TECHNICAL = "technical"
    ACCOUNT = "account"
    GENERAL = "general"


class Resolution(BaseModel):
    category: TicketCategory
    action_taken: str
    response_to_customer: str
    requires_followup: bool


# ── Tools ─────────────────────────────────────────────────────────────────────

@tool
def lookup_customer(email: str) -> dict:
    """Fetch customer record: plan, billing status, open tickets, account age."""
    return {"id": "cust_123", "email": email, "plan": "pro", "billing_status": "active"}


@tool
def lookup_ticket_history(customer_id: str) -> list[dict]:
    """Fetch the last 10 support tickets for this customer."""
    return [{"id": "TKT-001", "subject": "Login issue", "status": "resolved"}]


@tool
def send_reply(customer_id: str, message: str) -> dict:
    """Send a reply to the customer and mark the ticket as resolved."""
    return {"status": "sent", "customer_id": customer_id}


@tool(approval_required=True)
def issue_refund(customer_id: str, amount_usd: float, reason: str) -> dict:
    """Issue a refund to the customer. Requires human approval."""
    return {"status": "refund_issued", "amount": amount_usd}


@tool(approval_required=True)
def suspend_account(customer_id: str, reason: str) -> dict:
    """Suspend a customer account. Requires human approval."""
    return {"status": "suspended", "customer_id": customer_id}


@tool(approval_required=True)
def apply_credit(customer_id: str, amount_usd: float, note: str) -> dict:
    """Apply account credit. Requires human approval."""
    return {"status": "credit_applied", "amount": amount_usd}


# ── Agent with router ─────────────────────────────────────────────────────────

billing_agent = Agent(
    name="billing_agent",
    model="openai/gpt-4o-mini",
    instructions="Handle billing questions: refunds, credits, payment issues.",
    tools=[issue_refund, apply_credit],
)

technical_agent = Agent(
    name="technical_agent",
    model="openai/gpt-4o-mini",
    instructions="Handle technical issues: bugs, connectivity, configuration.",
    tools=[send_reply],
)

general_agent = Agent(
    name="general_agent",
    model="openai/gpt-4o-mini",
    instructions="Handle general inquiries and account questions.",
    tools=[lookup_customer, send_reply],
)

# Router agent classifies and dispatches
classifier = Agent(
    name="classifier",
    model="openai/gpt-4o-mini",
    instructions="Classify: billing, technical, or general. Reply with just the category.",
)

support_agent = Agent(
    name="support_agent",
    model="openai/gpt-4o-mini",
    output_type=Resolution,
    agents=[billing_agent, technical_agent, general_agent],
    strategy="router",
    router=classifier,
    tools=[lookup_customer, lookup_ticket_history, send_reply,
           issue_refund, suspend_account, apply_credit],
    instructions="""You are a support agent for a SaaS product.

When a ticket arrives:
1. Look up the customer's account and ticket history.
2. Diagnose the issue based on context.
3. For general and technical questions: resolve directly with send_reply.
4. For billing actions (refunds, credits): use the appropriate tool — these will
   pause for human review before executing.
5. Return a Resolution with what happened.

Always be clear and empathetic. Never invent facts about the customer's account.""",
)

# ── Run ───────────────────────────────────────────────────────────────────────

with AgentRuntime() as runtime:
    handle = start(support_agent, "I was charged twice. Please refund order ORD-8821.")

    for event in handle.stream():
        if event.type == "waiting":
            print(f"Paused for approval — tool: {event.tool_name}, args: {event.args}")
            decision = input("Approve? (y/n): ").strip().lower()
            if decision == "y":
                handle.approve()
            else:
                handle.reject(input("Rejection reason: ").strip())

        elif event.type == "done":
            print(f"\nResult: {event.output['result']}")
            break
```

**Key concepts:**
- `strategy="router"` with a dedicated classifier agent
- `approval_required=True` for destructive tools
- `output_type=Resolution` enforces structured output
- `AgentHandle(execution_id=...)` for reconnecting from webhooks

---

## 3. Batch Document Processing (Parallel)

Process multiple documents concurrently with idempotent restarts.

```python
# batch_processor.py
from agentspan.agents import Agent, tool, start
from pydantic import BaseModel, Field
from pathlib import Path
from enum import Enum
import json


# ── Output schema ─────────────────────────────────────────────────────────────

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ContractReview(BaseModel):
    file: str
    contract_type: str
    parties: list[str]
    effective_date: str | None
    auto_renewal: bool
    risks: list[str] = Field(default_factory=list)
    risk_level: RiskLevel
    action_required: str | None


# ── Sample contracts ───────────────────────────────────────────────────────────

CONTRACTS = {
    "acme-nda.txt": "MUTUAL NDA. Parties: Acme Corp and Beta Inc. Effective: 2026-01-15. Auto-renews.",
    "vendor-msa.txt": "MSA. Parties: TechCorp and GlobalCo. No auto-renewal. Net 60 days.",
    "saas-agreement.txt": "SaaS Agreement. Parties: CloudSoft and StartupXYZ. Auto-renews. $5K/mo.",
}


# ── Tool ──────────────────────────────────────────────────────────────────────

@tool
def read_contract(filename: str) -> str:
    """Read a contract by filename and return its text content."""
    if filename not in CONTRACTS:
        return f"Error: contract '{filename}' not found."
    return CONTRACTS[filename]


# ── Agent ─────────────────────────────────────────────────────────────────────

contract_reviewer = Agent(
    name="contract_reviewer",
    model="openai/gpt-4o-mini",
    output_type=ContractReview,
    tools=[read_contract],
    instructions="""You are a paralegal specializing in technology contracts.

For each contract:
1. Read the full text using read_contract
2. Extract all required fields into ContractReview
3. List specific risks
4. Assign a risk level: low, medium, or high

Be precise. If a field is not present, use null — do not guess.""",
)


# ── Batch runner ──────────────────────────────────────────────────────────────

def process_contracts(max_concurrent: int = 3):
    filenames = list(CONTRACTS.keys())
    print(f"Found {len(filenames)} contracts to process")

    # Skip already-completed (idempotent restarts)
    reviews_dir = Path("reviews")
    completed = {p.stem for p in reviews_dir.glob("*.json")} if reviews_dir.exists() else set()
    pending = [f for f in filenames if Path(f).stem not in completed]
    print(f"{len(completed)} already done, {len(pending)} remaining\n")

    for i in range(0, len(pending), max_concurrent):
        batch = pending[i:i + max_concurrent]
        handles = {fn: start(contract_reviewer, fn) for fn in batch}

        for filename, handle in handles.items():
            try:
                result = handle.stream().get_result()
                review = result.output
                if isinstance(review, dict) and "result" in review:
                    review = review["result"]

                reviews_dir.mkdir(exist_ok=True)
                out = reviews_dir / (Path(filename).stem + ".json")
                out.write_text(json.dumps(review, indent=2, default=str))
                print(f"  ✓ {filename}  [risk: {review.get('risk_level', '?')}]")
            except Exception as e:
                print(f"  ✗ {filename}  FAILED: {e}")


if __name__ == "__main__":
    process_contracts()
```

**Key concepts:**
- `start()` launches parallel workflows (no blocking)
- Idempotent restarts: skip already-completed items
- `output_type=ContractReview` enforces structured output
- Adjust `max_concurrent` for throughput

---

## 4. Crash and Resume (Durable Execution)

Agent loop runs on the server. Your worker process can crash and reconnect without losing state.

```python
# crash_resume_start.py — Step 1: Start the agent and exit
from agentspan.agents import Agent, tool, start


@tool
def analyze_chunk(chunk_id: int, data: str) -> dict:
    """Analyze a data chunk and return metrics."""
    return {"chunk_id": chunk_id, "processed": True, "metrics": {"count": len(data)}}


@tool
def aggregate_results(results: list) -> dict:
    """Aggregate metrics from all chunks into a final report."""
    return {"total_chunks": len(results), "summary": "Analysis complete"}


agent = Agent(
    name="data_analysis_agent",
    model="openai/gpt-4o-mini",
    tools=[analyze_chunk, aggregate_results],
    instructions="""Analyze data in chunks using analyze_chunk, then aggregate
    with aggregate_results. Process each chunk sequentially.""",
)

handle = start(agent, "Analyze customer feedback dataset: chunk 1, chunk 2, chunk 3")
print(f"execution_id: {handle.execution_id}")
# Copy the execution_id — workflow keeps running on the server after this process exits
```

```python
# crash_resume_reconnect.py — Step 2: Reconnect from a new process
from agentspan.agents import Agent, tool, AgentRuntime, AgentHandle


# Same tools must be re-registered so workers can handle queued tasks
@tool
def analyze_chunk(chunk_id: int, data: str) -> dict:
    """Analyze a data chunk and return metrics."""
    return {"chunk_id": chunk_id, "processed": True, "metrics": {"count": len(data)}}


@tool
def aggregate_results(results: list) -> dict:
    """Aggregate metrics from all chunks into a final report."""
    return {"total_chunks": len(results), "summary": "Analysis complete"}


agent = Agent(
    name="data_analysis_agent",
    model="openai/gpt-4o-mini",
    tools=[analyze_chunk, aggregate_results],
    instructions="...",
)

EXECUTION_ID = "<paste-from-step-1>"

with AgentRuntime() as runtime:
    runtime.serve(agent, blocking=False)
    handle = AgentHandle(execution_id=EXECUTION_ID, runtime=runtime)
    print(f"Reconnected. Status: {handle.get_status().status}")

    for event in handle.stream():
        if event.type == "tool_call":
            print(f"→ {event.tool_name}({event.args})")
        elif event.type == "tool_result":
            print(f"← {event.tool_name}: {event.result}")
        elif event.type == "done":
            print(f"\nResult: {event.output['result']}")
            break
```

**Key concepts:**
- Agent loop lives on the server, not in your process
- `AgentHandle(execution_id=...)` reconnects from any process
- Workers must be re-registered for `@tool` agents
- Production pattern: separate `worker.py` (long-running) from `invoker.py` (one-shot)

---

## 5. Human-in-the-Loop Approval

Pause agent execution at destructive tool calls for human review. State is held on the server indefinitely.

```python
# hitl_approval.py
import time
from agentspan.agents import Agent, tool, start


@tool
def get_order(order_id: str) -> dict:
    """Look up an order by ID."""
    return {"order_id": order_id, "amount": 29.99, "status": "delivered"}


@tool
def get_customer(customer_id: str) -> dict:
    """Get customer account details."""
    return {"customer_id": customer_id, "name": "Alex", "email": "alex@example.com"}


@tool(approval_required=True)
def process_refund(order_id: str, amount: float) -> dict:
    """Issue a refund. Requires human approval."""
    return {"refunded": True, "order_id": order_id, "amount": amount}


agent = Agent(
    name="refund_agent",
    model="openai/gpt-4o-mini",
    tools=[get_order, get_customer, process_refund],
    instructions="""You handle refund requests.
    1. Look up the order
    2. Look up the customer
    3. Call process_refund — it will pause for human approval automatically
    """,
)

# Start the agent — returns immediately, workflow runs on the server
handle = start(agent, "Customer Alex (cust_001) wants a refund on order ORD-8821")
print(f"Run ID: {handle.execution_id}")

# Poll until the agent reaches the approval checkpoint
for _ in range(60):
    time.sleep(2)
    status = handle.get_status()

    if status.is_waiting:
        print("\n--- Approval required ---")
        print(f"Agent wants to call: process_refund")
        print(f"Order: ORD-8821  Amount: $29.99")

        decision = input("Approve? (y/n): ").strip().lower()
        if decision == "y":
            handle.approve()
            print("Approved. Waiting for agent to complete...")
            result = handle.stream().get_result()
            print(f"\nResult: {result.output['result']}")
        else:
            reason = input("Rejection reason: ").strip()
            handle.reject(reason)
            print("Rejected.")
        break

    if status.is_complete:
        print(f"Completed: {status.output['result']}")
        break
```

**Key concepts:**
- `approval_required=True` is the one-line change
- State held indefinitely on the server (no timeout)
- `handle.approve()` / `handle.reject(reason)` to resume
- CLI alternative: `agentspan agent respond <execution-id> --approve`
- Webhook pattern: store `execution_id`, approve from FastAPI/Flask/Lambda

---

## 6. Guardrail Patterns

Five guardrail modes: retry, raise, fix, human, and LLM-as-judge.

```python
# guardrail_patterns.py
import json
import re
from agentspan.agents import (
    Agent, AgentRuntime, Guardrail, GuardrailResult, guardrail,
    OnFail, Position, RegexGuardrail, LLMGuardrail,
)


# ── Pattern 1: Retry with feedback ────────────────────────────────────────────

@guardrail
def word_limit(content: str) -> GuardrailResult:
    """Keep responses under 200 words."""
    if len(content.split()) > 200:
        return GuardrailResult(passed=False, message="Too long. Be more concise.")
    return GuardrailResult(passed=True)


# ── Pattern 2: Raise on violation ─────────────────────────────────────────────

@guardrail
def no_jailbreak(content: str) -> GuardrailResult:
    """Block jailbreak attempts on input."""
    red_flags = ["ignore previous instructions", "act as", "jailbreak"]
    if any(flag in content.lower() for flag in red_flags):
        return GuardrailResult(passed=False, message="Request blocked.")
    return GuardrailResult(passed=True)


# ── Pattern 3: Auto-fix output ────────────────────────────────────────────────

@guardrail
def ensure_json(content: str) -> GuardrailResult:
    """Ensure the output is valid JSON."""
    try:
        json.loads(content)
        return GuardrailResult(passed=True)
    except json.JSONDecodeError:
        return GuardrailResult(
            passed=False,
            message="Output must be valid JSON.",
            fixed_output='{"error": "Could not generate valid JSON"}',
        )


# ── Pattern 4: Escalate to human ──────────────────────────────────────────────

@guardrail
def no_pii(content: str) -> GuardrailResult:
    """Reject responses containing email addresses."""
    if re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", content):
        return GuardrailResult(
            passed=False,
            message="Response contains PII (email). Remove it.",
        )
    return GuardrailResult(passed=True)


# ── Pattern 5: LLM-as-judge ──────────────────────────────────────────────────

factual_check = LLMGuardrail(
    model="openai/gpt-4o-mini",
    policy="Is this response factually accurate and helpful? Reply YES or NO.",
    on_fail=OnFail.RETRY,
    max_retries=2,
)


# ── Regex guardrails ──────────────────────────────────────────────────────────

no_ssn = RegexGuardrail(
    patterns=[r"\b\d{3}-\d{2}-\d{4}\b"],
    name="no_ssn",
    message="Do not include SSNs.",
    on_fail=OnFail.RAISE,
)

no_profanity = RegexGuardrail(
    patterns=r"\b(badword1|badword2)\b",
    mode="block",
    on_fail=OnFail.RETRY,
)


# ── Chained guardrails ────────────────────────────────────────────────────────

safe_agent = Agent(
    name="safe_bot",
    model="openai/gpt-4o",
    guardrails=[
        # Input: block jailbreaks immediately
        Guardrail(no_jailbreak, position=Position.INPUT, on_fail=OnFail.RAISE),
        # Output: retry if PII found
        Guardrail(no_pii, position=Position.OUTPUT, on_fail=OnFail.RETRY, max_retries=3),
        # Output: enforce word limit
        Guardrail(word_limit, on_fail=OnFail.RETRY),
        # Output: block SSNs
        no_ssn,
    ],
)

with AgentRuntime() as runtime:
    result = runtime.run(safe_agent, "Explain AI safety best practices.")
    result.print_result()
```

**Key concepts:**
- `Position.INPUT` validates before LLM call; `Position.OUTPUT` (default) validates after
- `OnFail.RETRY`: append feedback and re-run (up to `max_retries`)
- `OnFail.RAISE`: fail the execution immediately
- `OnFail.FIX`: replace with `GuardrailResult.fixed_output`
- `OnFail.HUMAN`: pause for human review (same as HITL)
- `RegexGuardrail`: block/allow patterns without writing functions
- `LLMGuardrail`: use a second LLM as judge
- Chain multiple guardrails — they run in order

---

## 7. Memory-Augmented Agents

Combine `ConversationMemory` (chat history) and `SemanticMemory` (long-term knowledge) for context-aware agents.

```python
# memory_agent.py
from agentspan.agents import Agent, AgentRuntime, tool, ConversationMemory
from agentspan.agents.semantic_memory import SemanticMemory


# ── Conversation memory (chat history) ────────────────────────────────────────

conv_memory = ConversationMemory(max_messages=100)

chat_agent = Agent(
    name="chat_assistant",
    model="openai/gpt-4o-mini",
    instructions="You are a helpful assistant. Remember what the user tells you.",
    memory=conv_memory,
)

with AgentRuntime() as runtime:
    # First turn
    result1 = runtime.run(chat_agent, "My name is Alice and I work at Acme Corp.")
    conv_memory.add_user_message("My name is Alice and I work at Acme Corp.")
    conv_memory.add_assistant_message(result1.output["result"])
    print(f"Turn 1: {result1.output['result']}")

    # Second turn — agent remembers
    result2 = runtime.run(chat_agent, "What's my name and where do I work?")
    print(f"Turn 2: {result2.output['result']}")
    # "Your name is Alice and you work at Acme Corp."


# ── Semantic memory (long-term knowledge) ────────────────────────────────────

semantic_memory = SemanticMemory(max_results=3)
semantic_memory.add("Customer prefers email communication over phone.")
semantic_memory.add("Account is on the Enterprise plan since March 2021.")
semantic_memory.add("Previous issue: login problems resolved in ticket TKT-001.")


@tool
def get_context(query: str) -> str:
    """Retrieve relevant context from long-term memory."""
    return semantic_memory.get_context(query)


support_agent = Agent(
    name="support_with_memory",
    model="openai/gpt-4o-mini",
    instructions="You are a support agent. Use get_context to recall customer history.",
    tools=[get_context],
)

with AgentRuntime() as runtime:
    result = runtime.run(support_agent, "How should I contact this customer about their renewal?")
    print(f"Result: {result.output['result']}")
```

**Key concepts:**
- `ConversationMemory`: maintains chat history across turns
- `SemanticMemory`: stores and retrieves long-term facts via semantic search
- Combine both: conversation memory for short-term context, semantic memory for cross-session knowledge
- `max_messages` limits conversation history; `max_results` limits semantic retrieval

---

## 8. Nested Strategies

Combine multiple strategies in a single agent hierarchy for complex workflows.

```python
# nested_strategies.py
import os
from agentspan.agents import Agent, AgentRuntime, Strategy
from agentspan.agents import TextMentionTermination

model = os.environ.get("AGENTSPAN_LLM_MODEL", "openai/gpt-4o-mini")


# ── Inner parallel: analysis team ────────────────────────────────────────────

market = Agent(
    name="market_analyst",
    model=model,
    instructions="Analyze market size, growth trends, and competitive landscape.",
)

risk = Agent(
    name="risk_analyst",
    model=model,
    instructions="Analyze regulatory, technical, and market risks.",
)

financial = Agent(
    name="financial_analyst",
    model=model,
    instructions="Analyze financial projections, unit economics, and runway.",
)

analysis_team = Agent(
    name="analysis_team",
    model=model,
    agents=[market, risk, financial],
    strategy="parallel",
)


# ── Outer sequential: research → analyze → decide ─────────────────────────────

researcher = Agent(
    name="researcher",
    model=model,
    instructions="Gather all available information about the investment opportunity.",
)

decision_maker = Agent(
    name="decision_maker",
    model=model,
    instructions="""You are an investment committee member.

Review the research and multi-perspective analysis.
Weigh the market opportunity against the risks.
Provide a clear GO / NO-GO recommendation with reasoning.""",
)

# Sequential pipeline with parallel analysis in the middle
pipeline = researcher >> analysis_team >> decision_maker


# ── Alternative: handoff with swarm ──────────────────────────────────────────

triage = Agent(
    name="triage",
    model=model,
    instructions="Assess urgency. Say URGENT for critical issues, ROUTINE otherwise.",
)

urgency_handler = Agent(
    name="urgency_handler",
    model=model,
    instructions="Handle urgent issues immediately with decisive action.",
)

routine_handler = Agent(
    name="routine_handler",
    model=model,
    instructions="Handle routine issues with standard procedures.",
)

swarm_team = Agent(
    name="swarm_team",
    model=model,
    agents=[triage, urgency_handler, routine_handler],
    strategy=Strategy.SWARM,
    handoffs=[
        TextMentionTermination("URGENT", target="urgency_handler"),
        TextMentionTermination("ROUTINE", target="routine_handler"),
    ],
)


# ── Run ───────────────────────────────────────────────────────────────────────

with AgentRuntime() as runtime:
    print("=== Nested Sequential + Parallel ===")
    result = runtime.run(pipeline, "AI healthcare startup seeking Series A")
    result.print_result()

    print("\n=== Swarm Handoff ===")
    result2 = runtime.run(swarm_team, "Production database is down, all users affected!")
    result2.print_result()
```

**Key concepts:**
- Nest parallel analysis inside a sequential pipeline
- `Strategy.SWARM` with `TextMentionTermination` for condition-based handoffs
- Combine handoff, router, and sequential strategies in one hierarchy
- Each sub-agent can have its own tools, memory, and guardrails
