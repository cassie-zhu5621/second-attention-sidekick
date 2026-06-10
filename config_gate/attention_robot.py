"""
attention_robot.py — the RIG version of the attention pipeline. Her spec, verbatim:

    scan to a new pose -> read the structure (relations) -> VLM on trigger ->
    if it CONFIRMS, STOP HERE and keep watching -> when the episode ends (no relation
    for a while) and we're cooled down -> move on and start the next round.

States (one legible loop, like robot_demo):
    SCAN  : visit each pan/tilt pose; dwell --look-secs sampling relations into the gate.
    WATCH : a relation fired AND the VLM confirmed it -> stay at this pose. Gently orient
            so the TARGET is centred (joining the attention), nod, keep sampling: new
            relations can still fire here (the same key is in cooldown = habituated).
            WATCH ends when NO relation has been present for --watch-end seconds, or
            --max-watch caps it (don't stare forever). Then resume the sweep.

One GLOBAL RelationGate (not per-pose): the key (relation, subject, target) is about the
PEOPLE, not the heading — seeing the same person gaze the same cup from the next pose over
is the same attention, and must not re-fire.

Run (hardware: M5 + pan/tilt on serial, same as robot_demo):
    python attention_robot.py --offline --serve          # dry run, web UI on :8000
    export ANTHROPIC_API_KEY=sk-...
    python attention_robot.py --serve --save
"""

from __future__ import annotations
import argparse, os, time
import cv2

from judge import judge as run_judge, ReportabilityTaste
from gaze import HeadPoseEstimator, ArmRayEstimator, C_GREEN, C_RED, C_WHITE
from attention_demo import (RelationGate, extract_relations, mini_graph, render,
                            publish, serve_ui)
from perceive import make_detector
from robot_demo import orient_target


def main():
    ap = argparse.ArgumentParser(description="rig: SCAN -> relation gate -> VLM -> WATCH -> resume")
    ap.add_argument("--camera", default=None, help="M5 MJPEG URL (default: rig.py CAM_URL)")
    ap.add_argument("--port", default=None, help="servo serial port (default: rig.py SERIAL_PORT)")
    ap.add_argument("--detector", default="yolo", help="yolo | yoloworld | gdino")
    ap.add_argument("--vocab", default="person,laptop,monitor,keyboard,cup,bottle,chair,desk,"
                                       "bag,potted plant,book,phone")
    ap.add_argument("--conf", type=float, default=0.3)
    ap.add_argument("--tol", type=float, default=12.0)
    ap.add_argument("--persist", type=int, default=2, help="frames a relation must hold (2 @ ~2fps = ~1s)")
    ap.add_argument("--cooldown", type=float, default=60.0, help="habituation per relation key (s)")
    ap.add_argument("--worth", type=float, default=0.5)
    ap.add_argument("--look-secs", type=float, default=10.0,
                    help="dwell per scan pose (10s for the test period; ~3s once tuned)")
    ap.add_argument("--watch-end", type=float, default=5.0,
                    help="WATCH ends after this many seconds with NO relation present")
    ap.add_argument("--max-watch", type=float, default=120.0, help="hard cap on one WATCH (s)")
    ap.add_argument("--k-pan", type=float, default=0.06)
    ap.add_argument("--k-tilt", type=float, default=0.06)
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--save", action="store_true")
    ap.add_argument("--serve", action="store_true", help="web UI (live + feed + taste box)")
    ap.add_argument("--web-port", type=int, default=8000)
    ap.add_argument("--feed-dir", default="feed")
    args = ap.parse_args()
    if args.offline:
        os.environ["SECONDATTN_OFFLINE"] = "1"

    from rig import GimbalRig, CAM_URL, SERIAL_PORT
    est, arm_est = HeadPoseEstimator(), ArmRayEstimator()
    det = make_detector(args.detector, [v.strip() for v in args.vocab.split(",")], conf=args.conf)
    gate = RelationGate(persist=args.persist, cooldown=args.cooldown)
    taste = ReportabilityTaste()
    UI = None
    if args.serve:
        UI, taste = serve_ui(args)
    rig = GimbalRig(cam_url=args.camera or CAM_URL, port=args.port or SERIAL_PORT)

    pans = [-50, -25, 0, 25, 50]                      # same sweep as robot_demo
    scan = [(p, t) for t in (0, 8) for p in pans]
    banner = [None]

    def step(fr, status):
        """One frame through the whole pipeline. Returns (rels, confirmed_report?)."""
        H, W = fr.shape[:2]
        rays = est.estimate(fr)
        arms = arm_est.estimate(fr)
        dets = det.detect(fr)
        rels = extract_relations(rays, arms, dets, (W, H), tol_deg=args.tol)
        confirmed = None
        for key in gate.step(rels.keys()):
            claim, viz = rels[key]
            r = run_judge(cv2.imencode(".jpg", fr)[1].tobytes(), mini_graph(key), taste,
                          confirm=claim)
            tag = f"{key[0]} {key[2]}"
            if not r["confirmed"]:
                print(f"[VETO ] {tag} :: {r['note']}")
                banner[0] = (time.time() + 3, f"VLM veto: {tag}", C_RED)
            elif r["worth"] >= args.worth:
                print(f"[REPORT] {tag} worth={r['worth']:.2f} ({r['why']}) :: {r['note']}")
                banner[0] = (time.time() + 5, r["note"], C_GREEN)
                fid = time.strftime("%Y%m%d_%H%M%S")
                rec = {"time": time.strftime("%H:%M:%S"), "worth": round(r["worth"], 2),
                       "why": r["why"], "note": r["note"], "thumb": f"thumb_{fid}.jpg",
                       "frame": f"frame_{fid}.jpg", "rel": key[0], "target": key[2],
                       "pan": round(rig.pan), "tilt": round(rig.tilt)}
                publish(fr, rec, args, UI)
                confirmed = (key, rels[key][1])
            else:
                print(f"[skip ] {tag} worth={r['worth']:.2f} < {args.worth}")
        render(fr, rays, arms, dets, rels, gate, args.persist, banner[0], status)
        if UI is not None:
            UI.STATE["jpg"] = cv2.imencode(".jpg", fr)[1].tobytes()
        return rels, confirmed

    print(f"[rig] live. {len(scan)} poses; WATCH ends after {args.watch_end:.0f}s quiet. Ctrl-C stops.")
    i = 0
    try:
        while True:
            pan, tilt = scan[i % len(scan)]
            i += 1
            rig.move_to(pan, tilt)                            # ---- SCAN ----
            t_end = time.time() + args.look_secs
            confirmed = None
            while time.time() < t_end and confirmed is None:
                fr = rig.get_frame()
                rels, confirmed = step(fr, f"SCAN  pan {rig.pan:.0f} tilt {rig.tilt:.0f}")
            print(f"[SCAN] pan={pan:.0f} tilt={tilt:.0f}  rels={sorted(k[0] for k in rels)}"
                  f"  -> {'WATCH' if confirmed else 'next'}")
            if confirmed is None:
                continue

            key, viz = confirmed                              # ---- WATCH: stay here ----
            if "box" in viz:                                  # join the attention: centre target
                H, W = fr.shape[:2]
                tp, tt = orient_target(rig.pan, rig.tilt, viz["box"], (W, H),
                                       args.k_pan, args.k_tilt)
                rig.move_to(tp, tt)
            rig.nod()                                         # legible "noticed"
            t0 = last_present = time.time()
            while True:
                fr = rig.get_frame()
                left = args.watch_end - (time.time() - last_present)
                rels, again = step(fr, f"WATCH  {key[0]}  quiet-timeout {max(0, left):.0f}s")
                now = time.time()
                if rels:
                    last_present = now                        # someone's attention still here
                if again:
                    rig.nod()                                 # a NEW relation confirmed here
                if now - last_present > args.watch_end:
                    print(f"[WATCH] over (quiet {args.watch_end:.0f}s) -> resume scan")
                    break
                if now - t0 > args.max_watch:
                    print(f"[WATCH] max {args.max_watch:.0f}s reached -> resume scan")
                    break
    except KeyboardInterrupt:
        print("\nstopping…")
    finally:
        rig.close(); est.close(); arm_est.close()


if __name__ == "__main__":
    main()
