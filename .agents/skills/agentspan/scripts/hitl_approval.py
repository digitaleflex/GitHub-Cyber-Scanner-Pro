#!/usr/bin/env python3
"""Human-in-the-loop approval flow.

Demonstrates approval_required=True on tools that need human review.
The agent pauses at the approval checkpoint and waits for approve/reject.

Prerequisites:
  pip install agentspan
  agentspan server start
  export OPENAI_API_KEY=sk-...

Usage:
  python hitl_approval.py
"""

import time
from agentspan.agents import Agent, tool, start


@tool
def get_order(order_id: str) -> dict:
    """Look up an order by ID."""
    return {"order_id": order_id, "amount": 149.99, "status": "delivered", "customer_id": "cust_001"}


@tool
def get_customer(customer_id: str) -> dict:
    """Get customer account details."""
    return {"customer_id": customer_id, "name": "Alex", "email": "alex@example.com", "plan": "pro"}


@tool(approval_required=True)
def process_refund(order_id: str, amount: float) -> dict:
    """Issue a refund. Requires human approval before executing."""
    return {"refunded": True, "order_id": order_id, "amount": amount}


@tool(approval_required=True)
def delete_account(customer_id: str, reason: str) -> dict:
    """Permanently delete a customer account. Requires human approval."""
    return {"deleted": True, "customer_id": customer_id}


agent = Agent(
    name="refund_agent",
    model="openai/gpt-4o-mini",
    tools=[get_order, get_customer, process_refund, delete_account],
    instructions="""You handle refund and account requests.
    1. Look up the order and customer details first.
    2. For refunds, call process_refund — it will pause for human approval.
    3. For account deletions, call delete_account — also requires approval.
    Always gather context before taking action.""",
    max_turns=15,
)


if __name__ == "__main__":
    # Start the agent — workflow runs on the server
    handle = start(agent, "Customer Alex (cust_001) wants a refund on order ORD-8821")
    print(f"Execution ID: {handle.execution_id}")

    # Poll until the agent reaches an approval checkpoint
    for _ in range(60):
        time.sleep(2)
        status = handle.get_status()

        if status.is_waiting:
            print("\n" + "=" * 50)
            print("APPROVAL REQUIRED")
            print("=" * 50)
            print(f"Status: {status.status}")

            decision = input("\nApprove? (y/n): ").strip().lower()
            if decision == "y":
                handle.approve()
                print("Approved! Waiting for agent to complete...\n")
                result = handle.stream().get_result()
                print(f"Result: {result.output['result']}")
            else:
                reason = input("Rejection reason: ").strip()
                handle.reject(reason)
                print(f"Rejected: {reason}")
            break

        if status.is_complete:
            print(f"Completed without approval: {status.output['result']}")
            break
