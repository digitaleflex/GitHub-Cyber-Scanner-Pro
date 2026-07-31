---
name: rterm-discovery
description: Agentless asset discovery and CMDB on RTerm — discover Windows (WinRM/PowerShell), Linux/UNIX (SSH), network devices (SSH/SNMP), VMware vCenter/ESXi, and databases (MS SQL/Oracle/MySQL/Sybase), consolidate zone results outbound-only via the WebSocket gateway or NATS mesh, and maintain a versioned, diffable, queryable inventory. Covers the full BMC Helix Discovery (ADDM) protocol matrix using RTerm's backends, playbooks, and inventory ledger. Use when an agent needs to collect infrastructure inventory, build/maintain a CMDB, run discovery scans, or reconcile assets.
---

# RTerm Discovery & CMDB Skill

Build an **agentless asset discovery + CMDB** on RTerm — covering the entire BMC
Helix Discovery (ADDM) protocol matrix using only RTerm's existing primitives:
SSH/WinRM/Serial/local backends, playbooks, the WebSocket gateway, the NATS
event mesh, and a versioned **inventory ledger** (the CMDB). No agents on
targets, no external CMDB product.

This skill gives an agent everything to **implement and operate** discovery:
per-protocol collector playbooks, the CMDB schema, consolidation, scheduling,
reconciliation, security, and ready-made scripts/examples.

---

## 1. The model (mental picture)

```
  [Zone A]                 [Zone B]                  [Central hub]
 rterm-backend            rterm-backend              rterm-backend
  collectors ──┐            collectors ──┐            inventoryLedger (CMDB)
               └─ inventory:upsert ──────┴──────►     assets/snapshots/links
                (WS gateway or NATS mesh, outbound-only)
  every change → inventory:update event (broadcast + NATS) → dashboards/agents
```

- **Collector** = a playbook that runs per-host and emits one normalized asset JSON → `inventory:upsert`.
- **CMDB** = the `inventoryLedger` (SQLite): every asset's latest snapshot + full history + relationships.
- **Outpost** = a zone's rterm-backend daemon that scans locally and ships results outbound-only (ADDM Outpost→Appliance pattern).
- **Reconcile** = mark stale/missing, dedupe by hash, AI identity merge.

---

## 2. Protocol → RTerm channel (the ADDM matrix, covered)

| ADDM protocol (port) | Purpose | RTerm channel |
|---|---|---|
| SSH (22) | UNIX/Linux discovery, appliance CLI | `SSHBackend` |
| PowerShell HTTP/HTTPS (5985/5986) | Windows discovery (agentless) | `WinRMBackend` |
| SNMP (161) | network device discovery | `snmp` query step (read-only) |
| WBEM (5988/5989) | WBEM/CIM discovery | `Get-CimInstance` over WinRM |
| DCOM (135, 49152–65535) | Windows discovery | WinRM (WS-Man supersedes DCOM) |
| vCenter (443) | vCenter discovery | HTTPS API step (govc/PowerCLI/curl) |
| VMware ESX/ESXi (902) | hypervisor discovery | `SSHBackend` / HTTPS API step |
| MS SQL (1433) | MS SQL extended discovery | `sqlcmd`/`Invoke-Sqlcmd` step |
| Oracle SQL (1521) | Oracle extended discovery | `sqlplus` step |
| MySQL (3306) | MySQL extended discovery | `mysql` client step |
| Sybase ASE (4100) | Sybase extended discovery | `isql` step |
| Mainframe (3940) | mainframe discovery | `SSHBackend` / TN3270 (manual) |
| DNS (53), NTP (123), SMTP (25) | base detection / reachability | `probe_connectivity` step |
| HTTPS UI (443) | appliance ↔ outpost (consolidation) | WebSocket gateway + NATS mesh |
| AD/Credential Windows proxy (4321/4323) | Windows discovery proxy | rterm-backend zone outpost |

**Base Device Detection** (ports 4, 21, 22, 23, 25, 53, 80, 123, 135, 139, 161,
443, 445…) = the reachability + port-probe sweep that classifies a host before
deep collection (`probe_connectivity` + port scan).

---

## 3. The CMDB (inventory ledger)

Three SQLite tables (append-mostly, same pattern as `changeLedger`/`agentRunLedger`):

**assets** — one row per CI:
```jsonc
{ "id": "ast-<uuid>", "key": "host:web-01", "type": "windows|linux|netdevice|esx|vcenter|db",
  "name": "web-01", "fqdn": "...", "mgmtIp": "...", "status": "active|stale|missing",
  "firstSeen": "...", "lastSeen": "...", "attributes": { ... }, "source": "winrm|ssh|snmp|vcenter|manual" }
```

**snapshots** — versioned attribute history (dedupe identical re-scans by hash):
```jsonc
{ "id": "...", "assetId": "...", "capturedAt": "...",
  "attrs": { "os": "...", "version": "...", "cpu": "...", "memGb": 16,
             "disks": [], "nics": [], "services": [], "listeningPorts": [],
             "packages": [], "hypervisor": "...", "vms": [], "dbInstances": [] },
  "hash": "sha256(attrs)" }
```

**links** — relationships (blast radius / dependency view):
```jsonc
{ "id": "...", "fromAssetId": "...", "toAssetId": "...",
  "rel": "runs-on|hosts|contains|connects-to|depends-on|instance-of", "evidence": "...", "capturedAt": "..." }
```

**RPC surface (`inventory:*`):**
| Method | Purpose |
|---|---|
| `inventory:upsert` | collector writes/merges asset + snapshot (dedupe by hash) |
| `inventory:list` | list assets (filter type/status/scope/query) |
| `inventory:get` | one asset: latest attrs + snapshots + links |
| `inventory:diff` | attribute diff between two snapshots (or vs. last N) |
| `inventory:query` | structured search (`os='Windows Server 2022' AND disk<20%free`) |
| `inventory:links` | relationship graph for an asset |
| `inventory:markMissing` | mark assets unseen in N scans as stale/missing |

Every upsert that changes an asset's hash broadcasts **`inventory:update`** on the gateway + NATS mesh — live change feed for dashboards/agents, and a NATS trigger can fire a remediation playbook on a specific change (e.g. a new listener on a prod host).

---

## 4. Collectors (per protocol)

Collectors live in `collectors/` and are invoked from playbooks in `playbooks/`.
Each emits one normalized JSON doc.

- **`collectors/windows.ps1`** — agentless WinRM/PowerShell collector (OS, CPU, mem, disks, NICs, listening ports, services, installed software).
- **`collectors/linux.sh`** — SSH collector (os-release, cpu, mem, df, ip, ss, systemd, packages).
- **`collectors/network-device.sh`** — Cisco/IOS-XE/XR collector (`show version/inventory/interfaces/cdp/lldp`) + SNMP fallback.
- **`collectors/vcenter.sh`** — vCenter API (govc) + ESXi SSH (`vim-cmd`) collector; builds VM→ESX→datastore links.
- **`collectors/databases.sh`** — MS SQL / Oracle / MySQL / Sybase extended collectors; builds DB→server links.
- **`collectors/base-detect.sh`** — reachability + port-probe sweep that classifies a host.

**Normalization:** every collector writes the same asset shape (§3) to stdout as JSON. A playbook step pipes it to `inventory:upsert`.

---

## 5. Playbooks (ready to run)

`playbooks/` contains ready RTerm playbooks (YAML) that wire collectors to the CMDB:

- **`playbooks/discover-windows.yaml`** — WinRM collector across a `win-fleet` group.
- **`playbooks/discover-linux.yaml`** — SSH collector across a `linux-fleet` group.
- **`playbooks/discover-network.yaml`** — network-device collector across a `core-net` group (cisco preset + vt100).
- **`playbooks/discover-virtualization.yaml`** — vCenter/ESXi + links.
- **`playbooks/discover-databases.yaml`** — SQL extended + links.
- **`playbooks/reconcile.yaml`** — stale/missing marking + dedupe.

Run one:

```bash
run_playbook name="Discover Windows Fleet"
# or via the agent:
#   "run the Discover Windows Fleet playbook on group win-fleet"
```

---

## 6. Consolidation (outbound-only, ADDM Outpost pattern)

Each zone runs an **rterm-backend daemon as an Outpost** (discovers its local
scope) and ships results to the central hub over the **WebSocket gateway**
(outbound 17888) or the **NATS mesh** (outbound 4222) — never inbound.

```
zone outpost → (gateway / NATS) → hub inventoryLedger
```

For scale, the NATS mesh is the consolidation bus: Outposts publish
`inventory.upsert` events; the hub consumes them; `inventory:update` events flow
back for fleet-wide reactions.

---

## 7. Scheduling, freshness & reconciliation

| Scan | Cadence | Covers |
|---|---|---|
| Base detection sweep | hourly | reachability, new/unknown hosts, port changes |
| Deep collection | daily (off-peak) | full attribute set per asset |
| Virtualization + DB | daily | vCenter, ESXi, DB instances + links |
| Reconciliation | after each sweep | stale/missing marking, dedupe, link refresh |

**Stale/missing:** an asset unseen in N scans (default 3) → `active → stale → missing`. A watchdog trigger can alert or auto-open a MOP change.

**AI reconciliation:** the agent merges duplicate assets (same host via two protocols), resolves FQDN/short-name/IP conflicts, proposes link corrections — recorded in the run ledger.

---

## 8. Security & credentials

- **Vaulted credentials** (scrt / runbook secret params) — masked in every record/log; never plaintext in playbooks.
- **Least privilege** — read-only service account for Windows, read-only SNMP community, read-only vCenter/DB accounts.
- **Read-only collection** — collectors never write to targets (command-policy allowlist enforces exact read commands).
- **Transport security** — WinRM HTTPS 5986 in prod; gateway + NATS over TLS with token auth + CIDR allow-list.
- **Full audit** — every scan, upsert, and reconciliation in the run/change ledgers.

---

## 9. Operation (day-2)

- **Query the CMDB** — `inventory:list/query/get/links` over the gateway, or ask the agent ("list all WS2016 hosts <15% free disk").
- **What changed** — `inventory:diff` for a host or a time window.
- **React to changes** — a NATS trigger on `inventory:update` fires a playbook (e.g. alert on a new prod listener).
- **Consumers** — AI agent (NL queries, RCA, reconciliation), WebSocket clients (dashboards), optional thin REST layer, reactive playbooks/triggers.

### v2.9.x notes for discovery

- **Cloud-inventory correlation (v2.9.6):** the `cloud.accounts[]` settings block (Settings → Cloud) lets CloudInventory sync AWS/GCP/Azure instance lists into the same view as your discovered on-prem inventory — per-account region + credential `secretRef` (vault). Useful for hybrid CMDB reconciliation.
- **Alerting on discovery changes (v2.9.6):** route "new listener / drift detected" pages via the `alerts.channels[]` (Settings → Alerts) and `oncall.pagingChannels[]` (Settings → On-Call) blocks — slack/teams/smtp/telegram/webhook, secrets via vault `secretRef`.
- **Durable remediation (v2.9.9):** a discovery-driven trigger can now start a **durable AgentSpan/Conductor agent** (`agentspan_run`) that survives restarts while it remediates or re-scans — see Settings → AgentSpan and the `agentspan` skill.
- **Recording (v2.9.11):** `manage_recording` now actually captures (start routes through `TerminalService.startRecording`) — record a discovery scan or CMDB reconcile and replay/export it for the incident record. No asciinema needed.
- **Live triggers (v2.9.12):** triggers created via `manage_trigger` fire **without a backend restart** (they're upserted into the live TriggerEngine). Discovery-change triggers now react immediately.
- **Updater hygiene (v2.9.13):** the background version check no longer 403s (raw URL, silent on transient failures) and shows rterm.app (no GitHub) — cosmetic but keeps headless deployments quiet.
- **Self-discovery (v3.0.0):** call `gateway:describe` (or `list_gateway_methods`) to enumerate the live RPC/tool surface for discovery tooling instead of a static reference.
- **Browser dashboard (v3.0.2):** the unified dashboard (discovered fleet health, SLOs, incidents, APM/DEM, k8s) is now visible at `http://<host>:17888/dashboard` — served on the gateway port with live WS-push updates.
- **Web intelligence (v3.0.9):** the `web-intel` plugin (wigolo) gives the agent first-class web tools — multi-engine search, clean-page fetch, site crawl, research (synthesis by RTerm agent, no LLM key), and page-watch → `webintel_page_changed` trigger for auto-remediation. Lean by default; ~1.5 GB browser engine + models are opt-in. Discovered automatically from `plugins/web-intel/`.

---

## 10. Scripts & examples

**`scripts/rterm-discovery.mjs`** — zero-dep orchestration CLI (drives the gateway):
```bash
node scripts/rterm-discovery.mjs scan --group win-fleet --protocol windows
node scripts/rterm-discovery.mjs scan --group core-net --protocol network
node scripts/rterm-discovery.mjs inventory-list [--type windows]
node scripts/rterm-discovery.mjs inventory-get --host web-01
node scripts/rterm-discovery.mjs inventory-diff --host web-01 [--last 2]
node scripts/rterm-discovery.mjs reconcile
```

**`examples/` (runnable):**
- `examples/discover-fleet.mjs` — run all collectors across groups and print a summary.
- `examples/what-changed.mjs` — diff a host's last two snapshots.
- `examples/blast-radius.mjs` — walk an asset's link graph.
- `examples/outpost-ship.mjs` — a zone outpost shipping results to the central hub.

---

## Supporting files

- `scripts/rterm-discovery.mjs` — zero-dep orchestration CLI (scan/inventory/reconcile over the gateway).
- `collectors/` — per-protocol collectors (windows.ps1, linux.sh, network-device.sh, vcenter.sh, databases.sh, base-detect.sh).
- `playbooks/` — ready RTerm playbooks wiring collectors → CMDB (windows, linux, network, virtualization, databases, reconcile).
- `examples/` — discover-fleet, what-changed, blast-radius, outpost-ship.
