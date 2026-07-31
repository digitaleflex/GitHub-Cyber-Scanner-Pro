#!/usr/bin/env node
/**
 * Example: a zone Outpost shipping local discovery results to the central CMDB
 * hub over the gateway (outbound-only, ADDM Outpost→Appliance pattern).
 *
 * The Outpost runs collectors for its zone and POSTs each normalized asset to
 * the hub's inventory:upsert RPC. Only outbound egress to the hub is needed.
 *
 * Run:  node outpost-ship.mjs --zone zone-a --hub ws://hub-host:17888 --group win-fleet
 */
import { execFile } from 'node:child_process'
import { promisify } from 'node:util'
const run = promisify(execFile)
const CLI = new URL('../scripts/rterm-discovery.mjs', import.meta.url).pathname

const argv = (() => {
  const a = {}
  for (let i = 2; i < process.argv.length; i += 1) {
    if (process.argv[i].startsWith('--')) a[process.argv[i].slice(2)] = process.argv[i + 1]; i += 1
  }
  return a
})()
const ZONE = argv.zone || 'zone-a'
const HUB = argv.hub || process.env.RTERM_HUB_URL || 'ws://127.0.0.1:17888'
const GROUP = argv.group || 'win-fleet'

console.log(`[outpost:${ZONE}] running local discovery for group "${GROUP}" ...`)
const { stdout } = await run('node', [CLI, '--url', HUB, 'scan', '--group', GROUP, '--protocol', 'auto'].filter(Boolean), { timeout: 320000 })
console.log(stdout)
console.log(`[outpost:${ZONE}] results shipped to hub ${HUB} (outbound-only).`)
