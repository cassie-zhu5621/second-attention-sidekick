# Project handoff — Notice-Delegation Sidekick (master doc)

Single consolidated concept + state doc. Read this first; it points to the detail docs
(`SYSTEM_MAP.md`, `grounding_map.md`, `RELATED_WORK_hri.md`, `relation_table.md`,
`TITLE_ABSTRACT.md`, `MDR1_presentation_brief.md`). Supersedes the older `BRANCH_gaze_handoff.md`.
Last updated: June 2026.

---

## 1. THE CONCEPT (the crux — frame this hardest; reviewers are harsh on novelty)

**Notice Delegation** — a new form of human–robot collaboration: you **delegate the act of noticing**
to a placed agent. You tell it in plain words what's worth a second look; it watches your space and
**reports the moments you would have missed** — present OR absent (not specifically "when you're away").
The criterion of "worth-noticing" is **yours, compiled from language, and rewritable**.

- **One-liner:** *A placed sidekick you delegate the act of noticing to — it watches and reports the
  worth-noticing moments you'd have missed, steered by what you say in plain words.*
- **NOT auto-photography.** The earlier "AutoSnap" framing read as Google-Clips/Apple-best-shot (fixed
  aesthetic capture) → non-novel. Differentiators: (1) criterion is **user-defined & rewritable in
  language**; (2) it notices **relational/social moments**, not "a good frame"; (3) it's an **embodied
  placed social agent** you delegate to; (4) contribution = the **interaction** (delegation + steering),
  studied as HRI. **Never use snap/photo/camera/capture in the title.**
- **Title (HRI-tuned):** *Noticing What We Miss: Delegating the Act of Noticing to a Placed Robot
  Companion.* Final EN abstract in `TITLE_ABSTRACT.md`.

**VLM's role (resolved):** the VLM is a **compiler of context**, NOT a per-frame recognizer. Two jobs:
(a) **compile** the user's spoken taste → what to watch for (which relations/combos); (b) **gated
judge/narrator** — confirm a caught moment against the image + narrate it. The cheap CV relational
gate is the always-on front layer; the VLM sits behind it.

---

## 2. ARCHITECTURE — the pipeline

`User Contexts → VLM Compiler (planner) → Executor (CV) → Records`  (diagram: PROPOSED METHOD slide)

1. **VLM Compiler / planner** (`planner.py`): context text (+ optional frame) → a **watch-spec** =
   combos over the 11 relations. Two grammars: **restricted** (AND only) and **free** (+ any/not/then).
   Re-plans when the context changes. `VOCAB_VERSION = "v2.1"`.
2. **Vocabulary = 11 theory-grounded relations** (the building blocks; see §3). These come from the
   **literature on social attention/interaction**, NOT from the photos. (`relation_table.md`,
   `grounding_map.md`.)
3. **CV Executor** (`relations.py`, `attention_system.py`): MediaPipe Face(gaze) + Pose(body) +
   object detector (YOLO-World / closed-YOLO / Grounding DINO) → per-frame truth vector over the 11
   relations → an **executor** fires when a watch-spec combo is satisfied. Cheap 2D geometry proposes;
   the **VLM confirms** the moment (precision; depth can fool a 2D ray).
4. **Records**: each fired moment → a **storyboard** (event-driven keyframe sequence, 1–10 panels) +
   a **description** narrated from the real-time detection trace (see §5).
5. **Robot embodiment** (`rig.py`, firmware `pantilt_r4.ino`): pan-tilt **SCAN → LOOK(orient/join
   attention) → WATCH → nod**, + red LED (breathe while searching, fast flutter on "found") + buzzer
   chirp. The robot is the body of the Executor (NOT in the software diagram → introduce it on the
   prototyping slide).

**Key resolved decisions:**
- Detectors only **localize** objects/phrases; **relations are computed geometrically** then VLM-
  confirmed. Grounding DINO is NOT a relation verifier (don't feed it relational phrases).
- **No depth camera needed**: head-pose → 2D ray; ray-hits-box + multi-ray convergence are 2D tests.
- **Designed theory-grounded relations** are the gate (pivot away from the generic "config-surprise"
  gate, which exploded into unreadable relation soup on real frames).
- **Concept narrative logic** (for the paper): relations come from LITERATURE → system compiles over
  the vocabulary → scenarios are the EVALUATION/fieldwork (real photos), not the source of relations.
- **restricted vs free grammar = an ablation**, not a deployment choice: does the richer grammar earn
  its keep (expressiveness) and what does it cost (validity/stability)?

---

## 3. THE 11 RELATIONS — detection principles (cheap 2D; VLM confirms)

`sw = shoulder width (px) = on-screen ruler; box(o)=object bbox; tol in degrees.`

```
 1 gazing-at     head-pose ray (FaceMesh+solvePnP; far: nose→ear-midpoint) hits box(o), angle ≤ 12°
 2 joint-attn    ≥2 gaze rays' half-lines intersect in front of both (t>0), point inside frame
 3 eye-contact   3D: angle(face_forward, −head_pos) ≤ 12°  (looking into the lens)
 4 pointing      arm ray = wrist−elbow, ONLY if elbow ≥140° extended; hits box(o), angle ≤ 15°
 5 proxemic      dist(midhip_a, midhip_b)/mean(sw) ≤ 2.7   (Hall personal zone)
 6 F-formation   pair ≤ 8 sw AND each head ray hits the other's body box (tol 25°)  (Kendon)
 7 approach      over 3 s: sw ratio ≥1.2 or ≤0.83 (toward/away) OR Δ(norm dist to object) large
 8 lean-in       torso tilt = |atan2(midSh.x−midHip.x, −(midSh.y−midHip.y))| > 15°
 9 hands-on      wrist ∈ box(o)+10% margin AND dwell ≥ 1 s
10 gathering     person-count stable over window, then Δcount ≠ 0 (someone enters/leaves)
11 turn-taking   sole wrist-holder of a shared artifact switches A→B, B sustained ≥1 s, A still tracked
```
Theory channels (cite at channel level): gaze/oculesics (Kendon; Argyle&Dean), deixis (Kita),
proxemics (Hall), kinesics/posture (Mehrabian), object-action (Strabala), group org (Kendon; Goffman),
interaction regulation/turn-taking (Sacks et al. 1974; Ekman&Friesen). Row 11 was added from a VLM
plan-time probe. Full grounding in `grounding_map.md`; also Media Equation (legible gaze/movement =
social cue), tellability/news values (what's worth recounting).

**Distinctions:** zone(5)=two people close (distance) vs gathering(10)=headcount change.
approach(7)=whole-body translation over seconds vs lean-in(8)=instantaneous torso tilt.

**Perception robustness (current):** near faces → precise FaceMesh ray; far/lost faces → coarse Pose
head ray (nose→ears, yaw-only) auto-fallback. EMA smoothing + lowered presence/tracking confidence
reduce jitter/dropout. MediaPipe skeleton is drawn in the mediapipe backend. CoMotion (3D pose) backend
exists but is too slow/jittery on the laptop (duplicate skeletons under low fps) — offline only for now.

---

## 4. STORYBOARD — event-driven keyframe sampling

```
Open a story when a watched combo fires; capture panel₀ immediately.
At time t, capture a NEW panel iff:
    (t − t_last ≥ τ)                       # min spacing (--burst-interval)
    AND ( s_t ≠ s_last                     # relation truth-vector changed (a sub-event)
          OR  mean|I_t − I_last| > θ )      # OR the image moved enough (--scene-diff)
Close when the combo is no longer satisfied, or panel count = N_max (=10).  ⇒ panels ∈ [1,10].
```
Established family: **keyframe extraction / change-point sampling / shot-boundary detection**; same idea
as WorldScribe's keyframe extraction; grounded in **Event Segmentation Theory** (Zacks 2007). English
terms to use: **visual narrative** (concept), **storyboard** (artifact), **keyframe sequence /
event-driven keyframe extraction** (method).

---

## 5. DESCRIPTION — narrated from the real-time detection trace

The description is **recorded in real-time during the Executor step**, NOT re-captioned from a saved
photo. At each panel capture, `shot_trace(truth, viz)` logs the live detection (which relations + target
objects at that instant). At story completion the ordered, de-duplicated trace (e.g.
`approach → hands-on, lean-in → gazing-at laptop`) is narrated by the VLM into the description (the
comic strip image is a visual aid; the grounding is the trace). Finest real-time log = per-frame truth
vector in `feed/relation_log.jsonl` (with `--save`). Example record: *"Person repeatedly approached,
examined potted plant on shelf, leaned in close for inspection." (5-shot story)*.

---

## 6. STUDY + RESULTS (planner, v2.1)

`studies/planner_study.py`: 10 scenarios × 2 temps (0.0/0.7) × 2 grammars (restricted/free) × k5 = 200
runs, context-only (no frame yet). Figures `studies/make_report_figures.py` → F1–F8 (palette = the
green/red color card). Scenarios (keys are the original short names; texts were reworded from Cassie's
lab photos): assembly, guest, solo-work, lunch, demo-day, pair-prog(collab), entrance, fragile(prototype),
rehearsal(presentation), quiet.

**Temperature:** T=0 ≈ deterministic (canonical mapping); T=0.7 = stochastic token sampling (stress-tests
stability). **Agreement** = % of runs giving the exact same plan; **Jaccard** = overlap of the relation-
id SET (ignoring composition). High Jaccard + low agreement = same relations, different composition.

**Key findings (v2.1):**
- **v2.1 fix worked:** disambiguated gathering(10)=headcount-change vs approach(7)=single person toward
  a place; arrivals now correctly pick approach(7) (e.g. entrance free → `7; single:7`), gathering only
  for real groups. (Fixed the earlier "every plan was gathering" bug.)
- **Coverage:** vocabulary covers 9/10 scenarios; **presentation/rehearsal** is the gap (missing 5/5 —
  the model wants floor-holding / speaking-turn / presenter→slide gaze-shift / feedback-gesture).
- **F8 (translatability):** 8 rows pass; **prototype** fails on validity (free grammar ~90% invalid
  specs; restricted is 0% — a real bug) and **presentation** fails on coverage (0%).
- **free grammar** earns its keep (then/any/not used meaningfully: `then(7→3)` guest, `any(7)not(10)`
  solo) but costs reliability (higher violation/lower stability) → **expressiveness ↔ reliability**
  tradeoff is a reportable finding.

**Evaluation method (for judging vocab/plan quality):** gold relation-sets per scenario (precision/recall/
specificity/composition) + human rubric (Likert + error checklist) → aggregate **per-relation
mis-selection rate** to find the next vocab bug; ≥2 raters + Cohen's kappa; track non-null "missing"
frequency. (Tool not built yet — deferred.)

---

## 7. CURRENT LIMITATIONS
1. **Planner/free grammar validity** unstable — `prototype` ~90% invalid in free grammar (fix validator).
2. **Vocabulary coverage gap** — `presentation`: needs floor-holding/turn-to-speak/gaze-shift/feedback-
   gesture relations (→ v3).
3. **Room-scale gaze** — FaceMesh drops distant faces; pose fallback is coarse (yaw only, no eyeball).
4. **Relations are cheap 2D** — depth can fool them; multi-person tracking is nearest-mid-hip (ID churn);
   CoMotion not yet usable live.
5. **Hardware** — M5 ~2 fps UXGA, one viewer, IP changes; pan-tilt down-look ~12°; single placement =
   single viewpoint.
6. **Study is context-only** (no real frames); **no user study yet** (acceptance/trust/usefulness unmeasured);
   description quality depends on relation accuracy.

---

## 8. VENUE STRATEGY + NEXT STAGE
- **Target: HRI full paper** (highest ceiling, native fit: embodied companion + delegated noticing +
  joint attention + acceptance study). HRI is NOT technically hardcore — judged on interaction
  contribution + study rigor; off-the-shelf perception and even **Wizard-of-Oz are accepted** (escape
  hatch for hard perception). **DIS** is the strong, lower-risk alternative (research-through-design +
  in-the-wild). UIST only if the VLM-compiler-steers-CV is made a real, demoable technical contribution.
- Nearest related work in `RELATED_WORK_hri.md` (robot photographer HRI'20, PhotoBot, proactive
  assistance, joint-attention/Admoni HRI'13, LLM-in-HRI review). Differentiators in hand: delegation +
  steerable VLM-compiled taste + theory-grounded relations.

**Concrete next steps:**
1. Fix `prototype` free-grammar high violation (pull the invalid specs from the v2.1 jsonl, see the
   structural error, tighten the validator/grammar).
2. **v3 vocabulary** from elicited (survey/fieldwork) scenarios — add the presentation-gap relations.
3. Re-run the planner study **with real frames** (grounding/specificity; addresses context-only limit).
4. Wire the full robot loop for a deployment; design the HRI study (controlled comparison: steerable
   vs fixed taste / legible movement vs none / embodied vs static camera; + multi-person, real space).
5. MDR1 5-min deck (`MDR1_presentation_brief.md`): concept → lit → concept design (goal/fieldwork/
   method/iteration) → discussion (most important). Real fieldwork, not web survey.

## 9. FILE / SYSTEM POINTERS
- `SYSTEM_MAP.md` — full directory map, camera (M5 MJPEG) + pan-tilt wiring, calibration, the two fixed
  contracts (Detector `.detect()` + rig `move_to`/`get_frame`).
- Core: `planner.py`, `relations.py`, `attention_system.py`, `gaze.py`, `perceive.py`, `judge.py`,
  `rig.py`, firmware `pantilt_r4.ino` (servos D9/D10, buzzer D8, LED D6).
- Docs: `grounding_map.md`, `relation_table.md`, `RELATED_WORK_hri.md`, `TITLE_ABSTRACT.md`,
  `MDR1_presentation_brief.md`, `TEST_PLAN_gaze.md`. Results: `results/` (v2.1 jsonl/md + figures F1–F8).
- Run: `python attention_system.py --serve --save --plan-frame --camera 0` (mediapipe) /
  `--pose-backend comotion` / `--rig --port /dev/cu.usbmodem101`. Study commands in `SETUP_AND_COMMANDS.md`.
