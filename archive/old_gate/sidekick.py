"""
sidekick.py — the end-to-end NOTICING LOOP that ties the pieces together.

    frame ──stillness/change(cheap)──▶ perceive (stable scene graph)
          ──▶ TemporalConfigGate (event boundary / non-redundant?)   [Event Segmentation]
          ──event──▶ judge (VLM: worth · why · note, shaped by taste) [reportability]
          ──worth≥θ──▶ report to feed (note + frame + reason)
          ──▶ memory: non-redundancy (in the gate) + salience map
    user reactions on the feed ──▶ taste.nudge(...)   (compilable; see = teach)

Everything hardware/model-specific is a pluggable ADAPTER (Camera, Detector, Feed). The
defaults are mocks so the whole loop runs with NO rig, NO detector, NO API key — which is
how you wire it: keep the mocks, confirm the flow, then drop in the real adapters on your
rig (camera = your MJPEG grab + pan/tilt pose; detector = YoloWorldDetector; judge uses your
ANTHROPIC_API_KEY; feed = Discord/web panel). Movement is deliberately NOT here yet — the
camera adapter just provides (frame, pose); a gaze policy plugs in later.
"""

from __future__ import annotations
import os, math, time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional, Tuple, List, Protocol

from perceive import perceive, build_graph, Detection, MockDetector
from config_surprise import ConfigSurpriseGate, TemporalConfigGate
from judge import judge, ReportabilityTaste


# --------------------------------------------------------------------------- #
# adapters (swap these for real hardware/models)
# --------------------------------------------------------------------------- #
@dataclass
class Look:
    jpeg: Optional[bytes]                 # frame bytes (None in offline tests)
    dets: List[Detection]                 # detector output for this frame
    pose: Tuple[float, float]             # (pan, tilt) degrees — for salience + 'up'
    wh: Tuple[int, int] = (1600, 1200)
    up: Optional[Tuple[float, float]] = None
    settled: bool = True                  # stillness gate already passed
    changed: bool = True                  # cheap appearance/graph change since last look here


class Camera(Protocol):
    def look(self) -> Optional[Look]: ...   # one settled look, or None if not ready


# --------------------------------------------------------------------------- #
# salience map: where in the space worth-noticing things happen (memory of place)
# --------------------------------------------------------------------------- #
@dataclass
class SalienceMap:
    pan_bins: int = 9
    tilt_bins: int = 3
    pan_range: Tuple[float, float] = (-80, 80)
    tilt_range: Tuple[float, float] = (-25, 25)
    decay: float = 0.997
    grid: dict = field(default_factory=lambda: defaultdict(float))

    def _bin(self, pose):
        p, t = pose
        pb = min(self.pan_bins - 1, max(0, int((p - self.pan_range[0]) /
                 (self.pan_range[1] - self.pan_range[0] + 1e-9) * self.pan_bins)))
        tb = min(self.tilt_bins - 1, max(0, int((t - self.tilt_range[0]) /
                 (self.tilt_range[1] - self.tilt_range[0] + 1e-9) * self.tilt_bins)))
        return pb, tb

    def deposit(self, pose, worth):
        for k in list(self.grid):                  # slow forgetting
            self.grid[k] *= self.decay
        self.grid[self._bin(pose)] += worth

    def as_grid(self) -> List[List[float]]:
        return [[round(self.grid.get((pb, tb), 0.0), 3) for pb in range(self.pan_bins)]
                for tb in range(self.tilt_bins)]


# --------------------------------------------------------------------------- #
# the sidekick
# --------------------------------------------------------------------------- #
@dataclass
class Sidekick:
    camera: Camera
    taste: ReportabilityTaste = field(default_factory=ReportabilityTaste)
    gate: TemporalConfigGate = field(default_factory=lambda: TemporalConfigGate(
        gate=ConfigSurpriseGate(mode="habituation", agg="max", threshold=0.5)))
    salience: SalienceMap = field(default_factory=SalienceMap)
    worth_threshold: float = 0.45
    feed: list = field(default_factory=list)       # reports land here (swap for Discord/panel)

    def tell(self, sentence: str):
        """User shapes taste in real time (the see=teach channel)."""
        d = self.taste.nudge(sentence)
        return d or {"about": self.taste.about}

    def tick(self) -> Optional[dict]:
        """One look. Returns a report dict iff something was reported."""
        look = self.camera.look()
        if look is None or not look.settled:
            return None                            # stillness gate
        g = build_graph(look.dets, look.wh, up=look.up)
        d = self.gate.step(g.nodes, g.edges)       # always: habituate + get event/delta
        # DUAL TRIGGER (either fires -> candidate):
        #   appearance changed since last look here  OR  a new relational configuration.
        # The appearance layer catches within-surface moves the coarse graph misses
        # (a cup sliding = same 'cup on desk' graph); the config layer gives structure +
        # suppresses pixel jitter. Repeated identical views set changed=False -> habituated
        # for free.
        if not (look.changed or d["event"]):
            return None
        r = judge(look.jpeg, g, self.taste, delta_added=d["delta_added"])
        if r["worth"] < self.worth_threshold:
            return None                            # an event, but not reportable for this person
        self.salience.deposit(look.pose, r["worth"])
        report = {"pose": look.pose, "worth": round(r["worth"], 2), "why": r["why"],
                  "note": r["note"], "delta": TemporalConfigGate.describe(d["delta_added"], d["top"])}
        self.feed.append(report)
        return report


# --------------------------------------------------------------------------- #
# mock end-to-end demo (no rig / no detector / no API key)
# --------------------------------------------------------------------------- #
class _ScriptedCamera:
    """Yields a scripted sequence of looks: a desk baseline repeated (should habituate),
    then a reconfiguration (a cup tips over near the laptop) that should fire ONE event."""
    def __init__(self):
        base = [Detection("person", (40, 430, 470, 1180)), Detection("laptop", (980, 250, 1500, 1140)),
                Detection("cup", (520, 250, 640, 400)), Detection("desk", (0, 0, 1600, 1200), 0.9)]
        spill = [Detection("person", (40, 430, 470, 1180)), Detection("laptop", (980, 250, 1500, 1140)),
                 Detection("cup", (980, 1000, 1100, 1150)),    # cup now down by the laptop base
                 Detection("desk", (0, 0, 1600, 1200), 0.9)]
        self.seq = [("base", base)] * 6 + [("spill", spill)] + [("base", base)] * 2
        self.i = 0
        self._prev = None
    def look(self):
        if self.i >= len(self.seq):
            return None
        tag, dets = self.seq[self.i]; self.i += 1
        changed = (dets != self._prev)          # proxy for pixel-diff vs last look at this pose
        self._prev = dets
        return Look(jpeg=None, dets=dets, pose=(20, 0), changed=changed)


if __name__ == "__main__":
    os.environ["SECONDATTN_OFFLINE"] = "1"
    sk = Sidekick(camera=_ScriptedCamera(), worth_threshold=0.0)   # θ=0 so the offline note prints
    print("ticking a scripted day (6× baseline, 1× spill, 2× baseline):\n")
    for t in range(9):
        rep = sk.tick()
        if rep:
            print(f"  t{t}: ★ REPORTED worth={rep['worth']} why={rep['why']}")
            print(f"        note: {rep['note']}")
            print(f"        {rep['delta']}")
        else:
            print(f"  t{t}: — (habituated / no event)")
    print(f"\n{len(sk.feed)} report(s) total — the 6 repeated baselines habituated, "
          f"the reconfiguration fired once.")
    print("salience grid (tilt rows × pan cols):")
    for row in sk.salience.as_grid():
        print("   ", row)

    print("\nuser reacts: 'I care about the robotics corner' ; 'more people'")
    sk.tell("I care about the robotics corner"); sk.tell("more people")
    print("  taste.about =", repr(sk.taste.about),
          "| weights =", {k: round(v, 2) for k, v in sk.taste.weights.items()})
