---
name: rterm-agentspan
description: Bridge RTerm / neuralOS to an AgentSpan (Netflix Conductor) server for durable, crash-resilient agent execution — runs that survive restarts and resume from the last completed step. Use when an agent needs to (1) set up the AgentSpan↔RTerm bridge (server, RTerm Settings→AgentSpan, auth via vault), (2) launch/monitor/approve durable agents + Conductor workflows from RTerm via the agentspan_* tools, (3) register RTerm playbooks as reusable Conductor workflows, or (4) build real workflows on the server (HTTP data-fetch tasks → LLM steps) that actually complete — including the gotchas (Responses-API vs chat-completions, secrets injection, model ids).
---

# RTerm ↔ AgentSpan Bridge

Make RTerm's operations **durable**. Normal RTerm agent runs are interactive and die if RTerm/your machine restarts; the bridge hands work to an **AgentSpan (Netflix Conductor) server** that keeps going and **resumes from the last completed step** — plus plan-execute determinism, Kafka/SQS/AMQP event triggers, and a visual execution UI.

**Two agents, two LLMs (don't conflate):** RTerm's own agent uses RTerm's model profiles. A *durable agent you launch* runs on the AgentSpan server and uses **its own** provider config. The bridge between them is just an HTTP URL.

## 1. Setup (one time)

1. **Run the AgentSpan server** (default port 6767):
   ```bash
   agentspan server start        # or: launchd/systemd service, Docker, or the runtime JAR
   curl http://localhost:6767/actuator/health   # → {"status":"UP",...}
   ```
2. **Point RTerm at it:** Settings → **AgentSpan** → `serverUrl = http://localhost:6767` (default), `enabled = true`, Save. This is persisted (schema v5) and live — no RTerm restart.
3. **Auth (only if the AgentSpan server has standalone auth on):** put `AGENTSPAN_AUTH_KEY`/`AGENTSPAN_AUTH_SECRET` as a `KEY=VAL` blob in the RTerm vault (`manage_secret`), then set `authSecretRef` to that vault key. Never inline.

Verify from RTerm: ask the agent to "check AgentSpan health" (uses `agentspan_health`).

## 2. The bridge tools (RTerm agent)

| Tool | What it does |
|---|---|
| `agentspan_health` | Is the server up? (serverUrl, auth configured, status). |
| `agentspan_run` | Start a durable run: pass an `agentConfig` (LLM agent) **or** a `workflow` name (Conductor workflow) + `input`/`prompt`. Returns `executionId`/`workflowId` + UI link. |
| `agentspan_status` | Detailed status of an execution — current state, per-task progress, failure reason. Tries the agent surface, falls back to the workflow engine. |
| `agentspan_approve` | Respond to a paused human-in-the-loop (HUMAN) task → resumes the run. |
| `agentspan_list` | List recent executions (optional Conductor freeText query, e.g. `status:FAILED`). |
| `agentspan_stop` | Terminate a running execution. |
| `agentspan_export_playbook` | Dry-run: show what an RTerm playbook looks like as a Conductor WorkflowDef. |
| `agentspan_register_playbook` | Actually register an RTerm playbook as a reusable Conductor workflow (so `agentspan_run {workflow:"<name>"}` or a SUB_WORKFLOW can call it; command tasks call back into RTerm's policy-gated exec). |
| `agentspan_delegate` | Hand a prompt to a durable AgentConfig agent that runs start-to-finish on its own → `executionId` survives restart. |

Trigger: `agentspan_execution_failed` (fires on FAILED/TERMINATED/TIMED_OUT). Panel: `agentspan-executions` (live feed).

## 3. Use cases (plain)

- **"Might close my laptop" long task** — "Run the Friday-cleanup playbook across prod-web **as a durable agent on AgentSpan**." Close RTerm; it keeps going; check `agentspan_status` later.
- **"Approve when I'm back" deploy** — start a durable deploy that pauses for approval; `agentspan_approve` hours later resumes it.
- **"Same way every time" report** — plan-execute: LLM plans once → immutable workflow → deterministic run each week.
- **Event-driven fix** — a trigger fires → `agentspan_run` starts a durable cleanup even while RTerm is asleep; `agentspan_execution_failed` pages you if it dies.
- **Reusable workflow** — `agentspan_register_playbook` turns your playbook into a Conductor workflow other agents can call as steps.

## 4. Configuring the server's LLM (provider + model)

The server needs a provider key for any *LLM-driven* durable agent/step. Set env on the server (launchd/systemd/Docker), then restart:

```bash
export OPENAI_API_KEY=<key>                      # provider auto-enables when its key is present
export AGENTSPAN_LLM_MODEL=provider/model-name   # e.g. openai/gpt-4o-mini  (the SERVER-WIDE default model)
```

**Model format is `provider/model-name`** (e.g. `openai/gpt-4o-mini`, `anthropic/claude-sonnet-4-6`). For **OpenRouter** (OpenAI-compatible), point the provider at it:
`OPENAI_API_KEY=<openrouter key>` + `OPENAI_BASE_URL=https://openrouter.ai/api/v1` (reload the service so the env lands on the process — `launchctl bootout`+`bootstrap`, or `remove`+`load`; `kickstart -k` reuses the cached job).

## 5. GOTCHAS (learned the hard way — read before building workflows)

1. **`LLM_CHAT_COMPLETE` uses the OpenAI Responses API, not chat-completions.** On this Conductor build that task is hardwired to `POST /v1/responses`. OpenRouter's `/responses` is limited and 404s for many models/payloads. **Fix: don't use `LLM_CHAT_COMPLETE` for OpenRouter — use an `HTTP` task that calls `https://openrouter.ai/api/v1/chat/completions` directly.** That path is fully supported and reliable.
2. **Model id must be one the server/provider actually maps.** `z-ai/glm-5.2` is an OpenRouter catalog id, not a `provider/model-name` the server auto-maps. With an HTTP task you control the exact `model` string in the request body, so use the OpenRouter id there (e.g. `"model":"z-ai/glm-5.2"`).
3. **`${workflow.secrets.NAME}` does not auto-resolve into HTTP headers** on this build (results in 401 "Missing Authentication header"). Inject the key another way: inline the `Authorization` header in the definition, or use a server-side env/secret the task reads. (If the key was ever exposed, rotate it and update the def.)
4. **Reasoning models can return `content: null` with everything in `reasoning` when `max_tokens` is too low.** Give reasoning models room (e.g. `max_tokens` ≥ 800) and instruct "output ONLY the final answer in the assistant content field."
5. **External data:** LLMs have no live data. Fetch first with HTTP task(s) (e.g. CoinGecko public API, Luno with basic auth), pass the JSON into the LLM prompt, and have the LLM format it.

## 6. A workflow that actually completes (live BTC price, v6 pattern)

Three HTTP tasks, no `LLM_CHAT_COMPLETE`:

1. **fetch_coingecko** — `GET https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd,ngn&include_24hr_change=true` (public, no key).
2. **fetch_luno** — `GET https://api.luno.com/api/1/ticker?pair=XBTNGN` with `Authorization: Basic base64(luno_key_id:luno_secret)`.
3. **format_with_llm** — `POST https://openrouter.ai/api/v1/chat/completions` (Bearer openrouter key), body `{model:"z-ai/glm-5.2", max_tokens:800, messages:[system:"output ONLY the final answer in the content field", user:"CoinGecko: ${fetch_coingecko.output.response.body}\nLuno: ${fetch_luno.output.response.body}\n${workflow.input.prompt}"]}`.

Output map: `answer = ${format_with_llm.output.response.body.choices[0].message.content}`. Result: a formatted live BTC summary (CoinGecko USD+NGN, Luno last trade, 24h change). Get the Luno key id/secret and the OpenRouter key from the RTerm **secrets vault** (`manage_secret`) / the `secrets` skill — never inline into version-controlled definitions.

## 7. Reference

- RTerm Settings → AgentSpan (`agentspan.serverUrl`, `authSecretRef`) — persisted + live.
- AgentSpan API: `/actuator/health`, `/api/agent/*` (start/status/respond/stop/events/definitions), `/api/workflow/*` (start/get/terminate/retry/search), `/api/metadata/workflow` (register defs), `/api/secrets`.
- Plugin source: RTerm repo `plugins/agentspan-bridge/` (conductorClient.mjs + index.mjs, 9 tools, 26+ tests).
- Standalone AgentSpan SDK/CLI: the `agentspan` skill.
- **v3.0.0:** the gateway is now self-describing — call `gateway:describe` (or the `list_gateway_methods` agent tool) to enumerate the `agentspan_*` tools (and everything else) live from the method registry instead of this static list.
