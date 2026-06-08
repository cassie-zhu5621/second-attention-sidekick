"""
loop.py — the noticing loop. v1 runs WITHOUT the gimbal so you can see the
intelligence today: point it at a folder of photos, it scores each on the
taste dimensions, ranks them, and 'captures' the top moments.

Usage:
  # offline test (no API, dummy scores) — proves the pipeline:
  SECONDATTN_OFFLINE=1 python loop.py --folder ./photos --topk 5

  # real (needs ANTHROPIC_API_KEY + `pip install anthropic`):
  python loop.py --folder ./photos --topk 5

  # personalization demo — emphasize dimensions you care about:
  SECONDATTN_OFFLINE=1 python loop.py --folder ./photos --like story_potential aesthetic

Later: --source webcam / --source gimbal (needs opencv + rig.py) for live sweep.
"""

import os
import sys
import shutil
import argparse

import taste
from brain import score_dims

IMG_EXT = (".jpg", ".jpeg", ".png", ".webp")


def list_images(folder):
    return sorted(os.path.join(folder, f) for f in os.listdir(folder)
                  if f.lower().endswith(IMG_EXT))


def rank_folder(folder, weights, topk=5):
    imgs = list_images(folder)
    if not imgs:
        print(f"No images in {folder}"); return []
    ranked = []
    for p in imgs:
        dims = score_dims(p)
        ranked.append((compose := taste.compose(dims, weights), p, dims))
        print(f"  scored {os.path.basename(p)}  -> {compose:.3f}")
    ranked.sort(key=lambda r: r[0], reverse=True)
    return ranked[:topk]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--folder", required=True, help="folder of images to notice over")
    ap.add_argument("--topk", type=int, default=5)
    ap.add_argument("--like", nargs="*", default=[],
                    help="dimensions to emphasize (personalization), e.g. --like story_potential aesthetic")
    ap.add_argument("--out", default="captures", help="where to copy the captured moments")
    args = ap.parse_args()

    weights = taste.default_weights()
    if args.like:
        weights = taste.up_weight(weights, args.like, amount=1.5)
        print(f"Personalized taste — emphasizing: {', '.join(args.like)}\n")
    else:
        print("Equal-weight taste (no personalization)\n")

    top = rank_folder(args.folder, weights, args.topk)
    if not top:
        return
    os.makedirs(args.out, exist_ok=True)
    print(f"\n=== Top {len(top)} worth-noticing moments ===")
    for rank, (score, path, dims) in enumerate(top, 1):
        top_dims = sorted(dims.items(), key=lambda kv: weights.get(kv[0],0)*kv[1], reverse=True)[:3]
        why = ", ".join(f"{d}={v:.2f}" for d, v in top_dims)
        print(f"{rank}. {os.path.basename(path)}  score={score:.3f}  (why: {why})")
        shutil.copy(path, os.path.join(args.out, f"{rank:02d}_{os.path.basename(path)}"))
    print(f"\nCaptured copies saved to ./{args.out}/")


if __name__ == "__main__":
    main()
