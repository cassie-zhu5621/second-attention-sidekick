"""
sim.py — a synthetic "placed companion's day" as a stream of scene graphs.

We cannot run a GPU detector in this sandbox, so we simulate the OUTPUT of the
open-vocab-detection -> scene-graph stage (step 2 of the brief's cascade) with realistic
statistics, and use it to test the GATE (step 3), which is the actual contribution.

The stream is built to make the thesis falsifiable. It contains three kinds of frames:

  NORMAL  (habituated)  : the everyday working scene, repeated with instance variation
                          (different person/cup ids, same TYPES). Should NOT fire.
  EVENT   (interesting) : a genuine relational change that SHARES NODES with the normal
                          scene (a spill; a handover; a new actor enters). SHOULD fire.
                          These are the ground-truth "worth noticing" frames.
  NOISE   (distractor)  : a flickering screen / detector jitter -> a brand-new single
                          triplet almost every frame. Always "novel" but un-modelable.
                          Should NOT fire.

A gate that fires on EVENT, ignores NORMAL, and resists NOISE is doing the right thing.
The design deliberately gives NOISE lots of novel single-edges (to tempt a triplet gate)
and gives EVENT the same node set as NORMAL (to fool an image/node-bag gate).
"""

from __future__ import annotations
import random
from typing import Dict, List, Tuple

Edge = Tuple[str, str, str]


def _normal(rng: random.Random) -> Tuple[Dict[str, str], List[Edge], int]:
    """The habituated working scene. Different instance ids each time, same types."""
    pid = f"p{rng.randint(1, 4)}"          # one of a few regulars -> instance variation
    nodes = {pid: "person", "c1": "cup", "l1": "laptop", "d1": "desk", "ch1": "chair"}
    edges = [
        (pid, "typing", "l1"),
        ("c1", "beside", "l1"),
        ("l1", "on", "d1"),
        ("c1", "on", "d1"),
        (pid, "sitting_on", "ch1"),
    ]
    # occasional benign variant: takes a sip (still normal, not worth noticing)
    if rng.random() < 0.3:
        edges = [e for e in edges if e != ("c1", "beside", "l1")]
        edges.append((pid, "holding", "c1"))
    return nodes, edges, 0


def _event(rng: random.Random) -> Tuple[Dict[str, str], List[Edge], int]:
    """A genuine worth-noticing moment. Shares the normal node TYPES (no new objects in
    most cases) -> only the relational CONFIGURATION betrays it."""
    kind = rng.choice(["spill", "handover", "newcomer", "leaving"])
    pid = f"p{rng.randint(1, 4)}"
    if kind == "spill":
        nodes = {pid: "person", "c1": "cup", "l1": "laptop", "d1": "desk", "ch1": "chair"}
        edges = [
            (pid, "looking_at", "l1"),
            ("c1", "knocked_over", "d1"),     # novel relation in a familiar node set
            ("l1", "on", "d1"),
            (pid, "standing", "d1"),
        ]
    elif kind == "handover":
        nodes = {"p1": "person", "p2": "person", "c1": "cup", "d1": "desk"}
        edges = [
            ("p1", "handing", "c1"),
            ("c1", "received_by", "p2"),       # person-handing->cup-received_by->person path
            ("p1", "facing", "p2"),
        ]
    elif kind == "newcomer":
        nodes = {"p1": "person", "dog1": "dog", "d1": "desk", "l1": "laptop"}
        edges = [
            ("dog1", "approaching", "p1"),     # a new TYPE enters (dog) -> new motifs
            ("p1", "looking_at", "dog1"),
            ("l1", "on", "d1"),
        ]
    else:  # leaving
        nodes = {"p1": "person", "ch1": "chair", "d1": "desk", "l1": "laptop"}
        edges = [
            ("p1", "leaving", "d1"),
            ("ch1", "empty", "d1"),            # chair becomes empty -> end-of-presence event
            ("l1", "on", "d1"),
        ]
    return nodes, edges, 1


_SCREEN_CONTENT = ["face", "text", "chart", "logo", "menu", "ad", "map", "video",
                   "button", "photo", "game", "code", "form", "icon", "banner"]


def _noise(rng: random.Random) -> Tuple[Dict[str, str], List[Edge], int]:
    """A flickering screen + detector jitter: a brand-new single triplet nearly every
    frame, on top of the (stable) normal scene. Tempts a per-triplet novelty gate."""
    pid = f"p{rng.randint(1, 4)}"
    nodes = {pid: "person", "l1": "laptop", "d1": "desk", "scr1": "screen", "ch1": "chair"}
    edges = [
        (pid, "typing", "l1"),
        ("l1", "on", "d1"),
        (pid, "sitting_on", "ch1"),
    ]
    # the screen shows a different (novel) thing every frame -> churning, un-modelable
    content = rng.choice(_SCREEN_CONTENT)
    cid = f"x_{content}_{rng.randint(0, 999)}"
    nodes[cid] = content
    edges.append(("scr1", "shows", cid))
    # plus a little detector jitter: a spurious one-off edge
    if rng.random() < 0.5:
        jid = f"j{rng.randint(0, 9999)}"
        nodes[jid] = rng.choice(["shadow", "reflection", "blur"])
        edges.append(("scr1", "near", jid))
    return nodes, edges, 0


# --------------------------------------------------------------------------- #
# REGIME B: reconfiguration events -- the decisive test of the brief's thesis.
# Every relation here is drawn from one shared vocabulary. NORMAL frames each show ONE
# coherent activity. An EVENT is a novel CO-OCCURRENCE of relations that are each common
# on their own but never co-occur in any normal activity. So:
#   - single-edge (typed triple) marginals are ~identical normal vs event  -> triplet gate blind
#   - node TYPE counts are ~identical normal vs event                       -> node-embedding blind
#   - only the CONFIGURATION (which familiar edges co-occur) reveals the event.
# --------------------------------------------------------------------------- #
_BASE_NODES = {"p1": "person", "c1": "cup", "l1": "laptop",
               "d1": "desk", "ch1": "chair", "bk1": "book", "fl1": "floor"}

# each normal activity is a coherent bundle of edges (all relations reused across the set)
_ACTIVITIES = {
    "work":    [("p1", "typing", "l1"), ("l1", "on", "d1"), ("p1", "sitting_on", "ch1"),
                ("c1", "beside", "l1")],
    "break":   [("p1", "holding", "c1"), ("p1", "sitting_on", "ch1"), ("c1", "on", "d1"),
                ("l1", "on", "d1")],
    "read":    [("p1", "holding", "bk1"), ("p1", "looking_at", "bk1"),
                ("p1", "sitting_on", "ch1"), ("l1", "on", "d1")],
    "check":   [("p1", "looking_at", "l1"), ("p1", "sitting_on", "ch1"), ("l1", "on", "d1")],
    "stretch": [("p1", "standing", "fl1"), ("l1", "on", "d1"), ("ch1", "beside", "d1")],
}

# reconfiguration events: recombine ONLY edges/triples that occur in _ACTIVITIES above,
# into co-occurrences no single activity produces.
_RECONFIG = {
    # stood up, still staring at the screen (standing[stretch] + looking_at laptop[check])
    "alarm":  [("p1", "standing", "fl1"), ("p1", "looking_at", "l1"), ("l1", "on", "d1")],
    # standing while holding a cup AND a book (holding[break/read] co-occurring + standing)
    "fumble": [("p1", "standing", "fl1"), ("p1", "holding", "c1"), ("p1", "holding", "bk1")],
    # cup on the floor (on[seen for laptop/cup-on-desk] but cup-on-floor co-occurrence novel)
    #   uses only the triple (c1,on,...) and (p1,looking_at,l1), both seen as relations
    "spill":  [("p1", "looking_at", "l1"), ("c1", "on", "d1"), ("p1", "standing", "fl1"),
               ("l1", "on", "d1")],
    # slumped: sitting + book on desk + looking at laptop (book-on-desk co-occurrence novel)
    "slump":  [("p1", "sitting_on", "ch1"), ("p1", "looking_at", "l1"), ("c1", "on", "d1"),
               ("p1", "holding", "bk1")],
}


def _reconfig_normal(rng):
    act = rng.choice(list(_ACTIVITIES))
    return dict(_BASE_NODES), list(_ACTIVITIES[act]), 0


# pool of FAMILIAR person-centred edges (each appears in some normal activity)
_PERSON_EDGES = [("p1", "typing", "l1"), ("p1", "sitting_on", "ch1"), ("p1", "holding", "c1"),
                 ("p1", "holding", "bk1"), ("p1", "looking_at", "bk1"),
                 ("p1", "looking_at", "l1"), ("p1", "standing", "fl1")]
# which familiar pairs ALREADY co-occur in a normal activity (so they are NOT novel)
_NORMAL_PAIRS = set()
for _acts in _ACTIVITIES.values():
    _pe = [e for e in _acts if e[0] == "p1"]
    for _i in range(len(_pe)):
        for _j in range(_i + 1, len(_pe)):
            _NORMAL_PAIRS.add(frozenset((_pe[_i], _pe[_j])))


def _reconfig_event(rng):
    """A varied worth-noticing reconfiguration: 2-3 FAMILIAR person-edges combined into a
    co-occurrence that no normal activity contains. Combinatorial variety means most events
    are genuinely first-of-their-kind (tests detection), while some recur (tests
    habituation). Each edge is individually familiar -> triplet/embedding gates stay blind."""
    for _ in range(20):
        k = rng.choice([2, 3])
        es = rng.sample(_PERSON_EDGES, k)
        pairs = [frozenset((es[i], es[j])) for i in range(len(es)) for j in range(i + 1, len(es))]
        if any(p not in _NORMAL_PAIRS for p in pairs):      # at least one novel co-occurrence
            edges = list(es) + [("l1", "on", "d1")]         # keep the familiar backdrop
            return dict(_BASE_NODES), edges, 1
    return dict(_BASE_NODES), list(_RECONFIG["alarm"]), 1


def make_stream(n: int = 600, p_event: float = 0.06, p_noise: float = 0.25,
                seed: int = 0, mode: str = "novel_edge"):
    """Return a list of (nodes, edges, label) where label 1 = ground-truth worth-noticing.

    The stream front-loads a pure-NORMAL warm-up so every gate has a fair chance to build
    its baseline before events/noise begin (a placed companion habituates first)."""
    rng = random.Random(seed)
    norm = _reconfig_normal if mode == "reconfig" else _normal
    evt = _reconfig_event if mode == "reconfig" else _event
    out = []
    warm = max(20, n // 12)
    for i in range(n):
        if i < warm:
            out.append(norm(rng)); continue
        r = rng.random()
        if r < p_event:
            out.append(evt(rng))
        elif r < p_event + p_noise:
            out.append(_noise(rng))      # same churning-screen noise in both regimes
        else:
            out.append(norm(rng))
    return out


if __name__ == "__main__":
    s = make_stream(60, seed=1)
    n_ev = sum(l for _, _, l in s)
    print(f"{len(s)} frames, {n_ev} ground-truth events")
    for nodes, edges, lab in s[:6]:
        print(("EVENT" if lab else "normal"), "edges=", len(edges))
