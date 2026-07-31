#!/usr/bin/env node
/**
 * Example: CI/CD post-deploy health gate.
 *
 * A pipeline finishes a deploy, then calls the rterm-backend gateway to run the
 * post-deploy health check across the web fleet. The build passes/fails on
 * whether every node reports healthy.
 *
 * Run:  node fleet-health-gate.mjs [ws://127.0.0.1:17888]
 * Requires: `npm i ws` (or run from a dir that has it), and a running rterm-backend
 * with a "prod-web" connection group configured.
 */
import process from 'node:process'
import { createRequire } from 'node:module'
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
      'Run the post-deploy health check on every node in the "prod-web" connection group: ' +
      'curl the /health endpoint and confirm HTTP 200 with body containing "ok". ' +
      'Report a one-line-per-node summary (node: HEALTHY/UNHEALTHY) and a final verdict line "ALL HEALTHY" or "DEGRADED".' }, 180000)
    const ui = await rpc('agent:getUiMessages', { sessionId })
    const text = (ui.messages || []).map((m) => (m.text || m.content || '')).join('\n')
    console.log(text)
    const degraded = /DEGRADED/i.test(text)
    console.log(`\nCI verdict: ${degraded ? 'FAIL — fleet degraded' : 'PASS — fleet healthy'}`)
    process.exit(degraded ? 1 : 0)
  } catch (e) { console.error('error:', e.message); process.exit(2) }
})
ws.on('error', (e) => { console.error('connect:', e.message); process.exit(4) })
