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
        for n in valid.nonzero().flatten().tolist():
            pid = int(ids[n])
            uv = p2d[n].cpu().numpy()
            pts = {lm: (float(uv[sj, 0]), float(uv[sj, 1]))
                   for sj, lm in _SMPL2LM.items() if sj < len(uv)}
            if len(pts) < len(_SMPL2LM):
                continue
            self.pos3d[pid] = tuple(float(v) for v in trans[n].cpu())
            out.append(PersonPose(pid=pid, pts=pts, vis={k: 1.0 for k in pts}))
        return out

    def close(self):
        pass


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
            stamps.append(time.time())

    threading.Thread(target=worker, daemon=True).start()
    while True:
        ok, fr = cap.read()
        if not ok:
            continue
        shared["frame"] = fr.copy()      # hand the freshest frame to the worker
        for p in shared["people"]:       # draw last-known skeletons (slightly stale)
            for a, b in ((L_SH, R_SH), (L_SH, L_EL), (L_EL, L_WR), (R_SH, R_EL),
                         (R_EL, R_WR), (L_HIP, R_HIP), (L_SH, L_HIP), (R_SH, R_HIP)):
                cv2.line(fr, tuple(map(int, p.pts[a])), tuple(map(int, p.pts[b])),
                         (60, 230, 60), 3)
            cv2.putText(fr, f"p{p.pid}", tuple(map(int, p.pts[NOSE])),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 210, 60), 2)
        ifps = (len(stamps) - 1) / max(1e-6, stamps[-1] - stamps[0]) if len(stamps) > 1 else 0
        cv2.putText(fr, f"display: live   inference: {ifps:.1f} fps   "
                    f"{len(shared['people'])} people",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.imshow("comotion probe", fr)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    shared["stop"] = True
    cap.release(); cv2.destroyAllWindows()
