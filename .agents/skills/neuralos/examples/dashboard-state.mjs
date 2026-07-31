#!/usr/bin/env node
/**
 * Example: pull the unified dashboard state from rterm-backend and print a live
 * operational summary (fleet health, SLO, uptime, incidents, APM, DEM, capacity).
 *
 * Run:  node dashboard-state.mjs [ws://127.0.0.1:17888]
 */
import { createRequire } from 'node:module'
import process from 'node:process'
const require = createRequire(import.meta.url)
const WS = (() => { for (const c of ['ws', '/Users/olu/work/RTerm/node_modules/ws']) { try { return require(c) } catch {} } throw new Error('need ws (npm i ws)') })()

const URL = process.argv[2] || process.env.RTERM_GW_URL || 'ws://127.0.0.1:17888'
const ws = new WS(URL)
let seq = 0; const pending = new Map()
const rpc = (method, params = {}, t = 60000) => new Promise((res, rej) => {
  const id = `c${++seq}`; const timer = setTimeout(() => rej(new Error('timeout ' + method)), t)
  pending.set(id, { res, rej, timer }); ws.send(JSON.stringify({ id, method, params }))
})
ws.on('message', (raw) => { const m = JSON.parse(raw.toString())
  if (m.id && pending.has(m.id)) { const p = pending.get(m.id); clearTimeout(p.timer); pending.delete(m.id)
    const err = m.error || (m.ok === false ? m.error : null)
    err ? p.rej(new Error(err.message || 'error')) : p.res(m.result !== undefined ? m.result : m) } })

ws.on('open', async () => {
  try {
    const { sessionId } = await rpc('gateway:createSession')
    await rpc('agent:startTask', { sessionId, userInput:
      'Build the unified dashboard state (dashboard:state) from all observability ledgers and report: ' +
      'hosts with golden-signal health, SLO SLI/burn rate, uptime up/degraded/down, open incidents, ' +
      'APM bottleneck services, DEM slowest pages, k8s clusters, and capacity forecast. Be concise.' }, 120000)
    const ui = await rpc('agent:getUiMessages', { sessionId }).catch(() => ({}))
    const last = [...(ui.messages || [])].reverse().find((m) => (m.role || '') === 'assistant')
    console.log('=== Unified Dashboard State ===\n')
    console.log(last ? (last.text || last.content || '') : '(no dashboard state yet — feed monitor snapshots first)')
    process.exit(0)
  } catch (e) { console.error('error:', e.message); process.exit(2) }
})
ws.on('error', (e) => { console.error('connect:', e.message); process.exit(4) })
