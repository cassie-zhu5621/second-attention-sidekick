# brain/ — the offline intelligence (software milestone)

The sidekick's "noticing intelligence," runnable on your laptop with **no camera and
(mostly) no installs**. Works on `scores_cache.json` (220 photos already rated 0–1 on 9
dimensions), so it's all offline — no API spend.

## Files
| file | what it does |
|---|---|
| `session.py` | **the demo to run first.** Talk to the sidekick by typing; watch the 3 learning layers. |
| `taste.py` | the formula: `worth = Σ wₐ·sₐ` + personalization + EMA update. |
| `brain.py` | scores one image on the dimensions with a VLM (needs API key; has an OFFLINE test mode). |
| `loop.py` | rank a folder of photos by worth-noticing (the "notice" behaviour). |
| `audit.py` | dimension audit: range / redundancy / factors (needs `numpy`). |
| `regress.py` | learn the weights from pairwise picks (needs `numpy`). |
| `memory.py` | EMA working taste + long-term per-place memory. |
| `scores_cache.json` | the data: `{photo: {dimension: score 0–1}}`. |

## Run it (no install)
```
cd brain
python3 session.py
```
- type `I love story and people` → **Layer 1** (active): ranking re-sorts
- type `keep 1` / `skip 3` → **Layer 2** (passive): learns from your reaction
- blank line → ends, saves `taste_profile_lab.json`
- run again → **Layer 3** (long-term): it starts "remembering you." Delete `taste_profile_lab.json` to forget.

## Run the analysis (needs numpy once)
```
pip3 install numpy
python3 audit.py scores_cache.json     # which dimensions are good / redundant / how many factors
python3 regress.py                     # learn a taste from pairwise picks (self-test)
```

## What `scores_cache.json` looks like
```json
{
  "capture_20260420_172513_4.60.jpg": {
    "conflict": 0.30, "tension": 0.50, "story": 0.40, "aesthetic": 0.20,
    "novelty": 0.20, "color_harmony": 0.60, "mystery": 0.60,
    "decisive_moment": 0.05, "frame_within_frame": 0.10
  },
  ...  // one such row per image, 220 total
}
```
