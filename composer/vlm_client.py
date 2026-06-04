"""
vlm_client.py — generic VLM scorer for the Interestingness Composer (Part 2)
-----------------------------------------------------------------------------
ONE primitive: score a single image on a single named dimension via VLM.

    from vlm_client import score_one
    s = score_one(jpeg_bytes, prompt_text="Rate this image on tension ...")
    # → 0.62

This is the generalized form of Part 1's `score_metrics()`. Part 1 hardcoded
three dimensions (Conflict / Tension / Story) into one combined prompt; Part 2
treats each dimension as its own (prompt, score) pair so users can compose
them at will. The old `score_metrics()` is still here as a thin wrapper for
any Part 1 caller that wants the bundled 3-metric call.

Default backend: Anthropic Claude (claude-sonnet-4-6).
Adding GPT-5 or Gemini later = add one function to `_BACKENDS`.

CLI sanity check:
    export ANTHROPIC_API_KEY=sk-ant-...
    python vlm_client.py path/to/photo.jpg "Is this image dramatic? 0=no 1=yes"
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
import time
from io import BytesIO
from typing import Callable, TypedDict

log = logging.getLogger("vlm-client")

# ---------------------------------------------------------------------------
# Config — same defaults as Part 1 so cached scores transfer cleanly.
# ---------------------------------------------------------------------------

DEFAULT_BACKEND      = os.environ.get("VLM_BACKEND", "claude")
DEFAULT_CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")
MAX_TOKENS           = 64    # We ask for a single float, not a JSON object.
MAX_IMAGE_DIM        = int(os.environ.get("VLM_MAX_IMAGE_DIM", "768"))
JPEG_QUALITY         = 85

# Prompt wrapper for the generic single-dimension call. The user's dimension
# text is dropped into {prompt_text}. The model is instructed to return ONLY
# a number — this is the smallest possible reply, cheap and easy to parse.
_SCORE_ONE_TEMPLATE = """You are evaluating a single image on ONE dimension.

DIMENSION
{prompt_text}

Output exactly one number between 0.0 and 1.0 — nothing else.
0.0 means the dimension does not apply at all.
1.0 means the dimension applies strongly.
Use the full range; do not cluster near 0.5.
"""

# ---------------------------------------------------------------------------
# Bundled-3-metric prompt (Part 1 backward compat — used by score_metrics)
# ---------------------------------------------------------------------------

_BUNDLED_PROMPT = """You are evaluating a single image on three independent dimensions.
For each dimension, output a number between 0.0 and 1.0.

CONFLICT — semantic discord between elements in the image.
  0.0 = harmonious, expected together (dishes on a dining table).
  1.0 = strongly discordant (a dog at a wedding ceremony).

SEMANTIC TENSION — ambiguity, unresolved symbolism, psychological charge
that invites further looking.
  0.0 = flat, fully explained at first glance.
  1.0 = strongly charged or ambiguous (empty chair in a closed room,
        partially obscured face).

STORY POTENTIAL — whether the image suggests something happened before
or something is about to happen.
  0.0 = static, non-narrative scene (tidy desk).
  1.0 = strongly narrative (half-finished meal, footprints in fresh snow).

Output exactly this JSON, nothing else:
{"conflict": 0.X, "tension": 0.X, "story": 0.X}
"""


class Layer2Result(TypedDict):
    conflict: float
    tension: float
    story: float
    latency_ms: float
    backend: str
    model: str


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

_FLOAT_RE = re.compile(r"-?\d+(?:\.\d+)?")
_JSON_BLOCK_RE = re.compile(r"\{[^{}]*\}", re.DOTALL)


def _parse_first_float(text: str) -> float:
    """Pull the first float out of a possibly-noisy VLM reply.

    The model is asked for a bare number, but sometimes wraps it in
    backticks or prefaces it with 'Score: '. Be permissive — bail to
    0.0 only if no number at all is present (and log it).
    """
    m = _FLOAT_RE.search(text.strip())
    if not m:
        log.warning("vlm: no number found in reply %r — defaulting to 0.0", text[:100])
        return 0.0
    return float(m.group(0))


def _parse_json_response(text: str) -> dict:
    """Extract a JSON object — used only by the bundled (Part 1) path."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = _JSON_BLOCK_RE.search(text)
    if not m:
        raise ValueError(f"No JSON object found in VLM response: {text[:200]!r}")
    return json.loads(m.group(0))


def _resize_for_api(jpeg_bytes: bytes, max_dim: int = MAX_IMAGE_DIM) -> bytes:
    """Downscale a JPEG to `max_dim` on the longer side; preserves aspect.

    Same cost trick as Part 1 — Claude's image-token count scales with
    pixel area, and 768px is plenty for subjective 0–1 grading.
    """
    if max_dim <= 0:
        return jpeg_bytes
    try:
        from PIL import Image
    except ImportError:
        log.warning("Pillow not installed; skipping resize and sending original bytes")
        return jpeg_bytes

    img = Image.open(BytesIO(jpeg_bytes))
    if max(img.size) <= max_dim:
        return jpeg_bytes  # Already small.

    original_size = img.size
    img = img.convert("RGB")
    img.thumbnail((max_dim, max_dim), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=JPEG_QUALITY)
    resized = buf.getvalue()
    log.debug(
        "resized %s → %s, %d → %d bytes",
        original_size, img.size, len(jpeg_bytes), len(resized),
    )
    return resized


def _clamp01(x) -> float:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, v))


def _pick(d: dict, *keys: str, default: float = 0.0):
    lowered = {k.lower(): v for k, v in d.items()}
    for k in keys:
        if k.lower() in lowered:
            return lowered[k.lower()]
    return default


# ---------------------------------------------------------------------------
# Backends — each backend exposes one function that takes (jpeg_bytes, model,
# full_prompt_text) and returns the raw model reply as a string.
# ---------------------------------------------------------------------------

def _call_claude_raw(jpeg_bytes: bytes, model: str, prompt_text: str) -> str:
    try:
        import anthropic
    except ImportError as e:
        raise ImportError(
            "anthropic package not installed. Run: pip install anthropic"
        ) from e

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not set. "
            "Export it: export ANTHROPIC_API_KEY=sk-ant-..."
        )

    client = anthropic.Anthropic(api_key=api_key)
    jpeg_bytes = _resize_for_api(jpeg_bytes)
    b64 = base64.b64encode(jpeg_bytes).decode("ascii")

    response = client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": b64,
                        },
                    },
                    {"type": "text", "text": prompt_text},
                ],
            }
        ],
    )
    return "".join(block.text for block in response.content if hasattr(block, "text"))


_BACKENDS: dict[str, Callable[[bytes, str, str], str]] = {
    "claude": _call_claude_raw,
}

_DEFAULT_MODELS: dict[str, str] = {
    "claude": DEFAULT_CLAUDE_MODEL,
}


# ---------------------------------------------------------------------------
# Public API — Part 2 primitive
# ---------------------------------------------------------------------------

def score_one(
    jpeg_bytes: bytes,
    prompt_text: str,
    backend: str = DEFAULT_BACKEND,
    model: str | None = None,
) -> float:
    """Return a single 0–1 score for the image on the given dimension.

    `prompt_text` is the natural-language description of the dimension —
    what the user typed (or selected) in the Composer UI. It is dropped
    into a thin scaffolding prompt that instructs the model to return a
    bare number.

    Args:
        jpeg_bytes:  raw JPEG bytes (any resolution).
        prompt_text: description of the dimension to grade on.
        backend:     "claude" (default).
        model:       override the default model for the chosen backend.

    Returns:
        float in [0.0, 1.0].

    Raises the same exceptions as the backend call (missing key, bad JSON, ...).
    """
    if backend not in _BACKENDS:
        raise ValueError(f"Unknown VLM backend {backend!r}. Available: {list(_BACKENDS)}")
    model_id = model or _DEFAULT_MODELS[backend]

    full_prompt = _SCORE_ONE_TEMPLATE.format(prompt_text=prompt_text.strip())

    t0 = time.perf_counter()
    raw_reply = _BACKENDS[backend](jpeg_bytes, model_id, full_prompt)
    latency_ms = (time.perf_counter() - t0) * 1000

    score = _clamp01(_parse_first_float(raw_reply))
    log.info(
        "vlm[%s]: score=%.2f latency=%.0fms prompt=%r",
        backend, score, latency_ms, prompt_text[:50],
    )
    return score


# ---------------------------------------------------------------------------
# Backward-compatibility: Part 1's bundled 3-metric call.
# Useful when bootstrapping scores_cache.json from Part 1's vlm_cache.json.
# ---------------------------------------------------------------------------

def score_metrics(
    jpeg_bytes: bytes,
    backend: str = DEFAULT_BACKEND,
    model: str | None = None,
) -> Layer2Result:
    """Part 1's combined Conflict/Tension/Story scorer. One VLM call, three scores."""
    if backend not in _BACKENDS:
        raise ValueError(f"Unknown VLM backend {backend!r}. Available: {list(_BACKENDS)}")
    model_id = model or _DEFAULT_MODELS[backend]

    t0 = time.perf_counter()
    text = _BACKENDS[backend](jpeg_bytes, model_id, _BUNDLED_PROMPT)
    latency_ms = (time.perf_counter() - t0) * 1000

    raw = _parse_json_response(text)
    result: Layer2Result = {
        "conflict":   _clamp01(_pick(raw, "conflict")),
        "tension":    _clamp01(_pick(raw, "tension", "semantic_tension")),
        "story":      _clamp01(_pick(raw, "story", "story_potential")),
        "latency_ms": round(latency_ms, 1),
        "backend":    backend,
        "model":      model_id,
    }
    log.info(
        "vlm[%s] bundled: conflict=%.2f tension=%.2f story=%.2f latency=%.0fms",
        backend, result["conflict"], result["tension"], result["story"],
        result["latency_ms"],
    )
    return result


# ---------------------------------------------------------------------------
# CLI sanity check
#   python vlm_client.py path/to/image.jpg "Is the subject partially obscured?"
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if len(sys.argv) < 3:
        print('Usage: python vlm_client.py <path/to/image.jpg> "<prompt text>" [backend]')
        sys.exit(1)

    image_path  = sys.argv[1]
    prompt_text = sys.argv[2]
    backend     = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_BACKEND

    with open(image_path, "rb") as f:
        jpeg = f.read()

    score = score_one(jpeg, prompt_text, backend=backend)
    print(f"{score:.3f}")
