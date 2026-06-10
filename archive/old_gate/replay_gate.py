"""
replay_gate.py — OFFLINE gate test on a whole session.

Feed a `graphs.json` (produced by run_perception.py) as a TIME SEQUENCE through the gate,
and see which frames the system would FIRE on (a new configuration = an event worth the VLM)
vs which it HABITUATES to (already-seen / unchanged). No detector and no API key needed —
perception was already done once; this replays it cheaply so you can test and tune the gate.

    python replay_gate.py --graphs /path/to/_perception/graphs.json
    python replay_gate.py --graphs ... --threshold 0.6 --show-fires-only

This is how you answer "does the noticing actually work on my data?": on the overnight→morning
set you should see the night habituate to near-silence and the first morning activity fire.
"""

from __future__ import annotations
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from config_surprise import ConfigSurpriseGate, TemporalConfigGate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--graphs", required=True, help="graphs.json from run_perception.py")
    ap.add_argument("--threshold", type=float, default=0.5, help="higher = fewer fires")
    ap.add_argument("--show-fires-only", action="store_true")
    args = ap.parse_args()

    data = json.load(open(args.graphs))
    gate = TemporalConfigGate(gate=ConfigSurpriseGate(mode="habituation", agg="max",
                                                      threshold=args.threshold))
    print(f"{len(data)} frames | threshold={args.threshold}\n")
    fires = 0
    for i, rec in enumerate(data):
        nodes = rec["nodes"]
        edges = [tuple(e) for e in rec["edges"]]          # json gives lists -> back to tuples
        d = gate.step(nodes, edges)
        if d["event"]:
            fires += 1
            print(f"  [{i:4d}] FIRE  {rec['file']}  score={d['score']:.2f}")
            print(f"          {TemporalConfigGate.describe(d['delta_added'], d['top'])}")
        elif not args.show_fires_only:
            print(f"  [{i:4d}]  --   {rec['file']}")

    n = max(len(data), 1)
    print(f"\n{fires}/{len(data)} frames fired ({100*fires/n:.1f}%) — that's the VLM-call budget; "
          f"the rest habituated.")
    print("Tune --threshold: higher = fewer fires (more habituation), lower = more sensitive.")


if __name__ == "__main__":
    main()
