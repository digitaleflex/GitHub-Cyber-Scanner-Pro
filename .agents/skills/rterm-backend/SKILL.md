---
name: rterm-backend
description: Install, configure, run, administer, and manage the standalone RTerm backend (rterm-backend / gybackend) completely headlessly on macOS, Linux, and Windows. Use when an agent needs to set up RTerm-as-a-service — install the daemon, configure its data dir and gateway, run it as a service, manage saved connections/automation/schedules, and drive it over its WebSocket JSON-RPC gateway. Pair with the rterm-gateway skill for the RPC method reference and client examples.
---

# RTerm Backend — Headless Install & Operations Skill

The **RTerm backend** (`rterm-backend` on npm, CLI `gybackend`) is the full RTerm
runtime as a standalone Node daemon — **no desktop UI**. It boots the AI agent,
SSH/WinRM/Serial/local terminals, fleet orchestration, scheduled automation, and
change management, and serves them over a **WebSocket JSON-RPC gateway**
(default `ws://<host>:17888`).

Use this skill to install, configure, run, and administer it **completely
headlessly** on **macOS, Linux, or Windows** — then drive it with the
[`rterm-gateway`](../rterm-gateway/SKILL.md) skill for the actual RPC calls.

---

## 1. The 60-second path (any OS)

```bash
# 1. install (Node >= 18 required)
npm install -g rterm-backend

# 2. run it
gybackend
# -> [gybackend] WebSocket RPC endpoint: ws://0.0.0.0:17888

# 3. verify (in another shell)
echo '{"id":"1","method":"gateway:ping"}' | websocat -n1 ws://127.0.0.1:17888
# -> {"type":"gateway:response","id":"1","ok":true,"result":{"pong":true,...}}
```

The bundled **`scripts/rterm-backend.mjs`** CLI wraps every lifecycle step
(install, start, stop, status, logs, config, service) into one cross-platform
command. Run any of these with `node scripts/rterm-backend.mjs <cmd>`.

---

## 2. What runs inside (mental model)

```
┌──────────────┐  WebSocket JSON-RPC   ┌────────────────────────────────┐
│ your agent / │ ◄──────────────────► │ gybackend (rterm-backend)      │
│ program / CI │                       │  AgentService  (LLM + tools)   │
└──────────────┘                       │  TerminalService SSH/WinRM/    │
                                       │    Serial/local PTY          │
                                       │  AutomationManager + cron    │
                                       │  ChangeManagement (MOP)      │
                                       │  Ledgers (SQLite)            │
                                       └────────────────────────────────┘
                  Data dir: settings.json + *.sqlite + session-logs/
```

- **Requests:** `{ "id": "1", "method": "<name>", "params": {...} }`
- **Responses:** `{ "type": "gateway:response", "id": "1", "ok": true|false, "result"|"error" }`
- **Events (progress):** `{ "type": "gateway:event" | "gateway:raw" | "gateway:ui-update", ... }`

---

## 3. Install

### 3.1 Requirements

| Need | Notes |
|---|---|
| **Node.js ≥ 18** | Native deps (`better-sqlite3`, `node-pty`, `ssh2` crypto, tree-sitter wasm) ship prebuilt binaries for macOS x64/arm64, Linux x64/arm64, Windows x64. Unusual platforms compile from source → install a C/C++ toolchain (Xcode CLT / build-essential / MSVC Build Tools). |
| npm registry access | or your internal mirror (`npm config set registry <mirror>`). |
| Optional | `websocat` (ad-hoc calls), an LLM provider key for the agent. |

### 3.2 Install from npm (recommended)

```bash
npm install -g rterm-backend
gybackend --version 2>/dev/null || which gybackend || where gybackend
```

Or without a global install: `npx -y rterm-backend`.

### 3.3 Install from a repo checkout (development)

```bash
git clone https://github.com/DrOlu/RTerm.git && cd RTerm
npm install
npm run build:backend-standalone      # dist-standalone/gybackend.js
npm run start:backend                 # or: node apps/gybackend/dist-standalone/gybackend.js
```

### 3.4 OS-specific service install (run as a daemon/service)

Use the bundled helper, or the unit files in `service/`:

```bash
node scripts/rterm-backend.mjs install-service     # prints the right unit + enable cmd for this OS
```

- **Linux (systemd):** `service/rterm-backend.service` → `/etc/systemd/system/`, then `systemctl enable --now rterm-backend`.
- **macOS (launchd):** `service/ng.hyperspace.rterm-backend.plist` → `~/Library/LaunchAgents/`, then `launchctl load <plist>`.
- **Windows (Task Scheduler):** `service/install-windows-service.ps1` → registers an at-logon task (`schtasks`). Native deps install via `npm i -g` first.

---

## 4. Configure

### 4.1 Environment variables

| Variable | Default | Meaning |
|---|---|---|
| `GYBACKEND_WS_ENABLE` | `1` | enable the gateway (0/false disables) |
| `GYBACKEND_WS_HOST` | `0.0.0.0` | bind host (`127.0.0.1` = local-only) |
| `GYBACKEND_WS_PORT` | `17888` | gateway port |
| `GYBACKEND_DATA_DIR` | `./.gybackend-data` | settings, ledgers, skills, session logs |
| `GYBACKEND_BOOTSTRAP_LOCAL_TERMINAL` | `true` | open a local shell tab on boot |
| `GYBACKEND_TERMINAL_ID` | `local-main` | bootstrap terminal id |
| `GYBACKEND_TERMINAL_TITLE` | `Local` | bootstrap terminal title |
| `GYBACKEND_TERMINAL_CWD` | — | bootstrap terminal cwd |
| `GYBACKEND_TERMINAL_SHELL` | — | bootstrap terminal shell |

### 4.2 The data directory

| Path | Contents |
|---|---|
| `settings.json` | connections (ssh/winrm/serial), automation (groups/scripts/schedules/templates/playbooks), model profiles (incl. `reviewModelId`/`reviewMode`), command policy, gateway policy |
| `gyshell-history.sqlite` | chat + UI history |
| `gyshell-agent-runs.sqlite` | agent run ledger (audit + token cost) |
| `gyshell-changes.sqlite` | change ledger (MOP records + step events) |
| `session-logs/` | recorded terminal sessions (plain files) |
| `skills/` | agent skills |
| `plugins/` | user-installed plugins (auto-discovered on startup; the 6 official plugins ship in the npm package / desktop app bundle) |
| `policy.yaml` | optional custom AGT policy document (overrides the built-in default policy) |
| `access-tokens.json` | gateway access tokens |

### 4.3 Reuse desktop-app settings

```bash
# macOS
GYBACKEND_DATA_DIR="$HOME/Library/Application Support/rterm" gybackend
# Linux
GYBACKEND_DATA_DIR="$HOME/.config/rterm" gybackend
# Windows (cmd)
set GYBACKEND_DATA_DIR=%APPDATA%\rterm && gybackend
:: Windows (PowerShell)
$env:GYBACKEND_DATA_DIR="$env:APPDATA\rterm"; gybackend
```

> **Warn:** two instances sharing one data dir should not run the same scheduled
> tasks at once (duplicate execution). For a dedicated automation server, give it
> its own data dir and recreate only what it needs.

### 4.4 Command policy (autonomy)

| Mode | Unrecognized commands | Use for |
|---|---|---|
| `smart` | run (unless denylisted) | unattended / headless |
| `standard` | ask for approval | interactive / supervised |
| `safe` | deny | locked-down |

Pre-allowlist what a headless job needs, then run `smart`:

```bash
settings:addCommandPolicyRule {list:"allowlist", rule:"Update-MpSignature*"}
settings:addCommandPolicyRule {list:"allowlist", rule:"systemctl *"}
```

### 4.5 Securing the gateway

- **Local-only:** `GYBACKEND_WS_HOST=127.0.0.1` when callers are on the same host.
- **Token:** non-localhost clients need `Authorization: Bearer <token>` (manage in `access-tokens.json`).
- **CIDR allow-list:** `settings → gateway.allowedCidrs`.
- **Localhost bypass:** `127.0.0.1`/`::1` skip the token by default.

---

## 5. Run & administer

The bundled **`scripts/rterm-backend.mjs`** handles the lifecycle cross-platform
(uses only Node built-ins — no dependencies):

```bash
node scripts/rterm-backend.mjs doctor          # check Node, npm pkg, data dir, port
node scripts/rterm-backend.mjs install         # npm i -g rterm-backend
node scripts/rterm-backend.mjs start [--port N] [--host H] [--data DIR] [--daemon]
node scripts/rterm-backend.mjs stop
node scripts/rterm-backend.mjs restart
node scripts/rterm-backend.mjs status
node scripts/rterm-backend.mjs logs [--lines N]
node scripts/rterm-backend.mjs ping [--url ws://...]
node scripts/rterm-backend.mjs config-show     # effective env + data dir
node scripts/rterm-backend.mjs install-service # print service unit + enable cmd for this OS
node scripts/rterm-backend.mjs uninstall       # stop + npm uninstall -g
```

### Boot output (healthy)

```
[WebSocketGatewayAdapter] Listening on ws://0.0.0.0:17888
[gybackend] Started.
[gybackend] WebSocket RPC endpoint: ws://0.0.0.0:17888
[gybackend] Data directory: /var/lib/rterm-backend
```

### Foreground vs background

- **Foreground:** `gybackend` (Ctrl+C to stop) — good for first-run debugging.
- **Background/service:** systemd / launchd / Task Scheduler, or `... start --daemon` (uses `nohup`/`Start-Process` and writes a pidfile + log).

---

## 6. Observability & SRE features (v2.0.0–v2.3.1)

The backend boots with a full **observability** stack wired in (`createObservability`), fed live by monitor snapshots. All of it is callable over the gateway (see the `rterm-gateway` skill).

### SRE core
- **MetricsLedger** — time-series store for resource snapshots (cpu/mem/disk/load/net/gpu) per host, with trend slope + **days-to-threshold forecasting** ("disk full in N days").
- **UptimeWatchdog** — liveness probes (tcp/ssh/http/command) per host, up/degraded/down, with state transitions firing alerts.
- **SloService** — SLO/SLI definitions, error budget, **burn rate**, fast-burn alerting.
- **AlertService** — alertmanager-style routing: grouping, dedupe, silences, severity channels.
- **IncidentLedger** — auto-incidents with timelines, AI **RCA**, **postmortems**, runbook links.
- **GoldenSignals** — saturation/traffic/latency/errors per host + capacity forecast.
- **SyntheticChecks** — blackbox probes feeding the SLO SLI + golden latency/error.
- **DriftDetector** — template-vs-live config diff + MOP auto-remediation.

### APM / DEM / Infra / ETW
- **SpanLedger (APM)** — OTLP distributed-trace store + analysis (per-service p50/95/99, error rate, slowest traces, bottleneck services).
- **RumLedger (DEM)** — Core Web Vitals (LCP/INP/CLS/TTFB) per page + error rate, slowest/poor pages.
- **InfraMonitor (k8s/cloud)** — cluster health (running/notReady/CrashLoop/restarts/nodes + cpu/mem % of limit), unhealthy instances.
- **EtwService (Windows)** — built-in ETW diagnostics (network/file/registry/process providers, logman sessions, Get-WinEvent/Get-Counter) — agentless, no install.

### Predictive + behavioral + evals
- **AnomalyDetector** — z-score / robust z-score (median±MAD) anomaly detection over metric series.
- **EarlyWarningService** — predictive failure alerts (trend forecast + anomaly) + optional MOP auto-remediation.
- **BehaviorLedger** — UEBA-style baselines (runs/day, tokens/run, error rate, models) + deviations (run-spike, token-blowout, error-spike, unusual-model).
- **EvalHarness** — embedded evals measuring the agent's **accuracy, tool selection, safety/policy, determinism/replay** with an aggregate reliability report.

### Notifications (Slack / Teams / SMTP / Telegram)
Wire alert channels into the AlertService with vaulted webhook URLs / SMTP creds (rich, severity-colored payloads):

```bash
# via the gateway (rterm-gateway skill) — add a Slack channel
# (see examples/notify-channels.mjs)
```

### Unified live dashboard
A single `dashboard:state` object aggregates **every** ledger (fleet health, SLO board, uptime map, incident feed, APM bottleneck+slowest, DEM slowest/poor, k8s clusters, capacity forecast) — broadcast over the gateway for rich, live, cross-linked dashboards. A `renderDashboardHtml` renderer produces a **browser-viewable HTML dashboard** from that state (Aurora-themed, auto-refreshing) — serve it over HTTP to view the live dashboard in any browser.

### dagu workflows (v2.4.0+)
Run declarative [dagu](https://github.com/dagucloud/dagu) YAML DAG workflows natively on RTerm's orchestrated playbook engine — **no dagu server required**. The `daguParser` compiles dagu YAML into a playbook:
- **Steps** — `id`/`name`, `run`/`command`/`cmd`/`script`/`call` (all forms) → step commands.
- **Dependencies** — `depends` (string or array) → `dependsOn` (fan-out/fan-in DAG waves).
- **Failure handling** — `continue_on` → `onError: continue`; `retry_policy` noted.
- **Guards** — `preconditions` → a `desiredState` skip-when-satisfied guard.
- **Runbook params** — `params` (string or object with `default`) → playbook params with defaults.

Paste a dagu YAML workflow to the agent ("run this dagu workflow") or compile it via `parseDaguYaml` and run the resulting playbook with `run_playbook` — it executes on RTerm's orchestrated DAG runner across your hosts with validation and rollback.

### AWS APerf deep-dive (v2.6.0+)
Deploy the [AWS APerf](https://github.com/aws/aperf) CLI to any Linux host via SSH, record deep system performance metrics (CPU, memory, disk, network, PMU counters, processes, hotspot data), generate the aperf analysis report, and parse the findings into structured results that feed the metrics ledger + agent RCA. Combines aperf's deep profiling with RTerm's agent reasoning.

Ask the agent: *"Run an APerf deep-dive on web-01 and report the top performance issues"* — the agent installs aperf on the host (if needed), records for the sampling period, parses the report, and returns findings with severity thresholds (critical ≥90%, warning ≥75%, process ≥50% CPU).

### Plugin system (v2.5.0+)
Anyone can develop a custom plugin and have it auto-integrate. A plugin is a folder with a `plugin.json` manifest (name, version, entry, tools, triggers, panels, permissions) and an `index.mjs` entry module exporting `register(ctx)`. The `PluginRegistry` discovers plugins in:
1. `~/.gybackend-data/plugins` (user-installed)
2. `./plugins` (repo/dev)
3. `{bundle}/../plugins` (npm package)
4. `{resourcesPath}/plugins` (desktop app)

The backend **ships with 6 official plugins** out of the box (21 tools, 10 triggers, 6 panels):

| Plugin | What it does |
|---|---|
| **patch-manager** | Autonomous patch management — `patch_status`/`patch_plan`/`patch_apply` tools, `patch_failure`/`patch_completion` triggers, patch-compliance dashboard. Supports yum/apt/Windows Update. |
| **request-router** | Automated request handling — `submit_request`/`approve_request`/`list_requests`/`request_status` tools. Risk classification (low/med/high) → auto-approve/queue/MOP routing. |
| **sop-assistant** | IAM Knowledge & SOP Assistant — `sop_search`/`sop_get`/`sop_execute`/`iam_lookup` tools. 8 built-in SOPs (restart-service, disk-cleanup, reset-password, database-failover, ssl-cert-renewal, user-offboarding, backup-restore, incident-response) + 4 IAM policies. |
| **iam-connector** | IAM integration — `iam_user_info`/`iam_user_groups`/`iam_disable_user`/`iam_access_review` tools. Privileged access identification, access review. Linux (id/groups/usermod) + Windows (Get-LocalUser). |
| **fraudops** | FraudOps operational layer — `fraudops_pipeline_status`/`fraudops_str_assign`/`fraudops_str_status`/`fraudops_decision_summary` tools. Flink/NATS/Kafka health, STR workflow (7-day CBN deadline), decision summary. |
| **netdata-rterm** | Netdata integration — `netdata_alert_summary`/`netdata_correlate` tools. Ingests Netdata Cloud alert webhooks, correlates with RTerm metrics/incidents for RCA. Triggers for auto-remediation + MOP changes. |

### Audit trail + evidence sealing (v2.7.1)
Hash-chained, tamper-evident audit ledger — every audit-relevant event (agent runs, command evaluations, approvals, MOP changes, playbook steps, trigger firings, alert ingestions) is appended with the SHA-256 hash of the previous record. Any tampering breaks the chain and is detectable via `verify()`. The **evidence sealer** computes a Merkle-tree root over records → sealed, independently-verifiable evidence bundles (KLA audit framework domain 11). 18 event kinds recorded.

### Monitor diagnostics (v2.7.6)
`monitorStatus` diagnostic — reports exactly why monitor stats aren't displaying per terminal: publisher wired? session exists? collection stuck in-flight? terminal connected? platform detected? last-collect time? Diagnoses: `terminal_not_connected`, `no_monitor_session`, `collection_stuck_in_flight`, `never_collected`, `stale_collection (>30s)`, `publisher_not_wired`.

Ask the agent: *"Run monitor status diagnostics"* — instantly shows which terminals aren't collecting and why.

### AGT policy engine (v2.7.7)
Microsoft AGT-style policy engine — evaluates every consequential action against a YAML policy before execution. Decisions: `allow` / `deny` / `escalate` (route to approval). Features: glob-style action patterns (`"read"` matches `"read /etc/passwd"`), target wildcards (`prod-*`), first-match-wins, case-insensitive matching, agent identity + sponsoring principal for zero-trust. Built-in default policy: allow read/status/list; deny delete/drop/format; escalate restart/patch/deploy on `prod-*`. Drop a custom `policy.yaml` in the data dir to override.

### Review model / maker-checker (v2.7.8)
The **review model** (a second LLM, the "checker") independently verifies the action model's (the "maker's") output on **5 dimensions**: correctness, completeness, safety, compliance, and accuracy.

- **Verdicts:** `approved` / `needs_revision` / `escalate`.
- **Modes:** `strict` (block on any issue), `advisory` (flag but allow), `auto-approve` (skip review for low-risk actions).
- **Fast output mode:** if no `reviewModelId` is set in the model profile, reviews are skipped entirely (zero added latency).

Configure in `settings.json` → `models.profiles[].reviewModelId` + `reviewMode` — or in the desktop Settings UI (v2.7.9+).

### v2.9.x platform capabilities

v2.9.0 added 9 backend modules; **v2.9.2 exposed them as 41 `observability:*` gateway RPC methods + 9 agent tools** (see the `rterm-gateway` skill §4b); **v2.9.3 made the tools visible in the Tools section**. All are wired into `createObservability` and live on a stock install.

| Capability | Module | How you use it |
|---|---|---|
| **Prometheus /metrics + OTel push** | `sre/prometheusExporter`, `sre/otelExporter` | Scrape `observability:metricsPrometheus`, or set `OTEL_EXPORTER_OTLP_ENDPOINT` to push OTLP to a collector |
| **Secrets vault** | `secrets/secretsVault` | AES-256-GCM store; set `RTERM_SECRETS_MASTER_KEY` at boot; `observability:secrets*` (metadata only, never values) |
| **Incident escalation & on-call** | `oncall/escalationService` | Multi-level policies, ack deadlines, paging via `observability:oncall*` |
| **AI cost & budgets** | `cost/costBudgetService` | Per-model USD attribution + warn/throttle/deny budgets via `observability:cost*` |
| **Live dashboard hub** | `liveui/liveDashboardHub` | Push-based multi-client dashboard via `observability:liveDashboard*` |
| **Session recording/replay** | `recording/sessionRecorder` | asciinema `.cast` v2 via `observability:recording*` |
| **GitOps** | `gitops/gitOpsService` | Desired-state manifest, drift, reconcile via `observability:gitops*` |
| **Playbook versioning + lint** | `automation/playbookVersioning` | History/diff/rollback + static lint via `observability:playbook*` |
| **Cloud inventory (AWS/GCP/Azure)** | `cloud/cloudInventory` | Normalized instance inventory via `observability:cloud*` (inject fetchers) |

Agent tools (visible in the Tools section since v2.9.3): `get_metrics`, `manage_secret`, `manage_oncall`, `get_cost`, `manage_recording`, `manage_gitops`, `manage_playbook_version`, `get_cloud_inventory`, `get_live_dashboard`. Ask the agent: "add this API key to the vault", "show my AI spend today", "page the on-call", "lint this playbook", "list my AWS instances".

**v2.9.5 — APM/DEM/Infra/ETW ingestion.** The observability ledgers are now genuinely fed out of the box via `observability:apmIngestSpans` (OTLP spans → trace store), `observability:demIngestBeacon` (Core Web Vitals RUM beacons → per-page p75), `observability:infraCollect` (k8s cluster health from kubectl), and `observability:etwStartTrace/etwStopTrace/etwParse` (Windows ETW diagnostics) — plus the matching agent tools `ingest_apm_spans`/`get_apm_summary`, `ingest_dem_beacon`/`get_dem_summary`, `collect_infra`, `manage_etw`.

**New env vars:** `OTEL_EXPORTER_OTLP_ENDPOINT` / `RTERM_OTLP_METRICS_ENDPOINT` (OTel push), `RTERM_SECRETS_MASTER_KEY` (unlock the secrets vault).

### v2.9.6 — settings-driven cost, alerts, on-call & cloud (no placeholders)

Four capabilities that were constructor-injected but never wired to settings/UI are now **persisted settings blocks (schema v4→v5)**, editable in **Settings UI**, and **live-reloaded without a restart** (via `SettingsService.onDidChange` → `refreshCost` / `refreshAlertChannels` / `refreshOncallChannels` / `refreshCloudAccounts`). Secrets are never inline — `secretRef` into the AES-256-GCM vault, resolved at send/sync.

| Settings block | Backs | Settings UI | Notes |
|---|---|---|---|
| `cost.modelPrices` + `cost.budgets` | `CostBudgetService` | **Settings → AI Cost** | USD/1M-token price table (`default` fallback) + warn/throttle/deny budgets. Turns the run ledger's token counts into real dollars (was always `$0`). |
| `alerts.channels[]` | `AlertService` (slack/teams/smtp/telegram) | **Settings → Alerts** | Channel editor (type, severity, enable, secretRef, telegram chatId, full SMTP). Ships a dependency-free SMTP sender (`sendSmtpMail`, net/tls). |
| `oncall.pagingChannels[]` | `EscalationService` (slack/teams/smtp/telegram/**webhook**) | **Settings → On-Call** | Paging channels pages target by name; `setChannels`/`listChannels` hot-swap live. |
| `cloud.accounts[]` | `CloudInventory` (aws/gcp/azure) | **Settings → Cloud** | Per-account region + credential `secretRef` (vault `KEY=VAL` env injected into the provider CLI). Empty → ambient CLI creds. `setAccounts` live. |

Set them via `settings:set` (`{cost:{modelPrices:{…},budgets:[…]}}`, `{alerts:{channels:[…]}}`, `{oncall:{pagingChannels:[…]}}`, `{cloud:{accounts:[…]}}`) or the desktop UI — both persist and apply live. Seed the actual secret values into the vault separately (`manage_secret` / `RTERM_SECRETS_MASTER_KEY`).

### v2.9.7 — security republish + 3 bug fixes

- **SECURITY (npm only):** `neuralos@2.9.6`/`rterm-backend@2.9.6` accidentally bundled a local `.gybackend-data/settings.json` (created during a boot-verify) containing a live API key. Both 2.9.6 packages were **deprecated then unpublished**; clean 2.9.7 adds a hardened `.npmignore`. Git history was never affected. **If you installed 2.9.6 from npm, rotate the affected OpenRouter/provider key and upgrade.**
- **Cost attribution:** new `normalizeModelId()` collapses self-doubled provider model ids (e.g. `moonshotai/kimi-k3moonshotai/kimi-k3`) at the run-ledger boundary so pricing matches the configured model (was falling to `default`). Fixes forward.
- **GitOps gateway:** `assertManifest()` guard — calling `observability:gitopsDrift/inSync/reconcile` with no manifest returns a clear actionable error instead of an opaque `Cannot read properties of undefined`.

### v2.9.8 — backend typecheck fully green + CHANGELOG-driven release notes

- **Backend typecheck is now exit 0 across the whole backend.** ESM-safe native loaders via `createRequire(import.meta.url)`: `commandParser.ts` (web-tree-sitter `Language` type-vs-value), `NodePtyBackend.ts` (lazy `node-pty`), and `SSHBackend.ts` (the `let ssh2` variable shadowed the `ssh2` type namespace → renamed `ssh2Lib` + `import type * as ssh2`, ~50 errors cleared).
- **`build-release.yml` builds the GitHub release body from `CHANGELOG.md`** (extracts the current version's section) instead of a stale hardcoded template — v2.9.8's notes were generated by this new path.

### v2.9.9 (in progress) — AgentSpan/Conductor durable-agent bridge

The **`agentspan-bridge` plugin** connects RTerm to an [AgentSpan](https://github.com/agentspan-ai/agentspan) (Netflix Conductor) server, adding what RTerm didn't already have: **true durable agent execution** (a crashed run resumes from the last completed step, not just a ledger entry), **plan-execute determinism** (LLM plans once → immutable sub-workflow), **enterprise event triggers** (Kafka/SQS/AMQP/DB), and the server's **visual execution UI**.

- **Configure:** Settings → **AgentSpan** (`agentspan.serverUrl`, default `http://localhost:6767`, + optional `agentspan.authSecretRef` → a vault key holding `AGENTSPAN_AUTH_KEY`/`AGENTSPAN_AUTH_SECRET`). Run the server with `agentspan server start`.
- **6 agent tools:** `agentspan_health`, `agentspan_run` (AgentConfig or named workflow → executionId), `agentspan_status`, `agentspan_approve` (HITL respond), `agentspan_list`, `agentspan_stop`.
- **1 trigger:** `agentspan_execution_failed` (fires on FAILED/TERMINATED/TIMED_OUT). **1 panel:** `agentspan-executions` (live execution feed).
- **Resilient:** if the server is down, tools return a clear "server unreachable" hint instead of throwing. See the `agentspan` skill for the standalone AgentSpan SDK/CLI.

### v2.9.10 — AgentSpan Phase 2 (playbooks as workflows + delegate)

Deepened the bridge **both directions**: `agentspan_export_playbook` (dry-run a playbook as a Conductor WorkflowDef), `agentspan_register_playbook` (register an RTerm playbook as a reusable Conductor workflow other agents call via SUB_WORKFLOW), and `agentspan_delegate` (hand a prompt to a durable AgentConfig agent that runs start-to-finish → executionId survives restart). The plugin now has **9 tools**.

### v2.9.11 — agent-tool session recording fix

Recordings started via the agent's `manage_recording` tool captured **0 events** (the tool called `SessionRecorder.start()` directly, which never registered the terminal in `TerminalService.activeRecordings` — the live-output feed checks that map). `start` now routes through `TerminalService.startRecording()` (registers the terminal) and `stop` deregisters. Agent-started recordings now capture, replay, and export `.cast`. No asciinema needed.

### v2.9.12 — agent-created triggers fire live

Triggers created via `manage_trigger` were **persisted but never fired** (the `TriggerEngine` loaded persisted triggers once at startup; new ones weren't synced into the live engine). `manage_trigger` create/update/delete/enable/disable now upserts/removes them in the live engine, so they fire **without a backend restart**.

### v2.9.13 — version check 403 fix + silent background updates + no GitHub in UI

The updater fetched `version.json` from the **GitHub API contents endpoint** (rate-limited → red "Check Failed: HTTP 403" every hour). Now it fetches from the **raw GitHub URL** (`raw.githubusercontent.com`, no rate limit), checks **silently in the background** (transient network failures keep last-good and stay quiet instead of a red error), and the UI shows the app website **rterm.app** as the source and **rterm.app/#download** as the download URL — **no GitHub URL visible**.

### v3.0.0 — API self-discovery (`gateway:describe` + method registry + `list_gateway_methods`)

The gateway now **describes itself**. A single-source **`methodRegistry.ts`** holds the whole RPC surface (name, category, description, `since`, params) that the adapter's dispatch, the **`gateway:describe`** endpoint, the **`list_gateway_methods`** agent tool, and the reference docs all derive from — so they can never drift. **123 methods across 12 categories.** `gateway:describe` returns `{version, count, categories, methods}` with optional `category`/`prefix` filters; the agent tool does the same. Ask the gateway what it can do instead of reading `WebSocketGatewayAdapter.ts` or a static doc.

### v3.0.2 — live browser dashboard at `/dashboard` (same port as the WS gateway)

The unified dashboard is now **visible in any browser**. A new `httpRoutes` option on `WebSocketGatewayAdapter` lets the default server factory create ONE node `http.Server` — plain HTTP requests hit a route table, WS upgrades hit the WSS on the **same socket/port** (ESM-safe `createRequire` for `node:http`; no routes = old behavior). `startGyBackend` registers **`/dashboard`** (live HTML) + **`/dashboard/json`** (state): `renderLiveDashboardHtml()` renders initial state server-side, then an embedded client subscribes via `observability:liveDashboardSubscribe` and updates each section **in place** on every monitor-snapshot push (falls back to polling `/dashboard/json` 5s). Auth mirrors the WS gateway (loopback open, remote needs an access token via Bearer/header/query). Startup logs the dashboard URL. `open http://localhost:17888/dashboard`.

### v3.0.5 — terminal/session core + chat navigation + memory improvements

- **SSH auto-reconnect** with exponential backoff + jitter (1s→2s→5s→15s→60s cap, 10 max attempts); `tab.reconnectState` surfaces "reconnecting (attempt N)…" in the UI; manual kills cancel the schedule.
- **WinRM persistent runspaces** — `runCommandOnShell()` reuses one shell across commands (was 4 WS-Man round trips per command); **streaming** output via `onChunk`; **persistent cwd** so `cd` sticks; auto-recovery on dead shell.
- **Serial break/DTR/RTS** — `sendBreak()` (Cisco password recovery / ROMMON) + `setControlLines()`.
- **Chunked ring buffer** — `ChunkedRingBuffer` replaces the single re-sliced string (O(1)-ish appends, no O(n) copy per chunk on busy tabs).
- **Chat user-message navigation** — Prev/Next/Latest user buttons + Top/Bottom scroll; programmatic-scroll guard prevents the "can't scroll back to bottom" bug.
- **Memory manager** — `memoryManager.ts`: search, dedupe, append-with-cap, relevance-ranked `recallForPrompt()` (caps injected memory at 12k chars instead of the whole file).

### v3.0.6 — chat scroll fix + top/bottom buttons

Fixed the scroll bug where "Prev user" latched auto-scroll off permanently. `programmaticScrollRef` guard distinguishes programmatic jumps from user scrolls. Added ⇤ Top / ⇥ Bottom one-click buttons. Nav bar always present.

### v3.0.8 — SSH legacy/cisco algorithm preset hotfix

Removed ssh2-unsupported algorithms from the `legacy`/`cisco` presets (added in v3.0.6 but ssh2 1.17 throws on any offered algo it can't load). `filterToSupported()` defensively intersects presets with ssh2's SUPPORTED_* constants.

### v3.0.9 — `web-intel` plugin: local-first web intelligence (via wigolo)

The agent now has **first-class web tools** it didn't have: multi-engine search, clean-page fetch, site crawl, research, and page-watch → RTerm trigger automation. Built as a first-class plugin (`plugins/web-intel/`) following the agentspan-bridge pattern.

**9 tools / 1 trigger / 1 panel:**
- `webintel_health` — daemon status, lean-vs-full warmup, auto-start state.
- `web_search` — multi-engine ranked search with citations (keyless, $0).
- `web_fetch` — clean markdown + metadata + links (tiered router escalates to browser engine for JS/SPA/anti-bot).
- `web_crawl` — multi-page crawl (BFS/DFS/sitemap/map-only).
- `web_research` — decompose a question → ranked evidence + citations. **Synthesis uses RTerm's own agent — no LLM key needed or stored.**
- `web_find_similar` — pages similar to a URL/concept (keyword + semantic + live web fusion).
- `web_watch_add` / `web_watch_list` / `web_watch_remove` — watch a vendor/CVE/status page; the `webintel_page_changed` trigger fires so a playbook/MOP can react.
- Panel `web-intel` — watched pages + daemon status.

**Lean by default (stock RTerm stays lean):**
- The wigolo daemon starts **lazily on first use** (`npx -y wigolo serve`) — nothing downloaded at install time.
- Default is `WIGOLO_NO_WARMUP=1` — the ~1.5 GB browser engine + on-device models are **not** downloaded until a tool that needs them runs, or until `webIntel.warmupOnInit: true` (which kicks off a background `wigolo init`).
- Search/fetch/crawl work keyless without the heavy models.

**Settings block `webIntel`** (schema v5 + `normalizeWebIntelSettings`):
`{enabled, restUrl, token, autoStart, warmupOnInit}` — defaults keep everything lean and local. Token is optional (only if the daemon uses `WIGOLO_API_TOKEN`).

**Plugin infrastructure upgrades (shared):**
- `PluginContext.spawnProcess` (optional) — plugins can spawn local sidecar daemons; wired in `observability.ts` via `createRequire('node:child_process')`.
- `PluginContext.settings` / `getSettings` — live settings snapshots for plugins that read config blocks.
- `registerPanel` accepts both `(name, render)` and `{name, title?, render}` (pre-existing signature drift fixed).

**Resilient:** if the daemon is down and can't auto-start, every tool returns `{error, hint}` instead of throwing — the agent stays usable.

---

## 7. Manage connections, automation & schedules

Once running, manage it over RPC (see the `rterm-gateway` skill). Highlights:

- **Saved connections** — `settings:get` / `settings:set` → `connections.{ssh,winrm,serial}`; or ask the agent (`agent:startTask`) to "create an SSH connection X".
- **Automation** — groups, scripts, **scheduled tasks** (5-field cron), config templates, playbooks (validation + automatic rollback).
- **Scheduler** — runs inside the daemon on a per-minute tick; create/edit tasks via `settings:set` (automation.scheduledTasks).
- **Change (MOP)** — plan → approve → run → status, with a durable change ledger.

Create a cron task headlessly:

```jsonc
// settings:set -> automation.scheduledTasks +=
{
  "id": "friday-cleanup",
  "name": "Friday Night Cleanup",
  "cron": "0 0 * * 5",
  "enabled": true,
  "groupId": "cleanup-targets",
  "command": "find /var/app/cache -type f -mtime +30 -delete; journalctl --vacuum-time=7d"
}
```

---

## 7. Use cases

1. **CI/CD gate** — after deploy, `agent:startTask` → "health-check the fleet and report unhealthy nodes" → fail the pipeline on DEGRADED.
2. **Scheduled patch/AV** — cron task runs `Update-MpSignature` across a Windows fleet weekly; versions recorded to the run ledger. Or use the **patch-manager plugin**: `patch_status` → `patch_plan` → MOP approve → `patch_apply`, with a fleet-wide compliance dashboard.
3. **Multi-vendor change** — Jinja-render a Cisco BGP config, apply via `algorithmsPreset=cisco` + `vt100`, then update an AWS SG — with validation + rollback.
4. **Sub-agent** — an orchestrator LLM delegates ops tasks to RTerm's agent and reads transcripts.
5. **Audit** — run ledger + change ledger + session logs + **hash-chained audit ledger (v2.7.1)** + **evidence sealing (Merkle tree)** = complete, tamper-evident, independently-verifiable command-and-output trail.
6. **Autonomous patching** — patch-manager plugin discovers patches, builds deployment plans, executes with MOP approval, alerts on completion/failure, reports fleet compliance.
7. **Request handling** — request-router plugin receives operational requests, classifies risk, routes for approval (auto-approve/queue/MOP), executes end-to-end, audits every step.
8. **SOP-guided ops** — sop-assistant plugin answers "how do I X?" with relevant SOPs and executes them step-by-step with variable substitution + confirmation.
9. **IAM governance** — iam-connector plugin reviews user access, identifies privileged accounts, disables users (with approval), runs access reviews.
10. **FraudOps** — fraudops plugin monitors the fraud detection pipeline (Flink/NATS/Kafka), manages STR workflow with CBN deadlines, summarizes decisions.
11. **Performance deep-dive** — AWS APerf integration deploys aperf to any Linux host, records CPU/PMU/flamegraph metrics, parses findings into the metrics ledger + agent RCA.
12. **Governance** — AGT policy engine evaluates every consequential action against a YAML policy (allow/deny/escalate); the **review model (maker/checker)** independently verifies the action model's output on 5 dimensions (correctness, completeness, safety, compliance, accuracy).

See `examples/` for runnable programs.

---

## 8. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| close on connect | token missing/invalid or IP not in CIDR allow-list (localhost bypasses token) |
| `METHOD_NOT_FOUND` | RPC not in this build; use a supported method |
| `BAD_JSON`/`BAD_REQUEST` | malformed frame or wrong param type |
| WinRM "ready" but no output | you used `terminal:write` on WinRM (a no-op) — drive via the agent |
| task stalls awaiting approval | policy is `standard` — answer `agent:replyCommandApproval`, allowlist, or use `smart` |
| blocking `startTask` times out | long task — use `agent:startTaskAsync` + watch events |
| SSH "All configured authentication methods failed" | supply a credential (password **or** privateKey) — authMethod is inferred |
| native module load error | no prebuilt binary for your platform — install a C/C++ toolchain and reinstall |
| port already in use | another gybackend/RTerm app holds it — `... stop` or use a different `GYBACKEND_WS_PORT` |

**Artifacts to collect:** the run-ledger entry (status+error), the session log for
the terminal, the gateway boot log, and a minimal RPC repro (a websocat one-liner).

---

## Supporting files

- `scripts/rterm-backend.mjs` — cross-platform lifecycle CLI (install/start/stop/restart/status/logs/ping/config-show/install-service/uninstall/doctor). No dependencies.
- `service/rterm-backend.service` — systemd unit (Linux).
- `service/ng.hyperspace.rterm-backend.plist` — launchd plist (macOS).
- `service/install-windows-service.ps1` — Task Scheduler registration (Windows).
- `examples/fleet-health-gate.mjs` — CI/CD post-deploy gate.
- `examples/schedule-weekly-av.mjs` — create a weekly AV-update cron task headlessly.
- `examples/mop-approved-change.mjs` — approval-gated change (plan → approve → run).
