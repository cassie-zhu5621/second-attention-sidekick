"""
perceive.py — STABLE perception: a frame -> a scene graph with stable relations.

This is the linchpin the rest of the pipeline stands on. The whole point (see the
discussion / FINDINGS): the GATE needs a relational encoding that is *stable* across
frames, or it can never habituate ("same situation" must map to "same graph"). VLMs and
learned SGG models do NOT give stable relations (they relabel per frame — the
scientist/researcher/student flip-flop, PE-Net's intra/inter-class problem). So we get
stability the cheap, boring, reliable way:

    off-the-shelf OBJECT detection (stable boxes)  +  GEOMETRIC relations by rule.

The VLM is NOT used here; it is the downstream judgment brain. Object identity comes from
a detector (mature, consistent); relations come from geometry (deterministic), not from a
model guessing predicates.

ROTATION NOTE (found in the real lab frames): the camera sits on a pan/tilt head, so frames
arrive tilted/sideways. "on / above / below" assume a known up-direction and become
unreliable when the view is rotated. So relations split into:
  - rotation-INVARIANT (always safe): near, touching/overlapping, inside/contains
  - direction (needs an up-vector): on, above, below, left_of, right_of
The pan/tilt pose can supply `up`; without it we emit only the invariant relations.

The detector is a pluggable ADAPTER. The default is a MockDetector for testing the graph
logic here; on the rig you drop in YOLO-World (open-vocab, no hand-listed objects — matches
the brief) / Grounding DINO / YOLOv8. See `YoloWorldDetector` stub at the bottom.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Protocol

Box = Tuple[float, float, float, float]   # x1, y1, x2, y2 in pixels


# --------------------------------------------------------------------------- #
# detections + detector adapter
# --------------------------------------------------------------------------- #
@dataclass
class Detection:
    label: str            # object TYPE (e.g. "laptop"); becomes the node type
    box: Box
    score: float = 1.0

    @property
    def cx(self): return 0.5 * (self.box[0] + self.box[2])
    @property
    def cy(self): return 0.5 * (self.box[1] + self.box[3])
    @property
    def w(self):  return self.box[2] - self.box[0]
    @property
    def h(self):  return self.box[3] - self.box[1]
    @property
    def area(self): return max(self.w, 0) * max(self.h, 0)


class Detector(Protocol):
    """Anything that turns an image into detections. Swap implementations freely."""
    def detect(self, image) -> List[Detection]: ...


# --------------------------------------------------------------------------- #
# geometry helpers
# --------------------------------------------------------------------------- #
def _iou(a: Box, b: Box) -> float:
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    ua = (a[2]-a[0])*(a[3]-a[1]) + (b[2]-b[0])*(b[3]-b[1]) - inter
    return inter / ua if ua > 0 else 0.0


def _frac_inside(inner: Box, outer: Box) -> float:
    ix1, iy1 = max(inner[0], outer[0]), max(inner[1], outer[1])
    ix2, iy2 = min(inner[2], outer[2]), min(inner[3], outer[3])
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inner_area = (inner[2]-inner[0]) * (inner[3]-inner[1])
    return (iw * ih) / inner_area if inner_area > 0 else 0.0


# --------------------------------------------------------------------------- #
# the scene graph builder
# --------------------------------------------------------------------------- #
@dataclass
class SceneGraph:
    nodes: Dict[str, str]               # node_id -> type    (config_gate format)
    edges: List[Tuple[str, str, str]]   # (src_id, relation, dst_id)
    boxes: Dict[str, Box] = field(default_factory=dict)   # node_id -> box (for salience/viz)

    def as_gate_input(self):
        return self.nodes, self.edges


# Movers/agents are never a SURFACE or a CONTAINER — a person carries/sits, they don't hold
# things "inside" or serve as a surface. Without depth, a big foreground person's box swallows
# everything behind it -> false "X inside/on person"; blacklisting these types kills that.
NON_CONTAINER_TYPES = {"person", "people", "man", "woman", "boy", "girl", "child",
                       "hand", "cat", "dog", "bird", "animal"}


def build_graph(dets: List[Detection], image_wh: Tuple[int, int],
                up: Optional[Tuple[float, float]] = None,
                near_frac: float = 0.18, min_score: float = 0.30,
                surface_frac: float = 0.33, surface_min_holds: int = 3,
                overlapping: bool = False, min_area_frac: float = 0.0,
                max_container_frac: float = 0.5,
                depth_map=None, depth_tol: float = 0.15) -> SceneGraph:
    """Detections -> stable scene graph.

    near_frac: two objects are 'near' if their centre distance < near_frac * image diagonal.
    up: unit vector of 'up' in image pixel coords (e.g. from pan/tilt pose). If given, we
        additionally emit direction relations (on/above/below/left_of/right_of); if None we
        stay rotation-invariant (near/touching/inside) so we never assert a wrong 'on'.

    SURFACE rule (data-driven, no dataset tuning): a detection that (a) covers >= surface_frac
    of the frame AND (b) has >= surface_min_holds other objects sitting inside it is treated
    as a SURFACE/background (desk, mat, wall, floor). A surface only takes 'on' edges from the
    things it holds; it does NOT spray near/touching to everything. This kills the O(N^2) hub
    that a big table/mat otherwise creates, while keeping the informative "X is on the table".
    The rule auto-disables when no such hub exists, so it is safe on any data.
    """
    W, H = image_wh
    diag = math.hypot(W, H)
    frame_area = max(W * H, 1)
    # drop low-confidence AND too-small detections. Small boxes (a distant bottle) are the
    # least stable to detect (they flicker in/out frame to frame -> phantom relation changes)
    # and the least relationally important, so for the GATE we ignore objects below
    # min_area_frac of the frame. This is a per-deployment knob: raise it in a cluttered/far
    # scene (a shared room), keep it ~0 for a close simple scene (a single desk).
    dets = [d for d in dets if d.score >= min_score and d.area >= min_area_frac * frame_area]

    # assign stable-ish ids: type + an index by reading order (left->right, top->bottom).
    dets = sorted(dets, key=lambda d: (round(d.cy / max(H, 1), 2), d.cx))
    counts: Dict[str, int] = {}
    nodes, boxes, ids = {}, {}, []
    for d in dets:
        counts[d.label] = counts.get(d.label, 0) + 1
        nid = f"{d.label}{counts[d.label]}"
        nodes[nid] = d.label
        boxes[nid] = d.box
        ids.append(nid)

    # --- identify surfaces (data-driven) ---
    is_surface = [False] * len(dets)
    for k, s in enumerate(dets):
        if s.area >= surface_frac * frame_area and s.label not in NON_CONTAINER_TYPES:
            holds = sum(1 for m, o in enumerate(dets)
                        if m != k and _frac_inside(o.box, s.box) >= 0.5 and o.area < s.area)
            if holds >= surface_min_holds:
                is_surface[k] = True

    # per-detection median depth (0..1) if a depth map was supplied (monocular Depth-Anything).
    # Two boxes are only "inside/on"-related if they are at a SIMILAR depth — a thing BEHIND a
    # big foreground object is at a different depth, so it is NOT contained/supported by it.
    # This is the principled replacement for the size-cap / person-blacklist band-aids.
    import numpy as _np
    def _bd(box):
        if depth_map is None:
            return None
        H2, W2 = depth_map.shape[:2]
        x1, y1, x2, y2 = (max(0, int(box[0])), max(0, int(box[1])),
                          min(W2, int(box[2])), min(H2, int(box[3])))
        if x2 <= x1 or y2 <= y1:
            return None
        return float(_np.median(depth_map[y1:y2, x1:x2]))
    depth_of = [_bd(d.box) for d in dets]
    def dok(i, j):                       # depth-consistent? (always True when no depth map)
        if depth_map is None:
            return True
        di, dj = depth_of[i], depth_of[j]
        return di is not None and dj is not None and abs(di - dj) <= depth_tol

    edges: List[Tuple[str, str, str]] = []
    for i in range(len(dets)):
        for j in range(len(dets)):
            if i == j:
                continue
            a, b = dets[i], dets[j]
            ai, bi = ids[i], ids[j]

            # ---- surface handling: only 'X on surface', nothing else ----
            if is_surface[i] or is_surface[j]:
                if (is_surface[j] and not is_surface[i]
                        and _frac_inside(a.box, b.box) >= 0.5 and dok(i, j)):
                    edges.append((ai, "on", bi))          # a sits on surface b (same depth)
                continue                                   # suppress all other surface edges

            # ---- rotation-INVARIANT relations (always safe) ----
            fi = _frac_inside(a.box, b.box)
            # 'inside' only if b is a plausible CONTAINER, not a frame-filling foreground blob.
            # Without depth, a big near object's box swallows everything behind it -> false
            # 'inside'. Capping the container's size kills "monitor inside person" while keeping
            # real containment (sticker in laptop, book in bag). True fix = depth (future).
            if (fi >= 0.75 and b.area > a.area and b.area < max_container_frac * frame_area
                    and b.label not in NON_CONTAINER_TYPES and dok(i, j)):
                edges.append((ai, "inside", bi))
                continue
            if overlapping and _iou(a.box, b.box) > 0.02 and i < j:
                # OFF by default: on real lab data 'overlapping' was ~57% of all edges and
                # mostly depth OCCLUSION (a chair in front of a desk/person), not contact —
                # it bloated the graph 2x while barely changing what the gate fired on. We
                # keep near/inside/on (the meaningful spatial structure) and let the VLM
                # supply true physical relations at report time. Re-enable with overlapping=True.
                edges.append((ai, "overlapping", bi)); edges.append((bi, "overlapping", ai))
            dist = math.hypot(a.cx - b.cx, a.cy - b.cy)
            if i < j and dist < near_frac * diag and _iou(a.box, b.box) == 0:
                edges.append((ai, "near", bi)); edges.append((bi, "near", ai))
            # ---- DIRECTION relations (only with a known up-vector) ----
            if up is not None and i < j:
                ux, uy = up
                dx, dy = a.cx - b.cx, a.cy - b.cy
                along_up = dx * ux + dy * uy
                along_right = dx * (-uy) + dy * ux
                if dist < 0.45 * diag:
                    if abs(along_up) > abs(along_right):
                        edges.append((ai, "above" if along_up > 0 else "below", bi))
                    else:
                        edges.append((ai, "right_of" if along_right > 0 else "left_of", bi))

    sg = SceneGraph(nodes=nodes, edges=edges, boxes=boxes)
    sg.surfaces = [ids[k] for k in range(len(dets)) if is_surface[k]]   # for transparency
    return sg


def perceive(image, detector: Detector, image_wh: Tuple[int, int],
             up: Optional[Tuple[float, float]] = None) -> SceneGraph:
    """Full step: image -> detections -> stable scene graph."""
    return build_graph(detector.detect(image), image_wh, up=up)


# --------------------------------------------------------------------------- #
# detector adapters
# --------------------------------------------------------------------------- #
class MockDetector:
    """Returns a fixed detection list — for testing the graph logic without a model."""
    def __init__(self, dets: List[Detection]):
        self._dets = dets
    def detect(self, image=None) -> List[Detection]:
        return self._dets


class YoloWorldDetector:
    """Drop-in real detector on the rig. ~10 lines; open-vocab, no training, no object list
    baked in (you pass the vocabulary you care about, or a broad default).

        pip install ultralytics
        det = YoloWorldDetector(["person","laptop","cup","chair","desk","phone","book","plush toy"])
        graph = perceive(frame, det, (W,H), up=pose_up)
    """
    def __init__(self, vocabulary: List[str], weights: str = "yolov8s-world.pt",
                 conf: float = 0.25, device: str = None):
        try:
            from ultralytics import YOLO      # lazy import; only needed on the rig/laptop
        except ImportError:
            raise SystemExit("YOLO-World needs ultralytics. Install it:\n"
                             "    pip install ultralytics\n"
                             "(or run the batch with --mock to test the plumbing).")
        self.model = YOLO(weights)            # auto-downloads yolov8s-world.pt on first use
        self.model.set_classes(vocabulary)
        self.conf = conf
        self.device = device                  # None=auto, "cpu", or "0" for first GPU
    def detect(self, image) -> List[Detection]:
        r = self.model.predict(image, conf=self.conf, device=self.device, verbose=False)[0]
        names = r.names
        out = []
        for b in r.boxes:
            x1, y1, x2, y2 = b.xyxy[0].tolist()
            out.append(Detection(names[int(b.cls)], (x1, y1, x2, y2), float(b.conf)))
        return out


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from config_surprise import motifs

    # Two REAL lab frames, hand-encoded (boxes eyeballed; stand in for YOLO-World output).
    # Frame 1 (cap_20260604_112241): desk — laptop, phone, Piplup plush ON the phone, marker,
    #   breadboard, person's legs, all on a big CUTTING MAT (the surface/hub).
    desk = (1600, 1200, [
        Detection("person",      (40, 430, 470, 1180)),
        Detection("laptop",      (980, 250, 1600, 1140)),
        Detection("cutting mat", (120, 0, 1080, 1180), 0.9),     # big surface
        Detection("phone",       (360, 330, 900, 880)),
        Detection("plush toy",   (430, 400, 920, 900)),          # on the phone
        Detection("marker",      (760, 20, 1100, 320)),
        Detection("breadboard",  (120, 0, 430, 210)),
    ])
    # Frame 2 (IMG_00001): a big PEGBOARD wall (surface/hub) with scissors, tape rolls,
    #   cables, a plush, plus a monitor edge.
    pegboard = (800, 600, [
        Detection("pegboard",  (60, 90, 720, 600), 0.9),         # big surface
        Detection("monitor",   (0, 0, 130, 360)),
        Detection("poster",    (165, 60, 250, 150)),
        Detection("scissors",  (180, 250, 240, 360)),
        Detection("scissors",  (40, 410, 120, 520)),
        Detection("tape",      (190, 330, 250, 400)),
        Detection("tape",      (300, 330, 360, 400)),
        Detection("cable",     (300, 230, 470, 430)),
        Detection("plush toy", (520, 220, 580, 280)),
    ])

    for name, (W, H, dets) in [("desk", desk), ("pegboard", pegboard)]:
        # OFF: disable the surface rule (surface_frac=2.0 can never trigger)
        g_off = build_graph(dets, (W, H), surface_frac=2.0)
        # ON: data-driven surface rule (default)
        g_on = build_graph(dets, (W, H))
        m_off = sum(motifs(*g_off.as_gate_input()).values())
        m_on = sum(motifs(*g_on.as_gate_input()).values())
        print(f"[{name}] surfaces detected: {getattr(g_on,'surfaces',[])}")
        print(f"[{name}] motifs  surface-rule OFF: {m_off:4d}   ON: {m_on:4d}   "
              f"({100*(m_off-m_on)/max(m_off,1):.0f}% trivial hub edges removed)")
        print(f"[{name}] kept edges (ON):")
        for e in g_on.edges:
            print("     ", e)
        print()
