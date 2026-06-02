#!/usr/bin/env python3
"""
sidekick_collector.py — Second Attention dataset collector + viewer (laptop side).

Camera: flash unitcams3_webcam.ino (M5's web_cam example). It streams motion-JPEG
at  http://<camera-ip>/  (one viewer at a time).

This script reads that stream, does STILLNESS DETECTION (still = gimbal paused /
observing; moving = searching), saves ONLY still frames while RECORDING, and serves
the clean ZZZ WebUI + dataset at  http://localhost:8000 .

Run in your Spatial_Camera .venv (has requests + Pillow + numpy):
    python3 sidekick_collector.py --camera http://192.168.3.26
    # then open http://localhost:8000
NOTE: the camera serves ONE viewer at a time — don't also open its IP in a browser.

Options: --camera URL  --poll 0.5  --min-gap 2.5  --thresh 8  --port 8000
"""

import argparse
import io
import json
import re
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote

import requests
try:
    from PIL import Image
    import numpy as np
    STILLNESS_OK = True
except Exception:
    STILLNESS_OK = False

CAMERA  = "http://sidekick-cam.local"   # mDNS name — no IP needed (pass --camera to override)
POLL    = 0.5
MIN_GAP = 2.5
THRESH  = 8.0
DATASET = Path(__file__).parent / "dataset"
WEBUI   = Path(__file__).parent / "webui" / "index.html"

state = {"online": False, "recording": False, "count": 0,
         "still": False, "diff": 999, "last_jpeg": None}
_prev = None

_session = requests.Session()
_session.trust_env = False   # ignore any system proxy — camera is on the LAN


def frame_diff(jpeg):
    global _prev
    if not STILLNESS_OK:
        return 0
    try:
        im = Image.open(io.BytesIO(jpeg)).convert("L").resize((32, 24))
        cur = np.asarray(im, dtype=np.int16)
    except Exception:
        return 999
    if _prev is None:
        _prev = cur
        return 999
    d = float(np.mean(np.abs(cur - _prev)))
    _prev = cur
    return d


def stream_loop():
    """Read the camera's MJPEG stream with requests (robust); reconnect on error."""
    DATASET.mkdir(exist_ok=True)
    state["count"] = len(list(DATASET.glob("*.jpg")))
    seq = 0                                   # running photo number, continues across runs
    for f in DATASET.glob("IMG_*.jpg"):
        m = re.match(r"IMG_(\d+)_", f.name)
        if m and int(m.group(1)) < 1_000_000:   # ignore old date-named test files
            seq = max(seq, int(m.group(1)))
    last_proc = 0.0
    last_save = 0.0
    while True:
        try:
            r = _session.get(CAMERA + "/", stream=True, timeout=(5, 15))
            state["online"] = True
            print("[stream] connected — reading MJPEG. Open http://localhost:8000")
            buf = b""
            nframes = 0
            for chunk in r.iter_content(chunk_size=8192):
                if not chunk:
                    continue
                buf += chunk
                while True:
                    a = buf.find(b"\xff\xd8")
                    b = buf.find(b"\xff\xd9", a + 2) if a != -1 else -1
                    if a == -1 or b == -1:
                        break
                    jpeg = buf[a:b + 2]
                    buf = buf[b + 2:]
                    state["last_jpeg"] = jpeg
                    nframes += 1
                    if nframes % 30 == 0:
                        print(f"[stream] {nframes} frames received (live)")
                    now = time.time()
                    if now - last_proc >= POLL:
                        last_proc = now
                        d = frame_diff(jpeg)
                        state["diff"] = round(d, 1)
                        state["still"] = (d <= THRESH)
                        if state["recording"] and state["still"] and (now - last_save) >= MIN_GAP:
                            last_save = now
                            seq += 1
                            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                            fn = f"IMG_{seq:05d}_{ts}.jpg"
                            (DATASET / fn).write_bytes(jpeg)
                            state["count"] += 1
                            print(f"saved #{seq}  {fn}  ({len(jpeg)//1024}KB)  diff={d:.1f}")
                if len(buf) > 2_000_000:
                    buf = buf[-200_000:]
        except Exception as e:
            state["online"] = False
            print(f"[stream] {e} — retrying in 2s")
            time.sleep(2)


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, ctype, body=b""):
        if isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if body:
            self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path); p = u.path
        if p == "/":
            self._send(200, "text/html; charset=utf-8", WEBUI.read_text())
        elif p == "/api/live":
            if state["last_jpeg"]: self._send(200, "image/jpeg", state["last_jpeg"])
            else: self._send(503, "text/plain", "no frame yet")
        elif p == "/api/status":
            self._send(200, "application/json", json.dumps({
                "online": state["online"], "recording": state["recording"],
                "count": state["count"], "still": state["still"], "diff": state["diff"]}))
        elif p == "/api/list":
            self._send(200, "application/json",
                       json.dumps(sorted(f.name for f in DATASET.glob("*.jpg"))))
        elif p == "/api/img":
            name = Path(unquote(parse_qs(u.query).get("f", [""])[0])).name
            fp = DATASET / name
            if fp.exists(): self._send(200, "image/jpeg", fp.read_bytes())
            else: self._send(404, "text/plain", "not found")
        elif p == "/api/start":
            state["recording"] = True; self._send(200, "text/plain", "recording")
        elif p == "/api/stop":
            state["recording"] = False; self._send(200, "text/plain", "stopped")
        else:
            self._send(404, "text/plain", "?")

    def log_message(self, *a):
        pass


def main():
    global CAMERA, POLL, MIN_GAP, THRESH
    ap = argparse.ArgumentParser()
    ap.add_argument("--camera", default=CAMERA)
    ap.add_argument("--poll", type=float, default=POLL)
    ap.add_argument("--min-gap", type=float, default=MIN_GAP)
    ap.add_argument("--thresh", type=float, default=THRESH)
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    CAMERA = args.camera.rstrip("/"); POLL = args.poll; MIN_GAP = args.min_gap; THRESH = args.thresh

    threading.Thread(target=stream_loop, daemon=True).start()
    print(f"Camera    : {CAMERA}/  (MJPEG stream, via requests)")
    print(f"Stillness : {'ON' if STILLNESS_OK else 'OFF (pip install pillow numpy)'}  thresh {THRESH}")
    print(f"Dataset   : {DATASET}")
    print(f"Open      : http://localhost:{args.port}\n")
    ThreadingHTTPServer(("0.0.0.0", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
