"""
viz.py — the GLASS-BOX overlay: draw the whole pipeline's state onto the live frame.

This is the "compilable / readable" surface: for every frame you can SEE, on top of the
real image, exactly what the system perceived and decided — detected boxes, the geometric
relations, which big thing was called a surface, whether the gate fired, and the VLM's
worth / why / field note.

Styled for a clear REAL-TIME UI: bright/neon colours + black-outlined text so labels read on
any background (inspired by sports/AR overlays). Shared by the offline batch and live_demo.
"""

from __future__ import annotations
import cv2
import numpy as np
from typing import Optional

FONT = cv2.FONT_HERSHEY_SIMPLEX

# relation -> BGR colour — bright/neon for a clear real-time UI (OpenCV is BGR)
REL_COLOR = {
    "near":        (255, 255, 0),    # cyan
    "inside":      (255, 0, 255),    # magenta
    "on":          (0, 255, 255),    # yellow
    "overlapping": (0, 140, 255),    # orange (off by default)
    "above": (255, 255, 255), "below": (255, 255, 255),
    "left_of": (255, 255, 255), "right_of": (255, 255, 255),
}
_SYMMETRIC = {"near", "overlapping"}
BOX_COLOR = (0, 255, 0)              # neon-green object boxes (like the reference skeleton)
SURF_COLOR = (255, 255, 0)          # cyan surface highlight


def _ctr(b):
    return (int((b[0] + b[2]) / 2), int((b[1] + b[3]) / 2))


def _text(img, s, org, color, scale=0.7, thick=2):
    """Neon-style label: thick black outline + bright fill, readable on any background."""
    cv2.putText(img, s, org, FONT, scale, (0, 0, 0), thick + 3, cv2.LINE_AA)
    cv2.putText(img, s, org, FONT, scale, color, thick, cv2.LINE_AA)


def draw_overlay(img: np.ndarray, g, state: Optional[dict] = None,
                 caption: Optional[str] = None) -> np.ndarray:
    """Return a copy of `img` annotated with the scene graph + pipeline state.
    g: a SceneGraph (needs .nodes, .edges, .boxes, optional .surfaces).
    state: optional {settled, changed, event, worth, why, note} -> draws the full HUD.
    caption: optional one-line text drawn top-left (used by the perception-only batch)."""
    out = img.copy()
    H, W = out.shape[:2]
    surfaces = set(getattr(g, "surfaces", []))
    if caption:
        _text(out, caption, (12, 32), (255, 255, 255), 0.7, 2)

    # 1) surface: bright translucent fill + border + label
    for sid in surfaces:
        if sid in g.boxes:
            x1, y1, x2, y2 = map(int, g.boxes[sid])
            layer = out.copy()
            cv2.rectangle(layer, (x1, y1), (x2, y2), SURF_COLOR, -1)
            cv2.addWeighted(layer, 0.12, out, 0.88, 0, out)
            cv2.rectangle(out, (x1, y1), (x2, y2), SURF_COLOR, 2, cv2.LINE_AA)
            _text(out, f"{g.nodes.get(sid, sid)} [surface]", (x1 + 8, y1 + 30), SURF_COLOR, 0.7, 2)

    # 2) relation edges (dedupe symmetric; bright line + outlined label at midpoint)
    drawn = set()
    for (a, rel, b) in g.edges:
        key = (frozenset((a, b)), rel) if rel in _SYMMETRIC else (a, rel, b)
        if key in drawn:
            continue
        drawn.add(key)
        if a not in g.boxes or b not in g.boxes:
            continue
        pa, pb = _ctr(g.boxes[a]), _ctr(g.boxes[b])
        col = REL_COLOR.get(rel, (220, 220, 220))
        cv2.line(out, pa, pb, col, 2, cv2.LINE_AA)
        mx, my = (pa[0] + pb[0]) // 2, (pa[1] + pb[1]) // 2
        _text(out, rel, (mx - 4, my), col, 0.55, 2)

    # 3) object boxes (non-surface) + neon label
    for nid, box in g.boxes.items():
        if nid in surfaces:
            continue
        x1, y1, x2, y2 = map(int, box)
        cv2.rectangle(out, (x1, y1), (x2, y2), BOX_COLOR, 2, cv2.LINE_AA)
        cv2.circle(out, _ctr(box), 4, BOX_COLOR, -1)
        _text(out, g.nodes.get(nid, nid), (x1 + 4, max(y1 - 8, 22)), BOX_COLOR, 0.7, 2)

    # 4) HUD: clean real-time status strip + a NOTICED chip on fire
    if state is not None:
        bar = 132
        layer = out.copy()
        cv2.rectangle(layer, (0, H - bar), (W, H), (18, 18, 20), -1)
        cv2.addWeighted(layer, 0.62, out, 0.38, 0, out)
        ev = state.get("event")
        def ok(v): return "OK" if v else "--"
        _text(out, f"stillness {ok(state.get('settled', True))}    changed {ok(state.get('changed', True))}",
              (16, H - bar + 34), (235, 235, 235), 0.7, 2)
        _text(out, "GATE: EVENT (new configuration)" if ev else "GATE: habituated",
              (16, H - bar + 72), (0, 255, 0) if ev else (165, 165, 165), 0.78, 2)
        w = state.get("worth")
        if w is not None:
            _text(out, f'worth {w:.2f}  ({state.get("why", "")})  "{state.get("note", "")[:44]}"',
                  (16, H - bar + 106), (0, 255, 255), 0.6, 2)
        if ev:
            _text(out, ">> NOTICED", (W - 270, 48), (0, 255, 0), 0.95, 3)
    return out


def show_live(img, g, state=None, window="second-attention"):
    """Convenience for the live loop: pop a window with the overlay (q to quit)."""
    cv2.imshow(window, draw_overlay(img, g, state))
    return cv2.waitKey(1) & 0xFF


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from perceive import Detection, build_graph
    from judge import judge, ReportabilityTaste
    os.environ["SECONDATTN_OFFLINE"] = "1"

    path = sys.argv[1] if len(sys.argv) > 1 else \
        os.path.join(os.path.dirname(__file__), "..", "live_captures",
                     "cap_20260604_112241_0.85.jpg")
    img = cv2.imread(path)
    H, W = img.shape[:2]
    dets = [
        Detection("person",      (40, 430, 470, 1180)),
        Detection("laptop",      (980, 250, 1600, 1140)),
        Detection("cutting mat", (120, 0, 1080, 1180), 0.9),
        Detection("phone",       (360, 330, 900, 880)),
        Detection("plush toy",   (430, 400, 920, 900)),
        Detection("marker",      (760, 20, 1100, 320)),
        Detection("breadboard",  (120, 0, 430, 210)),
    ]
    g = build_graph(dets, (W, H))
    r = judge(None, g, ReportabilityTaste())
    state = {"settled": True, "changed": True, "event": True,
             "worth": r["worth"], "why": r["why"], "note": r["note"]}
    out = draw_overlay(img, g, state)
    dst = os.path.join(os.path.dirname(__file__), "viz_demo_desk.jpg")
    cv2.imwrite(dst, out)
    print("wrote", dst, "| nodes:", list(g.nodes.values()), "| edges:", len(g.edges))
