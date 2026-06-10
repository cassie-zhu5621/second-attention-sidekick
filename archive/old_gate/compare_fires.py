"""
compare_fires.py — eyeball WHAT changed at each fired frame.

For every frame the gate FIRES on, render the fired frame next to the PREVIOUS frame
(side by side, both with their clean scene-graph overlay — overlapping OFF), so you can
verify by eye: did a real relational change happen here? This is the cheap manual
precision check on your own data (pair it with spotting missed changes on non-fired frames).

Uses the boxes already stored in graphs.json (no detector needed) + the original images.

    python compare_fires.py --images /path/to/dataset_folder
    # graphs.json defaults to <images>/_perception/graphs.json
"""

from __future__ import annotations
import argparse, json, os
import cv2
from perceive import build_graph, Detection
from config_surprise import ConfigSurpriseGate, TemporalConfigGate
from viz import draw_overlay


def recon_graph(rec):
    """Rebuild a clean scene graph (overlapping OFF) from a graphs.json record's stored boxes."""
    dets = [Detection(rec["nodes"][i], tuple(rec["boxes"][i])) for i in rec["nodes"]]
    return build_graph(dets, tuple(rec["wh"]))


def stack(a, b, h=520):
    ra = cv2.resize(a, (int(a.shape[1] * h / a.shape[0]), h))
    rb = cv2.resize(b, (int(b.shape[1] * h / b.shape[0]), h))
    sep = 255 * (0 * ra[:, :6])  # thin separator
    import numpy as np
    return np.hstack([ra, np.full((h, 6, 3), 60, np.uint8), rb])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", required=True)
    ap.add_argument("--graphs", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--limit", type=int, default=0, help="max fired frames to render (0=all)")
    args = ap.parse_args()

    gpath = args.graphs or os.path.join(args.images, "_perception", "graphs.json")
    out = args.out or os.path.join(args.images, "_perception", "compares")
    os.makedirs(out, exist_ok=True)
    D = json.load(open(gpath))

    gate = TemporalConfigGate(gate=ConfigSurpriseGate(mode="habituation", agg="max",
                                                      threshold=args.threshold))
    made = 0
    for i, rec in enumerate(D):
        d = gate.step(rec["nodes"], [tuple(e) for e in rec["edges"]])
        if not d["event"] or i == 0:
            continue
        prev = D[i - 1]
        img_p = cv2.imread(os.path.join(args.images, prev["file"]))
        img_f = cv2.imread(os.path.join(args.images, rec["file"]))
        if img_p is None or img_f is None:
            continue
        ann_p = draw_overlay(img_p, recon_graph(prev), caption="BEFORE")
        ann_f = draw_overlay(img_f, recon_graph(rec),
                             caption=f"FIRED  {TemporalConfigGate.describe(d['delta_added'], d['top'])[:60]}")
        cv2.imwrite(os.path.join(out, f"compare_{i:04d}.jpg"), stack(ann_p, ann_f))
        made += 1
        if args.limit and made >= args.limit:
            break
    print(f"{made} comparison images -> {out}")
    print("Each: LEFT=previous frame, RIGHT=the frame that fired (+ what changed). "
          "Eyeball whether a real relational change happened.")


if __name__ == "__main__":
    main()
