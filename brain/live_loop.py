"""
live_loop.py — search / notice / dwell, judged by the 9-dimension COMPOSER, with
a web control panel. Language (voice or panel) shapes the taste WEIGHTS.

worth = taste.compose(dims, weights)  where dims are scored live on taste.py's 9
theory-anchored dimensions (Berlyne novelty/complexity/conflict/surprise; Kaplan
coherence/mystery; craft aesthetic/decisive_moment; story_potential). A spoken/typed
sentence ("more story, less clutter") nudges those weights (session.py-style), so you
shape WHAT KIND of moment counts as worth-noticing — not which object to find.

States: SEARCH (worth low -> scan) / DWELL (worth>=thresh -> stop, capture, stay
until cooldown or worth drops below `lost`). Panel: http://localhost:8090

Prereqs: R4 on USB (optional — runs camera+panel only without it), camera streaming,
pip install pyserial requests anthropic, export ANTHROPIC_API_KEY=sk-...
Run: python3 live_loop.py --camera http://sidekick-loop.local
"""

import argparse
import glob
import json
import os
import re
import threading
import time
from collections import deque
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import requests
import serial

import taste
from taste import DIM_NAMES
from live_brain import score_dims_live, caption

WEBHOOK = os.environ.get("SIDEKICK_WEBHOOK", "")   # Discord webhook URL (set via env or --webhook)

PAN_STEPS  = [-60, -40, -20, 0, 20, 40, 60]
TILT_STEPS = [-25, 0, 25]
COOLOFF    = 5          # after a dwell, this many search points can't re-lock (wander away first)
LR = 0.4
OUT     = Path(__file__).parent / "live_captures"
PREF    = Path(__file__).parent / "preference.txt"
PROFILE = Path(__file__).parent / "taste_profile_lab.json"

# language -> dimension keywords (mapped onto taste.py's 9 dims)
KEYWORDS = {
    "novelty":         ["new", "novel", "unusual", "unexpected", "different", "weird", "strange"],
    "complexity":      ["complex", "busy", "detailed", "rich", "layered", "texture", "intricate"],
    "conflict":        ["conflict", "tension", "contrast", "clash", "messy", "clutter", "cluttered", "chaos", "dramatic"],
    "surprise":        ["surprise", "surprising", "unexpected", "sudden", "shock", "incongruous"],
    "coherence":       ["coherent", "clean", "organized", "ordered", "simple", "tidy", "calm", "minimal"],
    "mystery":         ["mystery", "mysterious", "hidden", "intriguing", "curious", "depth"],
    "aesthetic":       ["beautiful", "pretty", "aesthetic", "gorgeous", "elegant", "light", "color", "colour", "composition"],
    "decisive_moment": ["moment", "action", "gesture", "happening", "peak", "decisive", "movement", "doing", "caught"],
    "story_potential": ["story", "people", "someone", "person", "human", "social", "conversation", "relationship", "together", "life"],
}
POS = ["love", "like", "more", "want", "prefer", "care", "focus", "emphasize", "good"]
NEG = ["no", "not", "less", "stop", "hate", "boring", "ignore", "avoid", "without", "don't", "dont"]

weights = taste.default_weights()
STATE = {
    "online": False, "mode": "idle", "worth": 0.0, "reason": "",
    "preference": "", "pan": 0, "tilt": 0, "noticed": 0, "held": 0.0,
    "event_id": 0, "event": "", "log": [],
    "thresh": 0.55, "lost": 0.4, "cooldown": 60.0, "settle": 0.6,
    "dims": {d: 0.0 for d in DIM_NAMES}, "weights": dict(weights),
    "content": "", "match": 0.0, "caption": "",
}
# words that signal "tune a dimension" vs "this is a content/object to look for"
DIRECTION = {"more", "less", "no", "not", "care", "focus", "emphasize",
             "love", "like", "want", "prefer", "avoid", "without", "stop"}
CAM = None
RECENT = deque(maxlen=12)   # (id, jpeg bytes) — recent captures for the panel thumbnail strip
_thumb_n = 0


def clamp(x):
    return max(-1.0, min(2.0, x))


def parse_sentence(u):
    """Per-dimension up/down: a dim goes down if a NEG word ('less','no','not'...) precedes
    its keyword, else up. So 'more story, less clutter' -> story +, conflict -."""
    tokens = re.findall(r"[a-z']+", u.lower())
    delta = {}
    for i, tok in enumerate(tokens):
        for d in DIM_NAMES:
            if tok in KEYWORDS[d]:
                val = 1.0                                  # nearest preceding direction word wins
                for w in reversed(tokens[max(0, i - 4):i]):
                    if w in NEG: val = -1.0; break
                    if w in POS: val = 1.0; break
                delta[d] = val
    return delta


def why(dims):
    return ", ".join(d for _, d in sorted(((weights[d] * dims.get(d, 0.0), d) for d in DIM_NAMES),
                                          reverse=True)[:2])


def emit(kind, msg):
    STATE["event_id"] += 1; STATE["event"] = kind
    STATE["log"] = ([f"{datetime.now():%H:%M:%S}  {msg}"] + STATE["log"])[:30]


def post_online(jpeg, text):
    """Send the noticed frame + its one-line report to the online feed (Discord webhook)."""
    if not WEBHOOK:
        return
    def _send():
        try:
            requests.post(WEBHOOK,
                          data={"content": text, "username": "potato \U0001F954"},  # display name
                          files={"file": ("notice.jpg", jpeg, "image/jpeg")}, timeout=15)
        except Exception as e:
            print(f"[post] {e}")
    threading.Thread(target=_send, daemon=True).start()


def evaluate(jpeg):
    """worth = 9-dim composer, blended with content-match when a content lean is set."""
    content = STATE["content"]
    dims, match = score_dims_live(jpeg, content)
    base = taste.compose(dims, weights)
    worth = (0.5 * base + 0.5 * match) if content else base
    reason = f'{content} ({match:.2f})' if (content and match >= base) else why(dims)
    return dims, match, worth, reason


def save_profile():
    try: PROFILE.write_text(json.dumps(weights, indent=2))
    except Exception: pass


_last_say = {"v": None}
def apply_taste_if_changed():
    """A new sentence from voice/panel either TUNES dimension weights (has a direction
    word like more/less + a dimension keyword) or sets the CONTENT to look for."""
    try: s = PREF.read_text().strip()
    except Exception: s = ""
    if s == _last_say["v"]:
        return
    _last_say["v"] = s
    STATE["preference"] = s
    if not s:
        return
    toks = set(re.findall(r"[a-z']+", s.lower()))
    delta = parse_sentence(s)
    if delta and (toks & DIRECTION):                 # "more story, less clutter" -> weights
        for d, dv in delta.items():
            weights[d] = clamp(weights[d] + LR * dv)
        STATE["weights"] = dict(weights)
        save_profile()
        emit("notice", f'taste: "{s}" -> {delta}')
    elif s.lower() in {"anything", "reset", "clear", "nothing", "none",
                        "anything worth noticing", "stop looking", "everything"}:
        STATE["content"] = ""                        # back to pure 9-dim noticing
        emit("notice", "content cleared — pure noticing")
    else:                                            # "animals", "photos", "people working" -> content
        STATE["content"] = s
        emit("notice", f'looking for: "{s}"')


class StreamReader:
    def __init__(self, url):
        self.url = url.rstrip("/") + "/"; self.latest = None
        threading.Thread(target=self._loop, daemon=True).start()
    def _loop(self):
        s = requests.Session(); s.trust_env = False
        while True:
            try:
                with s.get(self.url, stream=True, timeout=(5, 15)) as r:
                    buf = b""
                    for chunk in r.iter_content(8192):
                        buf += chunk
                        while True:
                            a = buf.find(b"\xff\xd8"); b = buf.find(b"\xff\xd9", a + 2) if a != -1 else -1
                            if a == -1 or b == -1: break
                            self.latest = buf[a:b + 2]; buf = buf[b + 2:]
                        if len(buf) > 2_000_000: buf = buf[-200_000:]
            except Exception:
                time.sleep(2)
    def grab(self):
        return self.latest


def find_port():
    for pat in ("/dev/tty.usbmodem*", "/dev/tty.usbserial*", "/dev/ttyACM*"):
        hits = sorted(glob.glob(pat))
        if hits: return hits[0]
    return None


def scan_path():
    wps = []
    for ti, t in enumerate(TILT_STEPS):
        for p in (PAN_STEPS if ti % 2 == 0 else list(reversed(PAN_STEPS))):
            wps.append((p, t))
    return wps


PAGE = r"""<!doctype html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>SECOND ATTENTION // CONTROL</title>
<style>
:root{--bg:#0a0b0a;--line:#23271f;--fg:#f3f5ef;--dim:#7c8175;--acid:#c8ff32}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font-family:"DejaVu Sans Mono",ui-monospace,Menlo,monospace}
header{display:flex;align-items:center;gap:12px;padding:12px 16px;border-bottom:1px solid var(--line)}
.logo{font-weight:700;letter-spacing:.14em;font-size:13px}.logo b{color:var(--acid)}.sp{flex:1}.dim{color:var(--dim)}.acid{color:var(--acid)}
input,button{font:inherit}
input[type=text]{background:#000;border:1px solid var(--line);color:var(--fg);padding:7px 9px;font-size:12px;width:230px;border-radius:2px}
button{background:var(--acid);color:#0a0b0a;border:0;padding:7px 12px;font-weight:700;font-size:12px;border-radius:2px;cursor:pointer}
button.ghost{background:transparent;color:var(--fg);border:1px solid var(--line)}
main{display:grid;grid-template-columns:380px 1fr;min-height:calc(100vh - 53px)}
.left{border-right:1px solid var(--line);padding:16px}
.frame{width:100%;aspect-ratio:4/3;background:#000;border:1px solid var(--line);object-fit:cover;display:block}
.badge{margin-top:12px;font-size:22px;font-weight:700;letter-spacing:.08em}
.bar{height:10px;background:#000;border:1px solid var(--line);margin-top:6px;border-radius:6px;overflow:hidden}
.bar i{display:block;height:100%;background:var(--acid);width:0}
.kv{font-size:12px;color:var(--dim);margin-top:8px}.kv b{color:var(--fg)}
.right{padding:16px}h2{font-size:11px;letter-spacing:.16em;color:var(--dim);margin:18px 0 10px}h2:first-child{margin-top:0}
.ctl{margin:0 0 14px}.ctl label{font-size:12px;color:var(--dim)}.ctl .v{color:var(--acid);font-weight:700}
input[type=range]{width:100%;accent-color:var(--acid)}
.dimrow{display:grid;grid-template-columns:130px 1fr 52px;align-items:center;gap:8px;font-size:11px;margin:3px 0}
.dimrow .nm{color:var(--dim)}.dimrow .w{text-align:right}
.dbar{height:8px;background:#000;border:1px solid var(--line);border-radius:5px;overflow:hidden}
.dbar i{display:block;height:100%;background:var(--acid)}
.log{margin-top:8px;font-size:11px;color:var(--dim);line-height:1.7;max-height:24vh;overflow:auto}.log div:first-child{color:var(--acid)}
.thumbs{display:flex;gap:4px;flex-wrap:wrap;margin-top:12px}
.thumbs img{width:56px;height:42px;object-fit:cover;border:1px solid var(--line);border-radius:3px}
.thumbs img:first-child{border-color:var(--acid)}
</style></head><body>
<header><div class="logo" style="font-size:22px;letter-spacing:0">🥔</div>
 <input id=say type=text placeholder="shape its taste: 'more story, less clutter'"><button id=setbtn>SET</button>
 <div class=sp></div><span class=dim>NOTICED <b id=noticed class=acid>0</b></span><button id=snd class=ghost>SOUND ON</button></header>
<main>
 <section class=left>
  <img id=frame class=frame>
  <div class=badge id=badge>—</div>
  <div class=bar><i id=worthbar></i></div>
  <div class=kv>worth <b id=worth>0.00</b> &middot; <span id=reason></span></div>
  <div class=kv>aim <b id=pan>0</b>,<b id=tilt>0</b> &middot; dwell <b id=held>0</b>s</div>
  <div class=kv>looking for <b id=content class=acid>—</b> &middot; match <b id=match>0.00</b></div>
  <div class=kv style="margin-top:14px">recent captures</div>
  <div class=thumbs id=thumbs></div>
 </section>
 <section class=right>
  <h2>TUNING (live)</h2>
  <div class=ctl><label>notice threshold <span class=v id=tv>0.55</span></label><input type=range id=thresh min=0 max=1 step=0.01></div>
  <div class=ctl><label>cooldown / dwell <span class=v id=cv>60</span>s</label><input type=range id=cooldown min=5 max=180 step=5></div>
  <div class=ctl><label>lost threshold <span class=v id=lv>0.40</span></label><input type=range id=lost min=0 max=1 step=0.01></div>
  <h2>DIMENSIONS (score &middot; weight)</h2>
  <div id=dims></div>
  <h2>EVENTS</h2>
  <div class=log id=log></div>
 </section>
</main>
<script>
const $=s=>document.querySelector(s);let soundOn=true,lastEvent=0,ac=null,sliderFocus=false,timer=null;
function tone(seq){if(!soundOn)return;ac=ac||new(window.AudioContext||window.webkitAudioContext)();let t=ac.currentTime;
 for(const[f,d]of seq){const o=ac.createOscillator(),g=ac.createGain();o.frequency.value=f;o.type="sine";o.connect(g);g.connect(ac.destination);
 g.gain.setValueAtTime(0.0001,t);g.gain.exponentialRampToValueAtTime(0.25,t+0.02);g.gain.exponentialRampToValueAtTime(0.0001,t+d);o.start(t);o.stop(t+d);t+=d;}}
const SFX={notice:[[660,.12],[990,.18]],bored:[[520,.14],[330,.2]],left:[[300,.1],[240,.12]],start:[[880,.08]]};
function play(k){tone(SFX[k]||SFX.notice);}
function setp(k,v){fetch("/set?"+k+"="+encodeURIComponent(v));}
function bindS(id,key,fmt){const e=$("#"+id);e.addEventListener("input",()=>{$("#"+({thresh:'tv',cooldown:'cv',lost:'lv'})[id]).textContent=fmt(e.value);clearTimeout(timer);timer=setTimeout(()=>setp(key,e.value),150);});}
bindS("thresh","thresh",v=>(+v).toFixed(2));bindS("cooldown","cooldown",v=>Math.round(v));bindS("lost","lost",v=>(+v).toFixed(2));
$("#setbtn").onclick=()=>{const v=$("#say").value.trim();if(v){setp("preference",v);$("#say").value="";}};
$("#say").addEventListener("keydown",e=>{if(e.key==="Enter")$("#setbtn").click();});
$("#snd").onclick=()=>{soundOn=!soundOn;$("#snd").textContent=soundOn?"SOUND ON":"SOUND OFF";$("#snd").style.color=soundOn?"":"var(--acid)";if(soundOn)play("start");};
document.querySelectorAll("input[type=range]").forEach(e=>{e.addEventListener("focus",()=>sliderFocus=true);e.addEventListener("blur",()=>sliderFocus=false);});
function dimRows(dims,w){return Object.keys(dims).map(d=>{const sc=dims[d]||0,wt=(w[d]==null?1:w[d]);
 const col=wt>1.05?'var(--acid)':(wt<0.95?'#ff6b6b':'var(--dim)');
 return `<div class=dimrow><span class=nm>${d}</span><span class=dbar><i style="width:${(sc*100)|0}%"></i></span><span class=w style="color:${col}">${wt.toFixed(2)}</span></div>`;}).join("");}
async function tick(){try{const s=await(await fetch("/state",{cache:"no-store"})).json();
 $("#badge").textContent=s.mode.toUpperCase();$("#badge").style.color=s.mode==="dwell"?"var(--acid)":(s.mode==="search"?"var(--fg)":"var(--dim)");
 $("#worth").textContent=s.worth.toFixed(2);$("#worthbar").style.width=(s.worth*100)+"%";$("#reason").textContent=s.reason;
 $("#pan").textContent=s.pan;$("#tilt").textContent=s.tilt;$("#held").textContent=Math.round(s.held);$("#noticed").textContent=s.noticed;
 $("#content").textContent=s.content||"—";$("#match").textContent=(s.match||0).toFixed(2);
 if(document.activeElement!==$("#say")&&!$("#say").value)$("#say").placeholder=s.preference?("taste: "+s.preference):"shape its taste: 'more story, less clutter'";
 if(!sliderFocus){$("#thresh").value=s.thresh;$("#tv").textContent=(+s.thresh).toFixed(2);$("#cooldown").value=s.cooldown;$("#cv").textContent=Math.round(s.cooldown);$("#lost").value=s.lost;$("#lv").textContent=(+s.lost).toFixed(2);}
 $("#dims").innerHTML=dimRows(s.dims,s.weights);
 $("#frame").src="/frame?t="+Date.now();
 if(s.event_id!==lastEvent){lastEvent=s.event_id;if(s.event)play(s.event);$("#log").innerHTML=s.log.map(l=>"<div>"+l+"</div>").join("");}
 try{const th=await(await fetch("/thumbs",{cache:"no-store"})).json();
  $("#thumbs").innerHTML=th.map(i=>'<img src="/thumb?id='+i+'">').join("");}catch(e){}
}catch(e){}}
setInterval(tick,1000);tick();
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, ctype, body=b""):
        if isinstance(body, str): body = body.encode()
        self.send_response(code); self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store"); self.end_headers()
        if body: self.wfile.write(body)
    def do_GET(self):
        u = urlparse(self.path); p = u.path; q = parse_qs(u.query)
        if p == "/":
            self._send(200, "text/html; charset=utf-8", PAGE)
        elif p == "/state":
            self._send(200, "application/json", json.dumps(STATE))
        elif p == "/frame":
            f = CAM.grab() if CAM else None
            self._send(200, "image/jpeg", f) if f else self._send(503, "text/plain", "no frame")
        elif p == "/thumbs":
            self._send(200, "application/json", json.dumps([i for i, _ in RECENT][::-1]))  # newest first
        elif p == "/thumb":
            i = int((q.get("id", ["0"])[0]) or 0)
            b = next((b for tid, b in RECENT if tid == i), None)
            self._send(200, "image/jpeg", b) if b else self._send(404, "text/plain", "gone")
        elif p == "/set":
            for k in ("thresh", "lost", "cooldown", "settle"):
                if k in q:
                    try: STATE[k] = float(q[k][0])
                    except ValueError: pass
            if "preference" in q:                      # a taste sentence (voice/panel share preference.txt)
                v = q["preference"][0].strip()
                if v:
                    PREF.write_text(v)                 # picked up by apply_taste_if_changed()
            self._send(200, "application/json", "{\"ok\":true}")
        else:
            self._send(404, "text/plain", "?")
    def log_message(self, *a):
        pass


def main():
    global CAM, WEBHOOK
    ap = argparse.ArgumentParser()
    ap.add_argument("--camera", default="http://sidekick-loop.local")
    ap.add_argument("--port", default=None)
    ap.add_argument("--webhook", default=WEBHOOK, help="online feed URL (Discord webhook); posts noticed frame + report")
    ap.add_argument("--thresh", type=float, default=0.55)
    ap.add_argument("--lost", type=float, default=0.4)
    ap.add_argument("--cooldown", type=float, default=60.0)
    ap.add_argument("--settle", type=float, default=0.6)
    ap.add_argument("--web-port", type=int, default=8090)
    args = ap.parse_args()
    WEBHOOK = args.webhook or ""

    # Layer 3: load this place's learned taste if it exists
    if PROFILE.exists():
        try:
            saved = json.loads(PROFILE.read_text())
            for d in DIM_NAMES:
                weights[d] = saved.get(d, weights[d])
        except Exception: pass
    STATE.update(thresh=args.thresh, lost=args.lost, cooldown=args.cooldown,
                 settle=args.settle, weights=dict(weights))
    try: _last_say["v"] = PREF.read_text().strip()     # don't re-apply an existing sentence on boot
    except Exception: pass

    port = args.port or find_port()
    ser = None
    if port:
        ser = serial.Serial(port, 115200, timeout=1); time.sleep(2)
    else:
        print("No R4 serial port — running camera + panel only (no movement).")
    CAM = StreamReader(args.camera); OUT.mkdir(exist_ok=True)

    threading.Thread(target=lambda: ThreadingHTTPServer(("0.0.0.0", args.web_port), Handler).serve_forever(),
                     daemon=True).start()
    print(f"cam {args.camera} | CONTROL PANEL: http://localhost:{args.web_port}")
    while CAM.grab() is None:
        time.sleep(0.2)
    STATE["online"] = True
    print("streaming. (Ctrl+C to stop)\n")

    def ensure_serial():
        nonlocal ser
        if ser is not None:
            return
        p = args.port or find_port()
        if not p:
            return
        try:
            ser = serial.Serial(p, 115200, timeout=1); time.sleep(2)
            print(f"[serial] (re)connected on {p}")
        except Exception:
            ser = None

    def move(p, t):
        nonlocal ser
        if ser is None:
            ensure_serial()
        if ser is None:
            return
        try:
            ser.write(f"{p},{t}\n".encode())
        except Exception as e:
            print(f"[serial] lost R4 ({e}) — retrying; check USB cable / servo 5V power")
            try: ser.close()
            except Exception: pass
            ser = None

    def capture(jpeg, worth):
        global _thumb_n
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        (OUT / f"cap_{ts}_{worth:0.2f}.jpg").write_bytes(jpeg)
        _thumb_n += 1
        RECENT.append((_thumb_n, jpeg))   # feed the panel thumbnail strip

    path = scan_path(); idx = 0; cooloff = 0
    try:
        while True:
            apply_taste_if_changed()
            p, t = path[idx]; STATE["pan"], STATE["tilt"] = p, t; STATE["mode"] = "search"
            move(p, t); time.sleep(STATE["settle"] + 0.3)
            jpeg = CAM.grab()
            if not jpeg:
                idx = (idx + 1) % len(path); continue
            dims, match, worth, reason = evaluate(jpeg)
            STATE["dims"], STATE["match"], STATE["worth"], STATE["reason"], STATE["held"] = dims, match, worth, reason, 0
            print(f"search {p:+4d},{t:+4d}  worth={worth:0.2f}  ({reason})")
            if cooloff > 0:                 # refractory: just moved on — wander, don't re-lock yet
                cooloff -= 1
                idx = (idx + 1) % len(path); continue
            if worth < STATE["thresh"]:
                idx = (idx + 1) % len(path); continue

            STATE["mode"] = "dwell"; STATE["noticed"] += 1
            cap = caption(jpeg)                     # one-line report (extra haiku call, only on notice)
            STATE["caption"] = cap
            emit("notice", f"noticed ({worth:.2f}) — {cap}")
            print(f"  NOTICE ({worth:.2f}) — {cap}")
            capture(jpeg, worth)                    # local copy in live_captures/ (separate from dataset/)
            post_online(jpeg, f"\U0001F50D noticed ({worth:.2f}) — {cap}")   # -> online feed
            dwell_start = time.time(); lost = 0
            posted = 1; last_post = time.time()     # at most 3 images per discovery, spaced ~8s
            while True:
                apply_taste_if_changed()
                time.sleep(2.5)
                jpeg = CAM.grab()
                if jpeg:
                    dims, match, w, reason = evaluate(jpeg)
                    STATE["dims"], STATE["match"], STATE["reason"] = dims, match, reason
                else:
                    w = 0.0
                held = time.time() - dwell_start
                STATE["worth"], STATE["held"] = w, held
                if jpeg and w >= STATE["thresh"]:
                    capture(jpeg, w)              # keep capturing every 2.5s while still above threshold
                    if posted < 3 and time.time() - last_post >= 8:   # online: up to 3 per discovery
                        post_online(jpeg, f"\U0001F50D still — {cap}")
                        posted += 1; last_post = time.time()
                lost = lost + 1 if w < STATE["lost"] else 0
                if held >= STATE["cooldown"]:
                    emit("bored", "bored -> turning away"); print("  bored -> turn away\n")
                    idx = (idx + len(path) // 2) % len(path); cooloff = COOLOFF; break
                if lost >= 2:
                    emit("left", "subject left -> searching"); print("  subject left\n")
                    idx = (idx + len(path) // 2) % len(path); cooloff = COOLOFF; break
    except KeyboardInterrupt:
        print(f"\nstopped. noticed {STATE['noticed']} -> {OUT}")
        if ser:
            try: ser.write(b"off\n"); time.sleep(0.2); ser.close()   # relax servos immediately
            except Exception: pass
        save_profile()


if __name__ == "__main__":
    main()
