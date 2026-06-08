# Configuration-Surprise Gate — references checked, prototype built, tested

*June 2026. Companion to `concept_brief_relational_surprise.md`. Code in this folder:
`config_surprise.py` (the gate), `sim.py` (synthetic scene-graph stream), `eval.py` /
`eval_final.py` (comparisons).*

## 1. References — all check out

Every citation in the brief is real and described accurately:

- **Itti & Baldi, *Bayesian Surprise Attracts Human Attention*, Vision Research 2009** — correct; surprise as KL(posterior‖prior), "strongest known attractor of attention." ✓
- **Cheng et al., *YOLO-World*, CVPR 2024** (arXiv:2401.17270) — correct venue/authors. ✓
- **Oudeyer, Kaplan, Hafner, *Intrinsic Motivation Systems* / IAC, IEEE TEC 2007** — correct; learning-progress maximisation, "neither too predictable nor too unpredictable." ✓
- **Hughes, Chang, Carlone, *Hydra*, RSS 2022** (arXiv:2201.13360) — correct. (Brief says "Hughes et al." — right; Armeni et al. is the separate *3D Scene Graph* line, also real.) ✓
- **From Pixels to Graphs**, arXiv:2404.00906, CVPR 2024 — correct; open-vocab scene-graph generation with VLMs. ✓
- **Bu, …, Ju, *VLMs as Proxies for Social Intelligence in HRI*, arXiv:2512.07177** — correct; the two-stage "cheap detector → VLM" pipeline you position against. ✓
- **Weng, *Learning Beyond Gradients* (blog, 2026)** — flagged in the brief itself as personal/un-reviewed; treat as motivation, not evidence. Correct framing.

Nothing was mis-cited. One framing note: the brief leans on Itti–Baldi *Bayesian* surprise, but the version of the gate that actually works uses a simpler **habituation-recency** novelty (below) — the Bayesian-KL variant underperformed in testing.

## 2. What I built

A standalone, dependency-free gate (`ConfigSurpriseGate`) implementing the brief's cascade
step 3. A scene graph → a **bag of typed motifs**: single edges, length-2 paths
`A–r1–B–r2–C`, and — the piece that makes "configuration" real — **co-occurrence motifs**
(two familiar edges sharing a node). Node identities are abstracted to types, so "a
different person typing" is the same motif (the brief's combinatorial-explosion fix #1).

Three design choices mattered, and each was forced by a failed test, not chosen up front:

1. **Habituation-recency, not −log p.** Raw self-information conflates *rare* with *novel*:
   a rare-but-normal layout (an occasional stretch) scored as high as a real event. The fix
   is `nov(m) = exp(−count(m))` over decaying counts — it measures *have I seen this*, not
   *how probable is this*. A rare config that nonetheless recurs habituates to ~0; a
   never-seen combination stays at 1. This is the brief's "recurrence → boredom," done right.
2. **Aggregate by MAX, not mean.** A configuration is surprising if it contains *any*
   improbable substructure. Averaging buried the one novel co-occurrence under ~15 familiar
   motifs (this is why the first reconfig test failed).
3. **Noise suppression = learning-progress, not diversity.** My first noise filter measured
   per-source *diversity* and wrongly silenced the **person** — who is legitimately varied —
   exactly like a flickering screen, killing all real events. The correct IAC signal is
   *repeat rate*: a screen's content is a one-off every frame (never learnable → suppress); a
   person's actions recur (learnable → trust), so a genuinely new person-centred moment is
   **not** suppressed. This is the subtle point Oudeyer's "learning progress" is actually about.

## 3. Does it work? Yes — within a clear, honest scope.

Tested on a simulated placed-camera stream (600 frames, screen-noise distractors, 25–30
seeds). Two regimes, because they give opposite answers:

- **novel-edge events** introduce a brand-new relation (a `knocked_over`).
- **reconfiguration events** are novel *combinations of familiar edges* — no new relation
  type at all (someone stands while still staring at the screen). This is the brief's
  central case ("the way the lines combine changes").

Detection = fires on a configuration's *first* occurrence. Habituation = correctly stays
quiet on repeats. Both should be high. Fixed operating threshold; baselines given every
fair advantage (same machinery, best thresholds).

| regime | gate | detection | habituation | normal FP | noise FP | VLM fire % |
|---|---|---|---|---|---|---|
| **reconfig** | **CONFIG (full)** | **1.00** | 0.81–0.98 | 0.00 | 0.09–0.22 | 4–8% |
| reconfig | TRIPLET (single-edge) | **0.00** | — | 0.00 | 0.35 | 9% |
| reconfig | NODE-EMBEDDING | **0.00** (≤0.25 at any threshold) | — | — | — | — |
| novel-edge | CONFIG (full) | 1.00 | 0.98 | 0.00 | 0.23 | 6% |
| novel-edge | TRIPLET (single-edge) | 1.00 | 0.51 | 0.00 | 0.35 | 12% |
| — | ALWAYS-ON (status quo) | 1.00 | 0.00 | 1.00 | 1.00 | 100% |

**The decisive result (reconfig):** the configuration gate detects **100%** of novel
relational reconfigurations; **single-triplet novelty and node-embedding detect 0%** — and
no threshold rescues them (node-embedding's node-type histogram is invariant to relational
structure; single edges are each already familiar). Detection is robust across thresholds
0.3–0.7; raising the threshold trades nothing in detection for better habituation and noise
rejection. The IAC/learning-progress filter cuts screen-noise false fires roughly in half
(~0.40 → ~0.20) and the VLM budget from ~12% to ~8% of frames (≈12–23× fewer VLM calls than
always-on).

**The honest limit (novel-edge):** when an event brings a new relation, the cheaper
single-triplet gate already detects it perfectly. So configuration-surprise is **not
universally better** — it is *necessary and uniquely sufficient* for reconfigurations of
familiar elements, and unnecessary for events that introduce new objects/relations. That is
a precise, defensible scope statement rather than an oversold claim.

## 4. Is this a paper yet? Honest answer: not on its own.

What's solid: a clean, reproducible mechanism, and a sharp comparative result showing the
two obvious cheaper baselines provably fail on exactly the moments the thesis targets. That
is a real intellectual contribution at the *mechanism* level.

What's missing for CHI/UIST/HRI:

1. **Real scene graphs.** Everything here runs on synthetic graphs I designed. The favorable
   case mirrors the brief's own thesis, and baselines were handled fairly — but a simulator
   I wrote cannot be the evidence. Next step: run Grounding DINO / YOLO-World on the 481
   frames already in `live_captures/` and re-run this exact evaluation on real graphs.
2. **Human-grounded "worth noticing."** Detection/habituation here are scored against
   *structural* novelty, which is a proxy. Whether structurally-novel == worth-noticing-to-a-
   -person is the actual research question and needs labels from you / lab members.
3. **Deployment.** HRI reviewers will want the gate running live on the rig, with a small
   study, not a notebook.

My recommendation: this is a strong *late-breaking / workshop* result now ("a cheap
structural gate that catches relational reconfigurations two standard baselines miss"), and
a credible *full-paper* contribution after steps 1–2. I'd not write a full paper around
simulated numbers — it would invite exactly the rebuttal that the result is built into the
simulator.

## Reproduce

```
cd SecondAttention/config_gate
python3 config_surprise.py   # the brief's working→spill example
python3 eval_final.py        # the table above
```
