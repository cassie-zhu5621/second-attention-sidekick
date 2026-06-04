"""
live_brain.py — score a LIVE camera frame for "worth noticing", given a
free-text preference the user spoke/typed (e.g. "I love animals and people").

This is the real-time companion to brain.py:
  - brain.py    scores a saved image file on 9 abstract dimensions (folder loop).
  - live_brain  scores in-memory JPEG bytes from the live stream, and takes a
    plain-language preference so any taste works without predefined dimensions.

One Claude call returns {worth: 0..1, reason: short text}. Uses a fast model by
default (cheap enough to run in a real-time loop). OFFLINE mode for wiring tests.

Standalone test (grabs ONE frame from the camera and scores it):
    export ANTHROPIC_API_KEY=sk-...
    python3 live_brain.py --camera http://sidekick-cam.local --preference "animals and people"

    # no API / no key — fake score to test plumbing:
    SECONDATTN_OFFLINE=1 python3 live_brain.py --camera http://sidekick-cam.local --preference "x"
"""

import argparse
import base64
import hashlib
import json
import os

MODEL = os.environ.get("SECONDATTN_LIVE_MODEL", "claude-haiku-4-5")  # fast + cheap for a loop


def _offline(jpeg: bytes, preference: str) -> dict:
    h = hashlib.md5(jpeg[:2000] + preference.encode()).hexdigest()
    return {"worth": (int(h[:8], 16) % 1000) / 1000.0, "reason": "offline pseudo-score"}


_GENERIC = {"", "anything", "interesting", "anything interesting", "worth noticing",
            "anything worth noticing", "everything", "whatever", "surprise me"}


def _build_prompt(preference: str) -> str:
    base = (
        "You are the noticing brain of a small companion robot that quietly watches a shared space.\n"
        "Rate 0.0-1.0 how WORTH NOTICING this single frame is right now — the kind of moment a "
        "perceptive person would glance up for: a real human moment or gesture, something surprising "
        "or unusual, striking light or composition, a small story unfolding, something alive or changing. "
        "An empty, static, boring, or blurry view scores low. This is about NOTICING a moment, "
        "not finding a specific object.\n"
    )
    pref = (preference or "").strip()
    if pref.lower() not in _GENERIC:
        base += (f'\nThis person especially cares about / is drawn to: "{pref}". Lean toward moments '
                 "that resonate with that — but a generally striking, worth-noticing moment still counts "
                 "even if unrelated.\n")
    base += '\nReturn ONLY a JSON object, no prose:\n{"worth": <0.0-1.0>, "reason": "<8 words max>"}'
    return base


def score_frame(jpeg: bytes, preference: str, model: str = MODEL) -> dict:
    """Score one JPEG (bytes) for this user. Returns {'worth':0..1,'reason':str}."""
    if os.environ.get("SECONDATTN_OFFLINE") == "1":
        return _offline(jpeg, preference)

    import anthropic  # lazy import
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    b64 = base64.standard_b64encode(jpeg).decode()
    msg = client.messages.create(
        model=model,
        max_tokens=120,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64",
                 "media_type": "image/jpeg", "data": b64}},
                {"type": "text", "text": _build_prompt(preference)},
            ],
        }],
    )
    text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()
    # tolerate stray prose around the JSON
    try:
        s, e = text.index("{"), text.rindex("}") + 1
        out = json.loads(text[s:e])
        return {"worth": float(out.get("worth", 0.0)), "reason": str(out.get("reason", ""))[:60]}
    except Exception:
        return {"worth": 0.0, "reason": f"parse-fail: {text[:40]}"}


# ---------------------------------------------------------------------------
# Composer mode: score the frame on taste.py's 9 theory-anchored dimensions.
# worth = taste.compose(dims, weights) is computed by the caller (live_loop).
# ---------------------------------------------------------------------------
import hashlib
from taste import DIMENSIONS, DIM_NAMES


def _dims_prompt(content: str = "") -> str:
    lines = ["Score this single frame on each dimension below, 0.0 to 1.0, using its rubric.",
             "Judge it as a 'worth-noticing moment' a perceptive person would glance up for.",
             "Return ONLY a JSON object mapping dimension name -> number."]
    for name, (_g, rubric) in DIMENSIONS.items():
        lines.append(f"- {name}: {rubric}")
    if content.strip():
        lines.append(f'- match: 0.0-1.0 — how strongly this frame shows or relates to: "{content.strip()}".')
    lines.append("\nNo prose, JSON only.")
    return "\n".join(lines)


def score_dims_live(jpeg: bytes, content: str = "", model: str = MODEL):
    """Return (dims{9}, match) for one live JPEG. match is 0..1 vs `content` (0 if none)."""
    if os.environ.get("SECONDATTN_OFFLINE") == "1":
        h = hashlib.md5(jpeg[:3000]).hexdigest()
        dims = {d: (int(h[i*3:i*3+3], 16) % 1000) / 1000.0 for i, d in enumerate(DIM_NAMES)}
        m = (int(h[27:30], 16) % 1000) / 1000.0 if content.strip() else 0.0
        return dims, m
    import anthropic
    client = anthropic.Anthropic()
    b64 = base64.standard_b64encode(jpeg).decode()
    msg = client.messages.create(
        model=model, max_tokens=320,
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}},
            {"type": "text", "text": _dims_prompt(content)}]}],
    )
    text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()
    try:
        s, e = text.index("{"), text.rindex("}") + 1
        raw = json.loads(text[s:e])
        dims = {d: float(raw.get(d, 0.0)) for d in DIM_NAMES}
        m = float(raw.get("match", 0.0)) if content.strip() else 0.0
        return dims, m
    except Exception:
        return {d: 0.0 for d in DIM_NAMES}, 0.0


def _grab_one_frame(camera_url: str) -> bytes:
    """Pull a single JPEG out of the camera's MJPEG stream."""
    import requests
    s = requests.Session(); s.trust_env = False
    with s.get(camera_url.rstrip("/") + "/", stream=True, timeout=(5, 15)) as r:
        buf = b""
        for chunk in r.iter_content(8192):
            buf += chunk
            a = buf.find(b"\xff\xd8"); b = buf.find(b"\xff\xd9", a + 2) if a != -1 else -1
            if a != -1 and b != -1:
                return buf[a:b + 2]
    raise RuntimeError("no frame")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--camera", default="http://sidekick-cam.local")
    ap.add_argument("--preference", default="animals and people")
    args = ap.parse_args()
    print(f"Preference: {args.preference!r}  model: {MODEL}")
    jpeg = _grab_one_frame(args.camera)
    print(f"grabbed frame ({len(jpeg)//1024} KB) — scoring...")
    print(score_frame(jpeg, args.preference))
