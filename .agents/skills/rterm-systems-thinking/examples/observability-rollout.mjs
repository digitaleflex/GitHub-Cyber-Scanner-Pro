#!/usr/bin/env node
/**
 * observability-rollout.mjs — stands up the full SRE pillar on a fleet with MOP approval.
 *
 * Usage:
 *   node examples/observability-rollout.mjs "prod-web"        # the fleet/group to instrument
 */
import { RTermGW } from '../scripts/lib/gw.mjs'

const fleet = process.argv[2] ?? 'all hosts'
const url = process.env.RTERM_GW_URL ?? 'ws://127.0.0.1:17888'
const gw = new RTermGW(url, process.env.RTERM_GW_TOKEN)
await gw.connect()
const sess = await gw.rpc('gateway:createSession')
await gw.rpc('agent:startTask', {
  sessionId: sess.sessionId,
  userInput: `Stand up the full SRE observability pillar for ${fleet}: (1) metrics ledger snapshots from ResourceMonitorService, (2) uptime watchdogs (tcp/ssh probes), (3) a 99.9% uptime SLO with burn-rate alerts, (4) a Slack/Teams notification channel, (5) the unified dashboard:state, (6) anomaly detection + early-warning forecast, and (7) the hash-chained audit ledger. Do it as an approved MOP change (plan → approve → run → status) and report when each piece is live.`,
}, 300000)
const ui = await gw.rpc('agent:getUiMessages', { sessionId: sess.sessionId })
console.log((ui.messages ?? []).map((m) => `[${m.role}] ${m.text ?? m.content ?? ''}`).join('\n\n'))
await gw.close()
