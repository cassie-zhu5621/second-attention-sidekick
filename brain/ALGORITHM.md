# Instruction → taste update: the parsing algorithm (for the supervisor)

How a natural sentence ("I love people and animals") becomes a change to the taste weights.

## Notation

- `u` — the utterance; `T(u)` = its set of lowercased tokens.
- `D = {d₁,…,d_m}` — the named dimensions (story, color_harmony, …).
- `K_d ⊆ V` — keyword set for dimension `d` (e.g. `K_story = {people, together, conversation, …}`).
- `POS, NEG ⊆ V` — sentiment lexicons (`love, more, …` / `not, ugh, less, …`).
- `v ∈ {+1, −1}` — valence (like vs dislike).
- `Δ ∈ ℝ^m` — the per-dimension update.
- `w ∈ ℝ^m` — the taste weights; `α ∈ (0,1]` — learning rate; `clip(x)=max(lo,min(hi,x))`.

**Shared update rule (both algorithms):**  `w ← clip(w + α·Δ)`

---

## Algorithm 1 — Rule-based (lexical) parser  *(what `session.py` runs now)*

```
Input : u ; keyword sets {K_d} ; lexicons POS, NEG
Output: Δ

1.  T ← tokenize(lowercase(u))
2.  v ← −1            if  T ∩ NEG ≠ ∅          # negation wins
        +1            otherwise                # default positive
3.  Δ ← 0^m
4.  for each d ∈ D:
5.      if T ∩ K_d ≠ ∅ :  Δ_d ← v
6.  return Δ
```

### Worked trace — u = "I love people and animals"
```
T = {i, love, people, and, animals}
v = +1                       (love ∈ POS ; T ∩ NEG = ∅)
people ∈ K_story        ⇒    Δ_story = +1
animals ∉ ⋃_d K_d        ⇒    (no dimension)   ← dropped: out-of-vocabulary SUBJECT
Δ = (story:+1, others:0)
update:  w_story ← clip(w_story + α)            (e.g. α = 0.4  →  story weight +0.4)
```
In your shorthand: **`story += α` , `valence = +1` , `animals = unhandled`.**

---

## Algorithm 2 — LLM (model-based) parser  *(`ears.py` LLM mode)*

```
Input : u ; dimension list D (names + 0–1 rubrics)
Output: Δ  (and C = out-of-vocabulary subjects)

1.  p ← PROMPT(u, D)         # "Return JSON {d: s∈{−1,0,+1}} for d∈D.
                             #  Also list any concrete subjects in u NOT in D."
2.  (J, C) ← LLM(p)          # J = structured judgement ; C = e.g. {animals}
3.  Δ ← Π_D(J)               # keep only valid dimensions
4.  return Δ, C
```

Same update `w ← clip(w + α·Δ)`. Unlike Algorithm 1, the LLM (i) handles free phrasing
("not a fan of clutter" → `conflict:−1`) and (ii) **explicitly surfaces** the leftover
subject `C = {animals}`, which hands off to Algorithm 3.

---

## Algorithm 3 — Open-vocabulary subject channel  *(NOT in `session.py` yet; the extension)*

Needed when the user names a **concrete subject** (animals, blue cars, plants) that is
not an abstract dimension. It creates a new scored dimension on the fly.

```
Input : subject phrase c ; images X ; embedder φ (SigLIP)  — OR a VLM judge
Output: a new dimension d_c with a score per image

  # Option A — embedding similarity (cheap, uses your existing SigLIP):
1.  q ← φ_text(c)
2.  for each x ∈ X :  s_{d_c}(x) ← cos( φ_img(x), q )      # "related, not literal"

  # Option B — LLM-as-judge (per image):
2'. for each x ∈ X :  s_{d_c}(x) ← LLM("rate 0–1: contains c ?", x)

3.  D ← D ∪ {d_c} ;  w_{d_c} ← α·v                          # add column, up-weight it
```

So "I love animals" ⇒ build an `animals` score across the images (SigLIP similarity) ⇒
add it as a dimension ⇒ up-weight it ⇒ re-rank.

---

## Your two questions, answered

**Does `session.py` already contain both channels of Step 2?**
No. `session.py` runs **only Algorithm 1** — the *abstract-quality* channel (reweighting
existing dimensions). "people" works only because it is hard-mapped to `K_story`; a true
**subject** like "animals" is dropped (it has no dimension and no open-vocab path).

**Do you need to add Step 3 later?**
Only if you want sentences with **concrete subjects** ("animals", "blue cars") to actually
work. Two honest options to put to the supervisor:
- **VRSJ preliminary:** keep to the abstract-quality dimensions (the 9), and list
  open-vocabulary subjects as *future work*. Cleaner, smaller.
- **Add Algorithm 3 now:** a lightweight **SigLIP-similarity** subject channel — cheap,
  and you already have SigLIP in `layer1.py`. This makes the demo handle real sentences.

Recommended: state the **two-channel taste** (abstract = reweight, subject = open-vocab)
as the design in the paper; implement Algorithm 1 for sure, and Algorithm 3 if time allows.
