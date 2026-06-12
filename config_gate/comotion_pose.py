"""
comotion_pose.py — EXPERIMENTAL pose backend: Apple CoMotion (ICLR'25) instead of
MediaPipe PoseLandmarker for the body half of the relation engine.

Why: CoMotion does multi-person 3D SMPL pose with ONLINE tracking through occlusion —
stable identities (kills our pid-churn guard) and 3D joints (rows 5/6/7 can use real
3D distance and true body orientation instead of the shoulder-width ruler).
Face/gaze rays (rows 1/2/3) STAY on MediaPipe FaceLandmarker — CoMotion has no face.

Setup (one-time, on the Mac):
    git clone https://github.com/apple/ml-comotion ~/Documents/Claude/Projects/ml-comotion
    conda create -n sidekick -y python=3.10 && conda activate sidekick
    pip install -e ~/Documents/Claude/Projects/ml-comotion        # model only (no aitviewer)
    (cd ~/Documents/Claude/Projects/ml-comotion && bash get_pretrained_models.sh)
    # SMPL body model: register at https://smpl.is.tue.mpg.de , download v1.1.0 neutral,
    # copy basicmodel_neutral_lbs_10_207_0_v1.1.0.pkl ->
    #   ml-comotion/src/comotion_demo/data/smpl/SMPL_NEUTRAL.pkl
    pip install -r requirements.txt --no-cache-dir                # our deps into the same env

Probe FIRST (fps + key/shape dump; expect to iterate once with Claude on the mapping):
    python comotion_pose.py --camera 0
Then run the system with it:
    python attention_system.py --serve --pose-backend comotion ...

NOTE: written against the public demo.py API (model(image, K) -> detection, track);
the exact tensor keys/shapes are verified at runtime — the probe prints them, and
`_extract_people` is the single place to adjust if Apple's key names differ.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple

import numpy as np

from relations import PersonPose, NOSE, L_SH, R_SH, L_EL, R_EL, L_WR, R_WR, L_HIP, R_HIP

# SMPL joint indices (24-joint convention) -> our landmark ids
_SMPL2LM = {15: NOSE,            # head (nose proxy)
            16: L_SH, 17: R_SH,  # shoulders
            18: L_EL, 19: R_EL,  # elbows
            20: L_WR, 21: R_WR,  # wrists
            1: L_HIP, 2: R_HIP}  # hips

# full SMPL kinematic tree (24 joints) for detailed visualization
# 0 pelvis 1/2 hips 3/6/9 spine 4/5 knees 7/8 ankles 10/11 feet 12 neck 13/14 collars
# 15 head 16/17 shoulders 18/19 elbows 20/21 wrists 22/23 hands; 24-26 aux face pts
SMPL_EDGES = [(0, 1), (0, 2), (0, 3), (1, 4), (2, 5), (3, 6), (4, 7), (5, 8), (6, 9),
              (7, 10), (8, 11), (9, 12), (12, 15), (9, 13), (9, 14), (13, 16), (14, 17),
              (16, 18), (17, 19), (18, 20), (19, 21), (20, 22), (21, 23)]
_LIMB_COLOR = {"torso": (200, 200, 60), "arm_l": (60, 230, 60), "arm_r": (60, 160, 255),
               "leg_l": (230, 120, 60), "leg_r": (180, 60, 230)}
_EDGE_GROUP = {(0, 1): "leg_l", (1, 4): "leg_l", (4, 7): "leg_l", (7, 10): "leg_l",
               (0, 2): "leg_r", (2, 5): "leg_r", (5, 8): "leg_r", (8, 11): "leg_r",
               (13, 16): "arm_l", (16, 18): "arm_l", (18, 20): "arm_l", (20, 22): "arm_l",
               (14, 17): "arm_r", (17, 19): "arm_r", (19, 21): "arm_r", (21, 23): "arm_r"}


class CoMotionPoseEstimator:
    """frame (BGR) -> List[PersonPose] with STABLE pids from CoMotion's online tracker.
    Also stashes per-pid 3D positions in self.pos3d (metres-ish, camera frame) for
    future 3D upgrades of rows 5/6/7."""

    def __init__(self):
        import torch
        from comotion_demo.models import comotion
        from comotion_demo.utils import dataloading
        self.torch, self.dataloading, self.comotion = torch, dataloading, comotion
        self.use_mps = torch.backends.mps.is_available()
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.model = comotion.CoMotion(use_coreml=self.use_mps).to(self.device).eval()
        self._init = False
        self.pos3d: Dict[int, Tuple[float, float, float]] = {}
        self.last_raw: List[Tuple[int, np.ndarray]] = []   # (pid, uv 27x2) — for detailed viz
        self._debut: Dict[int, int] = {}                   # pid -> consecutive frames seen
        self._dumped = False

    # ------------------------------------------------------------------ #
    def estimate(self, frame_bgr: np.ndarray) -> List[PersonPose]:
        torch = self.torch
        rgb = np.ascontiguousarray(frame_bgr[..., ::-1])
        image = self.dataloading.convert_image_to_tensor(rgb)
        K = self.dataloading.get_default_K(image)
        if not self._init:
            self.model.init_tracks(image.shape[-2:])
            self._init = True
        with torch.no_grad():
            detection, track = self.model(image, K, use_mps=self.use_mps)
        if not self._dumped:                       # one-time shape dump for the mapping
            self._dumped = True
            try:
                dk = {k: tuple(v.shape) for k, v in detection.items()}
                print(f"[comotion] detection keys: {dk}")
                print(f"[comotion] track type: {type(track).__name__}, "
                      f"fields: {[f for f in ('id','pose','trans','betas') if hasattr(track, f)]}")
            except Exception as e:
                print(f"[comotion] dump failed: {e}")
        return self._extract_people(detection, track, K, frame_bgr.shape[:2])

    # ------------------------------------------------------------------ #
    def _extract_people(self, detection, track, K, hw) -> List[PersonPose]:
        """TrackTensorState carries projected 2D joints DIRECTLY (track.pred_2d,
        shape (1, max_tracks, 27, 2), zero-padded; 27 = 'joints_face' = 24 SMPL + 3 aux).
        Valid slots: betas nonzero and id > 0 (their padding/cleanup convention)."""
        out: List[PersonPose] = []
        try:
            ids = track.id[0, :, 0]                 # (T,)
            betas = track.betas[0]                  # (T, 10)
            p2d = track.pred_2d[0]                  # (T, 27, 2)
            trans = track.trans[0]                  # (T, 3) — camera-frame position
        except Exception as e:
            print(f"[comotion] track unpack failed ({e}) — check the probe dump")
            return out
        valid = (betas != 0).any(-1) & (ids > 0)
        self.last_raw = []
        H, W = hw
        seen_now = set()
        for n in valid.nonzero().flatten().tolist():
            pid = int(ids[n])
            uv = p2d[n].cpu().numpy()
            # ---- GHOST FILTERS (live mode shows raw tracks; demo cleans offline) ----
            inb = ((uv[:, 0] >= 0) & (uv[:, 0] < W) & (uv[:, 1] >= 0) & (uv[:, 1] < H)).mean()
            sw = float(np.hypot(*(uv[16] - uv[17])))            # shoulder width px
            if inb < 0.6 or sw < 12:                            # mostly offscreen / tiny ghost
                continue
            seen_now.add(pid)
            # debut delay: a pid must survive 3 consecutive frames before we believe it
            self._debut[pid] = self._debut.get(pid, 0) + 1
            if self._debut[pid] < 3:
                continue
            self.last_raw.append((pid, uv))
            pts = {lm: (float(uv[sj, 0]), float(uv[sj, 1]))
                   for sj, lm in _SMPL2LM.items() if sj < len(uv)}
            if len(pts) < len(_SMPL2LM):
                continue
            self.pos3d[pid] = tuple(float(v) for v in trans[n].cpu())
            out.append(PersonPose(pid=pid, pts=pts, vis={k: 1.0 for k in pts}))
        for pid in list(self._debut):                           # absent -> streak resets
            if pid not in seen_now:
                del self._debut[pid]
        return out

    def close(self):
        pass


class AsyncCoMotionPoseEstimator:
    """Non-blocking wrapper (the probe's async pattern, packaged for the engine):
    inference runs in a background thread on the LATEST frame only; estimate() returns
    the most recent COMPLETED result immediately. The live loop stays at camera rate
    while skeletons update at CoMotion speed (~3fps) — poses are ≤ ~0.3s stale, which
    is irrelevant for relations judged on a seconds timescale."""

    def __init__(self, **kw):
        import threading
        self._inner = CoMotionPoseEstimator(**kw)
        self._lock = threading.Lock()
        self._frame = None
        self._people: List[PersonPose] = []
        self.last_raw: List[Tuple[int, np.ndarray]] = []
        self.pos3d = self._inner.pos3d
        self._stop = False
        threading.Thread(target=self._work, daemon=True).start()

    def _work(self):
        import time as _t
        while not self._stop:
            with self._lock:
                fr, self._frame = self._frame, None
            if fr is None:
                _t.sleep(0.005)
                continue
            people = self._inner.estimate(fr)
            with self._lock:
                self._people = people
                self.last_raw = list(self._inner.last_raw)

    def estimate(self, frame_bgr) -> List[PersonPose]:
        with self._lock:
            self._frame = frame_bgr.copy()
            return list(self._people)

    def close(self):
        self._stop = True


# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    import argparse, time
    import cv2

    ap = argparse.ArgumentParser(description="CoMotion live probe: fps + skeleton overlay")
    ap.add_argument("--camera", default="0")
    args = ap.parse_args()
    cap = cv2.VideoCapture(int(args.camera) if args.camera.isdigit() else args.camera)
    est = CoMotionPoseEstimator()
    print("q to quit — first frame prints the key/shape dump (send it to Claude if "
          "extraction comes back empty)")
    # ASYNC design: the display loop runs at full webcam rate; inference runs in a
    # background thread on the LATEST frame only (intermediate frames are skipped —
    # the "frameskip" suggestion, made adaptive). Skeletons are the most recent result,
    # so they lag ~1 inference (~0.3s) behind a perfectly smooth feed.
    import threading
    from collections import deque
    stamps = deque(maxlen=10)            # inference fps (rolling)
    shared = {"frame": None, "people": [], "stop": False}

    def worker():
        while not shared["stop"]:
            fr = shared["frame"]
            if fr is None:
                time.sleep(0.005)
                continue
            shared["frame"] = None       # claim the latest frame; newer ones replace it
            shared["people"] = est.estimate(fr)
            shared["raw"] = list(est.last_raw)
            stamps.append(time.time())

    threading.Thread(target=worker, daemon=True).start()
    while True:
        ok, fr = cap.read()
        if not ok:
            continue
        shared["frame"] = fr.copy()      # hand the freshest frame to the worker
        for pid, uv in shared.get("raw", []):   # FULL 27-joint skeleton (slightly stale)
            for a, b in SMPL_EDGES:
                cv2.line(fr, (int(uv[a, 0]), int(uv[a, 1])),
                         (int(uv[b, 0]), int(uv[b, 1])), (60, 230, 60), 3)
            for j in range(len(uv)):            # every joint as a dot
                cv2.circle(fr, (int(uv[j, 0]), int(uv[j, 1])), 4, (30, 30, 30), -1)
            # NOTE: gaze stays with MediaPipe (gaze.py). Tested 2026-06-11: CoMotion's
            # 3 face-aux points are nose/nose/ear (not eyes) — no usable facing geometry.
            # The rigorous route would be FK on SMPL head rotation; deprioritized.
            cv2.putText(fr, f"p{pid}", (int(uv[15, 0]) + 10, int(uv[15, 1]) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 210, 60), 2)
        ifps = (len(stamps) - 1) / max(1e-6, stamps[-1] - stamps[0]) if len(stamps) > 1 else 0
        cv2.putText(fr, f"display: live   inference: {ifps:.1f} fps   "
                    f"{len(shared['people'])} people",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.imshow("comotion probe", fr)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    shared["stop"] = True
    cap.release(); cv2.destroyAllWindows()
