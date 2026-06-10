"""
attention_ui.py — web UI for the VLM-FIRST pipeline (attention_system.py).

The control surface follows the inverted architecture: the old web_demo's taste box
(tuning a back-end judge) is replaced by a CONTEXT box (driving the front-end planner):

  LEFT   : live annotated stream
  RIGHT  : THE PLAN — current context, the VLM's "why", and each watch entry with its
           LIVE state (satisfied / cooling / progress) — the legible, contestable part
  BELOW  : NOTICED feed (records), same as before
  BOTTOM : "Describe the scene" input -> POST /context -> the system re-plans next frame

Same STATE/LOCK/thumbs contract as web_demo, so attention_demo.publish() works unchanged.
"""

from __future__ import annotations
import json, os, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

STATE = {"jpg": None, "feed": [], "thumbs": {},
         "context": "", "why": "", "entries": [],      # [(expr, label)]
         "status": [],                                  # [(label, satisfied, cooling, detail)]
         "pending_context": None}
LOCK = threading.Lock()
ARGS = None

PAGE = """<!doctype html><html><head><meta charset=utf-8><title>attention system</title>
<style>
 body{margin:0;background:#0e0f12;color:#e8e8ea;font-family:ui-sans-serif,system-ui,sans-serif}
 .wrap{display:flex;gap:14px;padding:14px;box-sizing:border-box;height:calc(100vh - 28px)}
 .left{flex:2;min-width:0;display:flex;flex-direction:column;gap:10px}
 .right{flex:1;min-width:320px;display:flex;flex-direction:column;gap:10px}
 img#v{width:100%;border:1px solid #2a2d33;border-radius:10px;background:#000}
 h3{margin:4px 2px;font-size:13px;color:#9aa0a8;font-weight:600;letter-spacing:.04em}
 .plan{background:#16181d;border:1px solid #2a2d33;border-radius:10px;padding:10px}
 .ctx{font-size:13.5px;color:#e8e8ea}
 .why{font-size:12px;color:#00d0d0;margin-top:6px;font-style:italic}
 .entry{display:flex;gap:8px;align-items:baseline;margin-top:8px;font-size:13px}
 .dot{width:9px;height:9px;border-radius:50%;flex:none;background:#555}
 .dot.sat{background:#37ff8b}.dot.cool{background:#ff9b37}
 .expr{color:#c5a3ff;font-family:ui-monospace,monospace;font-size:12px}
 .detail{color:#8a909a;font-size:11px}
 .feed{flex:1;overflow:auto;display:flex;flex-direction:column;gap:10px;padding-right:4px}
 .card{display:flex;gap:10px;background:#16181d;border:1px solid #2a2d33;border-radius:10px;padding:8px}
 .card img{width:96px;height:72px;object-fit:cover;border-radius:6px;flex:none;background:#000}
 .note{font-size:13.5px;line-height:1.4}
 .meta{font-size:11px;color:#8a909a;margin-top:3px}
 input{width:100%;box-sizing:border-box;background:#16181d;border:1px solid #2a2d33;color:#e8e8ea;
   border-radius:8px;padding:9px 11px;font-size:14px}
</style></head><body>
<div class=wrap>
 <div class=left>
   <h3>LIVE</h3>
   <img id=v src="/stream.mjpg">
 </div>
 <div class=right>
   <h3>THE PLAN — what it watches for, and why</h3>
   <div class=plan id=plan></div>
   <h3>NOTICED — the feed</h3>
   <div class=feed id=feed></div>
   <div>
     <h3>DESCRIBE THE SCENE — it will re-plan</h3>
     <input id=c placeholder='e.g. "two of us are assembling a robot arm this afternoon"'>
   </div>
 </div>
</div>
<script>
async function poll(){
  try{
    let p=await (await fetch('/plan.json')).json();
    document.getElementById('plan').innerHTML =
      `<div class=ctx>${p.context||'(no context)'}</div>`+
      (p.why?`<div class=why>why: ${p.why}</div>`:'')+
      p.status.map(s=>`<div class=entry>
        <span class="dot ${s[1]?'sat':(s[2]?'cool':'')}"></span>
        <span>${s[0]}</span><span class=detail>${s[3]||''}</span></div>`).join('');
    let f=await (await fetch('/feed.json')).json();
    document.getElementById('feed').innerHTML=f.map(m=>`<div class=card>
      <img src="/thumb/${m.thumb}">
      <div><div class=note>${m.note||m.label||''}</div>
      <div class=meta>${m.label||''} · ${m.time}</div></div>
    </div>`).join('');
  }catch(e){}
}
document.getElementById('c').addEventListener('keydown',async e=>{
  if(e.key==='Enter'&&e.target.value.trim()){
    await fetch('/context',{method:'POST',body:e.target.value});
    e.target.value=''; setTimeout(poll,600);
  }
});
setInterval(poll,1200); poll();
</script></body></html>"""


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
        elif p == "/plan.json":
            with LOCK:
                data = {"context": STATE["context"], "why": STATE["why"],
                        "entries": STATE["entries"], "status": STATE["status"]}
            self._send(200, "application/json", json.dumps(data).encode())
        elif p == "/feed.json":
            with LOCK:
                data = list(reversed(STATE["feed"]))
            self._send(200, "application/json", json.dumps(data).encode())
        elif p.startswith("/thumb/"):
            name = os.path.basename(p[7:])
            mem = STATE["thumbs"].get(name)
            if mem is not None:
                self._send(200, "image/jpeg", mem)
            else:
                fn = os.path.join(ARGS.feed_dir, name) if ARGS else name
                if os.path.exists(fn):
                    self._send(200, "image/jpeg", open(fn, "rb").read())
                else:
                    self._send(404, "text/plain", b"")
        else:
            self._send(404, "text/plain", b"")

    def do_POST(self):
        if self.path == "/context":
            n = int(self.headers.get("Content-Length", 0))
            sentence = self.rfile.read(n).decode("utf-8", "ignore").strip()
            with LOCK:
                STATE["pending_context"] = sentence
            self._send(200, "application/json", b'{"ok": true}')
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


def serve(args):
    global ARGS
    ARGS = args
    srv = ThreadingHTTPServer(("", args.web_port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print(f"open  http://localhost:{args.web_port}   (live + plan + feed + context box)")
    import sys
    return sys.modules[__name__]
