"""
run_perception.py — BATCH TEST of the perception step on a whole folder of frames.

This is the program to run tomorrow on the dataset you shoot from one fixed position.
For every image it runs:  detector → stable scene graph → annotated overlay,
and it saves:
  - <name>_viz.jpg  : the image with boxes + relations + object/relation counts drawn on it
  - graphs.json     : every frame's scene graph (nodes/edges/boxes/surfaces) — so later you
                      can replay the SEQUENCE through the gate OFFLINE without re-running the
                      detector (perception is the expensive part; do it once, reuse).
It also prints a summary so you can eyeball quality and decide what to tune.

ON YOUR MACHINE (real detector — this is the normal path, NOT hand-labelled boxes):
    pip install ultralytics
    python run_perception.py --images /path/to/your/dataset \
        --vocab "person,laptop,cup,chair,desk,monitor,keyboard,book,bag,phone,potted plant,bottle"

PLUMBING TEST (no detector available, e.g. this sandbox): add  --mock
TUNE later with: --near-frac --min-score --surface-frac --surface-min-holds --conf
If the camera orientation is roughly fixed, pass --up "ux,uy" to also get on/above relations.
"""

from __future__ import annotations
import argparse, glob, json, os
from collections import Counter
import cv2

from perceive import build_graph, Detection
from viz import draw_overlay

DEFAULT_VOCAB = ["person", "laptop", "monitor", "keyboard", "mouse", "cup", "bottle", "mug",
                 "chair", "desk", "table", "book", "backpack", "bag", "phone", "potted plant",
                 "plant", "whiteboard", "shelf", "bookshelf", "box", "screen", "headphones", "lamp"]


class _DemoDetector:
    """--mock: returns a few boxes scaled to each image, just to verify the batch plumbing
    (folder walk, drawing, JSON dump) without a real model."""
    def detect(self, image):
        h, w = image.shape[:2]
        return [Detection("person", (int(0.05*w), int(0.40*h), int(0.30*w), h)),
                Detection("laptop", (int(0.42*w), int(0.62*h), int(0.70*w), int(0.95*h))),
                Detection("desk",   (0, int(0.55*h), w, h), 0.9)]


def make_detector(args):
    if args.mock:
        print("[--mock] using demo boxes (NO real detector). On your machine drop --mock.")
        return _DemoDetector()
    from perceive import YoloWorldDetector
    vocab = [v.strip() for v in args.vocab.split(",")] if args.vocab else DEFAULT_VOCAB
    print(f"[detector] YOLO-World ({args.weights}), {len(vocab)} classes, conf={args.conf}, "
          f"device={args.device or 'auto'}")
    return YoloWorldDetector(vocab, weights=args.weights, conf=args.conf, device=args.device)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", required=True, help="folder of frames")
    ap.add_argument("--out", default=None, help="output folder (default: <images>/_perception)")
    ap.add_argument("--vocab", default=",".join(DEFAULT_VOCAB))
    ap.add_argument("--weights", default="yolov8s-world.pt")
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--near-frac", type=float, default=0.18)
    ap.add_argument("--min-score", type=float, default=0.30)
    ap.add_argument("--surface-frac", type=float, default=0.33)
    ap.add_argument("--surface-min-holds", type=int, default=3)
    ap.add_argument("--up", default=None, help="'ux,uy' up-vector if camera orientation is known")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--device", default=None, help="None=auto, 'cpu', or '0' for first GPU")
    ap.add_argument("--with-overlapping", action="store_true",
                    help="re-enable the 'overlapping' relation (off by default: it's ~57%% "
                         "depth-occlusion bloat)")
    ap.add_argument("--min-area", type=float, default=0.0,
                    help="ignore objects smaller than this fraction of the frame "
                         "(e.g. 0.015 in a cluttered/far scene; ~0 for a close single desk)")
    ap.add_argument("--mock", action="store_true")
    args = ap.parse_args()

    out = args.out or os.path.join(args.images, "_perception")
    os.makedirs(out, exist_ok=True)
    up = tuple(float(x) for x in args.up.split(",")) if args.up else None
    det = make_detector(args)

    files = sorted(sum([glob.glob(os.path.join(args.images, e))
                        for e in ("*.jpg", "*.jpeg", "*.png", "*.JPG")], []))
    if args.limit:
        files = files[:args.limit]
    print(f"{len(files)} images -> {out}\n")

    records, rel_hist, obj_hist, n_surf = [], Counter(), Counter(), 0
    csv_rows = ["file,n_objects,n_relations,n_surfaces,objects"]
    for i, fp in enumerate(files):
        img = cv2.imread(fp)
        if img is None:
            print("  skip (unreadable):", os.path.basename(fp)); continue
        H, W = img.shape[:2]
        dets = det.detect(img)
        g = build_graph(dets, (W, H), up=up, near_frac=args.near_frac, min_score=args.min_score,
                        surface_frac=args.surface_frac, surface_min_holds=args.surface_min_holds,
                        overlapping=args.with_overlapping, min_area_frac=args.min_area)
        cap = f"{len(g.nodes)} objects, {len(g.edges)} relations"
        ann = draw_overlay(img, g, caption=cap)
        name = os.path.splitext(os.path.basename(fp))[0]
        cv2.imwrite(os.path.join(out, name + "_viz.jpg"), ann)
        surfs = getattr(g, "surfaces", [])
        records.append({"file": os.path.basename(fp), "wh": [W, H], "nodes": g.nodes,
                        "edges": g.edges, "boxes": g.boxes, "surfaces": surfs})
        objs = sorted(g.nodes.values())
        csv_rows.append(f'{os.path.basename(fp)},{len(g.nodes)},{len(g.edges)},{len(surfs)},'
                        f'{"|".join(objs)}')
        for e in g.edges: rel_hist[e[1]] += 1
        for t in g.nodes.values(): obj_hist[t] += 1
        if surfs: n_surf += 1
        if i % 25 == 0 or i == len(files) - 1:
            print(f"  [{i+1}/{len(files)}] {name}: {cap}")

    n = max(len(records), 1)
    json.dump(records, open(os.path.join(out, "graphs.json"), "w"), indent=1)
    open(os.path.join(out, "per_frame.csv"), "w").write("\n".join(csv_rows))
    summary = {"frames": len(records),
               "avg_objects_per_frame": round(sum(obj_hist.values()) / n, 2),
               "avg_relations_per_frame": round(sum(rel_hist.values()) / n, 2),
               "frames_with_surface": n_surf,
               "object_frequency": dict(obj_hist.most_common()),
               "rarest_objects": [o for o, _ in obj_hist.most_common()[-8:]],
               "relation_types": dict(rel_hist)}
    json.dump(summary, open(os.path.join(out, "summary.json"), "w"), indent=1)

    print("\n==== SUMMARY ====")
    print(f"frames: {summary['frames']} | avg objects/frame: {summary['avg_objects_per_frame']} | "
          f"avg relations/frame: {summary['avg_relations_per_frame']} | "
          f"frames with a surface: {n_surf}")
    print("relation types:", dict(rel_hist))
    print("most common objects:", dict(obj_hist.most_common(12)))
    print("rarest objects     :", summary["rarest_objects"], " <- candidates for 'unusual'")
    print(f"\nsaved in {out}:  *_viz.jpg  |  graphs.json (replay through the gate offline)  |  "
          f"per_frame.csv  |  summary.json")


if __name__ == "__main__":
    main()
