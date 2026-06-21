# MDR1 final presentation — build brief (5 min slides)

Goal for the NEW chat: turn all of Cassie's existing work into a 5-minute MDR1 deck that follows the
required structure below. **The reviewer is HARSH on the novel concept — framing it is the #1 effort.**
This is a *first step* of the research: do NOT oversell results; show concept + a first prototyping
cycle + reflective discussion.

## Hard constraints (from the reviewer's own slides)
- It's a **first step** — "almost meaningless to get quantitative data with a dirty prototype." Focus on
  **fruitful experience + insights**, not solid answers.
- **Fieldwork / user study = SEE REAL USERS / FIELDS. AVOID web surveys.** (Need real contact with people
  in the shared lab, not an online questionnaire.)
- **Discussions = the most important part** (findings, limitations, new hypotheses, next steps).
- Research ≠ web search, ≠ gathering data from your social network, ≠ re-implementing something existing.
  **Research = a series of actions to solve issues / create the future based on a NOVEL CONCEPT.**

## Required structure + timing (MDR1, ~5 min)
1. **Introduction** — 1 slide / 30s — social background + motivation: *why did you start this?*
2. **Literature Review** — 2 slides / 1 min — related works: *how do you position this in history?*
3. **Concept Design**
   - Research Goal — 1 slide / 30s — *what questions, what to achieve?*
   - Fieldwork / User study — 1–2 slides / 30–60s — *understand the field & users (REAL, no web survey)*
   - Proposed method — 1 slide / 30s — *your idea to achieve the goal*
   - Prototyping iteration — 1–2 slides / 30–60s — *try the 1st cycle (make → try → make again)*
4. **Discussions** — 2 slides / 1 min — **MOST IMPORTANT**: findings, limitations, new hypotheses, next steps.

## THE NOVEL CONCEPT — frame this hardest (make-or-break)
**Name: Notice Delegation** — a new form of human–robot collaboration: you **delegate the act of noticing**
to a placed agent.

One-sentence concept: *A placed sidekick you delegate the act of noticing to — you tell it in plain words
what's worth a second look, it watches your space, and it reports the moments you would have missed.*

The shift (state it as before → after):
- FROM machines that **capture/record** everything (lifelogging) or **assist with tasks** (assistant robots)
- TO a machine that **notices on your behalf** and reports what you'd have missed — where the criterion of
  "worth noticing" is **YOURS, compiled from plain language, and rewritable**.

Why it isn't already solved (the reviewer will push here — pre-empt it):
- **Always-on capture / lifelogging (SenseCam, cameras)** = records indiscriminately; the burden of finding
  what mattered, and of defining "mattered," stays on the person.
- **Proactive / assistant robots** = act on **fixed, designer-set criteria**; you can't reshape what they
  care about by talking to them.
- **Per-frame VLM** = uneconomical + opaque.
- → **Nobody lets a person delegate AND steer noticing in plain language.** That gap is the concept.

Why now: multimodal VLMs can, for the first time, **compile open-ended human intent ("what I care about")
into what a cheap perceptual system watches for** — making "delegated, steerable noticing" feasible.

Avoid framing it as "I built a robot with a VLM." Frame it as a **paradigm / interaction concept**; the
robot is just the instantiation.

## Mapping Cassie's existing material → each slide
- **Introduction (background/motivation):** attention is finite; we constantly miss worth-noticing moments
  (present or absent). Personal hook: the shared lab is full of fleeting moments nobody catches. Use the
  final abstract's first two sentences.
- **Literature Review (2 slides):** position against the 4 clusters in `RELATED_WORK_hri.md`:
  (1) "should the robot act / what's worth flagging" (To Help or Not to Help; proactive assistance),
  (2) autonomous capture-the-moment robots (Robot Photographer HRI'20; PhotoBot) ← nearest neighbors,
  (3) joint attention / perceived robot attention (Admoni HRI'13; gaze cueing) ← theory + measurement,
  (4) LLM/VLM-in-HRI + end-user steering. **White space = delegated + steerable noticing.** Also the
  theory grounding in `grounding_map.md` (tellability, news values, Media Equation, joint attention).
- **Research Goal:** RQ — *can people delegate the act of noticing to a placed agent, and steer it through
  ordinary language?* (acceptance + use + appropriation). Keep it a question, not a result.
- **Fieldwork / User study:** ⚠️ GAP TO FILL — need REAL contact: observe the shared lab (KMD Embodied
  Media), short interviews with labmates about what they miss / would want noticed. The 560-photo lab
  dataset + observations of the space count as field grounding. (No web survey.)
- **Proposed method:** the idea = VLM-as-compiler-of-context + cheap structured perception + editable taste,
  on a pan-tilt placed robot. Pull the architecture from `SYSTEM_MAP.md` and the gaze/joint-attention
  pivot from `BRANCH_gaze_handoff.md`. Keep it ONE slide, conceptual.
- **Prototyping iteration (1st cycle):** what's already built — perception → relation gate → VLM confirm →
  report; pan-tilt SCAN→LOOK→nod; editable taste; the gaze/joint-attention relations (`gaze.py`,
  `relations.py`, `attention_system.py --rig`). Show the live overlay + feed screenshots. Frame as
  "make → try → revise" (e.g. the inside-relation explosion → whitelist fix; per-pose dwell fix). Honest,
  iterative, not polished results.
- **Discussions (most important):** what trying the 1st cycle taught (CV flicker is a real limit → VLM
  filters; rough gate + VLM judgment; relation explosion → designed relations; gaze at room scale is the
  open risk). Limitations. New hypotheses (legible short glances vs stares per Admoni; steerable taste
  improves acceptance). Next steps → the real HRI study (controlled comparison + multi-person deployment;
  WoZ option for the hard perception). Tie back to the novel concept.

## Content sources in the repo (the new chat should read these)
- `SYSTEM_MAP.md` — system, camera, pan-tilt, architecture.
- `BRANCH_gaze_handoff.md` — the gaze/joint-attention pivot + concept (notice delegation).
- `RELATED_WORK_hri.md` — 11 related papers + the 3 deep reads + bar assessment (use for Lit Review + positioning).
- `grounding_map.md` — theory references (tellability, news values, Media Equation, RCC-8, etc.).
- Title + abstract (EN + JP) — final versions in the chat history / to be saved.
- Memory: `branch-gaze-joint-attention`, `ref-media-equation`, `project-attentive-sidekick`.

## Open gaps to flag in the deck (honest, first-step framing)
1. Real fieldwork with labmates (do at least light interviews/observation before the talk).
2. The 1st prototyping cycle = qualitative reactions only; no quantitative claims yet.
3. Room-scale gaze robustness = known open technical risk (MediaPipe distance limit; CoMotion / WoZ as paths).
