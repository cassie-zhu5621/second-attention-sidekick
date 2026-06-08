"""
brain.py — score one image on all dimensions with an off-the-shelf VLM.

Self-contained: no dependency on the old Spatial_Camera / Composer code.
One VLM call returns all dimension scores as JSON (cheap & fast for v1; you can
switch to per-dimension calls later for the relative-attributes framing).

Modes:
  - REAL:    set ANTHROPIC_API_KEY, `pip install anthropic`. Uses Claude.
  - OFFLINE: set SECONDATTN_OFFLINE=1 — deterministic pseudo-scores, no API,
             so you can test the whole pipeline (loop, ranking, personalization)
             before paying for / wiring the VLM.
"""

import os
import json
import base64
import hashlib
from taste import DIMENSIONS, DIM_NAMES

MODEL = os.environ.get("SECONDATTN_MODEL", "claude-sonnet-4-6")


def _offline_scores(image_path: str) -> dict:
    """Deterministic pseudo-scores from the filename, for pipeline testing."""
    scores = {}
    for d in DIM_NAMES:
        h = hashlib.md5(f"{os.path.basename(image_path)}::{d}".encode()).hexdigest()
        scores[d] = (int(h[:8], 16) % 1000) / 1000.0
    return scores


def _media_type(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    return {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".webp": "image/webp", ".gif": "image/gif"}.get(ext, "image/jpeg")


def _build_prompt() -> str:
    lines = ["You are scoring one image on several named dimensions of a 'worth-noticing moment'.",
             "For EACH dimension, return a number from 0.0 to 1.0 using its rubric.",
             "Return ONLY a JSON object mapping dimension name -> number. No prose.\n",
             "Dimensions:"]
    for name, (_group, rubric) in DIMENSIONS.items():
        lines.append(f"- {name}: {rubric}")
    return "\n".join(lines)


def score_dims(image_path: str) -> dict:
    """Return {dimension: 0..1} for one image."""
    if os.environ.get("SECONDATTN_OFFLINE") == "1":
        return _offline_scores(image_path)

    import anthropic  # lazy: only needed in REAL mode
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    with open(image_path, "rb") as f:
        b64 = base64.standard_b64encode(f.read()).decode()

    msg = client.messages.create(
        model=MODEL,
        max_tokens=400,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64",
                 "media_type": _media_type(image_path), "data": b64}},
                {"type": "text", "text": _build_prompt()},
            ],
        }],
    )
    text = msg.content[0].text.strip()
    # be forgiving about ```json fences
    if text.startswith("```"):
        text = text.split("```")[1].replace("json", "", 1).strip()
    raw = json.loads(text)
    return {d: float(raw.get(d, 0.0)) for d in DIM_NAMES}


if __name__ == "__main__":
    import sys
    os.environ.setdefault("SECONDATTN_OFFLINE", "1")
    p = sys.argv[1] if len(sys.argv) > 1 else "example.jpg"
    print(json.dumps(score_dims(p), indent=2))
