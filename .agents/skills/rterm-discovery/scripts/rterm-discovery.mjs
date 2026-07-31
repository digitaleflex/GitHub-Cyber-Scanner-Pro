#!/usr/bin/env node
/**
 * rterm-discovery.mjs — agentless discovery & CMDB orchestration CLI.
 *
 * Drives an RTerm gateway (desktop app or rterm-backend daemon) over WebSocket
 * JSON-RPC to run discovery scans, query the CMDB, diff snapshots, and
 * reconcile assets. Pure Node (>=18) built-ins only — no npm dependencies.
 *
 * Usage:
 *   node rterm-discovery.mjs <command> [flags]
 *
 * Commands:
 *   scan --group <g> --protocol <windows|linux|network|virtualization|databases|base>
 *   inventory-list [--type T] [--status S] [--query Q]
 *   inventory-get --host <h>
 *   inventory-diff --host <h> [--last N]
 *   inventory-links --host <h>
 *   reconcile
 *   ping
 *
 * Flags: --url ws://host:17888   (default ws://127.0.0.1:17888 / RTERM_GW_URL)
 */
import process from 'node:process'
import http from 'node:http'
import crypto from 'node:crypto'

const argv = (() => {
  const a = { _: [] }
  for (let i = 2; i < process.argv.length; i += 1) {
    const t = process.argv[i]
    if (t.startsWith('--')) {
      const k = t.slice(2); const n = process.argv[i + 1]
      if (n === undefined || n.startsWith('--')) a[k] = true; else { a[k] = n; i += 1 }
    } else a._.push(t)
  }
  return a
})()

const CMD = argv._[0]
const GW_URL = argv.url || process.env.RTERM_GW_URL || 'ws://127.0.0.1:17888'

// --- minimal RFC6455 WebSocket JSON-RPC client (no deps) ---
function wsRpc(url, method, params = {}, timeoutMs = 15000) {
  return new Promise((resolve, reject) => {
    let u
    try {
      const normalized = String(url).replace(/^ws:\/\//i, 'http://').replace(/^wss:\/\//i, 'https://')
      u = new URL(normalized)
    } catch {
      return reject(new Error('bad url'))
    }
    const key = crypto.randomBytes(16).toString('base64')
    const req = http.request({
      hostname: u.hostname, port: u.port || 80, path: u.pathname || '/',
      headers: { Connection: 'Upgrade', Upgrade: 'websocket', 'Sec-WebSocket-Key': key, 'Sec-WebSocket-Version': '13' },
      timeout: timeoutMs,
    })
    req.on('upgrade', (res, socket) => {
      const send = (obj) => {
        const payload = Buffer.from(JSON.stringify(obj))
        const mask = crypto.randomBytes(4)
        const masked = Buffer.from(payload.map((b, i) => b ^ mask[i % 4]))
        let header
        if (masked.length < 126) header = Buffer.from([0x81, 0x80 | masked.length])
        else if (masked.length < 65536) { header = Buffer.alloc(4); header[0] = 0x81; header[1] = 0x80 | 126; header.writeUInt16BE(masked.length, 2) }
        else { header = Buffer.alloc(10); header[0] = 0x81; header[1] = 0x80 | 127; header.writeBigUInt64BE(BigInt(masked.length), 2) }
        socket.write(Buffer.concat([header, mask, masked]))
      }
      send({ id: '1', method, params })
      const chunks = []
      let done = false
      const finish = (val, isErr) => { if (!done) { done = true; socket.destroy(); isErr ? reject(val) : resolve(val) } }
      socket.setTimeout(timeoutMs, () => finish(new Error('rpc timeout'), true))
      socket.on('error', (e) => finish(e, true))
      socket.on('data', (d) => {
        chunks.push(d)
        const buf = Buffer.concat(chunks)
        // naive frame parse: strip 2-byte header (server frames unmasked)
        for (let i = 0; i < buf.length; i += 1) {
          if (buf[i] === 0x7b /* { */) {
            try {
              const msg = JSON.parse(buf.slice(i).toString())
              if (msg.id === '1' && (msg.result !== undefined || msg.error !== undefined || msg.ok !== undefined)) {
                if (msg.ok === false || msg.error) finish(new Error((msg.error && msg.error.message) || 'rpc error'), true)
                else finish(msg.result !== undefined ? msg.result : msg, false)
                return
              }
            } catch { /* keep buffering */ }
          }
        }
      })
    })
    req.on('error', reject)
    req.on('timeout', () => { req.destroy(); reject(new Error('http timeout')) })
    req.end()
  })
}

const out = (x) => console.log(typeof x === 'string' ? x : JSON.stringify(x, null, 2))
const PROTOCOLS = ['windows', 'linux', 'network', 'virtualization', 'databases', 'base']

async function scan() {
  const group = argv.group
  const protocol = argv.protocol
  if (!group) throw new Error('scan requires --group')
  if (!protocol || !PROTOCOLS.includes(protocol)) throw new Error(`scan requires --protocol one of ${PROTOCOLS.join('|')}`)
  const { sessionId } = await wsRpc(GW_URL, 'gateway:createSession')
  const instruction =
    `Run an agentless ${protocol} discovery scan across the "${group}" connection group. ` +
    `For each host, collect the normalized asset (OS, cpu, mem, disks, nics, services, listeningPorts, packages, and links where applicable) ` +
    `and write it to the CMDB via inventory:upsert. Report a per-host summary (host: ok/failed + asset type) and a final count.`
  await wsRpc(GW_URL, 'agent:startTask', { sessionId, userInput: instruction }, 300000)
  const ui = await wsRpc(GW_URL, 'agent:getUiMessages', { sessionId }).catch(() => ({}))
  const msgs = ui.messages || []
  const last = [...msgs].reverse().find((m) => (m.role || '') === 'assistant')
  out(last ? (last.text || last.content || '') : msgs.map((m) => m.text || m.content || '').join('\n').slice(-3000))
}

async function inventoryList() {
  const res = await wsRpc(GW_URL, 'inventory:list', {
    ...(argv.type ? { type: argv.type } : {}),
    ...(argv.status ? { status: argv.status } : {}),
    ...(argv.query ? { query: argv.query } : {}),
  })
  const assets = res.assets || res || []
  if (!assets.length) { out('No assets.'); return }
  for (const a of assets) out(`  ${a.status === 'active' ? '●' : '○'} ${(a.name || a.key || '?').padEnd(24)} [${a.type || '?'}] ${a.mgmtIp || ''}  (lastSeen ${a.lastSeen || '?'})`)
  out(`\n${assets.length} asset(s)`)
}

async function inventoryGet() {
  if (!argv.host) throw new Error('inventory-get requires --host')
  const res = await wsRpc(GW_URL, 'inventory:get', { host: argv.host })
  out(res)
}

async function inventoryDiff() {
  if (!argv.host) throw new Error('inventory-diff requires --host')
  const res = await wsRpc(GW_URL, 'inventory:diff', { host: argv.host, last: argv.last ? Number(argv.last) : 2 })
  out(res)
}

async function inventoryLinks() {
  if (!argv.host) throw new Error('inventory-links requires --host')
  const res = await wsRpc(GW_URL, 'inventory:links', { host: argv.host })
  out(res)
}

async function reconcile() {
  const { sessionId } = await wsRpc(GW_URL, 'gateway:createSession')
  await wsRpc(GW_URL, 'agent:startTask', { sessionId, userInput:
    'Reconcile the CMDB: mark assets not seen in 3 scans as stale/missing, dedupe assets by hash, refresh relationship links, and report the reconciliation summary.' }, 180000)
  const ui = await wsRpc(GW_URL, 'agent:getUiMessages', { sessionId }).catch(() => ({}))
  const msgs = ui.messages || []
  const last = [...msgs].reverse().find((m) => (m.role || '') === 'assistant')
  out(last ? (last.text || last.content || '') : '(reconciliation dispatched)')
}

async function ping() {
  const res = await wsRpc(GW_URL, 'gateway:ping')
  out(res)
}

async function main() {
  switch (CMD) {
    case 'scan': return scan()
    case 'inventory-list': return inventoryList()
    case 'inventory-get': return inventoryGet()
    case 'inventory-diff': return inventoryDiff()
    case 'inventory-links': return inventoryLinks()
    case 'reconcile': return reconcile()
    case 'ping': return ping()
    default:
      console.error(`unknown command: ${CMD || '(none)'}\n`)
      console.error('commands: scan | inventory-list | inventory-get | inventory-diff | inventory-links | reconcile | ping')
      process.exit(2)
  }
}

main().catch((e) => { console.error('error:', e.message); process.exit(1) })
