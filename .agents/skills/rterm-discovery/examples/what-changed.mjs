#!/usr/bin/env node
/**
 * Example: diff a host's last two snapshots ("what changed").
 * Run:  node what-changed.mjs <host> [ws://127.0.0.1:17888]
 */
import { execFile } from 'node:child_process'
import { promisify } from 'node:util'
const run = promisify(execFile)
const CLI = new URL('../scripts/rterm-discovery.mjs', import.meta.url).pathname
const HOST = process.argv[2]
const URL = process.argv[3] || process.env.RTERM_GW_URL || 'ws://127.0.0.1:17888'
if (!HOST) { console.error('usage: node what-changed.mjs <host> [url]'); process.exit(2) }

const { stdout } = await run('node', [CLI, '--url', URL, 'inventory-diff', '--host', HOST, '--last', '2'], { timeout: 60000 })
console.log(`What changed on ${HOST} (last 2 snapshots):\n`)
console.log(stdout)
