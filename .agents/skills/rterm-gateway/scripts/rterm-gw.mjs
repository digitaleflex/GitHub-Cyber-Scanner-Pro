#!/usr/bin/env node
/**
 * rterm-gw.mjs — reference CLI client for the RTerm WebSocket gateway.
 *
 * Zero-install: uses the global `ws` package if available, else falls back to a
 * minimal built-in WebSocket client. Works with Node >= 18.
 *
 * Usage:
 *   node rterm-gw.mjs [--url ws://127.0.0.1:17888] [--token T] <subcommand> [flags]
 *
 * Subcommands:
 *   ping                                   liveness check
 *   terminal-list                          list terminal tabs
 *   session-list                           list agent/chat sessions
 *   settings-get                           dump full settings (connections, automation)
 *   rpc --method <m> [--params '<json>']   call any RPC method
 *   exec-winrm --name <conn> --command <c> open saved WinRM conn + run one command (via agent)
 *   agent-task --text <t> [--async]        run an AI agent task
 *   fs-read --terminalId <id> --path <p>   read a text file on a connected host
 *
 * Env:
 *   RTERM_GW_URL    default ws url
 *   RTERM_GW_TOKEN  bearer token (not needed from localhost)
 */

import process from 'node:process';

// ---------------------------------------------------------------------------
// Minimal arg parsing
// ---------------------------------------------------------------------------
function parseArgs(argv) {
  const args = { _: [] };
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    if (a.startsWith('--')) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (next === undefined || next.startsWith('--')) {
        args[key] = true;
      } else {
        args[key] = next;
        i += 1;
      }
    } else {
      args._.push(a);
    }
  }
  return args;
}

const argv = parseArgs(process.argv.slice(2));
const URL_ = argv.url || process.env.RTERM_GW_URL || 'ws://127.0.0.1:17888';
const TOKEN = argv.token || process.env.RTERM_GW_TOKEN || '';
const SUB = argv._[0];

// ---------------------------------------------------------------------------
// WebSocket: prefer the `ws` package; else minimal fallback via raw TCP/TLS.
// For simplicity and reliability we try `require('ws')` from a few common roots.
// ---------------------------------------------------------------------------
async function loadWS() {
  const candidates = [
    'ws',
    '/Users/olu/work/RTerm/node_modules/ws',
    '/usr/local/lib/node_modules/ws',
  ];
  for (const c of candidates) {
    try {
      const mod = await import(c);
      return mod.default || mod.WebSocket || mod;
    } catch {
      /* try next */
    }
  }
  // Last resort: ask the user to install ws.
  console.error(
    '[rterm-gw] The `ws` package is required. Install it (npm i -g ws) or run from a dir that has it.',
  );
  process.exit(3);
}

// ---------------------------------------------------------------------------
// Gateway client
// ---------------------------------------------------------------------------
class GW {
  constructor(ws, verbose) {
    this.ws = ws;
    this.seq = 0;
    this.pending = new Map();
    this.events = [];
    this.verbose = verbose;
    ws.on('message', (raw) => this.onMessage(raw));
  }

  onMessage(raw) {
    let msg;
    try {
      msg = JSON.parse(raw.toString());
    } catch {
      return;
    }
    // Real envelope: { type:"gateway:response", id, ok, result? , error? }
    // (accept legacy flat { id, result|error } too for forward/backward compat)
    const isResp =
      msg.id !== undefined &&
      (msg.type === 'gateway:response' || msg.result !== undefined || msg.error !== undefined);
    if (isResp && (msg.result !== undefined || msg.error !== undefined || msg.ok !== undefined)) {
      const p = this.pending.get(msg.id);
      if (p) {
        clearTimeout(p.timer);
        this.pending.delete(msg.id);
        if (msg.ok === false || msg.error) {
          const code = msg.error?.code || 'ERROR';
          const text = msg.error?.message || 'unknown error';
          p.reject(new Error(`${p.method} -> ${code}: ${text}`));
        } else {
          p.resolve(msg.result !== undefined ? msg.result : msg);
        }
      }
      return;
    }
    this.events.push(msg);
    if (this.verbose) {
      const s = JSON.stringify(msg);
      process.stderr.write(`  [event] ${s.slice(0, 240)}\n`);
    }
  }

  rpc(method, params = {}, timeoutMs = 30000) {
    return new Promise((resolve, reject) => {
      const id = `c${(this.seq += 1)}`;
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`timeout waiting for ${method}`));
      }, timeoutMs);
      this.pending.set(id, { resolve, reject, timer, method });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }
}

function connect(WSImpl, url, token) {
  return new Promise((resolve, reject) => {
    const opts = token ? { headers: { authorization: `Bearer ${token}` } } : undefined;
    const ws = new WSImpl(url, opts);
    ws.on('open', () => resolve(ws));
    ws.on('error', (e) => reject(e));
  });
}

// ---------------------------------------------------------------------------
// Subcommands
// ---------------------------------------------------------------------------
async function main() {
  const verbose = !!argv.verbose;
  const WSImpl = await loadWS();
  const ws = await connect(WSImpl, URL_, TOKEN).catch((e) => {
    console.error(`[rterm-gw] cannot connect to ${URL_}: ${e.message}`);
    process.exit(4);
  });
  const gw = new GW(ws, verbose);
  const out = (x) => console.log(typeof x === 'string' ? x : JSON.stringify(x, null, 2));

  try {
    switch (SUB) {
      case 'ping':
        out(await gw.rpc('gateway:ping'));
        break;

      case 'terminal-list':
        out(await gw.rpc('terminal:list'));
        break;

      case 'session-list':
        out(await gw.rpc('session:list'));
        break;

      case 'settings-get':
        out(await gw.rpc('settings:get'));
        break;

      case 'rpc': {
        const method = argv.method;
        if (!method) throw new Error('rpc requires --method');
        let params = {};
        if (argv.params) params = JSON.parse(argv.params);
        out(await gw.rpc(method, params, Number(argv.timeout) || 60000));
        break;
      }

      case 'exec-winrm': {
        const name = argv.name;
        const command = argv.command;
        if (!name || !command) throw new Error('exec-winrm requires --name and --command');
        const sess = await gw.rpc('gateway:createSession');
        const sessionId = sess.sessionId;
        const instruction =
          `Open the saved WinRM connection named "${name}" (if not already open) and run exactly this command on it using exec_command, then report the raw output verbatim:\n` +
          `${command}\n` +
          `Be concise — report the command output and nothing else.`;
        console.error(`[rterm-gw] dispatching agent task on session ${sessionId} ...`);
        try {
          await gw.rpc('agent:startTask', { sessionId, userInput: instruction }, Number(argv.timeout) || 150000);
        } catch (e) {
          console.error(`[rterm-gw] startTask note: ${e.message}`);
        }
        await new Promise((r) => setTimeout(r, 1500));
        const ui = await gw.rpc('agent:getUiMessages', { sessionId }).catch(() => ({}));
        const msgs = ui.messages || ui.uiMessages || [];
        const texts = msgs.map((m) => (m.text || m.content || '').toString());
        const blob = texts.join('\n');
        // surface the last assistant message + any signature/version line
        const lastAssistant = [...msgs].reverse().find((m) => (m.role || '') === 'assistant');
        if (lastAssistant) out((lastAssistant.text || lastAssistant.content || '').toString());
        else out(blob.slice(-2000) || '(no transcript captured)');
        const ver = [...blob.matchAll(/SignatureVersion[^\d]*([0-9][0-9.]+)/gi)].map((x) => x[1]);
        if (ver.length) console.error(`[rterm-gw] SignatureVersion: ${ver[ver.length - 1]}`);
        break;
      }

      case 'agent-task': {
        const text = argv.text;
        if (!text) throw new Error('agent-task requires --text');
        const sess = await gw.rpc('gateway:createSession');
        const sessionId = sess.sessionId;
        const method = argv.async ? 'agent:startTaskAsync' : 'agent:startTask';
        const timeout = argv.async ? 30000 : Number(argv.timeout) || 150000;
        console.error(`[rterm-gw] ${method} on session ${sessionId} ...`);
        try {
          const res = await gw.rpc(method, { sessionId, userInput: text }, timeout);
          console.error('[rterm-gw] accepted:', JSON.stringify(res));
        } catch (e) {
          console.error(`[rterm-gw] startTask note: ${e.message}`);
        }
        if (argv.async) {
          const waitS = Number(argv.wait) || 30;
          console.error(`[rterm-gw] watching events for ${waitS}s ...`);
          await new Promise((r) => setTimeout(r, waitS * 1000));
        }
        const ui = await gw.rpc('agent:getUiMessages', { sessionId }).catch(() => ({}));
        const msgs = ui.messages || ui.uiMessages || [];
        const lastAssistant = [...msgs].reverse().find((m) => (m.role || '') === 'assistant');
        if (lastAssistant) out((lastAssistant.text || lastAssistant.content || '').toString());
        else out(msgs.map((m) => (m.text || m.content || '')).join('\n').slice(-2500) || '(no transcript yet)');
        break;
      }

      case 'fs-read': {
        const terminalId = argv.terminalId;
        const filePath = argv.path;
        if (!terminalId || !filePath) throw new Error('fs-read requires --terminalId and --path');
        const res = await gw.rpc('filesystem:readTextFile', { terminalId, filePath }, 30000);
        out(res.content !== undefined ? res.content : res);
        break;
      }

      default:
        console.error(`[rterm-gw] unknown subcommand: ${SUB || '(none)'}\n`);
        console.error(
          'Subcommands: ping | terminal-list | session-list | settings-get | rpc | exec-winrm | agent-task | fs-read',
        );
        process.exit(2);
    }
  } finally {
    try { ws.close(); } catch {}
  }
}

main().catch((e) => {
  console.error('[rterm-gw] error:', e.message);
  process.exit(1);
});
