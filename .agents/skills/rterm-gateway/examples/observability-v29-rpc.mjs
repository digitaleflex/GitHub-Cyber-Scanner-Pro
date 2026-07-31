#!/usr/bin/env node
/**
 * Example: drive the 9 v2.9.x observability capabilities DIRECTLY over the
 * gateway via the observability:* RPC methods (no agent round-trip) — secrets,
 * on-call paging, AI cost budgets, session recording, GitOps, playbook lint,
 * cloud inventory, metrics/Prometheus, and the live dashboard.
 *
 * Run:  RTERM_SECRETS_MASTER_KEY=pw node observability-v29-rpc.mjs [ws://127.0.0.1:17888]
 */
import { createRequire } from 'node:module'
import process from 'node:process'
const require = createRequire(import.meta.url)
const WS = (() => { for (const c of ['ws', '/Users/olu/work/RTerm/node_modules/ws']) { try { return require(c) } catch {} } throw new Error('need ws (npm i ws)') })()

const URL = process.argv[2] || process.env.RTERM_GW_URL || 'ws://127.0.0.1:17888'
const ws = new WS(URL)
let seq = 0; const pending = new Map()
const rpc = (method, params = {}, t = 30000) => new Promise((res, rej) => {
  const id = `c${++seq}`; const timer = setTimeout(() => rej(new Error('timeout ' + method)), t)
  pending.set(id, { res, rej, timer }); ws.send(JSON.stringify({ id, method, params }))
})
ws.on('message', (raw) => { const m = JSON.parse(raw.toString())
  if (m.id && pending.has(m.id)) { const p = pending.get(m.id); clearTimeout(p.timer); pending.delete(m.id)
    const err = m.error || (m.ok === false ? m.error : null)
    err ? p.rej(new Error(err.message || 'error')) : p.res(m.result !== undefined ? m.result : m) } })

const show = (k, v) => console.log(`\n=== ${k} ===\n${typeof v === 'string' ? v : JSON.stringify(v, null, 2)}`)

ws.on('open', async () => {
  try {
    // Metrics / dashboard
    show('dashboardSummary', await rpc('observability:dashboardSummary'))
    show('liveDashboardSubscriberCount', await rpc('observability:liveDashboardSubscriberCount'))

    // Secrets (metadata only — value never returned)
    await rpc('observability:secretsSet', { key: 'demo-token', value: 's3cr3t', labels: { service: 'demo' } })
    show('secretsList (no values)', await rpc('observability:secretsList', {}))
    show('secretsHas', await rpc('observability:secretsHas', { key: 'demo-token' }))
    await rpc('observability:secretsDelete', { key: 'demo-token' })

    // On-call: register a policy, raise a page, ack it
    await rpc('observability:oncallRegisterPolicy', {
      id: 'demo-pol', name: 'Demo on-call',
      levels: [{ targets: [{ id: '@oncall', channel: 'slack' }], ackTimeoutMs: 60000 }],
    })
    const page = await rpc('observability:oncallPage', { incidentId: 'inc-1', policyId: 'demo-pol', title: 'DB down', severity: 'sev2' })
    show('oncallOpenPages', await rpc('observability:oncallOpenPages'))
    show('oncallAck', await rpc('observability:oncallAck', { pageId: page.id, by: 'olu' }))
    show('oncallResolve', await rpc('observability:oncallResolve', { pageId: page.id }))

    // AI cost: record spend, summarize, check a budget
    await rpc('observability:costRecord', { model: 'gpt-4o', promptTokens: 500000, completionTokens: 100000 })
    show('costSummary (daily)', await rpc('observability:costSummary', { period: 'daily' }))
    show('costCheck', await rpc('observability:costCheck', { model: 'gpt-4o' }))

    // Playbook lint
    show('playbookLint (clean)', await rpc('observability:playbookLint', { def: { name: 'x', steps: [{ kind: 'command', command: 'ls' }] } }))
    show('playbookLint (undefined param)', await rpc('observability:playbookLint', { def: { name: 'x', steps: [{ kind: 'command', command: 'echo {{param.region}}' }] } }))

    // GitOps export + drift
    const manifest = await rpc('observability:gitopsExport')
    show('gitopsExport (hash)', { stateHash: manifest.stateHash, entities: manifest.entities.length })
    show('gitopsInSync', await rpc('observability:gitopsInSync', { manifest }))

    // Session recording
    const { recordingId } = await rpc('observability:recordingStart', { terminalId: 'local-main', title: 'demo' })
    await rpc('observability:recordingStop', { recordingId })
    show('recordingList', await rpc('observability:recordingList'))
    const cast = await rpc('observability:recordingExportCast', { recordingId })
    show('recordingExportCast (first line)', cast.split('\n')[0])
    await rpc('observability:recordingDelete', { recordingId })

    // Cloud inventory (no fetchers injected on a stock backend → summary is empty)
    show('cloudSummary', await rpc('observability:cloudSummary'))

    // Prometheus exposition text for a scraper
    const prom = await rpc('observability:metricsPrometheus')
    show('metricsPrometheus (first 200 chars)', String(prom).slice(0, 200) || '# (no host metrics yet)')

    process.exit(0)
  } catch (e) { console.error('error:', e.message); process.exit(2) }
})
ws.on('error', (e) => { console.error('connect:', e.message); process.exit(4) })
