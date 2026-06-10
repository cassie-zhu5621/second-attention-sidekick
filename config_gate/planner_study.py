"""
planner_study.py — PRELIMINARY STUDY: can the VLM reliably map a context onto relation
conjunctions from the fixed vocabulary? (Run this BEFORE building the live planner loop.)

Design
  - 10 context scenarios (typed prompts, the way a user would give them). NOT an ad-hoc
    list: a stratified sample over a 4-dimensional scenario design space, every level of
    every dimension covered (dimensions consistent with situation taxonomies, e.g.
    Rauthmann et al. 2014 "DIAMONDS" — Duty/Sociality — and time-use activity classes):
      * people present      0-1 (solo, entrance) / 2 (assembly, pair-prog) /
                            group (lunch, demo-day, rehearsal)
      * activity type       focused (solo) / collaborative (assembly, pair-prog) /
                            social (lunch, demo-day) / transit-waiting (guest, entrance) /
                            idle (quiet)
      * robot's role        watch people (guest) / watch an object (fragile) /
                            watch a place (entrance) / minimise noise (solo, quiet)
      * instruction style   precise ("watch the entrance") <-> open ("nothing much
                            should happen")
    The set is provisional by design: it will be replaced by ecologically valid prompts
    (an elicitation round with lab members; later, real typed contexts from deployment),
    and the study re-run on those.
  - For each scenario: k runs at temperature 0.0 (determinism check) and k at 0.7
    (robustness check). Context-only (no frame): this isolates the context->combo mapping,
    which is the capability in question; frame-conditioning is a later study.
  - Measures, per scenario x temperature:
      * schema violation rate     (is the output executable at all?)
      * modal agreement           (share of runs whose combo-set equals the most common one)
      * mean pairwise Jaccard     (graded overlap of selected relation ids across runs)
      * the modal spec itself     (for the face-validity pass — a human reads these)
  - Face validity is human work: the summary table prints each scenario's modal combos
    with labels/why; you (and the supervisor) judge whether they are sensible.

Run
    python planner_study.py --offline             # plumbing check, no API key
    export ANTHROPIC_API_KEY=sk-...
    python planner_study.py                       # default: k=5, haiku
    python planner_study.py --model claude-sonnet-4-6 --k 5
Outputs
    results/planner_study_<model>.jsonl           # every raw run
    results/planner_study_<model>.md              # the summary table (paper-ready draft)
"""

from __future__ import annotations
import argparse, itertools, json, os, time
from collections import Counter

from planner import plan, validate, canonical, ops_used, VOCAB, VOCAB_VERSION, MODEL

SCENARIOS = {
    "assembly":   "Two of us are assembling a robot arm at the workbench this afternoon.",
    "guest":      "I'm expecting a guest to arrive at the studio within the next hour.",
    "solo-work":  "I'm working alone on my thesis. Only people matter; ignore objects.",
    "lunch":      "It's lunch break; people drift in and out and chat around the table.",
    "demo-day":   "Open-lab demo day: visitors walk around and look at the exhibits.",
    "pair-prog":  "My labmate and I are pair-programming at one screen.",
    "entrance":   "Watch the entrance and tell me when someone comes in.",
    "fragile":    "I left a fragile prototype on the desk; I care about anyone handling it.",
    "rehearsal":  "We're rehearsing a presentation: one person presents, the others listen.",
    "quiet":      "A quiet reading corner in the evening; nothing much should happen.",
}


def jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if (a | b) else 1.0


def flat_ids(spec) -> set:
    out = set()
    for c in spec.get("watch", []):
        for f in ("all", "any", "not", "then"):
            out |= set(c.get(f, []) or [])
    return out | set(spec.get("single_ok", []) or [])


def fmt_entry(c) -> str:
    bits = []
    if c.get("all"):
        bits.append("+".join(map(str, sorted(c["all"]))))
    if c.get("any"):
        bits.append("any(" + ",".join(map(str, sorted(c["any"]))) + ")")
    if c.get("then"):
        bits.append("then(" + "→".join(map(str, c["then"])) + ")")
    if c.get("not"):
        bits.append("not(" + ",".join(map(str, sorted(c["not"]))) + ")")
    return " ".join(bits) + f" ({c.get('label', '')})"


def fmt_combos(spec) -> str:
    parts = [fmt_entry(c) for c in spec.get("watch", [])]
    if spec.get("single_ok"):
        parts.append("single: " + ",".join(map(str, sorted(spec["single_ok"]))))
    return "; ".join(parts)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--k", type=int, default=5, help="runs per scenario per temperature")
    ap.add_argument("--temps", default="0.0,0.7")
    ap.add_argument("--grammars", default="restricted,free",
                    help="study arms: restricted (OR-of-ANDs) vs free (all/any/not/then)")
    ap.add_argument("--scenarios", default=None,
                    help="comma-separated subset for targeted re-runs (e.g. 'guest'); "
                         "writes *_partial files so the full results are never overwritten")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--outdir", default="results")
    args = ap.parse_args()
    if args.offline:
        os.environ["SECONDATTN_OFFLINE"] = "1"
    temps = [float(t) for t in args.temps.split(",")]
    grammars = [g.strip() for g in args.grammars.split(",")]
    os.makedirs(args.outdir, exist_ok=True)
    scenarios = SCENARIOS
    if args.scenarios:
        keep = {s.strip() for s in args.scenarios.split(",")}
        scenarios = {k: v for k, v in SCENARIOS.items() if k in keep}
    tag = (args.model.replace("/", "_") + f"_vocab-{VOCAB_VERSION}"
           + ("_partial" if args.scenarios else "")
           + ("_offline" if args.offline else ""))
    raw_path = os.path.join(args.outdir, f"planner_study_{tag}.jsonl")
    md_path = os.path.join(args.outdir, f"planner_study_{tag}.md")

    rows, missing_seen = [], Counter()
    with open(raw_path, "w") as raw:
        for g in grammars:
            for name, ctx in scenarios.items():
                for T in temps:
                    runs = []
                    for k in range(args.k):
                        r = plan(ctx, model=args.model, temperature=T, grammar=g)
                        r.update(scenario=name, temperature=T, run=k)
                        raw.write(json.dumps(r) + "\n"); raw.flush()
                        runs.append(r)
                        print(f"[{g}|{name}|T={T}|run{k}] "
                              f"{'VIOL:' + ';'.join(r['violations']) if r['violations'] else fmt_combos(r['spec'])}")
                        time.sleep(0.2)
                    ok = [r for r in runs if r["spec"] and not r["violations"]]
                    viol_rate = 1 - len(ok) / len(runs)
                    canons = [canonical(r["spec"]) for r in ok]
                    modal, modal_n = (Counter(canons).most_common(1) + [(None, 0)])[0]
                    agree = modal_n / len(ok) if ok else 0.0
                    sets = [flat_ids(r["spec"]) for r in ok]
                    jac = (sum(jaccard(a, b) for a, b in itertools.combinations(sets, 2))
                           / max(1, len(sets) * (len(sets) - 1) // 2)) if len(sets) > 1 else 1.0
                    modal_spec = next((r["spec"] for r in ok if canonical(r["spec"]) == modal), None)
                    ops = Counter()
                    for r in ok:
                        for o in ops_used(r["spec"]):
                            ops[o] += 1
                    n_missing = 0
                    for r in ok:
                        m = r["spec"].get("missing")
                        if m:
                            n_missing += 1
                            missing_seen[str(m)[:80]] += 1
                    rows.append({"grammar": g, "scenario": name, "T": T, "viol": viol_rate,
                                 "agree": agree, "jaccard": jac,
                                 "ops": ",".join(f"{o}:{n}" for o, n in sorted(ops.items())) or "—",
                                 "missing": f"{n_missing}/{len(ok)}" if ok else "—",
                                 "modal": fmt_combos(modal_spec) if modal_spec else "—",
                                 "why": (modal_spec or {}).get("why", "")})

    with open(md_path, "w") as md:
        md.write(f"# Planner preliminary study — {args.model}"
                 f"{' (OFFLINE PLUMBING RUN — numbers meaningless)' if args.offline else ''}\n\n"
                 f"k={args.k} runs per scenario per temperature per grammar; context-only "
                 f"(no frame). Grammar arms: {', '.join(grammars)}.\n\n"
                 "| grammar | scenario | T | viol. | agree | Jaccard | ops beyond AND | missing | modal entries | why (modal) |\n"
                 "|---|---|---|---|---|---|---|---|---|---|\n")
        for r in rows:
            md.write(f"| {r['grammar']} | {r['scenario']} | {r['T']} | {r['viol']:.0%} "
                     f"| {r['agree']:.0%} | {r['jaccard']:.2f} | {r['ops']} | {r['missing']} "
                     f"| {r['modal']} | {r['why'][:70]} |\n")
        md.write("\n## Coverage probe — 'missing' relations named by the model\n\n")
        if missing_seen:
            for m, n in missing_seen.most_common():
                md.write(f"- ({n}×) {m}\n")
            md.write("\nThese are empirical vocabulary gaps: candidates for table edits.\n")
        else:
            md.write("None named — empirical support that the 10-row vocabulary covers "
                     "these scenarios.\n")
        md.write("\n## Reading guide\n"
                 "- **viol.** > 0 at T=0 ⇒ tighten schema wording in planner.py.\n"
                 "- **agree** low at T=0 ⇒ the context→combo mapping itself is unstable: the "
                 "vocabulary descriptions are ambiguous for that scenario.\n"
                 "- **Jaccard high while agree low** ⇒ same relations, different groupings "
                 "(less worrying).\n"
                 "- **Grammar decision**: if the free arm rarely uses any/not/then (ops column) "
                 "or uses them without face-valid need, ship the restricted grammar and cite "
                 "these runs as the justification; if 'then' appears often and sensibly, the "
                 "executor gains sequences.\n"
                 "- **Face validity** is human work: read modal entries against each scenario "
                 "with the supervisor; disagreements drive table edits.\n\n"
                 f"Vocabulary used (planner.py VOCAB):\n\n"
                 + "\n".join(f"- {i}. {d}" for i, d in VOCAB.items()) + "\n")
    print(f"\nwrote {raw_path}\nwrote {md_path}")


if __name__ == "__main__":
    main()
