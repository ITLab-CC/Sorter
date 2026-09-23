"""WebSocket bridge between the real marble sorter and the digital twin.

The web app (digital-twin/) connects to this server and mirrors the sorter:
motor, solenoid, LED ring, detections. Messages are JSON, one per frame:

    {"type": "state", "running": true, "motor": true, "solenoid": false,
     "led": {"rgb": [255, 255, 255], "brightness": 0.5}}
    {"type": "detection", "label": "green", "confidence": 0.93, "side": "left"}
    {"type": "release", "label": "red"}      # optional: marble left the tube
    {"type": "reset"}                         # clear the statistics

Use from main.py (runs in a background thread, never blocks the sort loop):

    from twin_bridge import TwinBridge   # copy this file next to main.py
    twin = TwinBridge(port=8765); twin.start()
    twin.state(running=True, motor=True, led=((255, 255, 255), 0.5))
    twin.detection(label, confidence / 100, "left")
    twin.state(solenoid=True)

Test without hardware (the web app then shows a live demo):

    pip install websockets
    python bridge/twin_bridge.py --demo
    # web app -> "Echter Sorter" -> ws://localhost:8765 -> Verbinden
"""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import threading
import time

import websockets

SORT_RULES = {"green": "left", "orange": "left", "red": "right", "black": "right"}


class TwinBridge:
    """Broadcasts sorter events to all connected digital-twin clients."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        self._clients: set = set()
        self._loop: asyncio.AbstractEventLoop | None = None
        # last full state, sent to every client that connects later
        self._state: dict = {"type": "state", "running": False, "motor": False, "solenoid": False,
                             "led": {"rgb": [0, 255, 0], "brightness": 0.05}}

    # -- public API (thread-safe) --------------------------------------------
    def start(self) -> None:
        ready = threading.Event()
        threading.Thread(target=self._run, args=(ready,), daemon=True).start()
        ready.wait(5)

    def state(self, running=None, motor=None, solenoid=None, led=None) -> None:
        msg: dict = {"type": "state"}
        for key, value in (("running", running), ("motor", motor), ("solenoid", solenoid)):
            if value is not None:
                msg[key] = bool(value)
        if led is not None:
            rgb, brightness = led
            msg["led"] = {"rgb": list(rgb), "brightness": float(brightness)}
        self._state.update({k: v for k, v in msg.items() if k != "type"})
        self._send(msg)

    def detection(self, label: str, confidence: float, side: str | None = None) -> None:
        self._send({"type": "detection", "label": label, "confidence": float(confidence),
                    "side": side or SORT_RULES.get(label, "right")})

    def release(self, label: str | None = None) -> None:
        self._send({"type": "release", **({"label": label} if label else {})})

    def reset(self) -> None:
        self._send({"type": "reset"})

    # -- internals -------------------------------------------------------------
    def _send(self, msg: dict) -> None:
        if self._loop:
            asyncio.run_coroutine_threadsafe(self._broadcast(json.dumps(msg)), self._loop)

    async def _broadcast(self, text: str) -> None:
        for ws in list(self._clients):
            try:
                await ws.send(text)
            except Exception:
                self._clients.discard(ws)

    async def _handler(self, ws) -> None:
        self._clients.add(ws)
        try:
            await ws.send(json.dumps(self._state))
            await ws.wait_closed()
        finally:
            self._clients.discard(ws)

    def _run(self, ready: threading.Event) -> None:
        async def main():
            self._loop = asyncio.get_running_loop()
            async with websockets.serve(self._handler, self.host, self.port):
                print(f"[twin] WebSocket bridge on ws://{self.host}:{self.port}")
                ready.set()
                await asyncio.Future()

        asyncio.run(main())


def demo(bridge: TwinBridge) -> None:
    """Fake sorter: behaves like main.py, but with random marbles."""
    bridge.reset()
    bridge.state(running=True, motor=True, led=((255, 255, 255), 0.5))
    while True:
        label = random.choice(list(SORT_RULES))
        bridge.release(label)
        time.sleep(0.9)  # marble falls to the camera
        side = SORT_RULES[label]
        bridge.detection(label, random.uniform(0.85, 0.99), side)
        bridge.state(solenoid=side == "left")
        time.sleep(1.6)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--demo", action="store_true", help="send fake sorter events")
    args = parser.parse_args()
    b = TwinBridge(port=args.port)
    b.start()
    try:
        demo(b) if args.demo else threading.Event().wait()
    except KeyboardInterrupt:
        pass
