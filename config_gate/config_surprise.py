"""
config_surprise.py — the configuration-surprise NOTICING GATE.

Thesis (concept_brief_relational_surprise.md): a placed companion should not run a
VLM on every frame. It should measure the *structural novelty of the relational-graph
configuration* of a scene, and only fire the VLM when that configuration is surprising
relative to what it has habituated to in THIS space.

Novelty lives in the CONFIGURATION, not the single edge:
    nodes {person, cup, laptop} stay the same; the way the edges combine changes ->
    person-typing->laptop, cup-beside->laptop      = working      (habituated)
    person-looking->laptop, cup-knocked_over        = a spill      (novel motif combo)

So surprise is computed over the space of MOTIFS (typed length-1 edges and length-2
relational paths A-r1-B-r2-C), abstracted to relation/type level so "a different person
typing" is NOT a new configuration. Recurrence -> the prior concentrates -> surprise -> 0
(boredom; Itti & Baldi 2009 Bayesian Surprise). A churning, un-modelable source
(a flickering screen) is always "new" but carries no learnable structure, so it is
down-weighted (learning-progress / IAC idea, Oudeyer et al.).

Cheap: pure-python Counters, no NN, no torch. The expensive VLM runs only when the gate
fires. Reuses taste.py's ema_update spirit (exponential habituation) but over
configurations instead of the 9 taste dimensions.

A scene graph is given as:
    nodes: dict  node_id -> type   e.g. {"p1":"person", "c1":"cup", "l1":"laptop"}
    edges: list of (src_id, relation, dst_id)
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Iterable

Node = str
Edge = Tuple[str, str, str]            # (src_id, relation, dst_id)


# --------------------------------------------------------------------------- #
# 1. Configuration representation: a scene graph -> a bag of typed motifs.
# --------------------------------------------------------------------------- #
def motifs(nodes: Dict[Node, str], edges: List[Edge]) -> Counter:
    """Decompose a scene graph into its configuration = a multiset of typed motifs.

    Two motif orders (the brief's 'motifs / length-2 paths'):
      - length-1: a single typed edge      (typeA, rel, typeB)
      - length-2: a relational path A-r1-B-r2-C   (typeA, r1, typeB, r2, typeC)

    Node IDENTITIES are abstracted to TYPES, so a different person doing the same thing
    maps to the same motif (this is the combinatorial-explosion fix #1 from the brief:
    habituate over relation types, not raw instances).
    """
    t = nodes  # id -> type
    bag: Counter = Counter()

    # length-1 typed edges
    for (a, r, b) in edges:
        if a in t and b in t:
            bag[("E", t[a], r, t[b])] += 1

    # length-2 paths through a shared middle node B:  A -r1-> B -r2-> C
    out_by_node: Dict[Node, List[Edge]] = defaultdict(list)
    in_by_node: Dict[Node, List[Edge]] = defaultdict(list)
    for e in edges:
        out_by_node[e[0]].append(e)
        in_by_node[e[2]].append(e)
    for mid in t:
        for (a, r1, _b) in in_by_node.get(mid, []):
            for (_b2, r2, c) in out_by_node.get(mid, []):
                if a == c:
                    continue  # skip trivial A-r-B-r-A back-and-forth
                if a in t and c in t:
                    bag[("P", t[a], r1, t[mid], r2, t[c])] += 1

    # CO-OCCURRENCE motifs: two edges sharing a node (any role). This is what makes
    # "configuration" novelty real -- it captures that two individually-familiar
    # relations now co-occur on the same node (the working->spill case: the EDGES are
    # familiar, the COMBINATION is not). Single-triplet novelty cannot see this.
    incident: Dict[Node, list] = defaultdict(list)
    for (a, r, b) in edges:
        if a in t and b in t:
            sig = (t[a], r, t[b])
            incident[a].append(sig)
            incident[b].append(sig)
    for n, sigs in incident.items():
        uniq = sorted(set(sigs))
        for i in range(len(uniq)):
            for j in range(i + 1, len(uniq)):
                bag[("C", t[n], uniq[i], uniq[j])] += 1
    return bag


# --------------------------------------------------------------------------- #
# 2. Habituated prior over configurations (online, decaying Dirichlet counts).
# --------------------------------------------------------------------------- #
@dataclass
class HabituatedPrior:
    """A decaying count prior over motifs for ONE space.

    decay implements exponential habituation (taste.py ema_update spirit): each step the
    whole count mass is multiplied by `decay`, so motifs that stop recurring fade and can
    surprise again, while a constantly-repeating motif saturates and stops surprising.

    alpha is add-alpha (Dirichlet) smoothing so a never-seen motif has finite, high
    surprise rather than infinite.
    """
    decay: float = 0.997     # slow forgetting: a config seen once stays habituated for a
                             # long time (~230-frame half-life), so rare-but-normal layouts
                             # don't re-surprise, while a truly abandoned config can
                             # eventually become novel again.
    alpha: float = 0.5
    counts: Counter = field(default_factory=Counter)
    total: float = 0.0
    vocab: set = field(default_factory=set)   # motifs ever seen (for the smoothing denom)

    def p(self, motif) -> float:
        """Smoothed probability of one motif under the current prior."""
        V = max(len(self.vocab), 1)
        return (self.counts.get(motif, 0.0) + self.alpha) / (self.total + self.alpha * V)

    def self_information(self, bag: Counter) -> float:
        """MVP surprise: mean -log p over the motifs present in this configuration.
        This is the brief's `surprise = -log p of the current configuration`."""
        if not bag:
            return 0.0
        s = 0.0
        n = 0
        for motif, k in bag.items():
            s += k * (-math.log(self.p(motif)))
            n += k
        return s / max(n, 1)

    def per_motif_si(self, bag: Counter) -> Dict[tuple, float]:
        """Self-information -log p for each motif in the configuration (un-aggregated)."""
        return {m: -math.log(self.p(m)) for m in bag}

    def per_motif_novelty(self, bag: Counter, beta: float = 1.0) -> Dict[tuple, float]:
        """Habituation-recency novelty in 0..1:  nov(m) = exp(-beta * decayed_count(m)).

        This is the crucial distinction from raw -log p: it measures HAVE-I-SEEN-THIS,
        not HOW-PROBABLE-IS-THIS. A configuration that is individually RARE but RECURS
        across the deployment (e.g. 'chair beside desk' during occasional stretches) drives
        its decayed count up and so habituates to nov->0 (Itti-Baldi boredom). A motif that
        has genuinely never occurred has count 0 -> nov = 1, even though it may be built
        from perfectly ordinary edges. That is what lets the gate separate a NOVEL
        CO-OCCURRENCE from a merely uncommon-but-known one."""
        return {m: math.exp(-beta * self.counts.get(m, 0.0)) for m in bag}

    def bayesian_surprise(self, bag: Counter) -> float:
        """Itti & Baldi (2009): KL( posterior || prior ) over the Dirichlet after
        observing this configuration. Recurrence -> posterior ~ prior -> KL -> 0 (boredom).
        Closed-form-free approximation: sum over affected motifs of the per-motif KL of a
        Beta(count+alpha, rest) before/after the +k update, which for a Dirichlet reduces
        to a stable, monotone function of how much each motif's mass moves."""
        if not bag:
            return 0.0
        V = max(len(self.vocab | set(bag)), 1)
        a0 = self.total + self.alpha * V          # prior concentration
        kl = 0.0
        for motif, k in bag.items():
            c = self.counts.get(motif, 0.0) + self.alpha
            # KL contribution of moving this component's mass by k (Dirichlet/Beta marginal)
            a1 = a0 + sum(bag.values())
            p_prior = c / a0
            p_post = (c + k) / a1
            if p_post > 0 and p_prior > 0:
                kl += p_post * math.log(p_post / p_prior)
        return kl

    def observe(self, bag: Counter) -> None:
        """Habituate: decay all mass, then add this configuration's motifs."""
        if self.decay < 1.0:
            for m in list(self.counts):
                self.counts[m] *= self.decay
            self.total *= self.decay
        for motif, k in bag.items():
            self.counts[motif] += k
            self.total += k
            self.vocab.add(motif)


# --------------------------------------------------------------------------- #
# 3. Learning-progress / noise suppression (IAC, Oudeyer et al.).
# --------------------------------------------------------------------------- #
@dataclass
class ChurnSuppressor:
    """Learning-progress / IAC noise suppression (Oudeyer et al.).

    The hard case: a BUSY-BUT-MEANINGFUL agent (a person, who types, then drinks, then
    stands) is highly DIVERSE, just like a flickering screen -- so a naive 'diversity =
    noise' rule wrongly suppresses real events. The true distinction is LEARNING PROGRESS:
    a person's motifs RECUR and become predictable; a screen's content is a one-off every
    frame and NEVER becomes predictable.

    So per ANCHOR we track the REPEAT RATE: of all motifs ever observed at this anchor,
    what fraction had already been seen (count>=1) when observed again. A screen anchor
    -> repeat rate ~0 (un-modelable -> low trust). A person anchor -> repeat rate high
    (learnable -> high trust), so a genuinely new person-centred configuration is NOT
    suppressed -- its anchor has proven itself learnable. A brand-new anchor (a dog that
    just entered) has no history -> trust defaults to 1 (we DO want to notice it)."""
    warm: int = 6                      # need this many obs at an anchor before we trust the rate
    n_obs: Dict[str, float] = field(default_factory=lambda: defaultdict(float))
    n_repeat: Dict[str, float] = field(default_factory=lambda: defaultdict(float))
    seen: Dict[str, set] = field(default_factory=lambda: defaultdict(set))

    @staticmethod
    def anchor(motif) -> str:
        """The node type a motif 'hangs off' -- its subject/middle."""
        if motif[0] == "E":     return motif[1]   # ("E", tA, r, tB)
        if motif[0] == "P":     return motif[3]   # ("P", tA, r1, tMID, r2, tC)
        return motif[1]                            # ("C", tShared, sigA, sigB)

    def trust_by_anchor(self, bag: Counter) -> Dict[str, float]:
        """Update per-anchor learning-progress stats; return anchor -> trust in 0..1
        (1 = a source that recurs / is modelable, ->0 = a source that is novel every time
        and never learnable, i.e. noise)."""
        trust = {}
        anchors = set(self.anchor(m) for m in bag)
        # update stats from this frame's motifs
        for m in bag:
            a = self.anchor(m)
            if m in self.seen[a]:
                self.n_repeat[a] += 1
            self.n_obs[a] += 1
            self.seen[a].add(m)
        for a in anchors:
            if self.n_obs[a] < self.warm:
                trust[a] = 1.0                       # new/young anchor: don't suppress yet
            else:
                trust[a] = self.n_repeat[a] / self.n_obs[a]
        return trust


# --------------------------------------------------------------------------- #
# 4. The gate.
# --------------------------------------------------------------------------- #
@dataclass
class ConfigSurpriseGate:
    """Cost-ordered: cheap structural surprise decides whether to spend a VLM call.

    A configuration is surprising if it contains ANY highly-improbable substructure, so
    we aggregate the per-motif surprise with MAX (not mean) -- otherwise a single novel
    co-occurrence is diluted by the many familiar motifs around it (the reconfiguration
    case). Churn/IAC trust is applied PER MOTIF, so a churning screen is suppressed
    without suppressing a genuine event occurring in the same frame.

    agg  : "max" (default) | "mean" | "topk"
    mode : "habituation" (per-motif exp(-count) recency novelty; the working gate)
         | "selfinfo"    (per-motif -log p; the brief's literal MVP)
         | "bayes"       (Itti-Baldi, config-level KL)
    """
    threshold: float = 0.5
    mode: str = "habituation"
    agg: str = "max"
    topk: int = 3
    beta: float = 1.0
    suppress_noise: bool = True
    prior: HabituatedPrior = field(default_factory=HabituatedPrior)
    churn: ChurnSuppressor = field(default_factory=ChurnSuppressor)

    def step(self, nodes: Dict[Node, str], edges: List[Edge]) -> dict:
        """Process one stable scene graph. Returns a decision dict; observes (habituates)
        regardless, so the prior tracks the lived statistics of the space."""
        bag = motifs(nodes, edges)
        top = []                                       # (motif, weighted_novelty) drivers
        if self.mode == "bayes":
            raw = self.prior.bayesian_surprise(bag)
            trust = (min(self.churn.trust_by_anchor(bag).values(), default=1.0)
                     if self.suppress_noise else 1.0)
            score = raw * trust
        else:
            si = (self.prior.per_motif_novelty(bag, self.beta) if self.mode == "habituation"
                  else self.prior.per_motif_si(bag))
            trust_anc = self.churn.trust_by_anchor(bag) if self.suppress_noise else {}
            wmap = {m: s * trust_anc.get(self.churn.anchor(m), 1.0) for m, s in si.items()}
            weighted = list(wmap.values())
            if not weighted:
                score = 0.0
            elif self.agg == "mean":
                score = sum(weighted) / len(weighted)
            elif self.agg == "topk":
                score = sum(sorted(weighted, reverse=True)[:self.topk]) / min(self.topk, len(weighted))
            else:  # max -- a configuration is novel if ANY substructure is improbable
                score = max(weighted)
            raw = max(si.values()) if si else 0.0
            trust = min(trust_anc.values()) if trust_anc else 1.0
            top = sorted(wmap.items(), key=lambda kv: -kv[1])[:3]
        fire = score >= self.threshold
        self.prior.observe(bag)           # habituate AFTER scoring
        return {"fire": fire, "score": score, "raw": raw, "trust": trust,
                "n_motifs": sum(bag.values()), "bag": bag, "top": top}


@dataclass
class TemporalConfigGate:
    """The temporal layer (brief: 'a configuration TRANSITION = an event').

    The frame-level gate above will keep firing for as long as a novel configuration
    persists. A placed companion should notice an event ONCE -- at the moment the scene
    transitions into the novel configuration -- and then settle. This wrapper:

      - fires only on the RISING EDGE (quiet/known -> novel), not every novel frame;
      - then stays silent until the scene returns to a non-novel state (re-arm), so a
        sustained novel state is one event, not a burst;
      - reports the TRANSITION delta (motifs ADDED vs the last stable configuration) and
        the driving motifs, i.e. exactly the structured 'what changed' to hand the VLM to
        *codify the moment* -- not the raw frame.

    This is the cheap step-3 gate that decides whether to spend the expensive step-4 VLM
    call, and packages the call's input."""
    gate: ConfigSurpriseGate = field(default_factory=ConfigSurpriseGate)
    persist: int = 2                     # a change must hold this many frames to be 'confirmed'
    threshold: float = 0.5
    decay: float = 0.98                  # how fast a recurring transition habituates
    beta: float = 1.0
    window: int = 8                      # rolling window for type-presence stability
    stable_frac: float = 0.6             # a type is 'stable' if present in >= this frac of window
    baseline: set = field(default_factory=set)        # last COMMITTED settled config (frozen)
    base_types: set = field(default_factory=set)
    absent: dict = field(default_factory=dict)        # baseline motif -> consecutive frames absent
    present: dict = field(default_factory=dict)       # non-baseline motif -> consecutive frames present
    trans_counts: Counter = field(default_factory=Counter)   # habituation over TRANSITIONS
    _twin: dict = field(default_factory=dict)         # type -> deque of recent present(1)/absent(0)

    @staticmethod
    def _types_of(m):
        if m[0] == "E": return (m[1], m[3])
        if m[0] == "P": return (m[1], m[3], m[5])
        return (m[1],)

    def step(self, nodes: Dict[Node, str], edges: List[Edge]) -> dict:
        d = self.gate.step(nodes, edges)         # keeps the config-prior habituating; gives bag/top
        bag = d["bag"]
        cur = set(bag)
        cur_types = set(nodes.values())
        if not self.baseline:                    # first frame: adopt as baseline, no event
            self.baseline, self.base_types = cur, cur_types
            d.update(event=False, delta_added=[], left=[], arrived=[], subject=None, change=0.0)
            return d

        # The EVENT is a persistent STRUCTURAL CHANGE vs the committed baseline (add OR remove —
        # so departures, arrivals AND returns all count). Flicker is filtered by `persist`. Then
        # HABITUATION is applied to the TRANSITION itself: the FIRST time a given change happens
        # it fires; if the SAME transition (e.g. this person leaving) recurs, its count rises and
        # it is optimised away (boredom). Pure structure; one mechanism; no novelty/type layer.
        # per-type rolling presence -> only STABLE types count (kills background detector flicker,
        # e.g. a bookshelf/desk flickering in&out or being briefly occluded; saves wasted VLM calls).
        for t in set(self._twin) | cur_types:
            dq = self._twin.setdefault(t, deque(maxlen=self.window))
            dq.append(1 if t in cur_types else 0)
        def stable(t):
            dq = self._twin.get(t)
            return bool(dq) and sum(dq) >= self.stable_frac * dq.maxlen
        def motif_stable(m):
            return all(stable(t) for t in self._types_of(m))

        for m in cur:
            self.present[m] = self.present.get(m, 0) + 1
        for m in [k for k in self.present if k not in cur]:
            del self.present[m]
        for m in self.baseline:
            self.absent[m] = 0 if m in cur else self.absent.get(m, 0) + 1
        confirmed_added = [m for m in cur if m not in self.baseline
                           and self.present.get(m, 0) >= self.persist and motif_stable(m)]
        confirmed_removed = [m for m in self.baseline
                             if self.absent.get(m, 0) >= self.persist and motif_stable(m)]

        event, delta_added, left, arrived, subject, change = False, [], [], [], None, 0.0
        if confirmed_added or confirmed_removed:
            # transition signature: arrivals/departures keyed at TYPE level (so "person leaves"
            # recurring habituates), pure reconfiguration keyed at motif level (distinct rewirings
            # each get their own first-time fire).
            t_add = cur_types - self.base_types
            t_rem = self.base_types - cur_types
            if t_add or t_rem:
                sig = ("type", frozenset(t_add), frozenset(t_rem))
            else:
                sig = ("cfg", frozenset(confirmed_added), frozenset(confirmed_removed))
            change = math.exp(-self.beta * self.trans_counts.get(sig, 0.0))    # 1 first time -> 0 if recurring
            for k in list(self.trans_counts):                                  # habituate transitions
                self.trans_counts[k] *= self.decay
            self.trans_counts[sig] += 1
            event = change >= self.threshold
            if event:
                delta_added = [(m, 1) for m in confirmed_added]
                left = sorted(self.base_types - cur_types)
                arrived = sorted(cur_types - self.base_types)
                chg = Counter()                                  # subject = most-changed node type
                for m in confirmed_added + confirmed_removed:
                    chg.update(self._types_of(m))
                subject = chg.most_common(1)[0][0] if chg else None
            # commit the new state as baseline whether or not we reported it (the change happened)
            self.baseline, self.base_types, self.absent, self.present = cur, cur_types, {}, {}
        d.update(event=event, delta_added=delta_added, left=left, arrived=arrived,
                 subject=subject, change=round(change, 3), armed=True)
        return d

    @staticmethod
    def describe(delta_added, top, left=None, arrived=None) -> str:
        """A compact, human-readable 'what changed' for logs / the VLM prompt."""
        def fmt(m):
            if m[0] == "E": return f"{m[1]}-{m[2]}->{m[3]}"
            if m[0] == "P": return f"{m[1]}-{m[2]}->{m[3]}-{m[4]}->{m[5]}"
            return f"({m[2][0]}-{m[2][1]}->{m[2][2]}) + ({m[3][0]}-{m[3][1]}->{m[3][2]})"
        parts = []
        if arrived: parts.append("arrived: " + ", ".join(arrived))
        if left:    parts.append("left: " + ", ".join(left))
        new = [fmt(m) for m, _ in delta_added] or [fmt(m) for m, _ in top]
        if new: parts.append("new structure: " + "; ".join(new[:3]))
        return " | ".join(parts) if parts else "configuration changed"


if __name__ == "__main__":
    # The brief's own example: same nodes, different edge configurations.
    g = ConfigSurpriseGate(threshold=1.5, mode="selfinfo")
    nodes = {"p1": "person", "c1": "cup", "l1": "laptop", "d1": "desk"}
    working = [("p1", "typing", "l1"), ("c1", "beside", "l1"), ("l1", "on", "d1")]
    spill   = [("p1", "looking_at", "l1"), ("c1", "knocked_over", "d1"), ("l1", "on", "d1")]

    print("warm-up on the working configuration (habituation):")
    for i in range(8):
        d = g.step(nodes, working)
        print(f"  t{i}: score={d['score']:.2f} fire={d['fire']}")
    print("then the spill (novel motif combination, same nodes):")
    d = g.step(nodes, spill)
    print(f"  spill: score={d['score']:.2f} fire={d['fire']}  <- should fire")

    # --- temporal layer: one event per transition, with the 'what changed' delta ---
    print("\nTEMPORAL gate over a sequence (work x4 -> spill x4 -> work x2):")
    tg = TemporalConfigGate(gate=ConfigSurpriseGate(threshold=0.5, mode="habituation"))
    seq = [working] * 4 + [spill] * 4 + [working] * 2
    for i, e in enumerate(seq):
        d = tg.step(nodes, e)
        tag = "  <== EVENT" if d["event"] else ""
        line = f"  t{i}: {'spill' if e is spill else 'work '} fire={int(d['fire'])} event={int(d['event'])}{tag}"
        if d["event"]:
            line += "\n        " + TemporalConfigGate.describe(d["delta_added"], d["top"])
        print(line)
    print("  (the 4-frame spill should yield exactly ONE event, on its rising edge.)")
