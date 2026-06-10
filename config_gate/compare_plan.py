"""
compare_plan.py — the LLM-vs-VLM planner ablation, one command:
same context, planned twice — text-only vs text+frame — print both specs side by side.

    python compare_plan.py --image scenes/roundtable.jpg \
        --context "this is our roundtable space for running regular meetings."

Appends both raw results to results/plan_ablation.jsonl (paper data).
"""

from __future__ import annotations
import argparse, json, os, time

from planner import plan, VOCAB, MODEL


def fmt(spec):
    if not spec:
        return ["(no spec)"]
    lines = []
    for c in spec.get("watch", []) or []:
        bits = []
        if c.get("all"):  bits.append("+".join(map(str, c["all"])))
        if c.get("any"):  bits.append("any(" + ",".join(map(str, c["any"])) + ")")
        if c.get("then"): bits.append("then(" + "→".join(map(str, c["then"])) + ")")
        if c.get("not"):  bits.append("not(" + ",".join(map(str, c["not"])) + ")")
        lines.append(f"  watch {' '.join(bits):24s} ({c.get('label','')})")
    if spec.get("single_ok"):
        lines.append(f"  single_ok: {sorted(spec['single_ok'])}")
    lines.append(f"  why: {spec.get('why','')}")
    if spec.get("missing"):
        lines.append(f"  MISSING: {spec['missing']}")
    return lines


def ids_of(spec):
    out = set()
    for c in (spec or {}).get("watch", []) or []:
        for f in ("all", "any", "not", "then"):
            out |= set(c.get(f, []) or [])
    return out | set((spec or {}).get("single_ok", []) or [])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--context", required=True)
    ap.add_argument("--image", required=True)
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--grammar", default="free")
    ap.add_argument("--outdir", default="results")
    args = ap.parse_args()
    jpeg = open(args.image, "rb").read()

    print(f"context: {args.context}\nmodel: {args.model}\n")
    results = {}
    for arm, img in (("TEXT-ONLY (LLM)", None), ("TEXT+FRAME (VLM)", jpeg)):
        r = plan(args.context, jpeg=img, model=args.model, grammar=args.grammar)
        results[arm] = r
        print(f"--- {arm} ---")
        if r["violations"]:
            print(f"  violations: {r['violations']}")
        for ln in fmt(r["spec"]):
            print(ln)
        print()

    a, b = (ids_of(results[k]["spec"]) for k in results)
    print(f"relation ids — text-only: {sorted(a)}   text+frame: {sorted(b)}")
    print(f"added by the frame: {sorted(b - a) or '—'}   dropped: {sorted(a - b) or '—'}")
    print("\nread the two 'why' lines: does the frame arm reference what is actually "
          "in the image (people count, screen, seating)? That reference is the V at work.")

    os.makedirs(args.outdir, exist_ok=True)
    with open(os.path.join(args.outdir, "plan_ablation.jsonl"), "a") as fh:
        for arm, r in results.items():
            fh.write(json.dumps({"t": time.strftime("%F %T"), "arm": arm,
                                 "context": args.context, "image": args.image,
                                 "model": args.model, "grammar": args.grammar,
                                 "spec": r["spec"], "violations": r["violations"]}) + "\n")
    print(f"\nappended both runs to {args.outdir}/plan_ablation.jsonl")


if __name__ == "__main__":
    main()
