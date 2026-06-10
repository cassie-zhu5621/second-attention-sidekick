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
import argparse, json, math, os, time
import cv2

from perceive import make_detector
from planner import plan, VOCAB, VOCAB_VERSION
from relations import RelationEngine
from watch_exec import WatchExecutor
from judge import judge as run_judge, ReportabilityTaste
from gaze import (draw_text, draw_box, draw_arrow, draw_circle, draw_panel,
                  C_GREEN, C_RED, C_YELLOW, C_ORANGE, C_MAGENTA, C_CYAN, C_WHITE)
from attention_demo import frame_source, publish


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
    ap.add_argument("--vocab", default="person,laptop,monitor,keyboard,mouse,cup,bottle,chair,"
                                       "desk,bag,book,cell phone,potted plant")
    ap.add_argument("--conf", type=float, default=0.3)
    ap.add_argument("--persist", type=int, default=2, help="frames a relation must hold")
    ap.add_argument("--cooldown", type=float, default=60.0, help="habituation per entry (s)")
    ap.add_argument("--confirm", action="store_true",
                    help="VLM double-checks the frame when an entry fires (judge confirm)")
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
                                          conf=args.conf))
    if args.save:
        os.makedirs(args.feed_dir, exist_ok=True)
        rel_log = open(os.path.join(args.feed_dir, "relation_log.jsonl"), "a")
    banner = None

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

        for e in fired:                                   # ---- a watched moment ----
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
            if rec_ok:
                print(f"[MOMENT] {label}" + (f" worth={worth:.2f}" if worth is not None else "")
                      + f" :: {note}")
                banner = (t + 5, note, C_GREEN)
                fid = time.strftime("%Y%m%d_%H%M%S")
                rec = {"time": time.strftime("%H:%M:%S"), "worth": worth if worth is not None else "—",
                       "why": "watch-spec", "note": note, "thumb": f"thumb_{fid}.jpg",
                       "frame": f"frame_{fid}.jpg", "label": label,
                       "truth": {k: int(v) for k, v in truth.items()}}
                publish(fr, rec, args, UI)

        # ---- overlay ----
        for d in viz["dets"]:
            x1, y1, x2, y2 = map(int, d.box)
            cv2.rectangle(fr, (x1, y1), (x2, y2), (160, 160, 160), 1)
            draw_text(fr, d.label, (x1, y1 - 6), (200, 200, 200), 0.5, 1)
        for p in viz["people"]:
            draw_box(fr, p.box, C_CYAN, 2)
            draw_text(fr, f"p{p.pid}", (p.box[0], p.box[1] - 10), C_CYAN, 0.6, 1)
        for a in viz.get("arms", []):
            draw_arrow(fr, a.origin, a.point_at(0.4 * math.hypot(W, H)), C_ORANGE, 3)
        for r0 in viz["rays"]:
            draw_arrow(fr, r0.origin, r0.point_at(0.5 * math.hypot(W, H)), C_YELLOW, 3)
        for c in viz.get("joint", []):
            draw_circle(fr, c["point"], 18, C_MAGENTA, 3)
        panel = []
        for s in statuses:
            col = C_GREEN if s.satisfied else (C_ORANGE if s.cooling else C_WHITE)
            tag = "[OK]" if s.satisfied else ("..." if s.detail else "-")
            panel.append((f"{tag} {s.label[:34]}  {s.detail[:28]}", col))
        draw_panel(fr, panel)
        tv = " ".join(f"{i}{'T' if truth[i] else '·'}" for i in sorted(truth))
        draw_text(fr, tv, (12, H - 40), C_WHITE, 0.5, 1)
        draw_text(fr, f"ctx: {ctx[:70]}", (12, H - 14), C_CYAN, 0.55, 1)
        if banner and t < banner[0]:
            draw_text(fr, str(banner[1])[:60], (16, 36), banner[2], 0.85, 2)
        if UI is not None:
            with UI.LOCK:
                UI.STATE["status"] = [(s.label, s.satisfied, s.cooling, s.detail)
                                      for s in statuses]
            UI.STATE["jpg"] = cv2.imencode(".jpg", fr)[1].tobytes()
        cv2.imshow("attention system (VLM-first)", fr)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cv2.destroyAllWindows(); engine.close()


if __name__ == "__main__":
    main()
