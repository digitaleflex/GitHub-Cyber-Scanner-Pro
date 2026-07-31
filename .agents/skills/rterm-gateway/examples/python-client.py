#!/usr/bin/env python3
"""
Example: drive the RTerm WebSocket gateway from Python (no Node required).

Demonstrates connect, ping, terminal:list, and an agent task with transcript.
Requires:  pip install websockets

Run:  python3 python-client.py [ws://127.0.0.1:17888]
"""
import asyncio
import json
import sys

try:
    import websockets
except ImportError:
    sys.stderr.write("This example needs `websockets`:  pip install websockets\n")
    raise

URL = sys.argv[1] if len(sys.argv) > 1 else "ws://127.0.0.1:17888"
TOKEN = None  # set a token string here when connecting from a non-localhost host


class RTermGW:
    def __init__(self):
        self._seq = 0
        self._pending = {}
        self.events = []

    async def connect(self):
        # `websockets` renamed extra_headers -> additional_headers in v14/v15.
        headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else None
        try:
            self.ws = await websockets.connect(URL, additional_headers=headers)
        except TypeError:
            self.ws = await websockets.connect(URL, extra_headers=headers)
        self._reader = asyncio.create_task(self._read_loop())

    async def _read_loop(self):
        try:
            async for raw in self.ws:
                msg = json.loads(raw)
                is_resp = msg.get("type") == "gateway:response" or (
                    "id" in msg and ("result" in msg or "error" in msg or "ok" in msg)
                )
                if is_resp:
                    fut = self._pending.pop(msg.get("id"), None)
                    if fut and not fut.done():
                        if msg.get("ok") is False or "error" in msg:
                            err = msg.get("error") or {}
                            fut.set_exception(
                                RuntimeError(f"{err.get('code')}: {err.get('message')}")
                            )
                        else:
                            fut.set_result(msg.get("result", msg))
                else:
                    self.events.append(msg)
        except Exception:
            pass

    async def rpc(self, method, params=None, timeout=60):
        self._seq += 1
        rid = f"c{self._seq}"
        fut = asyncio.get_event_loop().create_future()
        self._pending[rid] = fut
        await self.ws.send(json.dumps({"id": rid, "method": method, "params": params or {}}))
        return await asyncio.wait_for(fut, timeout)

    async def close(self):
        try:
            self._reader.cancel()
            await self.ws.close()
        except Exception:
            pass


async def main():
    gw = RTermGW()
    await gw.connect()
    print("ping ->", await gw.rpc("gateway:ping"))

    terms = await gw.rpc("terminal:list")
    print("terminals ->", [(t.get("title"), t.get("type")) for t in terms.get("terminals", [])])

    # Run a blocking agent task and print the transcript tail.
    sess = await gw.rpc("gateway:createSession")
    sid = sess["sessionId"]
    print("session ->", sid)
    await gw.rpc(
        "agent:startTask",
        {
            "sessionId": sid,
            "userInput": (
                "Update AV signatures on the saved WinRM connection AWS-Windows-Server-1 "
                "and report the AntispywareSignatureVersion. Be concise."
            ),
        },
        timeout=180,
    )
    ui = await gw.rpc("agent:getUiMessages", {"sessionId": sid})
    for m in (ui.get("messages") or [])[-3:]:
        text = (m.get("text") or m.get("content") or "")[:400]
        print(f"[{m.get('role', '?')}] {text}")

    await gw.close()


if __name__ == "__main__":
    asyncio.run(main())
