"""
eval.py — does the configuration-surprise gate actually work, and does it beat the
neighbours the brief names? Compares four gates on the simulated placed-camera stream:

  ALWAYS-ON        : run the VLM every frame (the status quo the brief argues against).
  TRIPLET-NOVELTY  : habituate/surprise over SINGLE edges only (no configurations, no
                     noise suppression). The 'definitely not single triplets' strawman.
  NODE-EMBEDDING   : whole-scene novelty from a bag-of-node-TYPES vector (structure
                     discarded) -> stands in for the holistic image-embedding approach.
  CONFIG-SURPRISE  : ours -- motif configurations + Bayesian habituation + churn/IAC
                     noise suppression.

Each gate gets its BEST-F1 threshold by a sweep (so no gate is sandbagged), and we also
report VLM-call budget and false fires on noise. Metrics are averaged over many seeds.
"""

from __future__ import annotations
import math
from collections import Counter, defaultdict
from statistics import mean, pstdev

from sim import make_stream
from config_surprise import motifs, HabituatedPrior, ConfigSurpriseGate


# --------------------------------------------------------------------------- #
# baseline gates
# --------------------------------------------------------------------------- #
class TripletNovelty:
    """Clean ablation of CONFIG: IDENTICAL machinery (per-motif -log p, max aggregation,
    per-anchor churn suppression) but the representation is SINGLE TYPED EDGES only -- no
    length-2 paths, no co-occurrence motifs. So any gap vs CONFIG is attributable purely
    to the configuration representation, nothing else."""
    def __init__(self, decay=0.98, alpha=0.5):
        from config_surprise import ChurnSuppressor
        self.prior = HabituatedPrior(decay=decay, alpha=alpha)
        self.churn = ChurnSuppressor()

    def score(self, nodes, edges):
        bag = Counter()
        for (a, r, b) in edges:
            if a in nodes and b in nodes:
                bag[("E", nodes[a], r, nodes[b])] += 1
        si = self.prior.per_motif_novelty(bag, beta=1.0)
        trust = self.churn.trust_by_anchor(bag)
        weighted = [s * trust.get(self.churn.anchor(m), 1.0) for m, s in si.items()]
        score = max(weighted) if weighted else 0.0
        self.prior.observe(bag)
        return score


class NodeEmbedding:
    """Holistic 'image embedding' stand-in: a running mean over bag-of-node-TYPE vectors.
    Novelty = 1 - cosine(current, running mean). Throws relational structure away."""
    def __init__(self, ema=0.05):
        self.ema = ema
        self.mean = defaultdict(float)

    @staticmethod
    def _vec(nodes):
        v = Counter(nodes.values())
        return v

    def score(self, nodes, edges):
        v = self._vec(nodes)
        keys = set(v) | set(self.mean)
        dot = sum(v.get(k, 0) * self.mean.get(k, 0.0) for k in keys)
        nv = math.sqrt(sum(x * x for x in v.values()))
        nm = math.sqrt(sum(x * x for x in self.mean.values()))
        cos = dot / (nv * nm) if nv > 0 and nm > 0 else 0.0
        nov = 1.0 - cos
        for k in keys:                          # EMA update of the running mean vector
            self.mean[k] = (1 - self.ema) * self.mean.get(k, 0.0) + self.ema * v.get(k, 0)
        return nov


# --------------------------------------------------------------------------- #
# scoring a whole stream -> list of (score, label, is_noise)
# --------------------------------------------------------------------------- #
def run_gate(gate_factory, stream, skip=0):
    """Run a gate over the stream. The first `skip` frames (the warm-up during which a
    deployed companion is still building its baseline) are observed/habituated but NOT
    scored for metrics -- judging a gate before it has a baseline is not meaningful."""
    g = gate_factory()
    scored = []
    for i, (nodes, edges, lab) in enumerate(stream):
        if hasattr(g, "step"):
            s = g.step(nodes, edges)["score"]
        else:
            s = g.score(nodes, edges)
        if i < skip:
            continue
        is_noise = (lab == 0 and any(nodes.get(n) == "screen" for n in nodes))
        scored.append((s, lab, is_noise))
    return scored


def best_f1(scored):
    """Sweep threshold; return (best_f1, precision, recall, thr, fire_rate, noise_fp_rate)."""
    labels = [l for _, l, _ in scored]
    P = sum(labels)
    N = len(labels)
    noise_total = sum(1 for _, _, nz in scored if nz)
    cand = sorted(set(s for s, _, _ in scored))
    best = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    for thr in cand:
        tp = sum(1 for s, l, _ in scored if s >= thr and l == 1)
        fp = sum(1 for s, l, _ in scored if s >= thr and l == 0)
        fires = tp + fp
        prec = tp / fires if fires else 0.0
        rec = tp / P if P else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        if f1 > best[0]:
            noise_fp = sum(1 for s, l, nz in scored if s >= thr and nz)
            best = (f1, prec, rec, thr, fires / N, noise_fp / max(noise_total, 1))
    return best


def recall_by_type(stream, scored, thr, skip=0):
    """Recall split by event kind, to show WHERE a gate fails."""
    stream = stream[skip:]
    # recover event kind from the edges (cheap heuristic on the relation set)
    def kind(edges):
        rels = {r for _, r, _ in edges}
        if "knocked_over" in rels: return "spill"
        if "handing" in rels or "received_by" in rels: return "handover"
        if "approaching" in rels: return "newcomer"
        if "leaving" in rels or "empty" in rels: return "leaving"
        # reconfig regime: identify by the co-occurrence signature
        n_hold = sum(1 for _, r, _ in edges if r == "holding")
        if n_hold >= 2: return "fumble"
        if any(r == "standing" for _, r, _ in edges) and any(r == "looking_at" for _, r, _ in edges):
            return "alarm/spill"
        if any(r == "sitting_on" for _, r, _ in edges): return "slump"
        return "other"
    by = defaultdict(lambda: [0, 0])
    for (nodes, edges, lab), (s, _l, _n) in zip(stream, scored):
        if lab == 1:
            k = kind(edges)
            by[k][1] += 1
            if s >= thr:
                by[k][0] += 1
    return {k: (hit / tot if tot else 0.0) for k, (hit, tot) in by.items()}


# --------------------------------------------------------------------------- #
# main comparison
# --------------------------------------------------------------------------- #
def regime_diagnostic(mode, seeds=10, n=600):
    """Confirm the regime is what we claim: in 'reconfig', event typed-edges should almost
    all have been seen in normal (so triplet novelty is blind), while event co-occurrence
    motifs should be mostly novel (so only configuration sees them)."""
    seen_edge = []
    seen_cooc = []
    for seed in range(seeds):
        stream = make_stream(n=n, seed=seed, mode=mode)
        norm_edges = set()
        norm_cooc = set()
        # first pass: learn what 'normal' contains
        for nodes, edges, lab in stream:
            if lab == 0:
                for (a, r, b) in edges:
                    if a in nodes and b in nodes:
                        norm_edges.add((nodes[a], r, nodes[b]))
                for m in motifs(nodes, edges):
                    if m[0] == "C":
                        norm_cooc.add(m)
        for nodes, edges, lab in stream:
            if lab == 1:
                es = [(nodes[a], r, nodes[b]) for (a, r, b) in edges if a in nodes and b in nodes]
                if es:
                    seen_edge.append(sum(e in norm_edges for e in es) / len(es))
                cs = [m for m in motifs(nodes, edges) if m[0] == "C"]
                if cs:
                    seen_cooc.append(sum(m in norm_cooc for m in cs) / len(cs))
    print(f"  [{mode}] event typed-edges already seen in normal: {mean(seen_edge):.0%}"
          f"  |  event co-occurrence motifs already seen: {mean(seen_cooc) if seen_cooc else 0:.0%}")


def main(seeds=25, n=600, mode="novel_edge"):
    gates = {
        "ALWAYS-ON":       None,   # special-cased
        "TRIPLET (habit+IAC)": lambda: TripletNovelty(),
        "NODE-EMBEDDING":  lambda: NodeEmbedding(),
        "CONFIG (habit+IAC)":  lambda: ConfigSurpriseGate(mode="habituation", agg="max", threshold=0.0),
        "CONFIG (-log p MVP)": lambda: ConfigSurpriseGate(mode="selfinfo", agg="max", threshold=0.0),
        "CONFIG (no-IAC)":     lambda: ConfigSurpriseGate(mode="habituation", agg="max",
                                                          suppress_noise=False, threshold=0.0),
    }
    agg = {name: defaultdict(list) for name in gates}
    typed = {name: defaultdict(list) for name in gates}

    skip = max(20, n // 12)            # warm-up frames: observed but not scored
    for seed in range(seeds):
        stream = make_stream(n=n, seed=seed, mode=mode)
        post = stream[skip:]
        P = sum(l for _, _, l in post)
        for name, fac in gates.items():
            if name == "ALWAYS-ON":
                # fires every frame: recall 1, precision = base rate, cost = N
                prec = P / len(post); rec = 1.0
                f1 = 2 * prec * rec / (prec + rec)
                agg[name]["f1"].append(f1); agg[name]["prec"].append(prec)
                agg[name]["rec"].append(rec); agg[name]["fire"].append(1.0)
                agg[name]["noise_fp"].append(1.0)
                continue
            scored = run_gate(fac, stream, skip=skip)
            f1, prec, rec, thr, fire, noise_fp = best_f1(scored)
            agg[name]["f1"].append(f1); agg[name]["prec"].append(prec)
            agg[name]["rec"].append(rec); agg[name]["fire"].append(fire)
            agg[name]["noise_fp"].append(noise_fp)
            for k, v in recall_by_type(stream, scored, thr, skip=skip).items():
                typed[name][k].append(v)

    print(f"\n=== REGIME: {mode} ===")
    print(f"Averaged over {seeds} seeds, {n} frames each "
          f"(~{mean([sum(l for _,_,l in make_stream(n=n, seed=s, mode=mode)) for s in range(seeds)]):.0f} events/stream)\n")
    hdr = f"{'gate':<20}{'F1':>7}{'prec':>7}{'recall':>8}{'fire%':>8}{'noiseFP%':>10}"
    print(hdr); print("-" * len(hdr))
    for name in gates:
        a = agg[name]
        print(f"{name:<20}{mean(a['f1']):>7.2f}{mean(a['prec']):>7.2f}"
              f"{mean(a['rec']):>8.2f}{100*mean(a['fire']):>7.1f}%{100*mean(a['noise_fp']):>9.1f}%")

    print("\nrecall by event type (at each gate's best-F1 threshold):")
    kinds = (["spill", "handover", "newcomer", "leaving"] if mode == "novel_edge"
             else ["alarm/spill", "fumble", "slump"])
    print(f"{'gate':<20}" + "".join(f"{k:>11}" for k in kinds))
    for name in gates:
        if name == "ALWAYS-ON":
            print(f"{name:<20}" + "".join(f"{1.0:>11.2f}" for _ in kinds)); continue
        row = typed[name]
        print(f"{name:<20}" + "".join(
            f"{mean(row[k]) if row[k] else 0.0:>11.2f}" for k in kinds))

    # headline cost saving
    cfg = agg["CONFIG (habit+IAC)"]
    print(f"\nVLM calls vs ALWAYS-ON: config gate fires on "
          f"{100*mean(cfg['fire']):.1f}% of frames "
          f"-> ~{1/ mean(cfg['fire']):.1f}x fewer VLM calls, "
          f"recall {mean(cfg['rec']):.2f}, noise false-fire {100*mean(cfg['noise_fp']):.1f}%.")


if __name__ == "__main__":
    print("Regime sanity check (are the streams what we claim?):")
    regime_diagnostic("novel_edge")
    regime_diagnostic("reconfig")
    main(mode="novel_edge")
    main(mode="reconfig")
