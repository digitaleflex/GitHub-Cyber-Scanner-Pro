---
name: rterm-plugin
description: Develop, test, and deploy custom RTerm plugins — drop a folder into plugins/ with a plugin.json manifest + a register(ctx) entry module, and RTerm auto-integrates it (agent tools, event-driven triggers, dashboard panels). Use when an agent needs to create a new plugin, scaffold a plugin template, test plugin loading, or deploy a plugin to an rterm-backend instance. Includes the manifest schema, PluginContext API, templates, and ready-made examples.
---

# RTerm Plugin Development Skill

Build custom plugins that **auto-integrate with RTerm**. You write a folder with a
`plugin.json` manifest + a small code file, drop it into `plugins/`, and RTerm
discovers it, loads it, calls its `register(ctx)` with RTerm's services, and your
capabilities appear automatically — **agent tools, event-driven triggers, and
dashboard panels** — with **no RTerm code changes**.

This skill gives an agent everything to **create, test, and deploy** plugins: the
manifest schema, the PluginContext API, ready-to-copy templates, a scaffold
command, a local test runner, and complete working examples.

---

## 1. The model (mental picture)

```
plugins/
  my-plugin/
    plugin.json   ──►  RTerm PluginRegistry discovers it
    index.ts      ──►  loads index.ts, calls register(ctx) ──►  your capabilities
                         (agent tools, triggers, panels) appear in RTerm
```

- **Discover** — RTerm scans `plugins/` (and `<dataDir>/plugins`) on boot/reload.
- **Load** — reads `plugin.json`, then dynamic-imports your entry module.
- **Register** — calls `register(ctx)`; your `registerTool`/`registerTrigger`/`registerPanel` calls are captured.
- **Integrate** — your tools become agent tools, your triggers join the TriggerEngine, your panels render in the dashboard.

---

## 2. The manifest (`plugin.json`)

```jsonc
{
  "name": "my-plugin",               // required — unique name
  "version": "1.0.0",                // required — semver
  "description": "what it does",      // optional
  "author": "you",                    // optional
  "entry": "index.ts",                // optional — entry module (default: index.js|index.ts|index.mjs)
  "tools": ["my_tool"],               // optional — declared agent tools
  "triggers": [{ "name": "my-trigger", "kind": "pattern", "match": "ERROR" }],  // optional
  "panels": ["my-panel"],             // optional — declared dashboard panels
  "permissions": ["exec_command", "read_ledger"]  // optional — requested permissions
}
```

`name` + `version` are **required**. Everything else is optional. The registry
validates it and records an error (without crashing other plugins) when a plugin
is invalid.

---

## 3. The PluginContext API (what `register(ctx)` gets)

Your entry module exports a `register(ctx)` function. RTerm calls it with a
`PluginContext`:

| Method | What it does |
|---|---|
| `ctx.registerTool(tool)` | Register an **agent tool** the agent can call: `{ name, description, handler(args) => result }`. |
| `ctx.registerTrigger(trigger)` | Register an **event-driven trigger**: `{ name, kind: 'pattern'\|'threshold'\|'webhook'\|'schedule', match?, metric?, op?, value?, action }`. |
| `ctx.registerPanel(name, render)` | Register a **dashboard panel**: `render()` returns HTML. |
| `ctx.exec(command, opts?)` | Run a command on a host (the agent's policy-gated exec path). `opts.host` selects the target. |
| `ctx.readLedger(name, query?)` | Read RTerm's ledgers (`'metrics'`, `'incidents'`, …). |
| `ctx.log(line)` | Write a line to the RTerm log. |

A plugin may also export `unregister()` for teardown on disable/uninstall.

---

## 4. A minimal plugin (copy this)

**`plugins/hello/plugin.json`**
```json
{
  "name": "hello",
  "version": "1.0.0",
  "description": "A hello-world plugin",
  "tools": ["hello_greet"],
  "permissions": []
}
```

**`plugins/hello/index.ts`**
```ts
export function register(ctx) {
  ctx.log('[hello] registering')
  ctx.registerTool({
    name: 'hello_greet',
    description: 'Greet someone by name.',
    handler: async (args) => ({ greeting: `Hello, ${args.name ?? 'world'}! (from the hello plugin)` }),
  })
}
```

Drop it in `plugins/` and RTerm auto-integrates it — the agent can now call
`hello_greet` ("greet olu") and get back `{"greeting":"Hello, olu! (from the hello plugin)"}`.

---

## 5. A full plugin (tools + trigger + panel)

See `examples/host-health-plugin/` — a complete working plugin that registers an
agent tool (evaluate host health from the metrics ledger), a CPU-threshold trigger,
and a dashboard panel. Copy it as your starting point.

---

## 6. Scaffold a new plugin (one command)

```bash
node scripts/scaffold-plugin.mjs --name my-plugin --out ./plugins
# -> creates ./plugins/my-plugin/{plugin.json,index.ts} ready to edit
```

Or copy `templates/plugin-template/` manually.

---

## 7. Test your plugin locally (before deploying)

The skill ships a **test runner** that loads your plugin through the real
`PluginRegistry` (the same code RTerm uses) and prints what it registered:

```bash
node scripts/test-plugin.mjs --dir ./plugins/hello
# -> discovered: hello@1.0.0 | tools: hello_greet | triggers: 0 | panels: 0
# -> calls hello_greet to prove it executes
```

This runs the exact `pluginRegistry.ts` from RTerm, so a pass here = it loads in RTerm.

---

## 8. Deploy to an rterm-backend instance

1. **Copy the plugin folder** into the backend's `plugins/` dir (or `<GYBACKEND_DATA_DIR>/plugins/`):
   ```bash
   scp -r plugins/hello user@backend:/opt/rterm-backend/plugins/
   ```
2. **Reload** — the backend discovers new plugins on boot; to hot-reload, restart or call the reload path (the registry reloads on `reload()`).
3. **Verify** — ask the agent: "list the loaded plugins" or "call hello_greet with name=olu".

The sample plugin `plugins/sample-k8s-slo` (shipped in RTerm) is a reference deployment.

---

## 9. The plugin lifecycle (manage it)

- **Enable/disable** — `pluginRegistry.setEnabled(name, enabled)` gates a plugin's capabilities without uninstalling it.
- **Uninstall** — `pluginRegistry.uninstall(name)` drops it and its capabilities.
- **Error handling** — a plugin that fails to load records an `error` on its record, is excluded from `allTools`/`allTriggers`/`allPanels`, but stays in the registry for diagnosis.
- **Dedupe** — reloading the same `name` replaces the previous record (new id).
- **Hot reload** — `pluginRegistry.reload()` re-discovers everything in the scan roots.

---

## 9b. v3.0.2 — where plugin panels surface + the gateway's HTTP seam

- **Panels on the browser dashboard:** since v3.0.2 the unified dashboard is served live at `http://<host>:17888/dashboard` (same port as the WS gateway) — plugin-registered dashboard panels feed that page's state (via `observability:dashboardState` / `liveDashboardState`), so a `registerPanel` plugin now has a zero-install browser surface.
- **`httpRoutes` (new adapter option):** the WS gateway's default server factory can now host plain-HTTP routes on the same port (`WebSocketGatewayAdapter` `httpRoutes`). That's how `/dashboard` is served. Plugins don't register routes themselves today, but if you ever need a plugin to expose an HTTP endpoint, this is the seam the backend uses — the pattern to follow is one shared `http.Server` + WS upgrade, not a second listener.

## 9c. v3.0.9 — `web-intel` plugin (sidecar daemons + live settings)

The `web-intel` plugin (integrating [wigolo](https://github.com/KnockOutEZ/wigolo)) is a real-world example of a plugin that:
- **Spawns a sidecar daemon** via `ctx.spawnProcess('npx', ['-y', 'wigolo', 'serve', …], {env, detached, stdio})` — the new `PluginContext.spawnProcess` (optional; wired in `observability.ts` via `createRequire('node:child_process')`).
- **Reads live settings** via `ctx.getSettings()` / `ctx.settings` — the new `PluginContext.settings` / `getSettings` (wired from `settingsService.getSettings()`). Reads the `webIntel` block for `{restUrl, token, autoStart, warmupOnInit}`.
- **Registers 9 tools + 1 trigger + 1 panel** — `web_search`, `web_fetch`, `web_crawl`, `web_research`, `web_find_similar`, `web_watch_add/list/remove`, `webintel_health`; trigger `webintel_page_changed`; panel `web-intel`.
- **Degrades gracefully** — if the daemon is down and `spawnProcess` is unavailable, every tool returns `{error, hint}` instead of throwing (the agentspan-bridge pattern).
- **Uses the object-form `registerPanel({name, title, render})`** — now supported alongside the `(name, render)` form (v3.0.9 fixed the pre-existing signature drift).

**Key pattern for sidecar plugins:**
```js
// Lazy start on first use (lean by default)
const sidecar = new WigoloSidecar({ spawnImpl: ctx.spawnProcess, config: { warmup: false } })
async function ensureDaemon() {
  const h = await client.health()
  if (h.ok) return true
  if (!ctx.spawnProcess) throw new Error('daemon not reachable; start it: npx -y wigolo serve')
  await sidecar.start()  // spawns `npx -y wigolo serve` with WIGOLO_NO_WARMUP=1
  // …poll health until ready…
}
```

---

## 10. Real examples in this skill

- **`examples/host-health-plugin/`** — a complete plugin (tool + threshold trigger + panel) you can run today.
- **`examples/host-health-plugin/test.mjs`** — a self-contained test that loads it via the registry and calls its tool.
- **`templates/plugin-template/`** — the minimal scaffold to copy.

### Reference plugin: `agentspan-bridge` (v2.9.9)

A production-grade example of an HTTP-backed plugin in the RTerm repo at `plugins/agentspan-bridge/`. It bridges RTerm to an [AgentSpan (Netflix Conductor)](https://github.com/agentspan-ai/agentspan) durable-agent server and shows the recommended patterns:

- **Split client from glue:** `conductorClient.mjs` is a pure, dependency-free HTTP client with an **injectable `fetchImpl`** (so it's fully unit-testable offline); `index.mjs` wires it to the PluginContext. Mirror this for any API-backed plugin — never hard-code `fetch` so tests can mock it.
- **Settings-driven config:** reads `settings.agentspan.serverUrl` + `agentspan.authSecretRef` (a vault `secretRef` holding `AGENTSPAN_AUTH_KEY`/`AGENTSPAN_AUTH_SECRET`) — never inline secrets. Resolves auth from the vault via `ctx.getSecret`.
- **Resilient by design:** every tool is wrapped so an unreachable server returns `{ error, hint }` instead of throwing — the agent stays usable when the external service is down.
- **6 tools** (`agentspan_health/run/status/approve/list/stop`), **1 trigger** (`agentspan_execution_failed`), **1 panel** (`agentspan-executions`).
- **Tests:** `agentspan-bridge.extreme.spec.ts` (26 tests) covers URL building, auth headers, error mapping, every endpoint, config resolution, and unreachable-server resilience — all offline via the mocked `fetchImpl`.

Copy this structure for any plugin that talks to an external HTTP service.

---

## Supporting files

- `scripts/scaffold-plugin.mjs` — scaffold a new plugin folder (manifest + entry).
- `scripts/test-plugin.mjs` — load a plugin via the real PluginRegistry and report what it registered.
- `templates/plugin-template/` — minimal plugin scaffold (plugin.json + index.ts).
- `examples/host-health-plugin/` — a complete working plugin (tool + trigger + panel) + its test.
