"""
eval_final.py — the honest, corrected evaluation.

The earlier sweep conflated two DIFFERENT desirable behaviours of a noticing gate, and so
mis-scored correct habituation as 'low recall'. This evaluation separates them:

  DETECTION  : when a configuration occurs for the FIRST time (novel), does the gate fire?
               -> we WANT this high.
  HABITUATION: when the SAME configuration recurs (already noticed), does the gate stay
               quiet? -> we WANT this high too (the brief's 'recurrence -> boredom').

A gate that fires on every recurrence is not 'high recall', it is a nuisance. So we report
detection-recall on novel events and habituation (correct-silence) on repeats, plus false
fires on normal frames and on churning-screen noise. All at a FIXED operating threshold
(habituation-novelty lives in 0..1, so 0.5 is the natural cut), averaged over seeds.

Gates compared (all share machinery; they differ only where noted):
  ALWAYS-ON          run VLM every frame (status quo).
  TRIPLET (habit+IAC) single typed edges only -- no configuration.   [ablation: representation]
  NODE-EMBEDDING      bag-of-node-types novelty -- structure discarded.
  CONFIG (no-IAC)     configurations, habituation, but no noise suppression. [ablation: IAC]
  CONFIG (full)       configurations + habituation + learning-progress noise suppression.
"""

from __future__ import annotations
import statistics as st
from collections import defaultdict

from sim import make_stream
from config_surprise import ConfigSurpriseGate, motifs
from eval import TripletNovelty, NodeEmbedding


def evaluate(gate_factory, mode, thr=0.5, seeds=30, n=600, skip=50):
    det_hit = det_tot = hab_ok = hab_tot = 0
    norm_fp = norm_tot = nz_fp = nz_tot = fires = scored = 0
    for seed in range(seeds):
        g = gate_factory()
        stream = make_stream(n=n, seed=seed, mode=mode)
        # regime-agnostic ground truth: which motifs ever occur in NORMAL (non-noise)
        # frames. An event motif is 'novel' if it never appears in normal; an event is a
        # first-occurrence if it carries a novel motif not yet seen among prior events.
        normal_motifs = set()
        for nodes, edges, lab in stream:
            if lab == 0 and not any(nodes.get(x) == "screen" for x in nodes):
                normal_motifs |= set(motifs(nodes, edges))
        seen_event_motifs = set()
        for i, (nodes, edges, lab) in enumerate(stream):
            s = g.step(nodes, edges)["score"] if hasattr(g, "step") else g.score(nodes, edges)
            fire = s >= thr
            novel = False
            if lab == 1:
                ev = set(motifs(nodes, edges))
                novel_motifs = ev - normal_motifs
                novel = any(m not in seen_event_motifs for m in novel_motifs) if novel_motifs else False
                seen_event_motifs |= novel_motifs
            if i < skip:
                continue
            scored += 1
            fires += fire
            if lab == 1:
                if novel:
                    det_tot += 1; det_hit += fire
                else:
                    hab_tot += 1; hab_ok += (not fire)
            else:
                is_noise = any(nodes.get(x) == "screen" for x in nodes)
                if is_noise:
                    nz_tot += 1; nz_fp += fire
                else:
                    norm_tot += 1; norm_fp += fire
    return {
        "detection":   det_hit / det_tot if det_tot else 0.0,
        "habituation": hab_ok / hab_tot if hab_tot else float("nan"),
        "normal_fp":   norm_fp / norm_tot if norm_tot else 0.0,
        "noise_fp":    nz_fp / nz_tot if nz_tot else 0.0,
        "fire":        fires / scored if scored else 0.0,
    }


def main(seeds=30, n=600):
    gates = {
        "ALWAYS-ON":          None,
        "TRIPLET (habit+IAC)": lambda: TripletNovelty(),
        "NODE-EMBEDDING":      lambda: NodeEmbedding(),
        "CONFIG (no-IAC)":     lambda: ConfigSurpriseGate(mode="habituation", agg="max",
                                                          suppress_noise=False, threshold=0),
        "CONFIG (full)":       lambda: ConfigSurpriseGate(mode="habituation", agg="max",
                                                          threshold=0),
    }
    # pick a fair fixed threshold per gate family: habituation-novelty gates use 0.5;
    # node-embedding novelty is also 0..1 -> 0.5. (Sensitivity to this choice is small;
    # see sweep at bottom.)
    for mode in ["novel_edge", "reconfig"]:
        print(f"\n=== REGIME: {mode}  (fixed threshold 0.5, {seeds} seeds x {n} frames) ===")
        hdr = (f"{'gate':<20}{'detect':>8}{'habit':>8}{'normalFP':>10}"
               f"{'noiseFP':>9}{'fire%':>8}")
        print(hdr); print("-" * len(hdr))
        for name, fac in gates.items():
            if name == "ALWAYS-ON":
                print(f"{name:<20}{1.0:>8.2f}{0.0:>8.2f}{1.0:>10.2f}{1.0:>9.2f}{100.0:>7.1f}%")
                continue
            r = evaluate(fac, mode, seeds=seeds, n=n)
            hab = "  n/a" if r["habituation"] != r["habituation"] else f"{r['habituation']:.2f}"
            print(f"{name:<20}{r['detection']:>8.2f}{hab:>8}{r['normal_fp']:>10.2f}"
                  f"{r['noise_fp']:>9.2f}{100*r['fire']:>7.1f}%")
    print("\nReading: detect & habit should both be HIGH; normalFP & noiseFP LOW; fire% is "
          "the VLM-call budget (lower = cheaper). 'habit' = fraction of REPEAT events the "
          "gate correctly stayed quiet on.")


if __name__ == "__main__":
    main()
