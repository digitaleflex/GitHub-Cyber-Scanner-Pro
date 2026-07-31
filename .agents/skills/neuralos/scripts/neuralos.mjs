#!/usr/bin/env node
/**
 * neuralos.mjs — cross-platform lifecycle manager for the RTerm backend.
 *
 * Pure Node (>= 18) built-ins only — no npm dependencies, works on macOS, Linux,
 * and Windows. Manages install, start/stop/restart (foreground or background
 * daemon), status, logs, ping, config, service install, and uninstall of the
 * standalone `neuralos` (gybackend) daemon.
 *
 * Usage:
 *   node neuralos.mjs <command> [flags]
 *
 * Commands:
 *   doctor                 Check Node, npm pkg, data dir, port, gateway.
 *   install                npm install -g neuralos
 *   uninstall              stop + npm uninstall -g neuralos
 *   start [--port N] [--host H] [--data DIR] [--daemon] [--log FILE]
 *   stop
 *   restart
 *   status
 *   logs [--lines N]
 *   ping [--url ws://host:port]
 *   config-show            Print effective env + data dir.
 *   install-service        Print the service unit + enable command for this OS.
 *
 * Flags:
 *   --port N        gateway port (default 17888 / GYBACKEND_WS_PORT)
 *   --host H        bind host (default 0.0.0.0 / GYBACKEND_WS_HOST)
 *   --data DIR      data dir (default ./.gybackend-data / GYBACKEND_DATA_DIR)
 *   --daemon        run detached in background (nohup / Start-Process)
 *   --log FILE      daemon log file (default <data>/gybackend.log)
 *   --url URL       full ws url for ping (default ws://127.0.0.1:<port>)
 */
import process from 'node:process'
import os from 'node:os'
import fs from 'node:fs'
import path from 'node:path'
import net from 'node:net'
import http from 'node:http'
import crypto from 'node:crypto'
import { spawn, spawnSync, execFileSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

const IS_WIN = process.platform === 'win32'
const IS_MAC = process.platform === 'darwin'
const HERE = path.dirname(fileURLToPath(import.meta.url))

// --------------------------------------------------------------------------
// args
// --------------------------------------------------------------------------
function parseArgs(argv) {
  const args = { _: [] }
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i]
    if (a.startsWith('--')) {
      const key = a.slice(2)
      const next = argv[i + 1]
      if (next === undefined || next.startsWith('--')) { args[key] = true } else { args[key] = next; i += 1 }
    } else args._.push(a)
  }
  return args
}
const argv = parseArgs(process.argv.slice(2))
const CMD = argv._[0]

const PORT = Number(argv.port || process.env.GYBACKEND_WS_PORT || 17888)
const HOST = argv.host || process.env.GYBACKEND_WS_HOST || '0.0.0.0'
const DATA_DIR = path.resolve(argv.data || process.env.GYBACKEND_DATA_DIR || './.gybackend-data')
const LOG_FILE = path.resolve(argv.log || path.join(DATA_DIR, 'gybackend.log'))
const PID_FILE = path.join(DATA_DIR, 'gybackend.pid')
const WS_URL = argv.url || `ws://127.0.0.1:${PORT}`

const c = {
  ok: (s) => console.log(`  ✔ ${s}`),
  info: (s) => console.log(`  • ${s}`),
  warn: (s) => console.log(`  ⚠ ${s}`),
  err: (s) => console.error(`  ✘ ${s}`),
  head: (s) => console.log(`\n${s}`),
}

function sh(cmd, args, opts = {}) {
  const r = spawnSync(cmd, args, { encoding: 'utf8', stdio: opts.quiet ? 'pipe' : 'inherit', shell: false, ...opts })
  return { code: r.status ?? 0, stdout: (r.stdout || '').trim(), stderr: (r.stderr || '').trim() }
}
function which(bin) {
  const cmd = IS_WIN ? 'where' : 'which'
  const r = spawnSync(cmd, [bin], { encoding: 'utf8' })
  return r.status === 0 ? (r.stdout || '').split('\n')[0].trim() : null
}
function nodeMajor() {
  const m = String(process.versions.node).split('.')[0]
  return Number(m)
}
function npmBin() {
  const nb = which('npm')
  return nb || (IS_WIN ? 'npm.cmd' : 'npm')
}
function nodeBin() {
  return process.execPath
}
// Resolve how to launch gybackend: prefer the on-PATH shim, else resolve
// node + the globally-installed package script via `npm root -g`.
function gybackendLaunch() {
  const shim = which('gybackend') || (IS_WIN ? 'gybackend.cmd' : 'gybackend')
  if (shim && fs.existsSync(shim)) {
    return IS_WIN ? { cmd: 'cmd.exe', args: ['/c', shim] } : { cmd: shim, args: [] }
  }
  try {
    const root = sh(npmBin(), ['root', '-g'], { quiet: true }).stdout
    const script = path.join(root, 'neuralos', 'bin', 'gybackend.js')
    if (fs.existsSync(script)) {
      return { cmd: nodeBin(), args: [script] }
    }
  } catch {}
  return null
}
function portInUse(port, host = '127.0.0.1') {
  return new Promise((resolve) => {
    const s = net.connect({ port, host })
    s.once('connect', () => { s.end(); resolve(true) })
    s.once('error', () => resolve(false))
    s.setTimeout(1200, () => { s.destroy(); resolve(false) })
  })
}
function readPid() {
  try { return Number(fs.readFileSync(PID_FILE, 'utf8').trim()) || null } catch { return null }
}
function pidAlive(pid) {
  if (!pid) return false
  try { process.kill(pid, 0); return true } catch { return false }
}

// Minimal WS client (RFC6455, no deps) for ping.
function wsPing(url, timeoutMs = 4000) {
  return new Promise((resolve, reject) => {
    let u
    try { u = new URL(url) } catch { return reject(new Error('bad url')) }
    const key = crypto.randomBytes(16).toString('base64')
    const req = http.request({
      hostname: u.hostname,
      port: u.port || 80,
      path: u.pathname || '/',
      headers: {
        Connection: 'Upgrade', Upgrade: 'websocket',
        'Sec-WebSocket-Key': key, 'Sec-WebSocket-Version': '13',
      },
      timeout: timeoutMs,
    })
    req.on('upgrade', (res, socket) => {
      // send a masked text frame containing the gateway:ping RPC
      const payload = Buffer.from(JSON.stringify({ id: '1', method: 'gateway:ping' }))
      const mask = crypto.randomBytes(4)
      const masked = Buffer.from(payload.map((b, i) => b ^ mask[i % 4]))
      const header = Buffer.from([0x81, 0x80 | masked.length])
      socket.write(Buffer.concat([header, mask, masked]))
      const chunks = []
      socket.on('data', (d) => {
        chunks.push(d)
        const buf = Buffer.concat(chunks)
        if (buf.includes('pong')) {
          socket.destroy()
          resolve(true)
        }
      })
      socket.setTimeout(timeoutMs, () => { socket.destroy(); reject(new Error('ws timeout')) })
      socket.on('error', reject)
    })
    req.on('error', reject)
    req.on('timeout', () => { req.destroy(); reject(new Error('http timeout')) })
    req.end()
  })
}

// --------------------------------------------------------------------------
// commands
// --------------------------------------------------------------------------
async function doctor() {
  c.head('neuralos doctor')
  const nm = nodeMajor()
  nm >= 18 ? c.ok(`Node ${process.versions.node}`) : c.err(`Node ${process.versions.node} — need >= 18`)
  const npm = npmBin(); npm ? c.ok(`npm: ${npm}`) : c.err('npm not found')
  const gyb = (gybackendLaunch() || {}).cmd; gyb ? c.ok(`gybackend: ${gyb}`) : c.warn('gybackend not on PATH (install with: install)')
  c.info(`platform: ${process.platform} ${process.arch}`)
  c.info(`data dir: ${DATA_DIR} ${fs.existsSync(DATA_DIR) ? '(exists)' : '(will be created)'}`)
  const busy = await portInUse(PORT)
  c.info(`port ${PORT}: ${busy ? 'in use (running?)' : 'free'}`)
  try { await wsPing(WS_URL); c.ok(`gateway ping OK (${WS_URL})`) }
  catch { c.warn(`gateway not answering at ${WS_URL}`) }
}

async function install() {
  c.head('Installing neuralos globally')
  const npm = npmBin()
  const r = sh(npm, ['install', '-g', 'neuralos'])
  if (r.code !== 0) { c.err('npm install failed'); process.exit(r.code) }
  c.ok('installed')
  const gyb = (gybackendLaunch() || {}).cmd; gyb && c.ok(`gybackend at ${gyb}`)
}

async function uninstall() {
  await stop()
  c.head('Uninstalling neuralos')
  const npm = npmBin()
  sh(npm, ['uninstall', '-g', 'neuralos'])
  c.ok('uninstalled')
}

async function start() {
  c.head('Starting neuralos')
  const launch = gybackendLaunch()
  if (!launch) { c.err('gybackend not installed. Run: node neuralos.mjs install'); process.exit(1) }
  const busy = await portInUse(PORT)
  if (busy) { c.warn(`port ${PORT} already in use — is it already running? (status)`); return }
  fs.mkdirSync(DATA_DIR, { recursive: true })
  const env = {
    ...process.env,
    GYBACKEND_WS_ENABLE: '1',
    GYBACKEND_WS_HOST: HOST,
    GYBACKEND_WS_PORT: String(PORT),
    GYBACKEND_DATA_DIR: DATA_DIR,
  }
  if (argv.daemon) {
    fs.mkdirSync(path.dirname(LOG_FILE), { recursive: true })
    const out = fs.openSync(LOG_FILE, 'a')
    const err = fs.openSync(LOG_FILE, 'a')
    const child = spawn(launch.cmd, launch.args, { env, detached: true, stdio: ['ignore', out, err] })
    child.on('error', (e) => c.err(`daemon spawn error: ${e.message}`))
    child.unref()
    fs.writeFileSync(PID_FILE, String(child.pid))
    c.ok(`daemon started (pid ${child.pid})`)
    c.info(`log: ${LOG_FILE}`)
    await new Promise((r) => setTimeout(r, 2500))
    try { await wsPing(WS_URL); c.ok(`gateway answering at ${WS_URL}`) }
    catch { c.warn(`gateway not answering yet — check: node neuralos.mjs logs`) }
  } else {
    c.info('foreground mode (Ctrl+C to stop)')
    const child = spawn(launch.cmd, launch.args, { env, stdio: 'inherit' })
    child.on('exit', (code) => process.exit(code ?? 0)
    )
  }
}

async function stop() {
  c.head('Stopping neuralos')
  const pid = readPid()
  if (pidAlive(pid)) {
    try {
      if (IS_WIN) sh('taskkill', ['/PID', String(pid), '/T', '/F'], { quiet: true })
      else process.kill(pid, 'SIGTERM')
      c.ok(`stopped pid ${pid}`)
    } catch (e) { c.err(`could not stop ${pid}: ${e.message}`) }
  } else {
    // best-effort: find by name
    if (IS_WIN) sh('taskkill', ['/IM', 'gybackend.cmd', '/F'], { quiet: true })
    else sh('pkill', ['-f', 'gybackend'], { quiet: true })
    c.info('no pidfile; attempted name-based stop')
  }
  try { fs.unlinkSync(PID_FILE) } catch {}
}

async function restart() { await stop(); await new Promise((r) => setTimeout(r, 1200)); await start() }

async function status() {
  c.head('neuralos status')
  const pid = readPid()
  const alive = pidAlive(pid)
  c.info(`pid: ${pid || 'none'} ${alive ? '(running)' : ''}`)
  const busy = await portInUse(PORT)
  c.info(`port ${PORT}: ${busy ? 'LISTENING' : 'not listening'}`)
  try { await wsPing(WS_URL); c.ok(`gateway OK at ${WS_URL}`) }
  catch { c.warn(`gateway not answering at ${WS_URL}`) }
  if (fs.existsSync(LOG_FILE)) c.info(`log: ${LOG_FILE}`)
}

async function logs() {
  const n = Number(argv.lines || 40)
  if (!fs.existsSync(LOG_FILE)) { c.warn(`no log at ${LOG_FILE}`); return }
  const lines = fs.readFileSync(LOG_FILE, 'utf8').split('\n')
  console.log(lines.slice(-n).join('\n'))
}

async function ping() {
  try { await wsPing(WS_URL); c.ok(`pong from ${WS_URL}`) }
  catch (e) { c.err(`no response from ${WS_URL}: ${e.message}`); process.exit(1) }
}

function configShow() {
  c.head('effective configuration')
  const rows = [
    ['GYBACKEND_WS_ENABLE', '1'],
    ['GYBACKEND_WS_HOST', HOST],
    ['GYBACKEND_WS_PORT', String(PORT)],
    ['GYBACKEND_DATA_DIR', DATA_DIR],
    ['log file', LOG_FILE],
    ['pid file', PID_FILE],
    ['platform', `${process.platform} ${process.arch}`],
    ['node', process.versions.node],
  ]
  for (const [k, v] of rows) console.log(`  ${k.padEnd(34)} ${v}`)
  c.info(`settings: ${path.join(DATA_DIR, 'settings.json')}`)
}

function installService() {
  c.head(`install-service (${process.platform})`)
  const gyb = (gybackendLaunch() || {}).cmd || 'gybackend'
  if (IS_MAC) {
    const plist = path.join(HERE, '..', 'service', 'ng.hyperspace.neuralos.plist')
    console.log(`  1. cp "${plist}" ~/Library/LaunchAgents/`)
    console.log(`  2. edit GYBACKEND_DATA_DIR in the plist (currently a placeholder)`)
    console.log(`  3. launchctl load ~/Library/LaunchAgents/ng.hyperspace.neuralos.plist`)
    console.log(`  gybackend resolves to: ${gyb}`)
  } else if (IS_WIN) {
    const ps1 = path.join(HERE, '..', 'service', 'install-windows-service.ps1')
    console.log(`  Run in an elevated PowerShell:`)
    console.log(`  powershell -ExecutionPolicy Bypass -File "${ps1}"`)
  } else {
    const unit = path.join(HERE, '..', 'service', 'neuralos.service')
    console.log(`  1. sudo cp "${unit}" /etc/systemd/system/`)
    console.log(`  2. sudo systemctl daemon-reload`)
    console.log(`  3. sudo systemctl enable --now neuralos`)
    console.log(`  gybackend resolves to: ${gyb}`)
  }
}

async function main() {
  switch (CMD) {
    case 'doctor': return doctor()
    case 'install': return install()
    case 'uninstall': return uninstall()
    case 'start': return start()
    case 'stop': return stop()
    case 'restart': return restart()
    case 'status': return status()
    case 'logs': return logs()
    case 'ping': return ping()
    case 'config-show': return configShow()
    case 'install-service': return installService()
    default:
      console.error(`unknown command: ${CMD || '(none)'}\n`)
      console.error('commands: doctor | install | uninstall | start | stop | restart | status | logs | ping | config-show | install-service')
      process.exit(2)
  }
}

main().catch((e) => { c.err(e.message); process.exit(1) })
