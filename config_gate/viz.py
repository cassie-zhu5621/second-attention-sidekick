"""
viz.py — the GLASS-BOX overlay: draw the whole pipeline's state onto the live frame.

This is the "compilable / readable" surface: for every frame you can SEE, on top of the
real image, exactly what the system perceived and decided —
    detected boxes · the geometric relations · which big thing was called a surface ·
    whether the gate fired · and the VLM's worth / why / field note.

It is detector-agnostic: you hand it the frame, the SceneGraph from perceive(), and a small
`state` dict (the cheap-gate flags + gate decision + judge result). In the live loop you call
draw_overlay() each tick and either cv2.imshow() it, write it to disk, or push it to the web
panel — so one screen shows every stage in real time.
"""

from __future__ import annotations
import cv2
import numpy as np
from typing import Optional

# relation -> BGR colour (OpenCV is BGR)
REL_COLOR = {
    "near":        (235, 99, 37),    # blue   — image-plane proximity
    "overlapping": (12, 65, 194),    # orange — image overlap (occlusion, NOT 3D contact)
    "inside":      (237, 58, 124),   # purple — image containment
    "on":          (110, 118, 15),   # teal   — within a surface region (depth-blind)
    "above": (160,160,160), "below": (160,160,160),
    "left_of": (160,160,160), "right_of": (160,160,160),
}
_SYMMETRIC = {"near", "overlapping"}


def _ctr(b):
    return (int((b[0] + b[2]) / 2), int((b[1] + b[3]) / 2))


def draw_overlay(img: np.ndarray, g, state: Optional[dict] = None,
                 caption: Optional[str] = None) -> np.ndarray:
    """Return a copy of `img` annotated with the scene graph + pipeline state.
    g: a SceneGraph (needs .nodes, .edges, .boxes, optional .surfaces).
    state: optional {settled, changed, event, worth, why, note} -> draws the full pipeline HUD.
    caption: optional one-line text drawn top-left (used by the perception-only batch)."""
    out = img.copy()
    H, W = out.shape[:2]
    surfaces = set(getattr(g, "surfaces", []))
    if caption:
        (tw, th), _ = cv2.getTextSize(caption, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
        cv2.rectangle(out, (0, 0), (tw + 20, th + 18), (20, 22, 25), -1)
        cv2.putText(out, caption, (10, th + 8), cv2.FONT_HERSHEY_SIMPLEX, 0.7,
                    (230, 230, 230), 2, cv2.LINE_AA)

    # 1) surface highlight (translucent teal fill + label)
    for sid in surfaces:
        if sid in g.boxes:
            x1, y1, x2, y2 = map(int, g.boxes[sid])
            layer = out.copy()
            cv2.rectangle(layer, (x1, y1), (x2, y2), (110, 118, 15), -1)
            cv2.addWeighted(layer, 0.10, out, 0.90, 0, out)
            cv2.rectangle(out, (x1, y1), (x2, y2), (110, 118, 15), 2)
            cv2.putText(out, f"{g.nodes.get(sid, sid)} [surface]", (x1 + 6, y1 + 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (110, 118, 15), 2)

    # 2) relation edges (dedupe symmetric; draw line + label at midpoint)
    drawn = set()
    for (a, rel, b) in g.edges:
        key = (frozenset((a, b)), rel) if rel in _SYMMETRIC else (a, rel, b)
        if key in drawn:
            continue
        drawn.add(key)
        if a not in g.boxes or b not in g.boxes:
            continue
        pa, pb = _ctr(g.boxes[a]), _ctr(g.boxes[b])
        col = REL_COLOR.get(rel, (180, 180, 180))
        thick = 1 if rel == "on" else 3
        cv2.line(out, pa, pb, col, thick, cv2.LINE_AA)
        mx, my = (pa[0] + pb[0]) // 2, (pa[1] + pb[1]) // 2
        (tw, th), _ = cv2.getTextSize(rel, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(out, (mx - 3, my - th - 4), (mx + tw + 3, my + 4), (255, 255, 255), -1)
        cv2.putText(out, rel, (mx, my), cv2.FONT_HERSHEY_SIMPLEX, 0.6, col, 2, cv2.LINE_AA)

    # 3) object boxes (non-surface) + label
    for nid, box in g.boxes.items():
        if nid in surfaces:
            continue
        x1, y1, x2, y2 = map(int, box)
        cv2.rectangle(out, (x1, y1), (x2, y2), (40, 40, 40), 2)
        cv2.circle(out, _ctr(box), 4, (40, 40, 40), -1)
        cv2.putText(out, g.nodes.get(nid, nid), (x1 + 3, max(y1 - 6, 16)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 4, cv2.LINE_AA)
        cv2.putText(out, g.nodes.get(nid, nid), (x1 + 3, max(y1 - 6, 16)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (20, 20, 20), 2, cv2.LINE_AA)

    # 4) HUD: the pipeline stages, bottom strip
    if state is not None:
        bar_h = 150
        layer = out.copy()
        cv2.rectangle(layer, (0, H - bar_h), (W, H), (20, 22, 25), -1)
        cv2.addWeighted(layer, 0.78, out, 0.22, 0, out)
        def ok(v): return "OK" if v else "--"
        ev = state.get("event")
        gate_txt = "EVENT (new configuration)" if ev else "habituated / no new config"
        gate_col = (90, 240, 120) if ev else (140, 140, 140)
        y = H - bar_h + 30
        cv2.putText(out, f"(1)stillness {ok(state.get('settled',True))}   "
                         f"(2)changed-here {ok(state.get('changed',True))}",
                    (16, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (230, 230, 230), 2)
        cv2.putText(out, f"(3)gate: {gate_txt}", (16, y + 34),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, gate_col, 2)
        w = state.get("worth"); why = state.get("why", "")
        if w is not None:
            cv2.putText(out, f"(4)judge: worth={w:.2f}  why={why}", (16, y + 68),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (120, 200, 255), 2)
        note = state.get("note", "")
        if note:
            cv2.putText(out, f'    "{note[:70]}"', (16, y + 100),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.62, (220, 220, 220), 2)
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
    # boxes eyeballed from this real frame (stand-in for the detector's output)
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
    r = judge(None, g, ReportabilityTaste())     # offline -> a sample worth/why/note
    state = {"settled": True, "changed": True, "event": True,
             "worth": r["worth"], "why": r["why"], "note": r["note"]}
    out = draw_overlay(img, g, state)
    dst = os.path.join(os.path.dirname(__file__), "viz_demo_desk.jpg")
    cv2.imwrite(dst, out)
    print("wrote", dst, "| nodes:", list(g.nodes.values()), "| edges:", len(g.edges))
