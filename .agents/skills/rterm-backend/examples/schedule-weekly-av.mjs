#!/usr/bin/env node
/**
 * Example: create a weekly antivirus-signature-update cron task on the backend.
 *
 * Reads current settings, appends a scheduled task to automation.scheduledTasks,
 * and writes settings back. The backend scheduler runs it every Friday at 00:00
 * on every server in the "win-prod" group — fully unattended.
 *
 * Run:  node schedule-weekly-av.mjs [ws://127.0.0.1:17888]
 */
import process from 'node:process'
import { createRequire } from 'node:module'
const require = createRequire(import.meta.url)
const WS = (() => { for (const c of ['ws', '/Users/olu/work/RTerm/node_modules/ws']) { try { return require(c) } catch {} } throw new Error('need ws (npm i ws)') })()

const URL = process.argv[2] || process.env.RTERM_GW_URL || 'ws://127.0.0.1:17888'
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
    const settings = await rpc('settings:get')
    const automation = settings.automation || {}
    const tasks = automation.scheduledTasks || []
    const task = {
      id: `weekly-av-${Date.now().toString(36)}`,
      name: 'Weekly AV Signature Update',
      cron: '0 0 * * 5',                      // every Friday at 00:00
      enabled: true,
      groupId: 'win-prod',
      command:
        'powershell -NoProfile -Command "Update-MpSignature; ' +
        '(Get-MpComputerStatus) | Select-Object AntispywareSignatureVersion, AntispywareSignatureLastUpdated | Format-List"',
    }
    const next = { ...settings, automation: { ...automation, scheduledTasks: [...tasks, task] } }
    await rpc('settings:set', { settings: next })
    console.log(`Created scheduled task "${task.name}" (${task.cron}) -> id ${task.id}`)
    console.log('The backend scheduler will run it every Friday at 00:00 on group "win-prod".')
    process.exit(0)
  } catch (e) { console.error('error:', e.message); process.exit(2) }
})
ws.on('error', (e) => { console.error('connect:', e.message); process.exit(4) })
