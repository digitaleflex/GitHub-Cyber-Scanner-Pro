#!/usr/bin/env node
/**
 * systems-thinking.mjs — the RTerm systems-thinking loop as a CLI over the gateway.
 *
 * Subcommands map to the 7-step loop:
 *   frame      <problem>     — restate as actor + action + constraint + success metric
 *   decompose  <system>      — break into bounded sub-systems with owners + RTerm operators
 *   prioritize <reqs...>     — MoSCoW the requirements, create tracked requests for Must-haves
 *   estimate   <dau> [rpu]   — DAU → QPS → storage → bandwidth → nodes (+ optional APerf check)
 *   tradeoff   <design>      — evaluate against CAP/PACELC/push-pull/sync-async
 *   build      <playbook>    — deploy a design on real hosts (playbook + MOP)
 *   operate    [host]        — stand up SRE operation (metrics, watchdogs, SLO, dashboard)
 *
 * Usage:
 *   node scripts/systems-thinking.mjs frame "we need better monitoring"
 *   node scripts/systems-thinking.mjs estimate 5000000 10
 *   node scripts/systems-thinking.mjs decompose "a payment switch for NIP"
 *
 * Env: RTERM_GW_URL (default ws://127.0.0.1:17888), RTERM_GW_TOKEN (optional).
 */
import { RTermGW } from './lib/gw.mjs'

const [cmd, ...rest] = process.argv.slice(2)
const url = process.env.RTERM_GW_URL ?? 'ws://127.0.0.1:17888'

function usage() {
  console.log(`systems-thinking.mjs — the RTerm systems-thinking loop as a CLI

  frame      <problem>          restate the real problem (actor+action+constraint+success)
  decompose  <system>           break into bounded sub-systems with owners + RTerm operators
  prioritize <req...>           MoSCoW requirements; create tracked requests for Must-haves
  estimate   <dau> [rpu]        DAU → QPS → storage → bandwidth → nodes (+ optional APerf)
  tradeoff   <design>           evaluate against CAP/PACELC/push-pull/sync-async
  build      <playbook-name>    deploy a design on real hosts (playbook + MOP)
  operate    [host]             stand up SRE operation (metrics, watchdogs, SLO, dashboard)

Env: RTERM_GW_URL (default ws://127.0.0.1:17888), RTERM_GW_TOKEN.`)
  process.exit(cmd ? 1 : 0)
}

async function withGw(fn) {
  const gw = new RTermGW(url, process.env.RTERM_GW_TOKEN)
  await gw.connect()
  try {
    const sess = await gw.rpc('gateway:createSession')
    const sid = sess.sessionId
    return await fn(gw, sid)
  } finally {
    await gw.close()
  }
}

async function agentTask(gw, sid, userInput, timeoutMs = 240000) {
  await gw.rpc('agent:startTask', { sessionId: sid, userInput }, timeoutMs)
  const ui = await gw.rpc('agent:getUiMessages', { sessionId: sid })
  const msgs = ui.messages ?? []
  return msgs.map((m) => `[${m.role}] ${m.text ?? m.content ?? ''}`).join('\n\n')
}

function estimateCapacity(dau, requestsPerUser = 10, payloadKb = 2, peakFactor = 2.5, retainFactor = 0.2, years = 3, qpsPerNode = 300) {
  const reqDay = dau * requestsPerUser
  const avgQps = reqDay / 86400
  const peakQps = avgQps * peakFactor
  const storageDayRaw = (reqDay * payloadKb) / (1024 * 1024) // GB
  const storageDay = storageDayRaw * retainFactor
  const storageTotal = storageDay * 365 * years
  const bandwidthMbps = (peakQps * payloadKb * 2 * 8) / 1024 // in+out, Mb/s
  const nodes = Math.ceil(peakQps / qpsPerNode)
  return { dau, requestsPerUser, reqDay, avgQps, peakQps, payloadKb, storageDayRaw, storageDay, storageTotal, bandwidthMbps, nodes, qpsPerNode }
}

async function main() {
  if (!cmd || cmd === '-h' || cmd === '--help') usage()

  if (cmd === 'frame') {
    const problem = rest.join(' ')
    if (!problem) usage()
    const out = await withGw(async (gw, sid) => {
      return agentTask(gw, sid,
        `Restate this problem as: who (actor) does what (action), under which constraint, and how we know it worked (success metric). Then search the SOP library (sop-assistant: sop_search) for anything relevant. Problem: ${problem}`)
    })
    console.log(out)
    return
  }

  if (cmd === 'decompose') {
    const system = rest.join(' ')
    if (!system) usage()
    const out = await withGw(async (gw, sid) => {
      return agentTask(gw, sid,
        `Decompose this system into bounded sub-systems using the data-in → processing → state → data-out pattern. For each sub-system give: its responsibility, its interface, its owner, and which RTerm capability (terminal backend, playbook, plugin, ledger) could operate it. Save the resulting sub-system map to memory. System: ${system}`)
    })
    console.log(out)
    return
  }

  if (cmd === 'prioritize') {
    const reqs = rest.join(' ')
    if (!reqs) usage()
    const out = await withGw(async (gw, sid) => {
      return agentTask(gw, sid,
        `MoSCoW these requirements (Must/Should/Could/Won't). Then for each Must-have, submit a tracked request via request-router (submit_request) with appropriate risk classification. Requirements: ${reqs}`)
    })
    console.log(out)
    return
  }

  if (cmd === 'estimate') {
    const dau = Number(rest[0])
    const rpu = rest[1] ? Number(rest[1]) : 10
    if (!dau || Number.isNaN(dau)) usage()
    const e = estimateCapacity(dau, rpu)
    console.log('=== Back-of-the-envelope estimate ===')
    console.log(`DAU              : ${e.dau.toLocaleString()}`)
    console.log(`requests/user/day: ${e.requestsPerUser}`)
    console.log(`requests/day     : ${e.reqDay.toLocaleString()}`)
    console.log(`avg QPS          : ${e.avgQps.toFixed(0)}`)
    console.log(`peak QPS (x2.5)  : ${e.peakQps.toFixed(0)}`)
    console.log(`storage/day raw  : ${e.storageDayRaw.toFixed(1)} GB`)
    console.log(`storage/day kept : ${e.storageDay.toFixed(1)} GB (x0.2)`)
    console.log(`storage 3 years  : ${e.storageTotal.toFixed(1)} GB (~${(e.storageTotal / 1024).toFixed(1)} TB)`)
    console.log(`bandwidth in+out : ${e.bandwidthMbps.toFixed(1)} Mb/s`)
    console.log(`app nodes        : ${e.nodes} (@ ${e.qpsPerNode} QPS/node) + LB + 2 standby`)
    if (rest[2]) {
      const host = rest[2]
      console.log(`\n=== Validating against real telemetry on ${host} ===`)
      const out = await withGw(async (gw, sid) => {
        return agentTask(gw, sid,
          `Run an APerf performance deep-dive on ${host} (60s sampling) and compare its measured CPU/mem/disk/network against this estimate: peak ${e.peakQps.toFixed(0)} QPS, ~${e.bandwidthMbps.toFixed(1)} Mb/s. Tell me if one such node could carry ~${e.qpsPerNode} QPS.`)
      })
      console.log(out)
    }
    return
  }

  if (cmd === 'tradeoff') {
    const design = rest.join(' ')
    if (!design) usage()
    const out = await withGw(async (gw, sid) => {
      return agentTask(gw, sid,
        `Evaluate this design against the trade-off frameworks: CAP (CP vs AP vs CA), PACELC (partition: A-vs-C, else: L-vs-C), push-vs-pull, sync-vs-async, strong-vs-eventual consistency. For each, say which side this design should take and why. Then check the real behavior where possible using the SpanLedger APM data and metrics ledger. Design: ${design}`)
    })
    console.log(out)
    return
  }

  if (cmd === 'build') {
    const playbook = rest.join(' ')
    if (!playbook) usage()
    const out = await withGw(async (gw, sid) => {
      return agentTask(gw, sid,
        `Deploy this design as a playbook with validation + automatic rollback, then run it as an approved MOP change (plan → approve → run → status), recording everything in the audit ledger. Design/playbook: ${playbook}`)
    })
    console.log(out)
    return
  }

  if (cmd === 'operate') {
    const host = rest[0] ?? 'all hosts'
    const out = await withGw(async (gw, sid) => {
      return agentTask(gw, sid,
        `Stand up SRE operation for ${host}: metrics ledger snapshots, uptime watchdogs, a 99.9% uptime SLO with burn-rate alerts, Slack/Teams notification channel, the unified dashboard:state, anomaly detection + early-warning forecast, and the hash-chained audit ledger. Report when each piece is live.`)
    })
    console.log(out)
    return
  }

  usage()
}

main().catch((e) => { console.error(e?.message ?? e); process.exit(1) })
