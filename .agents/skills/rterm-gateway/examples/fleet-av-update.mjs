#!/usr/bin/env node
/**
 * Example: update antivirus signatures across a WinRM fleet, collecting versions.
 *
 * For each saved WinRM connection, dispatch an agent task to run Update-MpSignature
 * and report the resulting AntispywareSignatureVersion. Prints a per-host table.
 *
 * Run:  node fleet-av-update.mjs [ws://127.0.0.1:17888] [connName1 connName2 ...]
 *       (defaults to all saved WinRM connections from settings:get)
 */
import process from 'node:process';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const WS = (() => { for (const c of ['ws', '/Users/olu/work/RTerm/node_modules/ws']) { try { return require(c); } catch {} } throw new Error('need ws'); })();

const URL = process.argv[2] || process.env.RTERM_GW_URL || 'ws://127.0.0.1:17888';
const ws = new WS(URL);
let seq = 0; const pending = new Map();
const rpc = (method, params = {}, t = 60000) => new Promise((res, rej) => {
  const id = `c${++seq}`; const timer = setTimeout(() => rej(new Error('timeout ' + method)), t);
  pending.set(id, { res, rej, timer }); ws.send(JSON.stringify({ id, method, params }));
});
ws.on('message', (raw) => { const m = JSON.parse(raw.toString());
  if (m.id && pending.has(m.id)) { const p = pending.get(m.id); clearTimeout(p.timer); pending.delete(m.id); m.error ? p.rej(new Error(m.error.message)) : p.res(m.result); } });

async function updateOne(name) {
  const { sessionId } = await rpc('gateway:createSession');
  const task =
    `Open the saved WinRM connection named "${name}" (if not open) and run exactly:\n` +
    `powershell -NoProfile -Command "Update-MpSignature; (Get-MpComputerStatus).AntispywareSignatureVersion"\n` +
    `Report only the resulting version number.`;
  try { await rpc('agent:startTask', { sessionId, userInput: task }, 150000); } catch {}
  const ui = await rpc('agent:getUiMessages', { sessionId }).catch(() => ({}));
  const text = (ui.messages || []).map((m) => (m.text || m.content || '')).join('\n');
  const m = text.match(/([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)/);
  return m ? m[1] : 'n/a';
}

ws.on('open', async () => {
  try {
    let names = process.argv.slice(3);
    if (names.length === 0) {
      const s = await rpc('settings:get');
      names = (s.connections?.winrm || []).map((c) => c.name);
    }
    console.log(`Updating AV signatures on ${names.length} host(s)...\n`);
    for (const name of names) {
      const ver = await updateOne(name);
      console.log(`  ${name.padEnd(28)} ${ver}`);
    }
    process.exit(0);
  } catch (e) { console.error('error:', e.message); process.exit(2); }
});
ws.on('error', (e) => { console.error('connect:', e.message); process.exit(4); });
