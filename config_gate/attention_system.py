"""
attention_system.py — the FULL VLM-first system (relation_table.md architecture, live):

    context (typed) + frame  ->  VLM PLANNER (planner.py)  ->  watch-spec JSON
        ->  RelationEngine (relations.py): per-frame truth vector over rows 1-11
        ->  WatchExecutor (watch_exec.py): all/any/not/then + windows + habituation
        ->  records (frame + truth slice + label) + web UI + relation_log.jsonl

Context comes from --context or a context FILE (default context.txt next to this script);
EDIT THE FILE WHILE RUNNING and the system re-plans on the next frame — that is the
"taste is re-writable at runtime" loop, now operating on plans instead of axis weights.

Run:
    echo "Two of us are assembling a robot arm this afternoon." > context.txt
    python attention_system.py --offline --camera 0 --serve      # keyless dry run
    export ANTHROPIC_API_KEY=sk-...
    python attention_system.py --camera 0 --serve --save         # real planner
    python attention_system.py --serve                           # M5 (rig.py CAM_URL)
"""

from __future__ import annotations
import argparse, json, math, os, subprocess, sys, time
import cv2
import numpy as np

from perceive import make_detector
from planner import plan, VOCAB, VOCAB_VERSION
from relations import RelationEngine
from watch_exec import WatchExecutor
from judge import judge as run_judge, ReportabilityTaste
from gaze import (draw_text, draw_box, draw_arrow, draw_circle, draw_panel,
                  C_GREEN, C_RED, C_YELLOW, C_ORANGE, C_MAGENTA, C_CYAN, C_WHITE)
from attention_demo import frame_source, publish


def beep():
    """Audible 'noticed' cue (tests are hard to watch while acting). macOS only; silent no-op elsewhere."""
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def make_strip(shots, height=300):
    """The comic strip: N shots -> one horizontal story image."""
    tiles = []
    for s in shots:
        h, w = s.shape[:2]
        tiles.append(cv2.resize(s, (max(1, int(w * height / h)), height)))
    return np.hstack(tiles)


def shot_trace(truth, viz):
    """One panel's GROUNDED detection summary (what the system actually saw this frame), so the
    story description is narrated from the real detected sequence — not re-captioned off a photo."""
    dets = viz.get("dets", [])
    parts, seen = [], set()
    for relname, h in viz.get("hits", []):              # gazing-at / pointing-at (have a target)
        di = h.get("det") if isinstance(h, dict) else None
        tgt = dets[di].label if isinstance(di, int) and 0 <= di < len(dets) else ""
        key = f"{relname} {tgt}".strip()
        if key not in seen:
            seen.add(key); parts.append(key)
    hit_names = {relname for relname, _ in viz.get("hits", [])}
    for i, on in truth.items():                         # truth-only rows (proxemic, approach, hands-on…)
        if on:
            nm = VOCAB.get(i, str(i)).split("—")[0].strip()
            if nm not in hit_names and nm not in seen:
                seen.add(nm); parts.append(nm)
    return ", ".join(parts) if parts else "quiet"


def read_context(path, fallback):
    try:
        s = open(path).read().strip()
        return s or fallback
    except OSError:
        return fallback


def spec_summary(spec):
    out = []
    for c in spec.get("watch", []) or []:
        bits = []
        if c.get("all"):  bits.append("+".join(map(str, c["all"])))
        if c.get("any"):  bits.append("any(" + ",".join(map(str, c["any"])) + ")")
        if c.get("then"): bits.append("then(" + "→".join(map(str, c["then"])) + ")")
        if c.get("not"):  bits.append("not(" + ",".join(map(str, c["not"])) + ")")
        out.append((" ".join(bits), c.get("label", "")))
    return out


# electric / cyber green — LIVE-ONLY, used for the BlazePose skeleton (BGR of #1EFF5A)
C_SKEL = (90, 255, 30)

# short labels for the bottom relation ribbon (rows 1–11), synced with the web UI vocab
LIVE_ABBR = {1: "gaze", 2: "joint", 3: "eye", 4: "point", 5: "prox", 6: "F-form",
             7: "appr", 8: "lean", 9: "hands", 10: "group", 11: "turn"}


def draw_relation_ribbon(fr, W, H, truth, entries):
    """Bottom-of-frame vocabulary strip: rows 1–11 as 'N abbr', lit yellow-green when
    detected THIS frame; watch-entry groups (≥2 ids) bracketed above with an AND/OR/THEN
    label that lights blue when its condition holds. Detection-only — no watch/cooldown."""
    import cv2
    n = 11
    margin = 34
    step = (W - 2 * margin) / (n - 1)
    xs = {i: int(margin + (i - 1) * step) for i in range(1, n + 1)}
    base_y = H - 18                                    # the label row
    for i in range(1, n + 1):                          # 1) the vocabulary labels
        on = bool(truth.get(i, False))
        col = C_YELLOW if on else (165, 165, 165)
        txt = f"{i} {LIVE_ABBR.get(i, '')}"
        (tw, _), _ = cv2.getTextSize(txt, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        draw_text(fr, txt, (xs[i] - tw // 2, base_y), col, 0.5, 2 if on else 1)

    level = [0]                                        # 2) the conjunction brackets, stacked up
    def connect(ids, label, lit):
        ids = [i for i in ids if i in xs]
        if len(ids) < 2:
            return
        y = base_y - 34 - level[0] * 28
        lo = min(ids, key=lambda i: xs[i]); hi = max(ids, key=lambda i: xs[i])
        col = C_CYAN if lit else (110, 110, 110)
        th = 3 if lit else 1
        cv2.line(fr, (xs[lo], y), (xs[hi], y), col, th, cv2.LINE_AA)        # the bar
        for i in ids:                                                       # down-ticks to each
            cv2.line(fr, (xs[i], y), (xs[i], base_y - 14), col, th, cv2.LINE_AA)
        mx = (xs[lo] + xs[hi]) // 2
        (tw, _), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        draw_text(fr, label, (mx - tw // 2, y - 7), col, 0.6, 2)
        level[0] += 1

    for e in entries:
        on = lambda i: bool(truth.get(i, False))
        if len(e.get("then", [])) >= 2:
            connect(e["then"], "THEN", all(on(i) for i in e["then"]))
        if len(e.get("all", [])) >= 2:
            connect(e["all"], "AND", all(on(i) for i in e["all"]))
        if len(e.get("any", [])) >= 2:
            connect(e["any"], "OR", any(on(i) for i in e["any"]))


def main():
    ap = argparse.ArgumentParser(description="VLM-first attention system (plan -> watch -> record)")
    ap.add_argument("--camera", default=None, help="M5 URL (default rig.py CAM_URL) or webcam index")
    ap.add_argument("--context", default=None, help="context sentence (overrides --context-file)")
    ap.add_argument("--context-file", default="context.txt",
                    help="re-plans when this file changes (default context.txt)")
    ap.add_argument("--grammar", default="free", help="planner grammar (study winner: free)")
    ap.add_argument("--plan-frame", action="store_true",
                    help="give the planner the CURRENT FRAME along with the context "
                         "(situated planning — the V in VLM; off by default to stay "
                         "comparable with the text-only study numbers)")
    ap.add_argument("--spec-file", default=None,
                    help="JSON watch-spec file: SKIP the planner and execute exactly this "
                         "(deterministic per-item testing; context hot-reload disabled)")
    ap.add_argument("--detector", default="yolo", help="yolo | yoloworld | gdino")
    ap.add_argument("--pose-backend", default="mediapipe",
                    help="mediapipe (default) | comotion (experimental 3D, see comotion_pose.py)")
    ap.add_argument("--vocab", default="person,laptop,monitor,keyboard,mouse,cup,bottle,chair,"
                                       "desk,bag,book,cell phone,potted plant")
    ap.add_argument("--conf", type=float, default=0.3)
    ap.add_argument("--persist", type=int, default=2, help="frames a relation must hold")
    ap.add_argument("--cooldown", type=float, default=60.0, help="habituation per entry (s)")
    ap.add_argument("--confirm", action="store_true",
                    help="VLM double-checks the frame when an entry fires (judge confirm)")
    ap.add_argument("--burst-n", type=int, default=10,
                    help="MAX panels per story (event-driven: a panel is added only when the scene "
                         "CHANGES, so short stories stay short and long ones use up to this many)")
    ap.add_argument("--burst-interval", type=float, default=4.0,
                    help="minimum seconds between panels (a panel is taken only if the scene also changed)")
    ap.add_argument("--scene-diff", type=float, default=8.0,
                    help="image-change fallback: mean gray-diff vs the last panel to count as a change")
    ap.add_argument("--no-sound", action="store_true", help="disable the audible 'noticed' cue")
    ap.add_argument("--rig", action="store_true",
                    help="pan-tilt mode: SCAN poses while all entries are quiet; on fire -> "
                         "buzzer+nod, STAY and watch the story; resume scanning when bored")
    ap.add_argument("--port", default=None, help="servo serial port (default: rig.py SERIAL_PORT)")
    ap.add_argument("--look-secs", type=float, default=6.0, help="rig: dwell per scan pose")
    ap.add_argument("--watch-end", type=float, default=8.0,
                    help="rig: seconds of quiet before leaving a WATCH pose")
    ap.add_argument("--worth", type=float, default=0.0,
                    help="with --confirm: min reportability worth to record")
    ap.add_argument("--offline", action="store_true", help="fake planner/judge, no API key")
    ap.add_argument("--save", action="store_true", help="records + relation_log.jsonl to feed dir")
    ap.add_argument("--serve", action="store_true", help="web UI (live + feed)")
    ap.add_argument("--web-port", type=int, default=8000)
    ap.add_argument("--feed-dir", default="feed")
    args = ap.parse_args()
    if args.offline:
        os.environ["SECONDATTN_OFFLINE"] = "1"
    if args.camera is None:
        from rig import CAM_URL
        args.camera = CAM_URL
    print(f"[camera] {args.camera}")

    # ---- plan ----
    fallback = "A shared lab space; notice socially meaningful moments."
    ctx = args.context or read_context(args.context_file, fallback)
    ctx_mtime = os.path.getmtime(args.context_file) if (not args.context and
                os.path.exists(args.context_file)) else None

    def make_plan(context, jpeg=None):
        r = plan(context, jpeg=jpeg if args.plan_frame else None, grammar=args.grammar)
        if r["spec"] is None:
            raise SystemExit(f"planner failed: {r['violations']}\nraw: {r['raw'][:300]}")
        if r["violations"]:
            print(f"[plan] WARNING violations: {r['violations']} (executing anyway)")
        print(f"[plan] context: {context}")
        for expr, label in spec_summary(r["spec"]):
            print(f"[plan]   watch {expr}   ({label})")
        print(f"[plan]   why: {r['spec'].get('why','')}")
        if r["spec"].get("missing"):
            print(f"[plan]   MISSING (vocab {VOCAB_VERSION} gap): {r['spec']['missing']}")
        return r["spec"], WatchExecutor(r["spec"], persist=args.persist, cooldown=args.cooldown)

    taste = ReportabilityTaste()                 # only used by --confirm (back-end judge)
    UI = None
    if args.serve:                               # the VLM-FIRST surface: context box, not taste box
        import attention_ui
        UI = attention_ui.serve(args)

    def push_plan():
        if UI is not None:
            with UI.LOCK:
                UI.STATE["context"] = ctx
                UI.STATE["why"] = (spec or {}).get("why", "")
                UI.STATE["entries"] = spec_summary(spec)

    rig = None
    if args.rig:                                  # motion chassis: same brain, scanning body
        from rig import GimbalRig, ServoOnlyRig, SERIAL_PORT
        if str(args.camera).isdigit():            # USB webcam on the head: servos only,
            rig = ServoOnlyRig(port=args.port or SERIAL_PORT)   # frames via VideoCapture
            frames = frame_source(str(args.camera))
        else:                                     # M5: rig owns the stream (fresh-frame)
            rig = GimbalRig(cam_url=str(args.camera), port=args.port or SERIAL_PORT)

            def _rig_frames():
                while True:
                    yield rig.get_frame()
            frames = _rig_frames()
        scan = [(p, tl) for tl in (0, 8) for p in (-50, -25, 0, 25, 50)]
        pose_i, mstate = 0, "SCAN"
        pose_until, last_active = 0.0, time.time()
        print(f"[rig] live — {len(scan)} scan poses; fire -> beep+nod+WATCH; "
              f"resume after {args.watch_end:.0f}s quiet")
    else:
        frames = frame_source(str(args.camera))
    first = next(frames)                          # camera live BEFORE planning; with
    if args.spec_file:                            # --plan-frame the planner sees the scene
        spec = json.load(open(args.spec_file))
        executor = WatchExecutor(spec, persist=args.persist, cooldown=args.cooldown)
        ctx, ctx_mtime = f"[spec-file] {args.spec_file}", None
        print("[plan] bypassed — executing spec from file:")
        for expr, label in spec_summary(spec):
            print(f"[plan]   watch {expr}   ({label})")
    else:
        spec, executor = make_plan(ctx, cv2.imencode(".jpg", first)[1].tobytes())
    push_plan()
    engine = RelationEngine(make_detector(args.detector,
                                          [v.strip() for v in args.vocab.split(",")],
                                          conf=args.conf),
                            pose_backend=args.pose_backend)
    if args.save:
        os.makedirs(args.feed_dir, exist_ok=True)
        rel_log = open(os.path.join(args.feed_dir, "relation_log.jsonl"), "a")
    banner = None
    bursts = []                                   # open story bursts (entries mid-narrative)

    import itertools
    for fr in itertools.chain([first], frames):
        t = time.time()
        H, W = fr.shape[:2]

        # hot re-plan: from the web UI context box…
        if UI is not None and not args.spec_file:
            with UI.LOCK:
                pending = UI.STATE.pop("pending_context", None)
                UI.STATE["pending_context"] = None
            if pending:
                ctx = pending
                spec, executor = make_plan(ctx, cv2.imencode(".jpg", fr)[1].tobytes())
                push_plan()
                banner = (t + 4, f"re-planned: {ctx[:60]}", C_CYAN)
        # …or when context.txt changes
        if ctx_mtime is not None:
            try:
                m = os.path.getmtime(args.context_file)
                if m != ctx_mtime:
                    ctx_mtime = m
                    ctx = read_context(args.context_file, fallback)
                    spec, executor = make_plan(ctx, cv2.imencode(".jpg", fr)[1].tobytes())
                    push_plan()
                    banner = (t + 4, f"re-planned: {ctx[:60]}", C_CYAN)
            except OSError:
                pass

        truth, viz = engine.step(fr, t)
        fired, statuses = executor.step(truth, t)
        if args.save:
            rel_log.write(json.dumps({"t": round(t, 2),
                                      "truth": {k: int(v) for k, v in truth.items()}}) + "\n")

        for e in fired:                                   # ---- a watched moment opens a STORY ----
            label = e["label"]
            rec_ok, note, worth = True, label, None
            if args.confirm:
                ids = e["all"] + e["any"] + e["then"]
                claim = label + " — i.e. " + "; ".join(VOCAB[i].split("—")[1].strip()
                                                       for i in ids if i in VOCAB)
                r = run_judge(cv2.imencode(".jpg", fr)[1].tobytes(), None, taste, confirm=claim)
                rec_ok = r["confirmed"] and r["worth"] >= args.worth
                note, worth = r["note"], r["worth"]
                if not r["confirmed"]:
                    print(f"[VETO ] {label} :: {note}")
                    banner = (t + 3, f"VLM veto: {label}", C_RED)
            if rec_ok:                                    # burst: keep shooting while it unfolds
                if rig is not None:                       # embodied cue: buzzer chirp + nod
                    rig.nod()
                    mstate, last_active = "WATCH", t      # stop scanning: stay with the story
                elif not args.no_sound:
                    beep()
                print(f"[STORY ] {label} — burst opened")
                banner = (t + 3, f"watching: {label}", C_CYAN)
                bursts.append({"label": label, "idx": executor.entries.index(e),
                               "shots": [fr.copy()], "traces": [shot_trace(truth, viz)],
                               "last_truth": dict(truth),
                               "last_gray": cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY),
                               "next": t + args.burst_interval,
                               "note": note, "worth": worth,
                               "truth": {k: int(v) for k, v in truth.items()}})

        # ---- advance open bursts; on completion publish the comic strip, then 'bored' ----
        for b in list(bursts):
            st_ = statuses[b["idx"]]
            # EVENT-DRIVEN panel: add one only when the scene CHANGED (truth-vector differs, or the
            # image moved enough) AND the min interval has passed — long stories get more panels,
            # short ones stay short, no near-duplicate frames.
            if st_.satisfied and t >= b["next"] and len(b["shots"]) < args.burst_n:
                g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
                changed = dict(truth) != b["last_truth"]
                if not changed and b["last_gray"].shape == g.shape:
                    changed = float(cv2.absdiff(g, b["last_gray"]).mean()) > args.scene_diff
                if changed:
                    b["shots"].append(fr.copy()); b["traces"].append(shot_trace(truth, viz))
                    b["last_truth"] = dict(truth); b["last_gray"] = g
                b["next"] = t + args.burst_interval
            if len(b["shots"]) >= args.burst_n or not st_.satisfied:
                bursts.remove(b)
                n = len(b["shots"])
                strip = make_strip(b["shots"])
                story = " → ".join(dict.fromkeys(b["traces"]))   # ordered, de-duplicated trace
                if args.offline:
                    note = f"{b['label']}: {story}"; worth = b["worth"]
                else:                                            # NARRATE from the detected sequence
                    r = run_judge(cv2.imencode(".jpg", strip)[1].tobytes(), None, taste, story=story)
                    note, worth = r["note"], r["worth"]
                note = f"{note} ({n}-shot story)"
                print(f"[MOMENT] {b['label']} :: {note} -> bored, cooling")
                banner = (t + 5, note, C_GREEN)
                fid = time.strftime("%Y%m%d_%H%M%S")
                rec = {"time": time.strftime("%H:%M:%S"),
                       "worth": worth if worth is not None else "—",
                       "why": "watch-spec", "note": note, "thumb": f"thumb_{fid}.jpg",
                       "frame": f"frame_{fid}.jpg", "label": b["label"], "shots": n,
                       "story": story, "truth": b["truth"]}
                publish(strip, rec, args, UI)

        # ---- motion policy (rig mode): quiet -> scan; story -> stay ----
        if rig is not None:
            if bursts or any(s.satisfied for s in statuses):
                last_active, mstate = t, "WATCH"
            if mstate == "WATCH" and not bursts and t - last_active > args.watch_end:
                mstate, pose_until = "SCAN", 0.0
                print("[rig] bored & quiet -> resume scan")
            if mstate == "SCAN" and t >= pose_until:
                pose_i += 1
                pn, tl = scan[pose_i % len(scan)]
                rig.move_to(pn, tl)                       # blocks through the glide
                pose_until = time.time() + args.look_secs

        # ---- overlay ----
        for d in viz["dets"]:                                       # object slots — yellow-green
            x1, y1, x2, y2 = map(int, d.box)
            cv2.rectangle(fr, (x1, y1), (x2, y2), C_YELLOW, 3, cv2.LINE_AA)
            draw_text(fr, d.label, (x1, y1 - 6), C_YELLOW, 0.6, 2)
        raw = getattr(engine.poses, "last_raw", None)
        if raw:                                       # comotion backend: full skeletons (THICK)
            from comotion_pose import SMPL_EDGES
            for pid_, uv_ in raw:
                for a_, b_ in SMPL_EDGES:
                    cv2.line(fr, (int(uv_[a_, 0]), int(uv_[a_, 1])),
                             (int(uv_[b_, 0]), int(uv_[b_, 1])), C_SKEL, 9, cv2.LINE_AA)
        else:                                         # mediapipe backend: BlazePose skeleton (THICK)
            from gaze import draw_pose_skeleton
            for p in viz["people"]:
                if getattr(p, "raw", None):
                    draw_pose_skeleton(fr, p.raw, C_SKEL, thick=9)
        # (no separate person box / p# label — the object detector's box already frames the person)
        for a in viz.get("arms", []):                                # pointing — yellow-green
            draw_arrow(fr, a.origin, a.point_at(0.4 * math.hypot(W, H)), C_YELLOW, 12)
        for r0 in viz["rays"]:                                       # gaze rays — blue (logic)
            draw_arrow(fr, r0.origin, r0.point_at(0.5 * math.hypot(W, H)), C_CYAN, 12)
        for c in viz.get("joint", []):                              # joint-attention moment — red
            draw_circle(fr, c["point"], 26, C_MAGENTA, 10)
        # bottom vocabulary ribbon (replaces the old truth-vector line + the top-left panel,
        # which duplicated the web UI's THE PLAN); detection-only highlight + conjunction brackets
        draw_relation_ribbon(fr, W, H, truth, executor.entries)
        if rig is not None:                            # live-only motion state (not on the right panel)
            draw_text(fr, f"{mstate} pan {rig.pan:.0f} tilt {rig.tilt:.0f}", (16, 30), C_GREEN, 0.6, 2)
        if banner and t < banner[0]:
            draw_text(fr, str(banner[1])[:60], (16, 36), banner[2], 0.85, 2)
        if UI is not None:
            with UI.LOCK:
                UI.STATE["status"] = UI.build_status(statuses, executor.entries, truth)
            UI.STATE["jpg"] = cv2.imencode(".jpg", fr)[1].tobytes()
        cv2.imshow("attention system (VLM-first)", fr)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cv2.destroyAllWindows(); engine.close()
    if rig is not None:
        rig.close()


if __name__ == "__main__":
    main()
