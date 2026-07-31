#!/usr/bin/env node
/**
 * Example: drive the observability stack over the rterm-gateway — unified dashboard,
 * SLO evaluation, predictive anomaly/early-warning, and an embedded eval run.
 *
 * Run:  node observability-demo.mjs [ws://127.0.0.1:17888]
 */
import { createRequire } from 'node:module'
import process from 'node:process'
const require = createRequire(import.meta.url)
const WS = (() => { for (const c of ['ws', '/Users/olu/work/RTerm/node_modules/ws']) { try { return require(c) } catch {} } throw new Error('need ws (npm i ws)') })()

const URL = process.argv[2] || process.env.RTERM_GW_URL || 'ws://127.0.0.1:17888'
const ws = new WS(URL)
let seq = 0; const pending = new Map()
const rpc = (method, params = {}, t = 120000) => new Promise((res, rej) => {
  const id = `c${++seq}`; const timer = setTimeout(() => rej(new Error('timeout ' + method)), t)
  pending.set(id, { res, rej, timer }); ws.send(JSON.stringify({ id, method, params }))
})
ws.on('message', (raw) => { const m = JSON.parse(raw.toString())
  if (m.id && pending.has(m.id)) { const p = pending.get(m.id); clearTimeout(p.timer); pending.delete(m.id)
    const err = m.error || (m.ok === false ? m.error : null)
    err ? p.rej(new Error(err.message || 'error')) : p.res(m.result !== undefined ? m.result : m) } })

async function ask(sessionId, title, prompt) {
  await rpc('agent:startTask', { sessionId, userInput: prompt })
  const ui = await rpc('agent:getUiMessages', { sessionId }).catch(() => ({}))
  const last = [...(ui.messages || [])].reverse().find((m) => (m.role || '') === 'assistant')
  console.log(`\n=== ${title} ===\n${last ? (last.text || last.content || '') : '(dispatched)'}`)
}

ws.on('open', async () => {
  try {
    const { sessionId } = await rpc('gateway:createSession')
    console.log('Driving observability via the agent...\n')
    await ask(sessionId, 'Unified Dashboard',
      'Build the dashboard:state — report fleet health (golden signals), SLO SLI/burn rate, uptime up/degraded/down, open incidents, APM bottleneck services, DEM slowest pages, k8s clusters, and capacity forecast. Be concise.')
    await ask(sessionId, 'Predictive Early Warning',
      'Detect anomalies in cpuUsagePercent and diskUsagePercentMax for all hosts, and report any forecast breaches (disk > 95%) within 7 days via the early-warning service.')
    await ask(sessionId, 'Embedded Eval',
      'Run the embedded eval harness on a small golden set (2 accuracy + 1 tool-selection + 1 safety case) and report the accuracy/tool/safety percentages and any failures.')
    process.exit(0)
  } catch (e) { console.error('error:', e.message); process.exit(2) }
})
ws.on('error', (e) => { console.error('connect:', e.message); process.exit(4) })
