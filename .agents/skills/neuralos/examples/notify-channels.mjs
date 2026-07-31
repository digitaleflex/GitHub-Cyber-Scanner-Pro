#!/usr/bin/env node
/**
 * Example: wire Slack / Teams / SMTP / Telegram alert channels into rterm-backend
 * and fire a test alert, proving the notification plumbing end-to-end.
 *
 * Requires webhook URLs / SMTP creds (from your secrets vault). Run:
 *   node notify-channels.mjs --slack https://hooks.slack.com/services/... [--test]
 */
import process from 'node:process'
import { createRequire } from 'node:module'
const require = createRequire(import.meta.url)
const WS = (() => { for (const c of ['ws', '/Users/olu/work/RTerm/node_modules/ws']) { try { return require(c) } catch {} } throw new Error('need ws (npm i ws)') })()

const argv = (() => {
  const a = {}
  for (let i = 2; i < process.argv.length; i += 1) {
    if (process.argv[i].startsWith('--')) { a[process.argv[i].slice(2)] = process.argv[i + 1]; i += 1 }
  }
  return a
})()
const URL = argv.url || process.env.RTERM_GW_URL || 'ws://127.0.0.1:17888'

const ws = new WS(URL)
let seq = 0; const pending = new Map()
const rpc = (method, params = {}, t = 60000) => new Promise((res, rej) => {
  const id = `c${++seq}`; const timer = setTimeout(() => rej(new Error('timeout ' + method)), t)
  pending.set(id, { res, rej, timer }); ws.send(JSON.stringify({ id, method, params }))
})
ws.on('message', (raw) => { const m = JSON.parse(raw.toString())
  if (m.id && pending.has(m.id)) { const p = pending.get(m.id); clearTimeout(p.timer); pending.delete(m.id)
    const err = m.error || (m.ok === false ? m.error : null)
    err ? p.rej(new Error(err.message || 'error')) : p.res(m.result !== undefined ? m.result : m) } })

ws.on('open', async () => {
  try {
    const { sessionId } = await rpc('gateway:createSession')
    const channels = []
    if (argv.slack) channels.push(`Slack (webhook ${argv.slack.slice(0, 40)}…)`)
    if (argv.teams) channels.push(`Teams (webhook ${argv.teams.slice(0, 40)}…)`)
    if (argv.telegram) channels.push(`Telegram (chat ${argv.telegram})`)
    if (argv.smtp) channels.push(`SMTP (${argv.smtp})`)

    const instruction =
      `Wire the following notification channels into the AlertService: ${channels.join(', ')}. ` +
      (argv.test ? 'Then fire a test critical alert ("watchdog web-01 down") to each and report which channel(s) delivered.' : 'Confirm the channels are registered.')
    console.log(`Wiring channels: ${channels.join(', ') || '(none given — pass --slack/--teams/--telegram/--smtp)'}\n`)
    if (channels.length === 0) { console.log('usage: node notify-channels.mjs --slack <url> [--teams <url>] [--telegram <chatId>] [--smtp <host>] [--test]'); process.exit(2) }

    await rpc('agent:startTask', { sessionId, userInput: instruction }, 120000)
    const ui = await rpc('agent:getUiMessages', { sessionId }).catch(() => ({}))
    const last = [...(ui.messages || [])].reverse().find((m) => (m.role || '') === 'assistant')
    console.log(last ? (last.text || last.content || '') : '(dispatched)')
    process.exit(0)
  } catch (e) { console.error('error:', e.message); process.exit(2) }
})
ws.on('error', (e) => { console.error('connect:', e.message); process.exit(4) })
