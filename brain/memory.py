"""
memory.py — two-timescale memory (see SecondAttention_intelligence_spec.md §6).

  WorkingTaste  : short-term EMA weight vector, nudged live by conversation (the session).
  signal log    : every conversational preference signal appended with context (jsonl).
  consolidate   : fold the logged signals into a stable long-term profile (recency-weighted).
  snapshots     : per-place profiles, so it warm-starts "knowing you" for that spot.
  semantic log  : notable verbatim utterances, so it can later explain itself.

No API, no deps beyond stdlib.
"""
import os, json, time
import taste


class WorkingTaste:
    """The current, fast-adapting taste for one session."""
    def __init__(self, weights=None):
        self.w = dict(weights) if weights else taste.default_weights()

    def apply(self, delta, lr=0.3):
        self.w = taste.ema_update(self.w, delta, lr=lr)
        return self.w


def log_signal(store, utterance, delta, valence, place="lab", target=None):
    """Append one conversational preference signal with context."""
    os.makedirs(os.path.dirname(store) or ".", exist_ok=True)
    rec = {"t": time.time(), "place": place, "utterance": utterance,
           "delta": delta, "valence": valence, "target": target}
    with open(store, "a") as f:
        f.write(json.dumps(rec) + "\n")
    return rec


def consolidate(store, place=None, half_life_days=14.0):
    """Fold logged signals into a stable long-term profile (recency-weighted average
    of deltas, added onto the equal-weight base). Optionally filter by place."""
    base = taste.default_weights()
    if not os.path.exists(store):
        return base
    now = time.time(); lam = 0.6931 / (half_life_days * 86400)  # ln2 / half-life
    acc = {d: 0.0 for d in taste.DIM_NAMES}; wsum = 0.0
    for line in open(store):
        rec = json.loads(line)
        if place and rec.get("place") != place:
            continue
        recency = pow(2.718281828, -lam * (now - rec["t"]))
        wsum += recency
        for d, dv in rec.get("delta", {}).items():
            if d in acc:
                acc[d] += recency * dv
    if wsum > 0:
        for d in base:
            base[d] = max(-1.0, min(2.0, base[d] + 0.3 * acc[d] / wsum))
    return base


def save_snapshot(path, place, weights):
    snaps = json.load(open(path)) if os.path.exists(path) else {}
    snaps[place] = weights
    json.dump(snaps, open(path, "w"), indent=2)


def load_snapshot(path, place):
    if os.path.exists(path):
        snaps = json.load(open(path))
        if place in snaps:
            return snaps[place]
    return taste.default_weights()


if __name__ == "__main__":
    # demo: a session's worth of talk -> logged -> consolidated profile -> snapshot
    store = "/tmp/sa_signals.jsonl"
    if os.path.exists(store): os.remove(store)
    wt = WorkingTaste()
    convo = [
        ("I love when people are working together", {"story_potential": +1}, +1),
        ("more of that warm light by the window", {"color_harmony": +1, "aesthetic": +1}, +1),
        ("ugh, not the cluttered desk again", {"conflict": -1}, -1),
    ]
    for utt, delta, val in convo:
        wt.apply(delta); log_signal(store, utt, delta, val, place="lab_shared")
    print("working taste after session:", {k: round(v,2) for k,v in wt.w.items() if abs(v-1)>1e-6})
    prof = consolidate(store, place="lab_shared")
    print("consolidated long-term profile:", {k: round(v,2) for k,v in prof.items() if abs(v-1)>1e-6})
    save_snapshot("/tmp/sa_snapshots.json", "lab_shared", prof)
    print("snapshot saved; next session warm-starts from this for 'lab_shared'.")
