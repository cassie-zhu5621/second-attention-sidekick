"""
robot_demo.py — first-version PAN-TILT sidekick. Movement is driven by, and tightly synced to,
the gate/VLM. One simple, legible logic:

    SCAN   : sweep the reachable pan/tilt grid; PAUSE (settle) at each spot and run the gate.
    LOOK   : when the gate FIRES (a structural change), orient to CENTRE the subject, then judge.
    REPORT : if worth >= theta, save the moment (+ optional 'nod' on a 3rd servo); dwell a beat.
    -> back to SCAN (the gate's habituation stops it re-looking at the same thing).

Contract: perception only runs after the head has SETTLED (no motion blur). The brain emits a
gaze STATE + target pose each tick; the rig just executes move_to(pan,tilt)+get_frame().
Swap MockRig for your real GimbalRig (rig.py). Shares perceive/gate/judge/viz with everything else.
"""

from __future__ import annotations
import argparse, json, os, threading, time
import cv2
import numpy as np
from perceive import build_graph, make_detector, StaticLatch, Detection
from config_surprise import ConfigSurpriseGate, TemporalConfigGate
from judge import judge as run_judge, ReportabilityTaste
from viz import draw_overlay

UI = None   # set to the web_demo module when --serve is on; lets run() push the live view + feed


def subject_box(g, subject_type):
    """Box of the node whose TYPE == the event subject (to centre the gaze on it)."""
    for nid, t in g.nodes.items():
        if t == subject_type and nid in g.boxes:
            return g.boxes[nid]
    return None


def orient_target(pan, tilt, box, wh, k_pan=0.06, k_tilt=0.06):
    """Proportional nudge so the subject's box centre moves toward the image centre.
    Uses the rig convention (+pan=right, +tilt=down): subject right-of-centre (cx>W/2) -> +pan;
    subject below centre (cy>H/2) -> +tilt. k_* are deg-per-pixel gains (tune to FOV)."""
    W, H = wh
    cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
    return pan + k_pan * (cx - W / 2), tilt + k_tilt * (cy - H / 2)


def run(rig, detector, taste, scan, args):
    # PER-GAZE-DIRECTION memory: a scanning camera sees a different scene at each pose, so each
    # pose keeps its OWN gate + static-latch. Revisiting a pose compares to THAT direction's
    # baseline -> habituation/change are meaningful, and these per-pose baselines ARE the
    # robot's spatial memory of the room ("what's normal at this heading").
    mem = {}  # (pan,tilt) -> (gate, latch)

    def memory_for(pos):
        if pos not in mem:
            # scanning -> each heading is sampled once per cycle, so use SMALL temporal windows
            mem[pos] = (TemporalConfigGate(gate=ConfigSurpriseGate(mode="habituation", agg="max",
                        threshold=args.threshold), persist=2, window=4, stable_frac=0.5),
                        StaticLatch())
        return mem[pos]

    if not getattr(args, "no_save", False):
        os.makedirs(args.feed_dir, exist_ok=True)
    i = 0
    while True:
        pan, tilt = scan[i % len(scan)]
        i += 1
        gate, latch = memory_for((round(pan), round(tilt)))
        rig.move_to(pan, tilt); time.sleep(args.settle)            # SCAN: go to the pose
        # DWELL & SAMPLE: watch this heading for a beat so the gate sees SEVERAL frames. A single
        # snapshot can't separate a real structural change from detector flicker; the temporal
        # gate needs a few consecutive frames at the same pose to confirm a stable change.
        fr = g = dec = None; n = 0
        t_end = time.time() + args.look_secs
        while time.time() < t_end:
            fr = rig.get_frame(); H, W = fr.shape[:2]; n += 1
            g = build_graph(latch.apply(detector.detect(fr), (W, H)), (W, H), min_area_frac=args.min_area)
            dec = gate.step(*g.as_gate_input())
            if UI is not None:                                     # live view updates during the dwell
                out = draw_overlay(fr, g, {"settled": True, "changed": True, "event": bool(dec["event"])},
                                   caption=f"pan {rig.pan:.0f} tilt {rig.tilt:.0f}  ·  "
                                           f"{len(g.nodes)} obj, {len(g.edges)} rel")
                UI.STATE["jpg"] = cv2.imencode(".jpg", out)[1].tobytes()
            if dec["event"]:
                break                                              # change confirmed -> stop dwelling, LOOK
        print(f"[SCAN] pan={pan:.0f} tilt={tilt:.0f}  {n}frames  "
              f"{len(g.nodes)}obj/{len(g.edges)}rel  event={int(dec['event'])}")
        st = {"settled": True, "changed": True, "event": bool(dec["event"])}

        if dec["event"]:                                           # LOOK: orient to the subject
            box = subject_box(g, dec["subject"])
            if box is not None:
                tp, tt = orient_target(pan, tilt, box, (W, H), args.k_pan, args.k_tilt)
                rig.move_to(tp, tt); time.sleep(args.settle)
                fr = rig.get_frame(); H, W = fr.shape[:2]
                g = build_graph(latch.apply(detector.detect(fr), (W, H)), (W, H), min_area_frac=args.min_area)
                print(f"[LOOK] -> centre on '{dec['subject']}'  pan={tp:.0f} tilt={tt:.0f}")
            r = run_judge(cv2.imencode('.jpg', fr)[1].tobytes(), g, taste, delta_added=dec["delta_added"])
            if r["worth"] >= args.worth:                           # REPORT
                ts = time.strftime("%H:%M:%S"); fid = time.strftime("%Y%m%d_%H%M%S")
                full = f"frame_{fid}.jpg"; thumb = f"thumb_{fid}.jpg"
                if not args.no_save:                               # test mode (--no-save): write nothing
                    cv2.imwrite(os.path.join(args.feed_dir, full), fr)
                    cv2.imwrite(os.path.join(args.feed_dir, thumb),
                                cv2.resize(fr, (192, max(1, int(192 * H / W)))))
                rec = {"time": ts, "worth": round(r["worth"], 2), "why": r["why"], "note": r["note"],
                       "thumb": thumb, "frame": full, "pan": round(rig.pan), "tilt": round(rig.tilt),
                       "subject": dec["subject"]}
                if not args.no_save:
                    with open(os.path.join(args.feed_dir, "noticed_log.jsonl"), "a") as fh:
                        fh.write(json.dumps(rec) + "\n")
                if UI is not None:                                 # push to the web feed (in-memory)
                    tjpg = cv2.imencode(".jpg", cv2.resize(fr, (192, max(1, int(192 * H / W)))))[1].tobytes()
                    with UI.LOCK:
                        UI.STATE["thumbs"][thumb] = tjpg
                        for old in list(UI.STATE["thumbs"])[:-60]:  # cap memory
                            UI.STATE["thumbs"].pop(old, None)
                        UI.STATE["feed"].append(rec); UI.STATE["feed"] = UI.STATE["feed"][-60:]
                print(f"[REPORT] worth={r['worth']:.2f} ({r['why']}) :: {r['note']}")
                if hasattr(rig, "nod"):
                    rig.nod()                                      # legible 'noticed' (tilt dip)
            time.sleep(args.dwell)                                 # DWELL, then resume SCAN

        if UI is not None:                                         # live view: current annotated frame
            out = draw_overlay(fr, g, st, caption=f"pan {rig.pan:.0f} tilt {rig.tilt:.0f}  ·  "
                                                  f"{len(g.nodes)} obj, {len(g.edges)} rel")
            ok, jpg = cv2.imencode(".jpg", out)
            UI.STATE["jpg"] = jpg.tobytes()


# ---------------------------------------------------------------------------
class MockRig:
    """Prints moves and returns scripted frames — to test the loop logic without hardware."""
    def __init__(self, frames): self.frames = frames; self.k = 0; self.pan = self.tilt = 0
    def move_to(self, pan, tilt): self.pan, self.tilt = pan, tilt
    def get_frame(self): fr = self.frames[self.k % len(self.frames)]; self.k += 1; return fr


class _ScriptDet:
    """Returns scripted detections per get_frame() call (paired with MockRig frames)."""
    def __init__(self, seq): self.seq = seq; self.k = 0
    def detect(self, img): d = self.seq[self.k % len(self.seq)]; self.k += 1; return d


def _run_real(args):
    """Drive the real pan-tilt rig + M5 camera through the SCAN->LOOK->REPORT->nod loop."""
    global UI
    from rig import GimbalRig, CAM_URL, SERIAL_PORT
    if args.offline:
        os.environ["SECONDATTN_OFFLINE"] = "1"        # dry run: skip the VLM (no API key needed)
    vocab = [v.strip() for v in args.vocab.split(",")]
    detector = make_detector(args.detector, vocab, conf=args.conf)
    taste = ReportabilityTaste()

    if args.serve:                                    # same web UI as web_demo: live view + feed + taste
        import web_demo
        from http.server import ThreadingHTTPServer
        web_demo.ARGS = args                          # handler reads ARGS.feed_dir for /thumb
        taste = web_demo.STATE["taste"]               # share so the taste box rewrites THIS taste live
        UI = web_demo
        if not args.no_save:
            os.makedirs(args.feed_dir, exist_ok=True)
        srv = ThreadingHTTPServer(("", args.web_port), web_demo.H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        print(f"open  http://localhost:{args.web_port}   (live view + feed)")

    # SCAN grid: a coarse pan sweep at two tilts (level + slightly down) so it catches both
    # standing people and seated people / desks. Each (pan,tilt) keeps its own per-pose memory.
    pans = [-50, -25, 0, 25, 50]
    scan = [(p, t) for t in (0, 8) for p in pans]
    rig = GimbalRig(cam_url=args.camera or CAM_URL, port=args.port or SERIAL_PORT)
    print(f"[rig] live. scanning {len(scan)} poses. Ctrl-C to stop.")
    try:
        run(rig, detector, taste, scan, args)
    except KeyboardInterrupt:
        print("\nstopping…")
    finally:
        rig.close()


def _run_mock():
    # Mock test (no hardware): scan 3 headings; from cycle 2 a person stands at pan=40.
    # Per-HEADING memory should fire at pan=40 once the person is persistently there, NOT at
    # the other headings. (Smaller temporal windows because each heading is sampled once/cycle.)
    os.environ["SECONDATTN_OFFLINE"] = "1"
    W, H = 640, 480
    desk = [Detection("desk", (220, 300, 520, 460))]
    desk_person = desk + [Detection("person", (300, 120, 470, 460))]   # person at this heading
    scan = [(-40, 0), (0, 0), (40, 0)]
    taste = ReportabilityTaste()
    mem = {}
    def memfor(pos):
        if pos not in mem:
            mem[pos] = TemporalConfigGate(gate=ConfigSurpriseGate(mode="habituation", agg="max",
                       threshold=0.5), persist=1, window=3, stable_frac=0.5)
        return mem[pos]
    latches = {}
    for cycle in range(8):
        for pan, tilt in scan:
            gate = memfor((pan, tilt)); latch = latches.setdefault((pan, tilt), StaticLatch())
            # person appears at heading pan=40 from cycle 4 (after the per-heading warm-up)
            dets = (desk_person if (pan == 40 and cycle >= 4) else desk)
            g = build_graph(latch.apply([Detection(d.label, d.box) for d in dets], (W, H)), (W, H))
            dec = gate.step(*g.as_gate_input())
            tag = f"c{cycle} pan={pan:>3}"
            if dec["event"]:
                box = subject_box(g, dec["subject"])
                ori = tuple(round(x, 1) for x in orient_target(pan, tilt, box, (W, H))) if box else None
                r = run_judge(None, g, taste, delta_added=dec["delta_added"])
                print(f"[{tag}] ★EVENT subj={dec['subject']} arrived={dec['arrived']} "
                      f"-> LOOK orient{ori} -> JUDGE worth={r['worth']:.2f}")
            else:
                print(f"[{tag}] scan… ({len(g.nodes)}obj) event=0")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Pan-tilt sidekick: SCAN->LOOK->REPORT->nod")
    ap.add_argument("--real", action="store_true", help="drive the real rig + M5 cam (else mock test)")
    ap.add_argument("--camera", default=None, help="M5 MJPEG URL (default: rig.py CAM_URL)")
    ap.add_argument("--port", default=None, help="servo serial port (default: rig.py SERIAL_PORT)")
    ap.add_argument("--detector", default="yoloworld",
                    help="yoloworld (open-vocab) | yolo (closed COCO-80, robust) | gdino (Grounding DINO)")
    ap.add_argument("--vocab", default="person,laptop,monitor,keyboard,cup,bottle,chair,desk,"
                                       "bag,potted plant,bookshelf")
    ap.add_argument("--conf", type=float, default=0.3)
    ap.add_argument("--min-area", type=float, default=0.015, help="drop boxes smaller than this frac of frame")
    ap.add_argument("--threshold", type=float, default=0.5, help="gate fire threshold")
    ap.add_argument("--worth", type=float, default=0.5, help="VLM worth needed to REPORT")
    ap.add_argument("--k-pan", type=float, default=0.06, help="LOOK orient gain (pan)")
    ap.add_argument("--k-tilt", type=float, default=0.06, help="LOOK orient gain (tilt)")
    ap.add_argument("--settle", type=float, default=0.0, help="extra wait after move (rig already settles)")
    ap.add_argument("--look-secs", type=float, default=2.5,
                    help="seconds to dwell+sample at each pose so the gate gets several frames")
    ap.add_argument("--dwell", type=float, default=1.0, help="seconds to dwell after a REPORT")
    ap.add_argument("--feed-dir", default="feed", help="save reported moments here (frame .jpg + jsonl)")
    ap.add_argument("--no-save", action="store_true",
                    help="test mode: write NO images and NO jsonl (web feed stays in-memory)")
    ap.add_argument("--offline", action="store_true", help="skip the VLM (dry run, no API key)")
    ap.add_argument("--serve", action="store_true", help="open the web UI (live view + feed) like web_demo")
    ap.add_argument("--web-port", type=int, default=8000, help="port for --serve")
    args = ap.parse_args()
    if args.real:
        _run_real(args)
    else:
        _run_mock()
