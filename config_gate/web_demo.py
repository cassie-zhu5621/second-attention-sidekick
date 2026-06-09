"""
web_demo.py — the user-facing FEED (the calm, legible, re-writable surface).

A small local web page (stdlib http.server, no extra deps) that runs the SAME pipeline as
live_demo but presents it as a product:
  - LEFT : the live annotated video stream (perceive -> gate overlay, MJPEG)
  - RIGHT: a scrolling FEED of noticed moments — thumbnail + field note + WHY + worth + time
  - BOTTOM: a taste box — type "more people" / "I care about the robotics corner" to re-write
            what it notices, in real time (the see = teach loop); current axis weights shown.

Run (open http://localhost:8000):
    python web_demo.py --webcam 0                                   # laptop webcam
    python web_demo.py --camera http://sidekick-cam.local           # the M5 rig cam
    python web_demo.py --video clip.mp4
Add --judge (needs ANTHROPIC_API_KEY) to run the VLM for real (do this at the lab).
Without --judge / with SECONDATTN_OFFLINE=1 it still runs (fake notes) so the whole flow works.
"""

from __future__ import annotations
import argparse, json, os, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import cv2
import numpy as np
from perceive import build_graph, YoloWorldDetector, StaticLatch
from config_surprise import ConfigSurpriseGate, TemporalConfigGate
from judge import judge as run_judge, ReportabilityTaste, AXES
from viz import draw_overlay

STATE = {"jpg": None, "feed": [], "taste": ReportabilityTaste(), "thumbs": {}}
LOCK = threading.Lock()
ARGS = None

PAGE = """<!doctype html><html><head><meta charset=utf-8><title>second attention</title>
<style>
 body{margin:0;background:#0e0f12;color:#e8e8ea;font-family:ui-sans-serif,system-ui,sans-serif}
 .wrap{display:flex;gap:14px;padding:14px;box-sizing:border-box;height:calc(100vh - 28px)}
 .left{flex:2;min-width:0;display:flex;flex-direction:column;gap:10px}
 .right{flex:1;min-width:300px;display:flex;flex-direction:column}
 img#v{width:100%;border:1px solid #2a2d33;border-radius:10px;background:#000}
 h3{margin:4px 2px;font-size:13px;color:#9aa0a8;font-weight:600;letter-spacing:.04em}
 .feed{flex:1;overflow:auto;display:flex;flex-direction:column;gap:10px;padding-right:4px}
 .card{display:flex;gap:10px;background:#16181d;border:1px solid #2a2d33;border-radius:10px;padding:8px}
 .card img{width:96px;height:72px;object-fit:cover;border-radius:6px;flex:none;background:#000}
 .note{font-size:13.5px;line-height:1.4}
 .meta{font-size:11px;color:#8a909a;margin-top:3px}
 .why{color:#00d0d0}
 .worth{color:#37ff8b;font-weight:700}
 .taste{margin-top:10px;border-top:1px solid #2a2d33;padding-top:10px}
 input{width:100%;box-sizing:border-box;background:#16181d;border:1px solid #2a2d33;color:#e8e8ea;
   border-radius:8px;padding:9px 11px;font-size:14px}
 .axes{font-size:11.5px;color:#9aa0a8;margin-top:8px;display:flex;flex-wrap:wrap;gap:8px}
 .axes b{color:#e8e8ea}
</style></head><body>
<div class=wrap>
 <div class=left>
   <h3>LIVE — what it perceives & decides</h3>
   <img id=v src="/stream.mjpg">
 </div>
 <div class=right>
   <h3>NOTICED — the feed</h3>
   <div class=feed id=feed></div>
   <div class=taste>
     <h3>YOUR TASTE — type to re-shape what it notices</h3>
     <input id=t placeholder='e.g. "more people"  /  "I care about the robotics corner"'>
     <div class=axes id=axes></div>
   </div>
 </div>
</div>
<script>
async function poll(){
  try{
    let f=await (await fetch('/feed.json')).json();
    document.getElementById('feed').innerHTML=f.map(m=>`<div class=card>
      <img src="/thumb/${m.thumb}">
      <div><div class=note>${m.note||''}</div>
      <div class=meta><span class=worth>worth ${m.worth}</span> · <span class=why>${m.why}</span> · ${m.time}</div></div>
    </div>`).join('');
    let t=await (await fetch('/taste.json')).json();
    document.getElementById('axes').innerHTML=Object.entries(t.weights).map(
      ([k,v])=>`<span><b>${k}</b> ${v.toFixed(1)}</span>`).join('') +
      (t.about?` · about: <b>${t.about}</b>`:'');
  }catch(e){}
}
document.getElementById('t').addEventListener('keydown',async e=>{
  if(e.key==='Enter'&&e.target.value.trim()){
    await fetch('/taste',{method:'POST',body:e.target.value});
    e.target.value=''; poll();
  }
});
setInterval(poll,1500); poll();
</script></body></html>"""


def pipeline():
    """Background: camera -> perceive -> gate -> (async) judge -> overlay; updates STATE."""
    a = ARGS
    det = YoloWorldDetector([v.strip() for v in a.vocab.split(",")], conf=a.conf)
    gate = TemporalConfigGate(gate=ConfigSurpriseGate(mode="habituation", agg="max",
                                                      threshold=a.threshold))
    os.makedirs(a.feed_dir, exist_ok=True)
    latch = StaticLatch()                    # immovable objects stay put (no flicker events)
    depth_model = None
    if a.depth:
        from depth import DepthAnything
        depth_model = DepthAnything()
        print("[depth] on (note: measured ~no benefit on the lab data + halves fps)")
    judging = [False]; last_t = [0.0]; prev_gray = [None]

    def src():
        if a.video:
            cap = cv2.VideoCapture(a.video)
            while cap.isOpened():
                ok, fr = cap.read()
                if not ok: break
                yield fr
            cap.release()
        else:
            latest = [None]
            def reader():
                if a.camera:
                    import requests
                    s = requests.Session(); s.trust_env = False
                    with s.get(a.camera.rstrip("/") + "/", stream=True, timeout=(5, 15)) as r:
                        buf = b""
                        for ch in r.iter_content(8192):
                            buf += ch
                            i = buf.find(b"\xff\xd8"); j = buf.find(b"\xff\xd9", i + 2) if i != -1 else -1
                            if i != -1 and j != -1:
                                latest[0] = cv2.imdecode(np.frombuffer(buf[i:j+2], np.uint8), 1); buf = buf[j+2:]
                else:
                    cap = cv2.VideoCapture(a.webcam)
                    while cap.isOpened():
                        ok, fr = cap.read()
                        if ok: latest[0] = fr
            threading.Thread(target=reader, daemon=True).start()
            seen = [None]
            while True:
                if latest[0] is None or latest[0] is seen[0]:
                    time.sleep(0.02); continue
                seen[0] = latest[0]; yield latest[0]

    for fr in src():
        H, W = fr.shape[:2]
        gray = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
        changed = True
        if prev_gray[0] is not None and prev_gray[0].shape == gray.shape:
            changed = cv2.absdiff(gray, prev_gray[0]).mean() > a.change_thr
        prev_gray[0] = gray
        dmap = depth_model.predict(fr) if depth_model is not None else None
        g = build_graph(latch.apply(det.detect(fr), (W, H)), (W, H), min_area_frac=a.min_area, depth_map=dmap)
        dec = gate.step(*g.as_gate_input())
        event = bool(dec["event"] and changed)
        st = {"settled": True, "changed": changed, "event": event}
        with LOCK:
            taste = STATE["taste"]
        # on a fresh event (throttled by cooldown) record a moment to the feed.
        if event and not judging[0] and time.time() - last_t[0] > a.cooldown:
            last_t[0] = time.time()
            ts = time.strftime("%H:%M:%S"); fid = time.strftime("%Y%m%d_%H%M%S")
            thumb = f"thumb_{fid}.jpg"; full = f"frame_{fid}.jpg"
            cv2.imwrite(os.path.join(a.feed_dir, thumb), cv2.resize(fr, (192, max(1, int(192 * H / W)))))
            cv2.imwrite(os.path.join(a.feed_dir, full), fr)        # full-resolution record
            delta = TemporalConfigGate.describe(dec["delta_added"], dec["top"],
                                                dec.get("left"), dec.get("arrived"))

            def add(worth, why, note):
                rec = {"time": ts, "worth": worth, "why": why, "note": note,
                       "thumb": thumb, "frame": full}
                with LOCK:
                    STATE["feed"].append(rec); STATE["feed"] = STATE["feed"][-60:]
                with open(os.path.join(a.feed_dir, "noticed_log.jsonl"), "a") as fh:  # persistent record
                    fh.write(json.dumps(rec) + "\n")

            if a.judge:                                   # VLM codifies (async, video stays smooth)
                judging[0] = True
                ok, jpg = cv2.imencode(".jpg", fr); snap = jpg.tobytes()
                def _job(snap=snap, graph=g, d=dec["delta_added"]):
                    try:
                        r = run_judge(snap, graph, taste, delta_added=d)
                        add(round(r["worth"], 2), r["why"], r["note"])
                    finally:
                        judging[0] = False
                threading.Thread(target=_job, daemon=True).start()
            else:                                         # no VLM yet: show the structural moment
                add(dec.get("change", round(dec["score"], 2)), "structural", delta)
        out = draw_overlay(fr, g, st, caption=f"{len(g.nodes)} obj, {len(g.edges)} rel")
        ok, jpg = cv2.imencode(".jpg", out)
        STATE["jpg"] = jpg.tobytes()


class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_GET(self):
        p = self.path.split("?")[0]
        if p == "/":
            self._send(200, "text/html", PAGE.encode())
        elif p == "/stream.mjpg":
            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
            self.end_headers()
            try:
                while True:
                    jpg = STATE["jpg"]
                    if jpg:
                        self.wfile.write(b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg + b"\r\n")
                    time.sleep(0.05)
            except Exception:
                pass
        elif p == "/feed.json":
            with LOCK:
                data = list(reversed(STATE["feed"]))
            self._send(200, "application/json", json.dumps(data).encode())
        elif p == "/taste.json":
            with LOCK:
                t = STATE["taste"]
                data = {"weights": t.weights, "about": t.about}
            self._send(200, "application/json", json.dumps(data).encode())
        elif p.startswith("/thumb/"):
            name = os.path.basename(p[7:])
            mem = STATE.get("thumbs", {}).get(name)               # in-memory (test/--no-save) first
            if mem is not None:
                self._send(200, "image/jpeg", mem)
            else:
                fn = os.path.join(ARGS.feed_dir, name)
                if os.path.exists(fn):
                    self._send(200, "image/jpeg", open(fn, "rb").read())
                else:
                    self._send(404, "text/plain", b"")
        else:
            self._send(404, "text/plain", b"")

    def do_POST(self):
        if self.path == "/taste":
            n = int(self.headers.get("Content-Length", 0))
            sentence = self.rfile.read(n).decode("utf-8", "ignore")
            with LOCK:
                STATE["taste"].nudge(sentence)
                data = {"weights": STATE["taste"].weights, "about": STATE["taste"].about}
            self._send(200, "application/json", json.dumps(data).encode())
        else:
            self._send(404, "text/plain", b"")

    def _send(self, code, ctype, body):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except Exception:
            pass


def main():
    global ARGS
    ap = argparse.ArgumentParser()
    s = ap.add_mutually_exclusive_group(required=True)
    s.add_argument("--webcam", type=int); s.add_argument("--camera"); s.add_argument("--video")
    ap.add_argument("--vocab", default=("person,laptop,monitor,keyboard,cup,bottle,chair,desk,"
                                        "book,bag,phone,potted plant,bookshelf"))
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--min-area", type=float, default=0.0)
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--change-thr", type=float, default=2.0)
    ap.add_argument("--cooldown", type=float, default=6.0)
    ap.add_argument("--judge", action="store_true")
    ap.add_argument("--depth", action="store_true",
                    help="monocular depth gating (optional; measured ~no benefit + halves fps)")
    ap.add_argument("--feed-dir", default="feed")
    ap.add_argument("--port", type=int, default=8000)
    ARGS = ap.parse_args()

    threading.Thread(target=pipeline, daemon=True).start()
    print(f"open  http://localhost:{ARGS.port}   (Ctrl-C to stop)")
    ThreadingHTTPServer(("", ARGS.port), H).serve_forever()


if __name__ == "__main__":
    main()
