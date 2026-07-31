#!/usr/bin/env node
/**
 * Example: approval-gated change (MOP) driven through the gateway.
 *
 * plan -> (human approves) -> run -> status. Demonstrates how a remote program
 * proposes a change and reads the auditable result; the approve step can also be
 * done by a human in the RTerm UI, or by an authorized caller here.
 *
 * Run:  node mop-change.mjs <playbookName> [ws://127.0.0.1:17888]
 */
import process from 'node:process';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const WS = (() => { for (const c of ['ws', '/Users/olu/work/RTerm/node_modules/ws']) { try { return require(c); } catch {} } throw new Error('need ws'); })();

const PLAYBOOK = process.argv[2];
const URL = process.argv[3] || process.env.RTERM_GW_URL || 'ws://127.0.0.1:17888';
if (!PLAYBOOK) { console.error('usage: node mop-change.mjs <playbookName> [url]'); process.exit(2); }

const ws = new WS(URL);
let seq = 0; const pending = new Map();
const rpc = (method, params = {}, t = 60000) => new Promise((res, rej) => {
  const id = `c${++seq}`; const timer = setTimeout(() => rej(new Error('timeout ' + method)), t);
  pending.set(id, { res, rej, timer }); ws.send(JSON.stringify({ id, method, params }));
});
ws.on('message', (raw) => { const m = JSON.parse(raw.toString());
  if (m.id && pending.has(m.id)) { const p = pending.get(m.id); clearTimeout(p.timer); pending.delete(m.id); m.error ? p.rej(new Error(m.error.message)) : p.res(m.result); } });

// manage_change is an agent tool; we invoke it by asking the agent to call it.
async function manage(action, changeId) {
  const { sessionId } = await rpc('gateway:createSession');
  const arg = changeId ? ` action=${action} changeId=${changeId}` : ` action=${action} name="${PLAYBOOK}"`;
  const task = `Call the manage_change tool with${arg}. Report the tool's output verbatim.`;
  try { await rpc('agent:startTask', { sessionId, userInput: task }, 150000); } catch {}
  const ui = await rpc('agent:getUiMessages', { sessionId }).catch(() => ({}));
  return (ui.messages || []).map((m) => (m.text || m.content || '')).join('\n');
}

ws.on('open', async () => {
  try {
    console.log('=== PLAN ===');
    const plan = await manage('plan');
    console.log(plan);
    const idm = plan.match(/chg-[a-z0-9-]+/i);
    if (!idm) { console.error('could not parse changeId'); process.exit(3); }
    const changeId = idm[0];

    console.log('\n=== APPROVE ===');
    console.log(await manage('approve', changeId));

    console.log('\n=== RUN ===');
    console.log(await manage('run', changeId));

    console.log('\n=== STATUS ===');
    console.log(await manage('status', changeId));
    process.exit(0);
  } catch (e) { console.error('error:', e.message); process.exit(2); }
});
ws.on('error', (e) => { console.error('connect:', e.message); process.exit(4); });
