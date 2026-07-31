#!/usr/bin/env node
/**
 * Example: run a dagu YAML workflow on rterm-backend (no dagu server needed).
 *
 * Compiles a dagu workflow into an RTerm playbook and runs it across the target
 * hosts via the orchestrated DAG runner — fan-out/fan-in, validation, rollback.
 *
 * Run:  node dagu-workflow.mjs [ws://127.0.0.1:17888]
 */
import { createRequire } from 'node:module'
import process from 'node:process'
const require = createRequire(import.meta.url)
const WS = (() => { for (const c of ['ws', '/Users/olu/work/RTerm/node_modules/ws']) { try { return require(c) } catch {} } throw new Error('need ws (npm i ws)') })()

const URL = process.argv[2] || process.env.RTERM_GW_URL || 'ws://127.0.0.1:17888'
const ws = new WS(URL)
let seq = 0; const pending = new Map()
const rpc = (method, params = {}, t = 180000) => new Promise((res, rej) => {
  const id = `c${++seq}`; const timer = setTimeout(() => rej(new Error('timeout ' + method)), t)
  pending.set(id, { res, rej, timer }); ws.send(JSON.stringify({ id, method, params }))
})
ws.on('message', (raw) => { const m = JSON.parse(raw.toString())
  if (m.id && pending.has(m.id)) { const p = pending.get(m.id); clearTimeout(p.timer); pending.delete(m.id)
    const err = m.error || (m.ok === false ? m.error : null)
    err ? p.rej(new Error(err.message || 'error')) : p.res(m.result !== undefined ? m.result : m) } })

// A real dagu workflow: extract (parallel) -> transform -> load, with a health check.
const DAGU_YAML = `
name: friday-data-pipeline
description: extract -> transform -> load across hosts, dagu-style
steps:
  - id: extract_a
    run: echo "extracting from source A"
  - id: extract_b
    run: echo "extracting from source B"
  - id: transform
    run: echo "transforming combined data"
    depends:
      - extract_a
      - extract_b
  - id: load
    run: echo "loading into warehouse"
    depends: transform
  - id: verify
    run: echo "verifying row counts"
    depends: load
`

ws.on('open', async () => {
  try {
    const { sessionId } = await rpc('gateway:createSession')
    console.log('Compiling + running a dagu workflow on rterm-backend...\n')
    console.log('--- dagu YAML ---')
    console.log(DAGU_YAML)
    await rpc('agent:startTask', { sessionId, userInput:
      `Compile this dagu YAML workflow into a playbook using the daguParser (parseDaguYaml), ` +
      `show the execution plan (the DAG waves via daguExecutionPlan), then run it and report the per-step results:\n\n${DAGU_YAML}` })
    const ui = await rpc('agent:getUiMessages', { sessionId }).catch(() => ({}))
    const last = [...(ui.messages || [])].reverse().find((m) => (m.role || '') === 'assistant')
    console.log('--- execution ---')
    console.log(last ? (last.text || last.content || '') : '(dispatched)')
    process.exit(0)
  } catch (e) { console.error('error:', e.message); process.exit(2) }
})
ws.on('error', (e) => { console.error('connect:', e.message); process.exit(4) })
