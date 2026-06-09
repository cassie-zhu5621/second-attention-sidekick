"""
live_demo.py — REAL-TIME glass-box demo (parallel to the offline run_perception.py batch).

Pulls frames from a live camera and runs the SAME config_gate pipeline (perceive -> gate),
drawing the dynamic scene-graph overlay + gate state on each frame in a live window — so you
can WATCH relations change in real time and see where it works / flickers. Shares
perceive / config_surprise / viz with the batch tool, so demo and data run behave identically.

Camera = your M5 UnitCam S3 (flashed with unitcams3_webcam.ino) streaming MJPEG at
http://<camera-ip>/ . NOTE: the cam allows ONE viewer at a time — stop the collector first.

    python live_demo.py --camera http://sidekick-cam.local --min-area 0.015   # the M5 rig cam
    python live_demo.py --camera http://192.168.3.26 --min-area 0.015          # or by IP
    python live_demo.py --webcam 0                                             # laptop webcam
    python live_demo.py --video clip.mp4                                       # a recorded clip
Options: --vocab "..."  --conf 0.25  --threshold 0.5  --judge (VLM; needs ANTHROPIC_API_KEY)
         --record out.mp4 .  NB this is a plain RGB cam (no depth) -> 2D relations.
Press q to quit.
"""

from __future__ import annotations
import argparse, json, os, sys, threading, time
import cv2
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from perceive import build_graph, YoloWorldDetector
from config_surprise import ConfigSurpriseGate, TemporalConfigGate
from viz import draw_overlay

DEFAULT_VOCAB = ("person,laptop,monitor,keyboard,cup,bottle,chair,desk,book,bag,phone,"
                 "potted plant,bookshelf")


class LiveGrabber:
    """Background reader that always holds only the LATEST frame, so the processing loop
    never lags behind a fast stream (it drops stale frames). For a video file we keep every
    frame (sequential) so playback isn't skipped."""
    def __init__(self, args):
        self.args = args
        self.latest = None
        self.seq = 0
        self.stopped = False

    def _mjpeg(self):
        import requests
        s = requests.Session(); s.trust_env = False
        try:
            with s.get(self.args.camera.rstrip("/") + "/", stream=True, timeout=(5, 15)) as r:
                buf = b""
                for chunk in r.iter_content(8192):
                    if self.stopped:
                        break
                    buf += chunk
                    a = buf.find(b"\xff\xd8")
                    b = buf.find(b"\xff\xd9", a + 2) if a != -1 else -1
                    if a != -1 and b != -1:
                        jpg, buf = buf[a:b + 2], buf[b + 2:]
                        fr = cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR)
                        if fr is not None:
                            self.latest = fr; self.seq += 1
        except Exception as e:
            print("[stream]", e)
        self.stopped = True

    def _webcam(self):
        cap = cv2.VideoCapture(self.args.webcam)
        while not self.stopped and cap.isOpened():
            ok, fr = cap.read()
            if not ok:
                break
            self.latest = fr; self.seq += 1
        cap.release(); self.stopped = True

    def start(self):
        target = self._mjpeg if self.args.camera else self._webcam
        threading.Thread(target=target, daemon=True).start()
        return self


def main():
    ap = argparse.ArgumentParser()
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--webcam", type=int, help="webcam index, e.g. 0")
    src.add_argument("--camera", help="M5 cam MJPEG URL, e.g. http://sidekick-cam.local")
    src.add_argument("--video", help="path to a recorded clip")
    ap.add_argument("--vocab", default=DEFAULT_VOCAB)
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--min-area", type=float, default=0.015)
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--change-thr", type=float, default=2.0)
    ap.add_argument("--depth", action="store_true",
                    help="use monocular Depth-Anything so relations are depth-consistent "
                         "(in-front vs behind); needs `pip install transformers`, slower")
    ap.add_argument("--judge", action="store_true", help="run the VLM on fired moments")
    ap.add_argument("--cooldown", type=float, default=6.0,
                    help="min seconds between VLM calls (keeps it calm + cheap)")
    ap.add_argument("--feed-dir", default="feed",
                    help="save each noticed moment here (frame .jpg + noticed_log.jsonl)")
    ap.add_argument("--record", default=None)
    args = ap.parse_args()

    vocab = [v.strip() for v in args.vocab.split(",")]
    det = YoloWorldDetector(vocab, conf=args.conf)
    depth_model = None
    if args.depth:
        from depth import DepthAnything
        depth_model = DepthAnything()
        print("[depth] Depth-Anything on — relations gated by depth consistency")
    gate = TemporalConfigGate(gate=ConfigSurpriseGate(mode="habituation", agg="max",
                                                      threshold=args.threshold))
    taste = None
    if args.judge:
        from judge import judge as run_judge, ReportabilityTaste
        taste = ReportabilityTaste()

    # frame iterator: live sources via the latest-frame grabber; a video file sequentially.
    def live_frames():
        grab = LiveGrabber(args).start()
        last = -1
        while not grab.stopped or grab.latest is not None:
            if grab.latest is None or grab.seq == last:
                if cv2.waitKey(5) & 0xFF == ord("q"):
                    return
                continue
            last = grab.seq
            yield grab.latest.copy()

    def video_frames():
        cap = cv2.VideoCapture(args.video)
        while cap.isOpened():
            ok, fr = cap.read()
            if not ok:
                break
            yield fr
        cap.release()

    frames = video_frames() if args.video else live_frames()

    # the VLM runs in the BACKGROUND so the video never freezes; HUD shows the latest result.
    judge_state = {"worth": None, "why": "", "note": ""}
    judging = [False]
    last_judge_t = [0.0]
    if args.judge:
        os.makedirs(args.feed_dir, exist_ok=True)   # the moment feed (image + text records)

    prev_gray = None
    writer = None
    fps_t, fps_n, fps = time.time(), 0, 0.0
    print("live demo running — q to quit")
    for fr in frames:
        H, W = fr.shape[:2]
        gray = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
        changed = True
        if prev_gray is not None and prev_gray.shape == gray.shape:
            changed = cv2.absdiff(gray, prev_gray).mean() > args.change_thr
        prev_gray = gray

        g = build_graph(det.detect(fr), (W, H), min_area_frac=args.min_area)
        dec = gate.step(*g.as_gate_input())
        event = bool(dec["event"] and changed)
        state = {"settled": True, "changed": changed, "event": event}
        # carry the latest codified moment in the HUD (persists between events)
        if judge_state["worth"] is not None:
            state.update(worth=judge_state["worth"], why=judge_state["why"], note=judge_state["note"])
        # on a fresh event, fire the VLM in the BACKGROUND (non-blocking), throttled by cooldown
        if event and taste is not None and not judging[0] and (time.time() - last_judge_t[0]) > args.cooldown:
            judging[0] = True
            last_judge_t[0] = time.time()
            ok, jpg = cv2.imencode(".jpg", fr)
            snap, delta = jpg.tobytes(), dec["delta_added"]

            def _job(snap=snap, graph=g, delta=delta):
                try:
                    r = run_judge(snap, graph, taste, delta_added=delta)
                    judge_state.update(worth=r["worth"], why=r["why"], note=r["note"])
                    print(f"[VLM] worth={r['worth']:.2f} ({r['why']}) :: {r['note']}")
                    # save the moment to the feed: image record + text record
                    ts = time.strftime("%Y%m%d_%H%M%S")
                    fn = os.path.join(args.feed_dir, f"noticed_{ts}.jpg")
                    with open(fn, "wb") as fh:
                        fh.write(snap)
                    with open(os.path.join(args.feed_dir, "noticed_log.jsonl"), "a") as fh:
                        fh.write(json.dumps({"time": ts, "worth": round(r["worth"], 2),
                                             "why": r["why"], "note": r["note"],
                                             "frame": os.path.basename(fn)}) + "\n")
                finally:
                    judging[0] = False
            threading.Thread(target=_job, daemon=True).start()

        fps_n += 1
        if time.time() - fps_t >= 1.0:
            fps, fps_n, fps_t = fps_n / (time.time() - fps_t), 0, time.time()
        out = draw_overlay(fr, g, state,
                           caption=f"{len(g.nodes)} obj, {len(g.edges)} rel | {fps:.1f} fps")
        if args.record:
            if writer is None:
                writer = cv2.VideoWriter(args.record, cv2.VideoWriter_fourcc(*"mp4v"),
                                         15, (out.shape[1], out.shape[0]))
            writer.write(out)
        cv2.imshow("second-attention live", out)
        if (cv2.waitKey(1) & 0xFF) == ord("q"):
            break

    if writer is not None:
        writer.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
