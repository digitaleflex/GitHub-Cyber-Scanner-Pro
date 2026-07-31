---
name: rterm-systems-thinking
description: The ultimate problem-solving and complex-systems playbook for RTerm / rterm-backend. Use when an agent needs to break down ambiguous, large, or messy systems into bounded sub-systems; estimate capacity (users, QPS, storage, bandwidth); prioritize requirements (MoSCoW); reason about trade-offs (CAP, PACELC, consistency vs availability, push vs pull, sync vs async); and then EXECUTE the design across real infrastructure using RTerm's terminals, fleet orchestration, playbooks, MOP change management, SRE observability, plugins, governance (AGT policy + maker/checker review), and audit trail. Turns "figure out the system" into "deploy, measure, and operate it."
---

# RTerm Systems Thinking — Problem Solving & Breaking Down Complex Systems

This skill is the **operating manual for attacking hard, ambiguous systems problems with
RTerm**. Most system-design frameworks stop at the whiteboard. RTerm goes further: the same
agent that helps you decompose the problem, estimate the load, and pick the trade-offs can
then **build, measure, and operate the real thing** — across SSH/WinRM/Serial fleets, with
playbooks, MOP approvals, SRE telemetry, governance, and a tamper-evident audit trail.

Use it when the request sounds like:
- "Design / break down / reason about system X" (a payment switch, a URL shortener, a data platform, an observability stack, a fraud engine, a multi-region deployment).
- "How much capacity do we need?" (users → QPS → storage → bandwidth → node count).
- "What's the right trade-off here?" (consistency vs availability, push vs pull, sync vs async, SQL vs NoSQL, monolith vs services).
- "Take this ambiguous blob and turn it into bounded sub-systems we can build."
- "Prove the design works on real infrastructure" — then deploy it, measure it, and operate it.

---

## 1. The RTerm systems-thinking loop

Every complex-systems engagement with RTerm runs the same 7-step loop. Each step maps to a
concrete RTerm capability — so the thinking never floats free of the infrastructure.

```
1. FRAME      →  what is the real problem? (agent chat, SOP retrieval)
2. DECOMPOSE  →  break the blob into bounded sub-systems (agent reasoning + plugins)
3. PRIORITIZE →  MoSCoW the requirements (agent + request-router)
4. ESTIMATE   →  users → QPS → storage → bandwidth → nodes (agent math + APerf/metrics)
5. TRADE-OFFS →  CAP / PACELC / sync-vs-async / push-vs-pull (agent reasoning + AGT policy)
6. BUILD      →  deploy the design on real hosts (playbooks, MOP, fleet ops, templates)
7. OPERATE    →  measure, alert, remediate, audit (SRE pillar, triggers, audit ledger, review model)
```

The killer feature: **steps 1–5 are the agent thinking with you; steps 6–7 are the agent
doing it for you.** One surface, no handoff.

---

## 2. FRAME — pin down the real problem

Ambiguous requests hide the actual problem. Force it into the open before any design work.

**The RTerm way:** ask the agent to restate the problem as *actor + action + constraint +
success metric*, and pull any relevant SOPs/runbooks for context.

> "Restate this problem as: who does what, under which constraint, and how we know it worked.
> Then search the SOP library for anything relevant (sop-assistant: sop_search)."

Example — "we need a better monitoring system":
```
Actor:      on-call SRE for 40 mixed Linux/Windows hosts
Action:     detect + diagnose + remediate incidents
Constraint: no new agents on hosts (SSH/WinRM only), ≤ 5 min MTTD
Success:    95% of incidents auto-diagnosed with RCA in the incident ledger
```

**RTerm features used:** the agent's reasoning, `sop-assistant` (`sop_search`, `sop_get`)
for existing runbooks, and `memory.md` to persist the framing across the engagement.

---

## 3. DECOMPOSE — break the blob into bounded sub-systems

Complex systems are only hard because they're unbounded. Bound them. The pattern that works
every time: **data in → processing → state → data out → edge cases**.

**The RTerm way:** have the agent produce a sub-system map with explicit boundaries,
ownership, and interfaces — then check each box against what RTerm can already operate.

> "Decompose this system into bounded sub-systems using the data-in → processing → state →
> data-out pattern. For each sub-system: its responsibility, its interface, its owner, and
> which RTerm capability (terminal, playbook, plugin, ledger) could operate it."

Example — a payment switch decomposed:
```
1. Edge / protocol adapter     (ISO 8583 / NIP in-out)      → RTerm: terminal backends, plugins
2. Buffer / queue              (Kafka / NATS JetStream)     → RTerm: NATS event mesh
3. Scoring / rules engine      (rules + ML)                 → RTerm: agent reasoning, evals
4. State stores                (feature store, decisions)   → RTerm: SQLite ledgers, templates
5. Decision fan-out            (20+ consumers)              → RTerm: NATS mesh, gateway push
6. Ops & monitoring            (health, SLO, incidents)     → RTerm: SRE pillar, dashboard
7. Governance & audit          (who did what, provably)     → RTerm: AGT policy, audit ledger
```

Each sub-system is now **bounded** (one responsibility), **owned** (a named owner), and
**operable** (an RTerm capability attached). That last column is what turns a diagram into
a running system.

**RTerm features used:** agent reasoning, the plugin system (each sub-system can become a
plugin), `manage_template` for interface contracts, `manage_device_memory` for per-host notes.

---

## 4. PRIORITIZE — MoSCoW the requirements

Not everything matters equally. **MoSCoW**: Must have, Should have, Could have, Won't have
(this time). It kills scope creep before it starts.

**The RTerm way:** have the agent MoSCoW the requirements, then encode the Must-haves as
requests (request-router) or SLOs (SloService) so they're tracked, not just listed.

> "MoSCoW these requirements for the monitoring system. Then create a tracked request for
> each Must-have (request-router: submit_request) and an SLO for the availability one."

Example:
```
MUST:   per-second metrics on 40 hosts; ≤5 min MTTD; incident ledger with RCA
SHOULD: SLO burn-rate alerts; capacity forecast (days-to-disk-full)
COULD:  APM traces; RUM web vitals; ETW deep-dives
WON'T:  replace Netdata's per-second collectors; build a custom TSDB
```

**RTerm features used:** `request-router` (`submit_request`, risk-classified routing),
`sloService` (SLO/SLI + error budget), `manage_scheduled_task` for Won't-later items.

---

## 5. ESTIMATE — users → QPS → storage → bandwidth → nodes

Back-of-the-envelope estimation turns vibes into numbers. The canonical chain:

```
DAU → requests/day → QPS → peak QPS (×2–3) → storage/day → total storage → bandwidth → nodes
```

**The RTerm way:** have the agent do the math explicitly, then *validate the estimates
against reality* with RTerm's own telemetry (metrics ledger, APerf deep-dive, golden signals).

> "Estimate capacity for a 5M DAU API: requests/day, average QPS, peak QPS, storage/day,
> 3-year storage, egress bandwidth. Then compare the CPU/network estimate against what
> APerf actually measures on our current box."

Worked example — 5M DAU, 10 requests/user/day:
```
requests/day   = 5M × 10            = 50M/day
avg QPS        = 50M / 86400        ≈ 580 QPS
peak QPS       = 580 × 2.5          ≈ 1,450 QPS
payload        = 2 KB/req
storage/day    = 50M × 2 KB         = 100 GB/day (raw), ×0.2 retained = 20 GB/day
3-year storage = 20 GB × 365 × 3    ≈ 22 TB
bandwidth      = 1,450 × 2 KB × 2   ≈ 5.8 MB/s ≈ 46 Mbps (in+out)
nodes          = 1,450 QPS / 300 QPS-per-node ≈ 5 app nodes (+ LB + 2 standby)
```

**RTerm features used to validate the envelope:** `aperfService` (deep CPU/PMU/process
profiling on a real host), `metricsLedger` (live cpu/mem/disk/net per host), `goldenSignals`
(saturation + capacity forecast), `earlyWarningService` (days-to-threshold).

---

## 6. TRADE-OFFS — the decision frameworks

Every design is a bundle of trade-offs. These are the frameworks that structure the
thinking — and how RTerm lets you *test the trade-off on real infrastructure*.

### 6.1 CAP theorem
Under a network **Partition**, a distributed system must choose between **Consistency**
(every read gets the latest write or an error) and **Availability** (every request gets a
non-error response, maybe stale). You can only fully have two of three.

| Choice | When it's right | RTerm angle |
|---|---|---|
| **CP** (consistency over availability) | money movement, inventory, STR/fraud decisions | encode as MOP-gated changes (manage_change) so nothing half-applies |
| **AP** (availability over consistency) | metrics, dashboards, discovery, presence | RTerm's metrics ledger + dashboard are AP by design (best-effort, eventually consistent) |
| **CA** (only when no partition) | single-node systems, the gybackend SQLite ledgers | gybackend's local SQLite is CA — no partition on one node |

### 6.2 PACELC (the fuller picture)
CAP ignores the no-partition case. **PACELC**: **if Partition** then Availability vs
Consistency; **Else** (normal operation) **Latency** vs Consistency.

> "Evaluate our fraud-decision fan-out with PACELC: during a partition do we favor A or C,
> and in normal operation do we favor L or C? Then check the actual latency vs consistency
> behavior using the SpanLedger APM data."

### 6.3 Push vs pull
- **Pull (scraping)**: simple, resilient, e.g., RTerm's `ResourceMonitorService` pulling
  snapshots from each terminal. Great for telemetry.
- **Push (streaming)**: low latency, e.g., Netdata webhooks → `netdata-rterm`, or NATS
  events pushing to the mesh. Great for alerts.

### 6.4 Sync vs async
- **Sync**: request → response, e.g., `agent:startTask` (blocking). Use when the caller
  needs the answer to proceed.
- **Async**: fire-and-forget + events, e.g., `agent:startTaskAsync` + `gateway:event`.
  Use for long tasks (patches, deep-dives, fleet sweeps).

### 6.5 Strong vs eventual consistency
- **Strong**: MOP change management (plan → approve → run, with validation + rollback) —
  the change either fully applies or rolls back.
- **Eventual**: metrics ledger, dashboards, discovery inventories — fast to write, converge.

### 6.6 The AGT policy angle (v2.7.7+)
Trade-offs aren't just architectural — they're **operational**. The AGT policy engine lets
you encode "availability vs consistency" as *runtime policy*: read/status/list allowed
(autonomous), destructive denied, prod changes escalated to a human. Trade-off thinking,
enforced at execution time.

---

## 7. BUILD — deploy the design on real infrastructure

This is where RTerm leaves every other "systems thinking" framework behind. The agent that
helped you design the system can now **build it** — across your real fleet, with validation,
rollback, and approvals.

**The RTerm build toolkit:**

| Task | RTerm capability |
|---|---|
| Render configs for N hosts | `manage_template` (Jinja-subset templates with `{{var}}`) |
| Apply a multi-step rollout | `manage_playbook` (validation + automatic rollback) |
| Gate a risky change | `manage_change` (MOP: plan → approve → run → status) |
| Run the same command on the fleet | `run_fleet_command` (parallel, structured results) |
| Inventory the estate | `collect_facts` (per-host facts in parallel) |
| Stand up a scheduled job | `manage_scheduled_task` (5-field cron) |
| Wire event-driven behavior | `manage_trigger` (pattern/threshold/webhook → playbook/MOP) |
| Add a new capability | a custom **plugin** (tools + triggers + panels) |
| Deploy a packaged capability | an **official plugin** (patch-manager, fraudops, netdata-rterm, …) |
| Deep-dive a host's performance | `aperfService` (CPU/PMU/process/hotspot profiling) |

> "Render the nginx config from the template for all 5 web nodes, apply it as a playbook
> with validation (nginx -t) and automatic rollback on failure, then run the rollout as an
> approved MOP change. Record everything in the audit ledger."

---

## 8. OPERATE — measure, alert, remediate, audit

A system isn't done when it's built — it's done when it's *operated*. RTerm's SRE pillar
runs the whole loop.

| Operating concern | RTerm capability |
|---|---|
| Live metrics per host | `ResourceMonitorService` + `MetricsLedger` (snapshots, trend slope) |
| Golden signals | `goldenSignals` (saturation/traffic/latency/errors + capacity forecast) |
| Liveness | `uptimeWatchdog` (tcp/ssh/http/command probes, up/degraded/down) |
| SLOs | `sloService` (SLI, error budget, burn rate) |
| Alerts | `alertService` + `notifyService` (Slack/Teams/SMTP/Telegram) |
| Incidents | `incidentLedger` (timeline, AI RCA, postmortems) |
| Anomalies | `anomalyDetector` (z-score / robust z-score) + `earlyWarningService` (forecast) |
| Traces | `spanLedger` (OTLP APM: p50/95/99, error rate, bottlenecks) |
| Web vitals | `rumLedger` (LCP/INP/CLS/TTFB per page) |
| k8s/cloud health | `infraMonitor` (pods, restarts, node readiness, cpu/mem %) |
| Windows diagnostics | `etwService` (built-in ETW providers, agentless) |
| Auto-remediation | `manage_trigger` → playbook/MOP on pattern or threshold |
| Audit | `auditLedger` (hash-chained) + `evidenceSealer` (Merkle tree) |
| Independent verification | `reviewService` (maker/checker: correctness, completeness, safety, compliance, accuracy) |

---

## 9. Worked end-to-end examples (with RTerm commands)

### 9.1 Design + stand up a fleet-wide observability stack
```
FRAME:      "We can't see our 40 hosts. Actor=on-call SRE, action=detect+diagnose,
             constraint=no new agents, success=95% auto-RCA."
DECOMPOSE:  collection → storage → analysis → alerting → dashboard → audit
PRIORITIZE: MUST per-host metrics + incidents; SHOULD SLO burn rate; COULD APM/RUM
ESTIMATE:   40 hosts × 1 snapshot/5s ≈ 8 writes/s (trivial for SQLite ledger)
TRADE-OFFS: AP (metrics) + pull (ResourceMonitorService) + async alerts (NATS)
BUILD:      createObservability wires it all; add uptime watchdogs per host;
            wire Slack via notifyService.
OPERATE:    dashboard:state live; anomalyDetector + earlyWarningService watching;
            incidentLedger auto-creates incidents with RCA.
```
Ask the agent: *"Stand up the observability stack for all 40 hosts: metrics ledger, uptime
watchdogs, a 99.9% uptime SLO, Slack alerts, and the unified dashboard. Report when live."*

### 9.2 Break down + operate a fraud-detection pipeline
```
FRAME:      sub-second fraud scoring on NIP payments (see the architecture doc).
DECOMPOSE:  NIP edge → Kafka/Flink core (scoring) → decision fan-out → STR workflow →
            monitoring → audit. RTerm owns the boundary + ops, not the 25ms hot path.
PRIORITIZE: MUST zero-loss edge + decision fan-out + STR deadlines; SHOULD LLM review;
            COULD shadow scoring.
ESTIMATE:   3,000 TPS peak → NATS JetStream buffer sized; 20+ fan-out consumers.
TRADE-OFFS: CP for decisions (MOP-gated), AP for monitoring; push (NATS) for fan-out,
            pull for metrics.
BUILD:      fraudops plugin for pipeline health + STR; netdata-rterm for anomaly ingest;
            aperfService for scoring-host deep-dives.
OPERATE:    fraudops_pipeline_status health checks; fraudops_str_overdue escalations;
            auditLedger for CBN-grade evidence; reviewService double-checks agent actions.
```

### 9.3 Capacity-plan a new API product
```
FRAME:      launch a public API, unknown load, must not fall over at launch.
DECOMPOSE:  edge/LB → app nodes → DB → cache → async workers → observability.
PRIORITIZE: MUST survive 10× launch estimate; SHOULD auto-scale signals; COULD RUM.
ESTIMATE:   5M DAU chain (see §5) → ~1,450 peak QPS → ~5 app nodes + LB + 2 standby.
TRADE-OFFS: AP + eventual consistency for reads; CP for writes to the ledger;
            pull metrics + push alerts.
BUILD:      manage_template for app config; manage_playbook for the rollout;
            manage_change MOP for prod approval; run_fleet_command to verify.
OPERATE:    goldenSignals for saturation; earlyWarningService for "disk full in N days";
            sloService burn-rate alerts; aperfService weekly deep-dive on the busiest node.
```

### 9.4 Decompose a legacy monolith migration
```
FRAME:      a 15-year-old monolith must be de-risked, not big-banged.
DECOMPOSE:  strangle the edges: identity → billing → reporting → core. Each becomes a
            bounded sub-system with an owner and an RTerm operator.
PRIORITIZE: MUST zero-downtime; SHOULD per-module rollback; COULD parallel-run.
ESTIMATE:   per-module cutover windows from uptimeWatchdog + metrics (low-traffic hours).
TRADE-OFFS: strong consistency per cutover (MOP), eventual consistency for reporting.
BUILD:      per-module MOP changes (plan → approve → run → rollback-on-fail);
            driftDetector to catch template-vs-live divergence.
OPERATE:    incidentLedger per cutover with RCA + postmortem; auditLedger for the
            whole migration; reviewService checks each agent-proposed step.
```

---

## 10. The scripts & examples

The `scripts/` and `examples/` folders contain runnable programs that put this playbook to
work over the RTerm gateway (`ws://127.0.0.1:17888`):

- `scripts/systems-thinking.mjs` — the 7-step loop as a CLI: `frame`, `decompose`,
  `estimate`, `tradeoff`, `build`, `operate` subcommands that drive the agent with the
  right prompts and collect the structured results.
- `examples/capacity-estimator.mjs` — DAU → QPS → storage → bandwidth → nodes, then
  validates the estimate with a live APerf deep-dive on a target host.
- `examples/decompose-system.mjs` — turns an ambiguous system description into a bounded
  sub-system map with owners + RTerm operators, and saves it to memory.
- `examples/observability-rollout.mjs` — stands up the full SRE pillar on a fleet
  (metrics, watchdogs, SLO, alerts, dashboard) with MOP approval.
- `examples/tradeoff-check.mjs` — evaluates a design against CAP/PACELC/push-pull/sync-async
  and checks the real behavior against SpanLedger/metrics data.

---

## 11. Quick reference — which RTerm feature for which thinking step

| Thinking step | RTerm feature |
|---|---|
| Frame the problem | agent chat, `sop-assistant` (sop_search/get), `memory.md` |
| Decompose into sub-systems | agent reasoning, plugin system, `manage_device_memory` |
| Prioritize (MoSCoW) | `request-router`, `sloService`, `manage_scheduled_task` |
| Estimate capacity | agent math, `aperfService`, `metricsLedger`, `goldenSignals`, `earlyWarningService` |
| Trade-offs (CAP/PACELC/etc.) | agent reasoning, `manage_change` (CP) vs metrics/dashboard (AP), AGT policy engine |
| Build | `manage_template`, `manage_playbook`, `manage_change`, `run_fleet_command`, `collect_facts`, plugins |
| Operate | `ResourceMonitorService`, `goldenSignals`, `uptimeWatchdog`, `sloService`, `alertService`, `incidentLedger`, `anomalyDetector`, `spanLedger`, `rumLedger`, `infraMonitor`, `etwService`, `manage_trigger` |
| Govern | `auditLedger` + `evidenceSealer`, `agtPolicyEngine`, `reviewService` (maker/checker) |

**v2.9.6+ additions to the map:**
- **Operate → notify:** route alerts/pages out via `alerts.channels[]` (Settings → Alerts) + `oncall.pagingChannels[]` (Settings → On-Call) — slack/teams/smtp/telegram/webhook, secrets via vault.
- **Operate → cost:** gate AI spend with `cost.modelPrices` + `cost.budgets` (Settings → AI Cost) — per-model USD attribution + warn/throttle/deny budgets.
- **Operate → hybrid:** fold cloud VMs into the estate view with `cloud.accounts[]` (Settings → Cloud).
- **Build/Operate → durable agents (v2.9.9):** for long-running or crash-prone work, delegate to a **durable AgentSpan/Conductor agent** (Settings → AgentSpan; `agentspan_run/status/approve`) that resumes from the last completed step — a better fit than an interactive ReAct loop when a task must survive restarts (e.g. multi-hour fleet remediation).
- **Operate → record the run (v2.9.11):** `manage_recording` now captures agent-started sessions (start routes through `TerminalService.startRecording`) — record an incident-response or a design-decision walkthrough and replay/export `.cast` as evidence for the postmortem. No asciinema needed.
- **Build/Operate → live triggers (v2.9.12):** triggers created via `manage_trigger` fire immediately (no restart) — reactive automation lands the moment you define it.
- **Operate → quiet updater (v2.9.13):** the background version check is now silent (raw URL, no 403, transient failures stay quiet) and shows rterm.app — one less false-alarm in an ops channel.
- **Build/Operate → self-discovery (v3.0.0):** the gateway describes itself via `gateway:describe` / `list_gateway_methods` — enumerate capabilities live when designing/operating instead of a static doc.
- **Operate → browser dashboard (v3.0.2):** the unified dashboard (fleet health, SLOs, incidents, APM/DEM, k8s, capacity) is served at `http://<host>:17888/dashboard` with live WS-push updates — share a live ops view with the team, no client install.
- **Research → web intelligence (v3.0.9):** the `web-intel` plugin (wigolo) gives the agent first-class web tools — search, fetch, crawl, research (synthesis by RTerm agent, no LLM key), and page-watch → trigger. Use for current-doc-grounded RCA ("search for this Cisco error + release notes, correlate with what you see on cisco-xe-1"), CVE/vendor-advisory watching (page-change → playbook/MOP), and durable research. Lean by default; ~1.5 GB browser engine + models are opt-in.

---

## Supporting files

- `scripts/systems-thinking.mjs` — the 7-step loop as a CLI over the gateway.
- `examples/capacity-estimator.mjs` — DAU → QPS → storage → bandwidth → nodes + APerf validation.
- `examples/decompose-system.mjs` — ambiguous blob → bounded sub-system map.
- `examples/observability-rollout.mjs` — stand up the SRE pillar on a fleet.
- `examples/tradeoff-check.mjs` — CAP/PACELC/push-pull/sync-async evaluation + real-data check.
