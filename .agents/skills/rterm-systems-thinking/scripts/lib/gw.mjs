/**
 * gw.mjs — minimal RTerm gateway client (WebSocket JSON-RPC) for the systems-thinking scripts.
 * Dependency-light: uses the global WebSocket when available (Node ≥21) or the 'ws' package.
 */
let WS = globalThis.WebSocket
if (!WS) {
  try {
    WS = (await import('ws')).default
  } catch {
    // will error on connect with a helpful message
  }
}

export class RTermGW {
  constructor(url, token) {
    this.url = url
    this.token = token
    this.seq = 0
    this.pending = new Map()
    this.events = []
  }

  async connect() {
    if (!WS) throw new Error('No WebSocket implementation — install the "ws" package (npm i ws) or use Node ≥21')
    const headers = this.token ? { Authorization: `Bearer ${this.token}` } : undefined
    this.ws = headers ? new WS(this.url, { headers }) : new WS(this.url)
    this.ws.onmessage = (ev) => this._onMessage(ev.data)
    this.ws.onerror = () => { for (const [, p] of this.pending) p.reject(new Error('ws error')) }
    await new Promise((resolve, reject) => {
      this.ws.onopen = resolve
      setTimeout(() => reject(new Error('connect timeout')), 10000)
    })
  }

  _onMessage(raw) {
    let msg
    try { msg = JSON.parse(raw) } catch { return }
    if (msg.type === 'gateway:response' || ('id' in msg && ('ok' in msg || 'result' in msg || 'error' in msg))) {
      const p = this.pending.get(msg.id)
      if (p) {
        this.pending.delete(msg.id)
        if (msg.ok === false || msg.error) {
          const err = msg.error ?? {}
          p.reject(new Error(`${err.code ?? 'ERR'}: ${err.message ?? 'unknown error'}`))
        } else {
          p.resolve(msg.result ?? msg)
        }
      }
    } else {
      this.events.push(msg)
    }
  }

  rpc(method, params = {}, timeoutMs = 60000) {
    const id = `c${++this.seq}`
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject })
      this.ws.send(JSON.stringify({ id, method, params }))
      setTimeout(() => {
        if (this.pending.has(id)) {
          this.pending.delete(id)
          reject(new Error(`rpc timeout: ${method}`))
        }
      }, timeoutMs)
    })
  }

  async close() {
    try { this.ws?.close() } catch { /* noop */ }
  }
}
