#!/usr/bin/env node
/**
 * tradeoff-check.mjs — evaluates a design against CAP/PACELC/push-pull/sync-async and
 * checks the real behavior against SpanLedger/metrics data where possible.
 *
 * Usage:
 *   node examples/tradeoff-check.mjs "a fraud-decision fan-out to 20 downstream consumers"
 */
import { RTermGW } from '../scripts/lib/gw.mjs'

const design = process.argv.slice(2).join(' ')
if (!design) {
  console.log('usage: tradeoff-check.mjs "<design description>"')
  process.exit(1)
}

const url = process.env.RTERM_GW_URL ?? 'ws://127.0.0.1:17888'
const gw = new RTermGW(url, process.env.RTERM_GW_TOKEN)
await gw.connect()
const sess = await gw.rpc('gateway:createSession')
await gw.rpc('agent:startTask', {
  sessionId: sess.sessionId,
  userInput: `Evaluate this design against the trade-off frameworks, then check the real behavior where possible. (1) CAP: should it be CP, AP, or CA — and why? (2) PACELC: during a partition, A or C? In normal operation, L or C? (3) push-vs-pull: which fits better? (4) sync-vs-async: which fits better? (5) strong-vs-eventual consistency? Then use the SpanLedger APM data and metrics ledger to check whether the real latency/consistency behavior matches the recommendation. Design: ${design}`,
}, 240000)
const ui = await gw.rpc('agent:getUiMessages', { sessionId: sess.sessionId })
console.log((ui.messages ?? []).map((m) => `[${m.role}] ${m.text ?? m.content ?? ''}`).join('\n\n'))
await gw.close()
