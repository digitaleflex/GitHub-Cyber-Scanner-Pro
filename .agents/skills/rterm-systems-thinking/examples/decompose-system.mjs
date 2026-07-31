#!/usr/bin/env node
/**
 * decompose-system.mjs — turns an ambiguous system description into a bounded sub-system
 * map (responsibility, interface, owner, RTerm operator) via the agent, and saves it to memory.
 *
 * Usage:
 *   node examples/decompose-system.mjs "a payment switch for NIP interbank transfers"
 */
import { RTermGW } from '../scripts/lib/gw.mjs'

const system = process.argv.slice(2).join(' ')
if (!system) {
  console.log('usage: decompose-system.mjs "<ambiguous system description>"')
  process.exit(1)
}

const url = process.env.RTERM_GW_URL ?? 'ws://127.0.0.1:17888'
const gw = new RTermGW(url, process.env.RTERM_GW_TOKEN)
await gw.connect()
const sess = await gw.rpc('gateway:createSession')
await gw.rpc('agent:startTask', {
  sessionId: sess.sessionId,
  userInput: `Decompose this system into bounded sub-systems using the data-in → processing → state → data-out pattern. For each sub-system give: its responsibility, its interface, its owner, and which RTerm capability (terminal backend, playbook, plugin, ledger) could operate it. Then save the resulting sub-system map to memory. System: ${system}`,
}, 240000)
const ui = await gw.rpc('agent:getUiMessages', { sessionId: sess.sessionId })
console.log((ui.messages ?? []).map((m) => `[${m.role}] ${m.text ?? m.content ?? ''}`).join('\n\n'))
await gw.close()
