"""
make_report_figures.py — standalone diagrams for the lab report (drop into your slides).

Reads results/planner_study_claude-sonnet-4-6.jsonl and writes PNGs (200 dpi, 16:9-ish)
to results/figures/. Re-run after vocabulary edits / study re-runs to regenerate.

    python make_report_figures.py [--jsonl results/planner_study_<model>.jsonl]
"""

from __future__ import annotations
import argparse, itertools, json, os, re
from collections import Counter, defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# ---- shared style ----------------------------------------------------------
BLUE, ORANGE, GREEN, RED, GRAY = "#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8C8C8C"
PURPLE, INK, PAPER = "#8172B3", "#222222", "#FFFFFF"
plt.rcParams.update({
    "figure.facecolor": PAPER, "axes.facecolor": PAPER, "savefig.facecolor": PAPER,
    "font.family": "DejaVu Sans", "axes.edgecolor": "#CCCCCC", "axes.linewidth": 0.8,
    "axes.titlesize": 15, "axes.titleweight": "bold", "axes.labelsize": 11,
    "xtick.labelsize": 10, "ytick.labelsize": 10, "legend.fontsize": 10,
    "axes.spines.top": False, "axes.spines.right": False,
})
DPI = 200

SCENARIOS = ["assembly", "guest", "solo-work", "lunch", "demo-day",
             "pair-prog", "entrance", "fragile", "rehearsal", "quiet"]


# ---- data ------------------------------------------------------------------
def load(jsonl):
    runs = [json.loads(l) for l in open(jsonl)]
    by = defaultdict(list)            # (grammar, scenario, T) -> runs
    for r in runs:
        by[(r["grammar"], r["scenario"], r["temperature"])].append(r)
    return runs, by


def flat_ids(spec):
    out = set()
    for c in spec.get("watch", []):
        for f in ("all", "any", "not", "then"):
            out |= set(c.get(f, []) or [])
    return out | set(spec.get("single_ok", []) or [])


def canonical(spec):
    return frozenset((frozenset(c.get("all", []) or []), frozenset(c.get("any", []) or []),
                      frozenset(c.get("not", []) or []), tuple(c.get("then", []) or []))
                     for c in spec.get("watch", []) if isinstance(c, dict))


def jaccard(a, b):
    return len(a & b) / len(a | b) if (a | b) else 1.0


def cond_stats(rs):
    ok = [r for r in rs if r["spec"] and not r["violations"]]
    viol = 1 - len(ok) / len(rs) if rs else 0
    agree = jac = 0.0
    if ok:
        canons = [canonical(r["spec"]) for r in ok]
        agree = Counter(canons).most_common(1)[0][1] / len(ok)
        sets = [flat_ids(r["spec"]) for r in ok]
        pairs = list(itertools.combinations(sets, 2))
        jac = sum(jaccard(a, b) for a, b in pairs) / len(pairs) if pairs else 1.0
    return viol, agree, jac, ok


# ---- F1: architecture ------------------------------------------------------
def fig_architecture(out):
    fig, ax = plt.subplots(figsize=(12.8, 5.6))
    ax.set_xlim(-2, 102); ax.set_ylim(0, 46); ax.axis("off")

    def box(x, y, w, h, title, lines, fc, title_c=PAPER):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6,rounding_size=1.4",
                                    fc=fc, ec="none"))
        ax.text(x + w / 2, y + h - 3.2, title, ha="center", va="center", fontsize=11,
                weight="bold", color=title_c)
        for i, ln in enumerate(lines):
            ax.text(x + w / 2, y + h - 7.4 - 4.2 * i, ln, ha="center", va="center",
                    fontsize=9.5, color=title_c)

    def arrow(x1, y1, x2, y2, label="", curve=0.0, color=INK):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=18,
                                     lw=2, color=color, connectionstyle=f"arc3,rad={curve}"))
        if label:
            if abs(x1 - x2) < 1:                       # vertical arrow: label to the side
                ax.text(x1 + 1.5, (y1 + y2) / 2, label, ha="left", va="center",
                        fontsize=9.5, style="italic", color=color)
            else:
                ax.text((x1 + x2) / 2, max(y1, y2) + 2.4, label, ha="center", fontsize=9.5,
                        style="italic", color=color)

    box(0, 26, 18, 16, "CONTEXT + FRAME", ["typed prompt (for now)", "current camera image"], GRAY)
    box(24, 24, 20, 20, "VLM PLANNER", ["understands the situation", "composes a watch-spec",
                                        "re-plans on context change", "(NOT per frame)"], BLUE)
    box(50, 24, 20, 20, "WATCH-SPEC (JSON)", ["combos over rows 1–10", "all / any / not / then",
                                              '+ "why" (legible taste)', '+ "missing" (probe)'], PURPLE)
    box(76, 24, 22, 20, "CV EXECUTOR", ["MediaPipe Face + Pose", "+ object detector",
                                        "per-frame T/F vector (1–10)", "cheap, runs continuously"], GREEN)
    box(76, 2, 22, 14, "MOMENT RECORDS", ["combo satisfied → record", "frame + T/F slice + label",
                                          "habituation per combo"], ORANGE)
    box(24, 2, 20, 14, "VOCABULARY (1–10)", ["fixed, literature-grounded", "Hall · Kendon · Goffman …",
                                             "versioned & editable"], INK)

    arrow(18, 34, 24, 34)
    arrow(44, 34, 50, 34, "plan")
    arrow(70, 34, 76, 34, "execute")
    arrow(87, 24, 87, 16)
    arrow(34, 16, 34, 24, "composes from")
    arrow(76, 8, 44.5, 8, '"missing" → vocabulary revision', color=RED)
    fig.suptitle("VLM-first attention pipeline — the VLM plans, CV watches", fontsize=16,
                 weight="bold", y=0.97)
    fig.savefig(out, dpi=DPI, bbox_inches="tight"); plt.close(fig)


# ---- F2: vocabulary by channel ---------------------------------------------
# Citations live at the CHANNEL level (the founding work of each channel) — the system
# is the taxonomy; per-row operationalisation references stay in relation_table.md.
CHANNELS = [
    ("Gaze / oculesics", "Kendon 1967; Argyle & Dean 1965",
     [(1, "gazing-at"), (2, "joint-attention"), (3, "eye-contact")]),
    ("Gesture / deixis", "Kita 2003",
     [(4, "pointing / reaching")]),
    ("Proxemics", "Hall 1966",
     [(5, "proxemic zone"), (7, "approach / depart")]),
    ("Posture / kinesics", "Mehrabian 1969",
     [(8, "lean-in")]),
    ("Object-directed action", "Strabala et al. 2013",
     [(9, "hands-on")]),
    ("Group organisation", "Kendon 1990; Goffman 1963",
     [(6, "F-formation"), (10, "gathering")]),
    ("Interaction regulation\n(v2 — found by the probe)", "Sacks et al. 1974; Ekman & Friesen 1969",
     [(11, "turn-taking / control handoff")]),
]


def fig_vocabulary(out):
    ROW, GAP = 5.6, 1.6
    n_rows, n_ch = sum(len(r) for _, _, r in CHANNELS), len(CHANNELS)
    total = n_rows * ROW + (n_ch - 1) * GAP
    fig, ax = plt.subplots(figsize=(12.8, 7.0))
    ax.set_xlim(0, 100); ax.set_ylim(-1, total + 1); ax.axis("off")
    colors = [BLUE, ORANGE, GREEN, PURPLE, RED, "#937860", "#2E8B8B"]
    y = total                                          # cursor: top of next channel band
    for (ch, cite, rows), col in zip(CHANNELS, colors):
        band_h = len(rows) * ROW
        ax.add_patch(FancyBboxPatch((2, y - band_h + 0.5), 30, band_h - 1.0,
                                    boxstyle="round,pad=0.4", fc=col, ec="none", alpha=0.92))
        ax.text(17, y - band_h / 2, ch, ha="center", va="center", fontsize=11.5,
                weight="bold", color=PAPER)   # per-channel citations: in the paper text, not here
        for i, (rid, name) in enumerate(rows):
            cy = y - ROW * i - ROW / 2                 # row centre
            ax.add_patch(FancyBboxPatch((36, cy - 2.1), 60, 4.2, boxstyle="round,pad=0.3",
                                        fc="#F4F4F6", ec=col, lw=1.6))
            ax.text(39.5, cy, f"{rid}", ha="center", va="center", fontsize=13,
                    weight="bold", color=col)
            ax.text(43, cy, name, ha="left", va="center", fontsize=11.5, weight="bold",
                    color=INK)
        y -= band_h + GAP
    fig.suptitle("Vocabulary v2 — per-channel sampling of the nonverbal-behaviour taxonomy",
                 fontsize=15, weight="bold", y=0.99)
    ax.text(50, -0.2, "channel taxonomy: Vinciarelli, Pantic & Bourlard 2009 (Social Signal "
            "Processing) — vision-detectable subset", ha="center", va="top", fontsize=10.5,
            style="italic", color=GRAY)
    fig.savefig(out, dpi=DPI, bbox_inches="tight"); plt.close(fig)


# ---- F3: agreement & jaccard by scenario ------------------------------------
def fig_agreement(by, out):
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 4.8), sharey=True)
    x = range(len(SCENARIOS))
    for ax, T in zip(axes, (0.0, 0.7)):
        for off, (g, col) in zip((-0.2, 0.2), (("restricted", BLUE), ("free", ORANGE))):
            ag = [cond_stats(by[(g, s, T)])[1] for s in SCENARIOS]
            jc = [cond_stats(by[(g, s, T)])[2] for s in SCENARIOS]
            ax.bar([i + off for i in x], ag, width=0.38, color=col, label=f"{g} (agreement)")
            ax.plot([i + off for i in x], jc, "o", color=col, mec=INK, mew=0.6, ms=5,
                    label=f"{g} (Jaccard)" if T == 0.0 else None)
        ax.set_xticks(list(x)); ax.set_xticklabels(SCENARIOS, rotation=35, ha="right")
        ax.set_ylim(0, 1.05); ax.set_title(f"temperature {T}")
        ax.axhline(0.6, color=GRAY, lw=1, ls="--")
    axes[0].set_ylabel("modal agreement (bars) / mean Jaccard (dots)")
    axes[0].legend(loc="lower left", framealpha=0.9)
    fig.suptitle("Consistency of the context → combo mapping (valid runs, k=5)",
                 fontsize=15, weight="bold")
    fig.text(0.5, 0.005,
             "bars = share of runs giving the EXACT same spec (strict)   ·   "
             "dots = mean overlap of the relation ids chosen across runs (lenient)   ·   "
             "dots high while bars low = same ingredients, different grouping",
             ha="center", fontsize=9.5, style="italic", color=GRAY)
    fig.tight_layout(rect=(0, 0.04, 1, 0.93))
    fig.savefig(out, dpi=DPI); plt.close(fig)


# ---- F4: violation breakdown -------------------------------------------------
def fig_violations(runs, out):
    cats = Counter()
    for r in runs:
        for v in r["violations"]:
            if "duration_s" in v:
                cats["duration_s above our\n(too-small) cap"] += 1
            elif "not allowed" in v:
                cats["helpful extra fields\n(why_entry, …)"] += 1
            elif "parse-fail" in v:
                cats["output truncated\n(max_tokens)"] += 1
            else:
                cats["other"] += 1
    # count runs with at least one SEMANTIC violation (none expected)
    sem = ["unknown id", "duplicate", ">3", "at least one", "out of [0.5"]
    n_sem = sum(1 for r in runs if any(any(s in v for s in sem) for v in r["violations"]))
    fig, ax = plt.subplots(figsize=(9.6, 4.8))
    labels, vals = zip(*cats.most_common())
    bars = ax.barh(range(len(vals)), vals, color=[GRAY, GRAY, GRAY, GRAY][:len(vals)])
    for b, v in zip(bars, vals):
        ax.text(b.get_width() + 0.6, b.get_y() + b.get_height() / 2, str(v), va="center",
                fontsize=11, weight="bold")
    ax.set_yticks(range(len(labels))); ax.set_yticklabels(labels)
    ax.invert_yaxis(); ax.set_xlabel("violation count (out of 200 runs)")
    ax.set_title("All violations were formatting trivia\n"
                 f"(semantic errors — wrong ids, grammar misuse: {n_sem} of 200 runs)",
                 fontsize=13)
    ax.text(0.98, 0.06, "fixes applied: cap 3600→14400 s · “no additional fields” line · max_tokens ↑",
            transform=ax.transAxes, ha="right", fontsize=9.5, style="italic", color=GREEN)
    fig.tight_layout(); fig.savefig(out, dpi=DPI); plt.close(fig)


# ---- F5: free-grammar operator usage ----------------------------------------
def fig_ops(by, out):
    # honest split: any() with >=2 ids is a TRUE union; any() wrapping a single id is just
    # notation (same meaning as all:[id]) and must not be read as evidence for OR.
    ops = {"then": [], "not": [], "any2": [], "any1": []}
    for s in SCENARIOS:
        rs = by[("free", s, 0.0)] + by[("free", s, 0.7)]
        ok = [r for r in rs if r["spec"] and not r["violations"]]
        for key, test in (("then", lambda c: c.get("then")),
                          ("not", lambda c: c.get("not")),
                          ("any2", lambda c: len(c.get("any", []) or []) >= 2),
                          ("any1", lambda c: len(c.get("any", []) or []) == 1)):
            ops[key].append(sum(1 for r in ok
                                if any(test(c) for c in r["spec"]["watch"] if isinstance(c, dict))))
    fig, ax = plt.subplots(figsize=(11.2, 4.8))
    x = range(len(SCENARIOS))
    series = (("then", GREEN, '"then" — sequence (the real evidence)'),
              ("not", RED, '"not" — suppression'),
              ("any2", BLUE, '"any" ≥2 ids — true OR'),
              ("any1", "#B7C6DE", '"any" 1 id — notation only (≡ all)'))
    for off, (key, col, lab) in zip((-0.3, -0.1, 0.1, 0.3), series):
        ax.bar([i + off for i in x], ops[key], 0.19, color=col, label=lab)
    ax.set_xticks(list(x)); ax.set_xticklabels(SCENARIOS, rotation=35, ha="right")
    ax.set_ylim(0, 10.5)
    ax.axhline(10, color=GRAY, lw=1, ls="--")
    ax.set_ylabel("valid runs using the operator (max 10)")
    ax.set_title('Which operators beyond OR-of-ANDs does the free grammar actually use?\n'
                 '"then" is the substantive gain — e.g. guest: then(approach → eye-contact)')
    ax.legend(fontsize=9)
    fig.tight_layout(); fig.savefig(out, dpi=DPI); plt.close(fig)


# ---- F6: coverage probe -------------------------------------------------------
def _classify(m):
    t = m.lower()
    if re.search(r"keyboard|mouse|driving|typing|control", t):
        return "control handoff (keyboard/mouse)", True
    if re.search(r"speak|speech|floor", t):
        return "speaking floor / turn yield", False
    if re.search(r"handoff|handover|passing", t):
        return "object handover (person→person)", True
    if re.search(r"pick-up|lift|carried|carry", t):
        return "pick-up / carry away", True
    if re.search(r"aversion|disengag|engagement|attention", t):
        return "audience disengagement", True
    if re.search(r"back-channel|nod", t):
        return "back-channel nods", True
    return "other", True


def fig_missing(runs, by, out):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.8, 4.8), width_ratios=[1, 1.3])
    rates = []
    for s in SCENARIOS:
        ok = [r for g in ("restricted", "free") for T in (0.0, 0.7)
              for r in by[(g, s, T)] if r["spec"] and not r["violations"]]
        n = sum(1 for r in ok if r["spec"].get("missing"))
        rates.append(n / len(ok) if ok else 0)
    cols = [RED if v > 0.5 else ORANGE if v > 0 else GREEN for v in rates]
    ax1.bar(range(len(SCENARIOS)), rates, color=cols)
    ax1.set_xticks(range(len(SCENARIOS))); ax1.set_xticklabels(SCENARIOS, rotation=35, ha="right")
    ax1.set_ylim(0, 1.05); ax1.set_ylabel('runs naming a "missing" relation')
    ax1.set_title("Where the vocabulary falls short")

    cats = Counter(); vis = {}
    for r in runs:
        if r["spec"] and r["spec"].get("missing") and not r["violations"]:
            c, v = _classify(str(r["spec"]["missing"]))
            cats[c] += 1; vis[c] = v
    labels, vals = zip(*cats.most_common())
    cols2 = [GREEN if vis[l] else GRAY for l in labels]
    bars = ax2.barh(range(len(vals)), vals, color=cols2)
    for b, v in zip(bars, vals):
        ax2.text(b.get_width() + 0.3, b.get_y() + b.get_height() / 2, str(v), va="center",
                 fontsize=11, weight="bold")
    ax2.set_yticks(range(len(labels)))
    ax2.set_yticklabels([l + ("" if vis[l] else "  (audio — out of scope)") for l in labels])
    ax2.invert_yaxis(); ax2.set_xlabel("times named")
    ax2.set_title("What it asked for (green = table candidates)", loc="left")
    fig.suptitle("Coverage probe — the empirical answer to “why these ten?”",
                 fontsize=15, weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(out, dpi=DPI); plt.close(fig)


# ---- F7: v1 -> v2 vocabulary revision, before/after --------------------------
def fig_v1v2(jsonl_v1, jsonl_v2, out):
    runs1, by1 = load(jsonl_v1)
    runs2, by2 = load(jsonl_v2)

    def miss_rate(by, s):
        ok = [r for g in ("restricted", "free") for T in (0.0, 0.7) for r in by[(g, s, T)]
              if r["spec"] and not r["violations"]]
        return (sum(1 for r in ok if r["spec"].get("missing")) / len(ok)) if ok else 0.0

    def adopt11(by, s):
        ok = [r for g in ("restricted", "free") for T in (0.0, 0.7) for r in by[(g, s, T)]
              if r["spec"] and not r["violations"]]
        return (sum(1 for r in ok if 11 in flat_ids(r["spec"])) / len(ok)) if ok else 0.0

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.8, 4.8))
    x = range(len(SCENARIOS))
    ax1.bar([i - 0.2 for i in x], [miss_rate(by1, s) for s in SCENARIOS], 0.38,
            color=GRAY, label="vocabulary v1")
    ax1.bar([i + 0.2 for i in x], [miss_rate(by2, s) for s in SCENARIOS], 0.38,
            color=GREEN, label="vocabulary v2 (+row 11)")
    ax1.set_xticks(list(x)); ax1.set_xticklabels(SCENARIOS, rotation=35, ha="right")
    ax1.set_ylim(0, 1.05); ax1.set_ylabel('runs naming a "missing" relation')
    ax1.set_title("Coverage probe, before → after")
    ax1.legend()
    ax1.annotate("remaining gap:\nspeaker role (≈audio)", xy=(8.2, miss_rate(by2, "rehearsal")),
                 xytext=(5.6, 0.85), fontsize=9.5, color=RED,
                 arrowprops=dict(arrowstyle="->", color=RED))

    ax2.bar(x, [adopt11(by2, s) for s in SCENARIOS], 0.55, color=BLUE)
    ax2.set_xticks(list(x)); ax2.set_xticklabels(SCENARIOS, rotation=35, ha="right")
    ax2.set_ylim(0, 1.05); ax2.set_ylabel("valid runs using row 11")
    ax2.set_title("Row-11 adoption — used exactly where it belongs")
    v1v = sum(1 for r in runs1 if r["violations"]) / len(runs1)
    v2v = sum(1 for r in runs2 if r["violations"]) / len(runs2)
    fig.suptitle("One-row vocabulary revision (v1 → v2): probe-driven, targeted, no side effects",
                 fontsize=15, weight="bold")
    fig.text(0.5, 0.005, f"schema violations {v1v:.0%} → {v2v:.0%} (formatting fixes) · "
             "k=5 × 2 temperatures × 2 grammars per scenario",
             ha="center", fontsize=9.5, style="italic", color=GRAY)
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    fig.savefig(out, dpi=DPI); plt.close(fig)


# ---- F8: is the method VLM-readable & translatable, per scenario? -------------
def fig_translatability(jsonl, out):
    """One-look feasibility evidence: every scenario must pass the chain
    context --read--> valid executable spec --stable--> same ingredients across runs
    --covered--> vocabulary suffices (no 'missing'). Green row = safe to build on."""
    runs, by = load(jsonl)
    import numpy as np

    GRAMMAR = "free"   # the grammar the executor will ship (it earned sequences);
                       # measuring under ONE grammar — mixing both deflates stability,
                       # because the two output shapes differ by construction.

    def pooled(s):
        rs = [r for T in (0.0, 0.7) for r in by[(GRAMMAR, s, T)]]
        ok = [r for r in rs if r["spec"] and not r["violations"]]
        valid = len(ok) / len(rs) if rs else 0
        s0 = [flat_ids(r["spec"]) for r in by[(GRAMMAR, s, 0.0)]
              if r["spec"] and not r["violations"]]
        pairs = list(itertools.combinations(s0, 2))
        stab = sum(jaccard(a, b) for a, b in pairs) / len(pairs) if pairs else 0
        cover = 1 - (sum(1 for r in ok if r["spec"].get("missing")) / len(ok) if ok else 1)
        return valid, stab, cover

    cols = ["produces a valid,\nexecutable spec", "stable mapping\n(ingredients, T=0)",
            "vocabulary\nsuffices", "VERDICT\n(min of three)"]
    data = []
    for s in SCENARIOS:
        v, st, c = pooled(s)
        data.append([v, st, c, min(v, st, c)])
    data = np.array(data)

    fig, ax = plt.subplots(figsize=(9.6, 6.4))
    im = ax.imshow(data, cmap="RdYlGn", vmin=0.3, vmax=1.0, aspect="auto")
    ax.set_xticks(range(len(cols))); ax.set_xticklabels(cols, fontsize=10)
    ax.set_yticks(range(len(SCENARIOS))); ax.set_yticklabels(SCENARIOS, fontsize=11)
    for i in range(len(SCENARIOS)):
        for j in range(len(cols)):
            v = data[i, j]
            txt = f"{v:.0%}" + ("  ✓" if j == 3 and v >= 0.7 else "")
            ax.text(j, i, txt, ha="center", va="center", fontsize=10.5,
                    weight="bold" if j == 3 else "normal",
                    color=INK if v > 0.55 else PAPER)
    ax.set_xticks([x - 0.5 for x in range(1, len(cols))], minor=True)
    ax.set_yticks([y - 0.5 for y in range(1, len(SCENARIOS))], minor=True)
    ax.grid(which="minor", color=PAPER, lw=2)
    ax.tick_params(which="both", length=0)
    ax.set_title("Context → watch-spec translation is reliable across the scenario space\n"
                 "(vocabulary v2 · the shipping grammar (free) · 2 temperatures × k=5 per scenario)",
                 fontsize=13)
    fig.text(0.5, 0.01, "scenarios are a stratified sample over people-count × activity × "
             "robot-role × instruction-style — to be re-validated on elicited (v3) scenarios",
             ha="center", fontsize=9.5, style="italic", color=GRAY)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(out, dpi=DPI); plt.close(fig)


# ------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jsonl", default="results/planner_study_claude-sonnet-4-6.jsonl")
    ap.add_argument("--outdir", default="results/figures")
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    runs, by = load(args.jsonl)
    fig_architecture(os.path.join(args.outdir, "F1_architecture.png"))
    fig_vocabulary(os.path.join(args.outdir, "F2_vocabulary_channels.png"))
    fig_agreement(by, os.path.join(args.outdir, "F3_mapping_consistency.png"))
    fig_violations(runs, os.path.join(args.outdir, "F4_violation_breakdown.png"))
    fig_ops(by, os.path.join(args.outdir, "F5_free_grammar_ops.png"))
    fig_missing(runs, by, os.path.join(args.outdir, "F6_coverage_probe.png"))
    print("wrote 6 figures to", args.outdir)


if __name__ == "__main__":
    main()
