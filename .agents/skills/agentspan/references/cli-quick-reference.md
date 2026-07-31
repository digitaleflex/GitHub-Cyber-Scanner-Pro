# Agentspan CLI Quick Reference

> Complete command reference for the Agentspan CLI (`agentspan`)

## Installation

```bash
# Python SDK + CLI (recommended)
pip install agentspan

# CLI only (no Python SDK) — downloads Go binary at install time
npm install -g @agentspan-ai/agentspan
```

The pip package registers the `agentspan` command as a console script. On first invocation it downloads the Go binary from S3 and caches it.

```bash
agentspan version    # Print the CLI version
agentspan --help     # List all commands
```

---

## Server Commands

### `agentspan server start`

Download (if needed) and start the Agentspan server.

```bash
# Basic start (downloads JAR on first run, ~50 MB, cached afterward)
agentspan server start

# Server runs on port 6767 by default
# UI + API both served at http://localhost:6767
```

Environment variable overrides:

| Variable | Default | Description |
|----------|---------|-------------|
| `SERVER_PORT` | `6767` | Server port |
| `SPRING_PROFILES_ACTIVE` | `default` (SQLite) | Set to `postgres` for PostgreSQL |
| `SPRING_DATASOURCE_URL` | `jdbc:sqlite:agent-runtime.db` | Database URL |

### `agentspan server stop`

Stop the running server.

```bash
agentspan server stop
```

### `agentspan server logs`

View server logs.

```bash
agentspan server logs
```

---

## Diagnostics

### `agentspan doctor`

Check system dependencies and AI provider configuration.

```bash
agentspan doctor
```

Verifies:
- CLI is installed and working
- Java runtime is available (required for the server)
- Python SDK is installed
- API keys are configured
- Server is reachable

---

## Credential Management

Store secrets on the server once. Tools resolve them automatically at runtime — no `.env` files, no hardcoded keys, no secrets in git. Credentials are encrypted at rest with AES-256-GCM. Only key names are shown in `list` — values are never exposed.

### `agentspan credentials set KEY value`

Store a credential (encrypted at rest).

```bash
agentspan credentials set GITHUB_TOKEN ghp_xxxxxxxxxxxx
agentspan credentials set SEARCH_API_KEY xxx-your-key
agentspan credentials set STRIPE_API_KEY sk_live_xxxxxxxx
```

### `agentspan credentials list`

List stored credential keys (values are never shown).

```bash
agentspan credentials list
```

### `agentspan credentials delete KEY`

Delete a credential.

```bash
agentspan credentials delete GITHUB_TOKEN
```

### `agentspan credentials bindings`

List logical key → store name bindings.

```bash
agentspan credentials bindings
```

### `agentspan credentials bind KEY name`

Bind a logical key to a custom store name.

```bash
agentspan credentials bind GITHUB_TOKEN my_github_store
```

### Using Credentials in Tools

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

---

## Agent Commands

### `agentspan agent status <execution-id>`

Get detailed status of a running execution.

```bash
agentspan agent status abc123-def456
```

### `agentspan agent run --name <agent-name> "prompt"`

Run a deployed agent and stream output.

```bash
# Run by agent name
agentspan agent run --name my_agent "What is quantum computing?"

# Run from config file
agentspan agent run --config agent.yaml "What is quantum computing?"
```

### `agentspan agent stream <execution-id>`

Stream events from a running execution.

```bash
agentspan agent stream abc123-def456
```

### `agentspan agent list`

List all registered agents.

```bash
agentspan agent list
```

### `agentspan agent get <agent-name>`

Get agent configuration JSON.

```bash
agentspan agent get my_agent
```

### `agentspan agent compile <agent-name>`

Compile and inspect execution plan (dry run).

```bash
agentspan agent compile my_agent
```

### `agentspan agent execution`

View execution history with filters.

```bash
# All executions in the last hour
agentspan agent execution --since 1h

# Filter by agent name
agentspan agent execution --name my_agent --since 1d

# Filter by status
agentspan agent execution --status COMPLETED --since 7d
agentspan agent execution --name my_agent --status FAILED --since 1mo

# Combine filters
agentspan agent execution --name contract_reviewer --status FAILED --since 1d
```

Time formats: `30s`, `5m`, `1h`, `6h`, `1d`, `7d`, `1mo`, `1y`

Status values: `RUNNING`, `COMPLETED`, `FAILED`, `WAITING`

### `agentspan agent respond <execution-id>`

Respond to a human-in-the-loop approval checkpoint.

```bash
# Approve
agentspan agent respond <execution-id> --approve

# Deny with reason
agentspan agent respond <execution-id> --deny --reason "Amount too large, escalate to finance"

# Send a message (redirect the agent)
agentspan agent respond <execution-id> --message "Please use a different approach"
```

---

## Configuration

### `agentspan configure`

Configure the server URL and auth credentials.

```bash
# Set server URL
agentspan configure --url https://your-server.example.com

# Set server URL with auth
agentspan configure --url https://your-server.example.com --auth-key my-key --auth-secret my-secret
```

### Environment Variables

Alternative to `agentspan configure`:

```bash
export AGENTSPAN_SERVER_URL=https://your-server.example.com
export AGENTSPAN_AUTH_KEY=your-key
export AGENTSPAN_AUTH_SECRET=your-secret
```

### Python Configuration

```python
from agentspan.agents import configure

configure(
    server_url="https://your-server.example.com",
    auth_key="your-key",
    auth_secret="your-secret",
)
```

---

## Quick Reference Card

| Command | Description |
|---------|-------------|
| `agentspan version` | Print CLI version |
| `agentspan --help` | List all commands |
| `agentspan doctor` | Check system dependencies |
| `agentspan server start` | Start server (downloads JAR on first run) |
| `agentspan server stop` | Stop server |
| `agentspan server logs` | View server logs |
| `agentspan credentials set KEY value` | Store encrypted credential |
| `agentspan credentials list` | List credential keys |
| `agentspan credentials delete KEY` | Delete a credential |
| `agentspan credentials bindings` | List key → store bindings |
| `agentspan credentials bind KEY name` | Bind key to custom store |
| `agentspan agent status <id>` | Check execution status |
| `agentspan agent run --name X "prompt"` | Run and stream agent |
| `agentspan agent run --config f.yaml "prompt"` | Run from config file |
| `agentspan agent stream <id>` | Stream running execution |
| `agentspan agent list` | List registered agents |
| `agentspan agent get <name>` | Get agent config JSON |
| `agentspan agent compile <name>` | Compile and inspect plan (dry run) |
| `agentspan agent execution` | View execution history |
| `agentspan agent respond <id> --approve` | Approve HITL checkpoint |
| `agentspan agent respond <id> --deny --reason R` | Reject HITL checkpoint |
| `agentspan agent respond <id> --message M` | Send message to agent |
| `agentspan configure --url URL` | Configure server URL |
| `agentspan configure --url U --auth-key K --auth-secret S` | Configure with auth |

---

## LLM Provider Environment Variables

| Provider | Env Var(s) | Model Prefix |
|----------|-----------|-------------|
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
