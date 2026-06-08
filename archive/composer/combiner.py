"""
combiner.py — pure-arithmetic compose of per-prompt scores into one ranking.
---------------------------------------------------------------------------
NO MACHINE LEARNING IN THIS FILE. By design.

The build plan is explicit: V1's combiner is a weighted mean. The user IS
the combiner. ML would be circular here (we'd be fitting to the user's own
labels), which is exactly why V2 was cut from the project.

Public API:
    compose(scores_cache, weights, image_filter=None) -> list[ImageResult]

    ImageResult = {
        "filename": str,
        "score": float,          # normalized to [0,1] across corpus, for display
        "raw": float,            # unnormalized weighted sum, for debugging
        "contributions": {prompt_id: weight * raw_score},  # explanation breakdown
    }

The function is fast enough to run on every slider drag — 220 images × 9
dimensions takes <5ms on an M4.
"""

from __future__ import annotations

from typing import Iterable, TypedDict


class ImageResult(TypedDict):
    filename: str
    score: float
    raw: float
    contributions: dict[str, float]


def compose(
    scores_cache: dict[str, dict[str, float]],
    weights: dict[str, float],
    image_filter: Iterable[str] | None = None,
) -> list[ImageResult]:
    """Compose per-image rankings from per-dimension VLM scores.

    Args:
        scores_cache:
            {filename: {prompt_id: score_in_[0,1]}}
            (i.e. scores_cache.json contents)
        weights:
            {prompt_id: weight}
            The UI passes the current slider state. Prompts NOT in this dict
            are excluded from the composition (the checkbox is off). A prompt
            present with weight=0 is also effectively excluded.
        image_filter:
            If given, only compose for these filenames. Otherwise compose for
            every image in scores_cache.

    Returns:
        list of ImageResult, sorted by `score` descending.
    """
    # 1. Compute raw weighted sums for each image.
    candidates = (image_filter if image_filter is not None
                  else scores_cache.keys())
    raw_results: list[ImageResult] = []
    for filename in candidates:
        per_image_scores = scores_cache.get(filename, {})
        if not per_image_scores:
            continue
        raw_sum = 0.0
        contributions: dict[str, float] = {}
        for prompt_id, weight in weights.items():
            if weight == 0:
                continue
            s = per_image_scores.get(prompt_id)
            if s is None:
                # Image was added after this prompt was scored — silently skip.
                # The /scoring dashboard will catch this gap.
                continue
            contrib = weight * s
            raw_sum += contrib
            contributions[prompt_id] = contrib
        raw_results.append({
            "filename":      filename,
            "raw":           raw_sum,
            "score":         raw_sum,  # placeholder; overwritten below
            "contributions": contributions,
        })

    if not raw_results:
        return []

    # 2. Normalize raw sums to [0, 1] across the corpus for display.
    #    Why normalize: the slider weight scale is arbitrary — sum_of_weights
    #    could be 0.3 or 7.0 depending on user input. Normalizing makes the
    #    displayed score independent of the weight magnitudes; only RELATIVE
    #    rankings matter to the user.
    raw_min = min(r["raw"] for r in raw_results)
    raw_max = max(r["raw"] for r in raw_results)
    span = raw_max - raw_min
    if span < 1e-9:
        # All images scored equally (e.g. all weights = 0). Hand back 0.5 each.
        for r in raw_results:
            r["score"] = 0.5
    else:
        for r in raw_results:
            r["score"] = (r["raw"] - raw_min) / span

    # 3. Sort high → low. Stable secondary sort by filename keeps ties consistent
    #    so the UI doesn't shuffle equal-scored images on every recomputation.
    raw_results.sort(key=lambda r: (-r["score"], r["filename"]))
    return raw_results


# ---------------------------------------------------------------------------
# CLI sanity check:
#   python combiner.py story=1.0 aesthetic=0.5
# Prints top 10 images by the given weights using the live cache.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json
    import sys
    from pathlib import Path

    SCORES = Path(__file__).resolve().parent / "scores_cache.json"
    cache = json.loads(SCORES.read_text())

    weights: dict[str, float] = {}
    for arg in sys.argv[1:]:
        if "=" not in arg:
            print(f"usage: python combiner.py prompt_id=weight [prompt_id=weight ...]")
            sys.exit(1)
        k, v = arg.split("=", 1)
        weights[k.strip()] = float(v)

    if not weights:
        # Default: equal weight on every prompt in the first image's cache
        sample = next(iter(cache.values()), {})
        weights = {k: 1.0 for k in sample}
        print(f"(no weights given; using {weights})")

    results = compose(cache, weights)
    print(f"\nTop 10 of {len(results)} images:")
    for r in results[:10]:
        contribs = ", ".join(f"{k}={v:+.2f}" for k, v in
                             sorted(r["contributions"].items(),
                                    key=lambda kv: -abs(kv[1]))[:3])
        print(f"  {r['score']:.2f}  {r['filename']:48}  [{contribs}]")
