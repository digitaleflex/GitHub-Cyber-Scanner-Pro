#!/usr/bin/env node
/**
 * Example: run all collectors across groups and print a discovery summary.
 * Run:  node discover-fleet.mjs [ws://127.0.0.1:17888]
 */
import { execFile } from 'node:child_process'
import { promisify } from 'node:util'
const run = promisify(execFile)
const CLI = new URL('../scripts/rterm-discovery.mjs', import.meta.url).pathname
const URL = process.argv[2] || process.env.RTERM_GW_URL || 'ws://127.0.0.1:17888'

const SCANS = [
  ['win-fleet', 'windows'],
  ['linux-fleet', 'linux'],
  ['core-net', 'network'],
  ['esx-hosts', 'virtualization'],
  ['db-tier', 'databases'],
]

console.log(`Running discovery across ${SCANS.length} groups via ${URL}...\n`)
for (const [group, protocol] of SCANS) {
  try {
    const { stdout } = await run('node', [CLI, '--url', URL, 'scan', '--group', group, '--protocol', protocol], { timeout: 320000 })
    const lines = String(stdout).trim().split('\n')
    console.log(`[${protocol.padEnd(14)}] ${group.padEnd(14)} -> ${lines[lines.length - 1] || 'done'}`)
  } catch (e) {
    console.log(`[${protocol.padEnd(14)}] ${group.padEnd(14)} -> ERROR: ${e.message.split('\n')[0]}`)
  }
}
console.log('\nDiscovery sweep complete. Query with: node ../scripts/rterm-discovery.mjs inventory-list')
