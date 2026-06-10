"""
depth.py — monocular DEPTH from a plain RGB frame (no depth camera, no added hardware).

Wraps Depth-Anything V2 (a software model) so the gate can tell "in front of / behind"
from a single ordinary image. This replaces the 2D band-aids (size cap, person blacklist)
with the real distinguisher: two boxes are related only if they're at a SIMILAR depth; a
thing behind a big foreground object is at a DIFFERENT depth -> not "inside/on" it. The
camera stays tiny — depth is computed on the laptop. Output is RELATIVE depth (good for
ordering / "same plane?"), not metric centimetres.

On your machine:  pip install transformers   (torch you already have)
First use downloads the small model (~100MB). Runs on Apple-Silicon MPS / CPU.
"""

from __future__ import annotations
import numpy as np


class DepthAnything:
    """depth = DepthAnything();  dmap = depth.predict(bgr_frame)  -> HxW float in [0,1]
    (larger = nearer, after our normalisation; only RELATIVE values are meaningful)."""
    def __init__(self, model="depth-anything/Depth-Anything-V2-Small-hf",
                 device=None, max_side=384):
        try:
            from transformers import pipeline
            import torch
        except ImportError:
            raise SystemExit("Depth needs transformers. Install:\n    pip install transformers")
        if device is None:
            device = ("mps" if torch.backends.mps.is_available()
                      else (0 if torch.cuda.is_available() else -1))
        self.pipe = pipeline("depth-estimation", model=model, device=device)
        self.max_side = max_side                 # downscale for speed; per-box median is robust

    def predict(self, bgr) -> np.ndarray:
        import cv2
        from PIL import Image
        h, w = bgr.shape[:2]
        scale = min(1.0, self.max_side / max(h, w))
        small = cv2.resize(bgr, (int(w * scale), int(h * scale))) if scale < 1.0 else bgr
        pil = Image.fromarray(cv2.cvtColor(small, cv2.COLOR_BGR2RGB))
        d = np.asarray(self.pipe(pil)["depth"], dtype=np.float32)   # relative, ~0..255
        d = cv2.resize(d, (w, h))                                   # back to full size
        lo, hi = float(d.min()), float(d.max())
        return (d - lo) / (hi - lo + 1e-6)                          # normalise to 0..1


def median_depth(box, depth_map) -> float:
    """Median depth inside a box (robust to a few stray pixels). Returns 0..1 or None."""
    if depth_map is None:
        return None
    H, W = depth_map.shape[:2]
    x1, y1, x2, y2 = [int(v) for v in box]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(W, x2), min(H, y2)
    if x2 <= x1 or y2 <= y1:
        return None
    return float(np.median(depth_map[y1:y2, x1:x2]))
