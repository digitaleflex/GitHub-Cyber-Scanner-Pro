#!/usr/bin/env node
/**
 * capacity-estimator.mjs — DAU → QPS → storage → bandwidth → nodes, with optional
 * APerf validation against a real host. Pure math (no gateway needed for the estimate);
 * pass a host as the 3rd arg to validate against live APerf telemetry via the gateway.
 *
 * Usage:
 *   node examples/capacity-estimator.mjs 5000000 10            # estimate only
 *   node examples/capacity-estimator.mjs 5000000 10 web-01     # estimate + APerf check on web-01
 */
import { RTermGW } from '../scripts/lib/gw.mjs'

const dau = Number(process.argv[2])
const rpu = process.argv[3] ? Number(process.argv[3]) : 10
const host = process.argv[4]

if (!dau || Number.isNaN(dau)) {
  console.log('usage: capacity-estimator.mjs <dau> [requests-per-user] [host-for-aperf-check]')
  process.exit(1)
}

const payloadKb = 2, peakFactor = 2.5, retainFactor = 0.2, years = 3, qpsPerNode = 300
const reqDay = dau * rpu
const avgQps = reqDay / 86400
const peakQps = avgQps * peakFactor
const storageDayRaw = (reqDay * payloadKb) / (1024 * 1024)
const storageDay = storageDayRaw * retainFactor
const storageTotal = storageDay * 365 * years
const bandwidthMbps = (peakQps * payloadKb * 2 * 8) / 1024
const nodes = Math.ceil(peakQps / qpsPerNode)

console.log('=== Capacity estimate ===')
console.log(`DAU              : ${dau.toLocaleString()}`)
console.log(`requests/user/day: ${rpu}`)
console.log(`requests/day     : ${reqDay.toLocaleString()}`)
console.log(`avg QPS          : ${avgQps.toFixed(0)}`)
console.log(`peak QPS (x${peakFactor}) : ${peakQps.toFixed(0)}`)
console.log(`storage/day raw  : ${storageDayRaw.toFixed(1)} GB`)
console.log(`storage/day kept : ${storageDay.toFixed(1)} GB`)
console.log(`storage ${years} years  : ${storageTotal.toFixed(1)} GB (~${(storageTotal / 1024).toFixed(1)} TB)`)
console.log(`bandwidth in+out : ${bandwidthMbps.toFixed(1)} Mb/s`)
console.log(`app nodes        : ${nodes} (@ ${qpsPerNode} QPS/node) + LB + 2 standby`)

if (host) {
  const url = process.env.RTERM_GW_URL ?? 'ws://127.0.0.1:17888'
  const gw = new RTermGW(url, process.env.RTERM_GW_TOKEN)
  await gw.connect()
  const sess = await gw.rpc('gateway:createSession')
  await gw.rpc('agent:startTask', {
    sessionId: sess.sessionId,
    userInput: `Run an APerf deep-dive on ${host} (60s) and compare its measured CPU/mem/disk/network against this estimate: peak ${peakQps.toFixed(0)} QPS, ~${bandwidthMbps.toFixed(1)} Mb/s. Could one such node carry ~${qpsPerNode} QPS?`,
  }, 240000)
  const ui = await gw.rpc('agent:getUiMessages', { sessionId: sess.sessionId })
  console.log('\n=== APerf validation on', host, '===')
  console.log((ui.messages ?? []).map((m) => `[${m.role}] ${m.text ?? m.content ?? ''}`).join('\n\n'))
  await gw.close()
}
