"""
taste.py — the sidekick's noticing intelligence: dimensions + weighted combine + adaptation.

Dimensions are theory-anchored (see SecondAttention_intelligence_spec.md):
  - Berlyne collative variables (primary anchor): novelty, complexity, conflict, surprise
  - Kaplan & Kaplan environmental preference (spatial layer): coherence, mystery
  - Photographic craft (craft layer): aesthetic, decisive_moment
  - Narrative: story_potential
This set is a starting point — validate/prune on data later (do NOT treat as canonical).
"""

# name -> (group, 0..1 grading rubric shown to the VLM)
DIMENSIONS = {
    # --- Berlyne collative variables (primary anchor) ---
    "novelty":        ("berlyne", "How novel/unusual is this — does it depart from what's expected for this kind of scene? 0 = utterly ordinary, 1 = strikingly unusual."),
    "complexity":     ("berlyne", "How visually rich/complex is it — many elements, textures, layers? 0 = bare/empty, 1 = densely rich."),
    "conflict":       ("berlyne", "Is there conflict/contrast/competing elements (opposing directions, light vs dark, tension between subjects)? 0 = none, 1 = strong."),
    "surprise":       ("berlyne", "How surprising/incongruous is the moment — something unexpected happening? 0 = predictable, 1 = very surprising."),
    # --- Kaplan & Kaplan environmental preference (spatial layer) ---
    "coherence":      ("kaplan",  "How coherent/legible is the scene as a whole — does it read clearly as an organized space? 0 = chaotic, 1 = very coherent."),
    "mystery":        ("kaplan",  "Mystery: does the scene promise more if you moved into it (a partly hidden view, a path, something around a corner)? 0 = all revealed, 1 = strong promise."),
    # --- Photographic craft (craft layer) ---
    "aesthetic":      ("craft",   "Overall aesthetic/technical quality (light, balance, composition). 0 = poor, 1 = beautiful."),
    "decisive_moment":("craft",   "Is this a peak/decisive instant — gesture, expression, action caught at its height? 0 = nothing happening, 1 = perfect instant."),
    # --- Narrative ---
    "story_potential":("story",   "Story potential: does it imply a narrative, relationship, or 'something is going on'? 0 = none, 1 = rich story."),
}

DIM_NAMES = list(DIMENSIONS.keys())


def default_weights() -> dict:
    """Equal-weight baseline taste."""
    return {d: 1.0 for d in DIM_NAMES}


def compose(scores: dict, weights: dict) -> float:
    """worth_noticing = weighted mean of dimension scores. The core 'codify a moment'."""
    num = sum(weights.get(d, 0.0) * scores.get(d, 0.0) for d in DIM_NAMES)
    den = sum(abs(weights.get(d, 0.0)) for d in DIM_NAMES) or 1.0
    return num / den


def up_weight(weights: dict, names, amount: float = 1.0) -> dict:
    """Personalize by emphasizing named dimensions ('I care about story and color')."""
    w = dict(weights)
    for n in names:
        if n in w:
            w[n] = w[n] + amount
    return w


def ema_update(weights: dict, delta: dict, lr: float = 0.3,
               lo: float = -1.0, hi: float = 2.0) -> dict:
    """Passive online update from a parsed conversational delta:
        w <- clip(w + lr * delta)
    delta is a partial dict {dim: change}. Clipped to keep weights in range."""
    w = dict(weights)
    for d, dv in delta.items():
        if d in w:
            w[d] = max(lo, min(hi, w[d] + lr * dv))
    return w


if __name__ == "__main__":
    # tiny self-test (no dependencies)
    s = {d: 0.5 for d in DIM_NAMES}
    s["story_potential"] = 0.9
    w0 = default_weights()
    w1 = up_weight(w0, ["story_potential", "aesthetic"], 1.5)
    print("equal   :", round(compose(s, w0), 3))
    print("personal:", round(compose(s, w1), 3), "(should be higher — story is high & up-weighted)")
    w2 = ema_update(w1, {"conflict": +1.0, "complexity": -1.0})
    print("after talk-delta conflict+ complexity- :", {k: round(v,2) for k,v in w2.items()})
