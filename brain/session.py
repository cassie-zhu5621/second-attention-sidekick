"""
session.py — watch all THREE layers of the sidekick's learning run, offline,
on your real cached scores (no API).

  Layer 1  ACTIVE control:   type a sentence  -> weights change -> re-rank
  Layer 2  PASSIVE learning:  type 'keep N' / 'skip N' (react to top pick N)
                              -> it learns from your behaviour, no command given
  Layer 3  LONG-TERM memory:  on exit it saves a per-place taste profile; next
                              run it LOADS it and starts "already knowing you"

RUN (from this folder):
  python3 session.py
Commands while running:
  I love story and people      (Layer 1: explicit)
  keep 1                       (Layer 2: I'd keep top pick #1)
  skip 3                       (Layer 2: not #3)
  <blank line>                 end session (saves long-term memory)
"""
import sys, json, time, os

LR = 0.4
LR_REACT = 0.3
TOPK = 5
PLACE = "lab"

KEYWORDS = {
    "aesthetic": ["beautiful", "pretty", "aesthetic", "gorgeous", "nice shot", "elegant"],
    "conflict": ["clutter", "cluttered", "messy", "chaos", "conflict", "busy"],
    "tension": ["tension", "dramatic", "dynamic", "edge", "intense"],
    "story": ["story", "people", "someone", "together", "social", "conversation", "person"],
    "novelty": ["new", "novel", "unusual", "unexpected", "different", "surprising", "weird"],
    "color_harmony": ["color", "colour", "warm", "golden", "palette", "vivid", "light"],
    "mystery": ["mysterious", "hidden", "intriguing", "curious", "mystery"],
    "decisive_moment": ["moment", "action", "gesture", "caught", "happening", "peak"],
    "frame_within_frame": ["frame", "doorway", "window", "layered", "through"],
}
POS = ["love", "like", "more", "want", "keep", "yes", "good", "nice", "great"]
NEG = ["no", "not", "less", "stop", "ugh", "hate", "don't", "dont", "boring", "skip"]


def load_scores(path):
    d = json.load(open(path))
    dims = sorted({k for v in d.values() if isinstance(v, dict) for k in v})
    items = {f: v for f, v in d.items() if isinstance(v, dict) and all(k in v for k in dims)}
    mx = max(s for v in items.values() for s in v.values())
    if mx > 1.5:
        items = {f: {k: v[k] / 10.0 for k in dims} for f, v in items.items()}
    return items, dims


def parse(u, dims):
    u = u.lower()
    val = -1.0 if any(w in u for w in NEG) else 1.0
    delta = {d: val for d in dims if any(k in u for k in KEYWORDS.get(d, []))}
    return delta


def compose(scores, w, dims):
    return sum(w[d] * scores[d] for d in dims) / (sum(abs(w[d]) for d in dims) or 1.0)


def top(items, w, dims, k=TOPK):
    return sorted(items.items(), key=lambda kv: compose(kv[1], w, dims), reverse=True)[:k]


def show(items, w, dims):
    print(f"  top {TOPK} worth-noticing:")
    for i, (f, sc) in enumerate(top(items, w, dims), 1):
        why = ", ".join(d for _, d in sorted(((w[d] * sc[d], d) for d in dims), reverse=True)[:2])
        print(f"    {i}. {f:42s} ({why})")


def clamp(x):
    return max(-1.0, min(2.0, x))


def main():
    default = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scores_cache.json")
    path = os.path.abspath(os.path.expanduser(sys.argv[1])) if len(sys.argv) > 1 else os.path.abspath(default)
    if not os.path.exists(path):
        print("Could not find the scores file. Looked here:\n  " + path +
              "\n\nFix: pass the path, e.g.\n  python3 session.py ~/Documents/Claude/Projects/Interestingness_Composer/scores_cache.json")
        return
    items, dims = load_scores(path)

    # --- Layer 3: long-term memory — load this place's profile if it exists ---
    profile_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"taste_profile_{PLACE}.json")
    if os.path.exists(profile_path):
        saved = json.load(open(profile_path))
        w = {d: saved.get(d, 1.0) for d in dims}
        print(f"[Layer 3] Loaded what I learned about you last time at '{PLACE}':")
        print("   " + ", ".join(f"{d}={w[d]:.2f}" for d in dims if abs(w[d]-1.0) > 1e-6) + "\n")
    else:
        w = {d: 1.0 for d in dims}
        print(f"[Layer 3] No memory yet for '{PLACE}' — starting from a neutral taste.\n")

    print(f"Loaded {len(items)} views. --- starting taste ---")
    show(items, w, dims)
    print("\nTalk: a sentence (Layer1) | 'keep N' / 'skip N' (Layer2) | blank line = end\n")

    for line in iter(lambda: sys.stdin.readline(), ""):
        line = line.strip()
        if line == "":
            break
        parts = line.split()
        if parts[0].lower() in ("keep", "skip") and len(parts) >= 2 and parts[1].isdigit():
            # --- Layer 2: passive learning from a reaction ---
            idx = int(parts[1]); val = 1.0 if parts[0].lower() == "keep" else -1.0
            picks = top(items, w, dims, k=max(idx, TOPK))
            if 1 <= idx <= len(picks):
                fname, sc = picks[idx - 1]
                strong = sorted(dims, key=lambda d: sc[d], reverse=True)[:2]
                for d in strong:
                    w[d] = clamp(w[d] + LR_REACT * val)
                print(f"you> {line}")
                print(f"  [Layer 2] learned from your reaction to {fname}: "
                      f"{'+' if val>0 else '-'}{', '.join(strong)}")
        else:
            # --- Layer 1: active control from a sentence ---
            delta = parse(line, dims)
            for d, dv in delta.items():
                w[d] = clamp(w[d] + LR * dv)
            print(f"you> {line}")
            print(f"  [Layer 1] {delta or '(no known dimension matched)'}")
        show(items, w, dims)
        print()

    # --- Layer 3: save the updated profile for next time ---
    json.dump(w, open(profile_path, "w"), indent=2)
    print("--- session end ---")
    print("  consolidated taste: " + ", ".join(f"{d}={w[d]:.2f}" for d in dims if abs(w[d]-1.0) > 1e-6))
    print(f"  [Layer 3] saved to {os.path.basename(profile_path)} — next run starts remembering this.")


if __name__ == "__main__":
    main()
