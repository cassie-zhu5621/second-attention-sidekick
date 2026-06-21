# MDR1 Slide Structure — Notice Delegation (5 min)

> **#1 priority:** The novel concept must land before anything else. Every slide is either setting up
> or defending "Notice Delegation." Never say "I built a robot with a VLM."

---

## Slide 1 — Introduction (30s)

**Headline:** We miss things.

**Body (3 bullets max):**
- Human attention is finite. Shared spaces are full of fleeting moments — collaborations forming,
  objects changing hands, someone arriving — that vanish before anyone catches them.
- We have devices that *record* everything and robots that *assist with tasks*. Neither lets you say
  **what's worth noticing** and have something watch for it.
- → *What if you could delegate the act of noticing?*

**Visual:** A photo or simple illustration of the shared KMD lab space — people at desks, whiteboard,
a moment of passing something. Something that feels lived-in and incidentally rich.
*(Can shoot this — one candid of the lab.)*

**Tone:** personal, grounded. The reviewer needs to feel the problem in 30 seconds.

---

## Slide 2 — Literature Review ① (30s)

**Headline:** What are robots already doing about this?

**Three clusters, one line each:**

| Cluster | Example | Limit |
|---|---|---|
| Proactive assistance | To Help or Not to Help (THRI); PACT | Criteria are **designer-fixed** |
| Auto "capture-the-moment" | Robot Photographer (HRI'20); PhotoBot | **Aesthetic/offer-triggered**; you can't tell it what matters |
| Lifelogging | SenseCam, always-on cameras | Records everything; **burden of finding what mattered stays on you** |

**White space (say it aloud):** Nobody lets a person **delegate AND steer** noticing in plain language.

**Visual:** A 2×2 or simple axis diagram.
- X-axis: Fixed criteria → User-defined criteria
- Y-axis: Capture everything → Notice selectively
- Other work clusters bottom-left; our work is top-right, alone.

*(I can make this diagram — just tell me the style.)*

---

## Slide 3 — Literature Review ② (30s)

**Headline:** Theory + the enabling technology.

**Two sub-sections:**

**Theory grounding (why these are the right moments to watch for):**
- Joint attention (Tomasello 1995) — attending together = socially meaningful
- Gaze cueing (Friesen & Kingstone 1998) — a glance is a directive act
- Admoni HRI'13 — multiple short glances beat one long stare for conveying attention → *design implication for our robot*
- Media Equation (Reeves & Nass 1996) — legible robot gaze reads as social presence

**Why now (the enabling shift):**
- VLMs (2022–) can compile open-ended language into structured perception
- LLM/VLM-in-HRI review (arXiv 2602.15063) names the pitfall: per-frame VLM is uneconomical →
  our answer: VLM-as-compiler + gated cheap CV, **not** per-frame.

**Visual:** Could be a citation map or just a clean two-column text layout.
No diagram needed here — keep it fast.

---

## Slide 4 — Research Goal (30s)

**Headline:** Can you delegate the act of noticing?

**RQ (one clear question):**
> Can a placed agent, steered in plain language, catch the moments a person would have missed — and
> be accepted as a noticing delegate?

**Three sub-questions (small):**
1. **Acceptance** — do people trust it to notice on their behalf?
2. **Use** — do they act on what it reports?
3. **Appropriation** — do they reshape what it watches for over time?

**Important framing note for the talk:** *This is the question, not the answer. MDR1 is the first step.*

**Visual:** Just the RQ in large text + the three sub-questions. Clean, no clutter.

---

## Slide 5 — Fieldwork / User Study (30–60s)

**⚠️ OPEN GAP — this slide needs real fieldwork before the talk.**

**What to do before the presentation:**
- 20–30 min observation of the KMD Embodied Media lab: what kinds of moments happen? (arrivals,
  whiteboard collaborations, object handoffs, attention shifts)
- 3–5 short (5 min) interviews with labmates: "What do you miss in this space?" / "What would you
  want a sidekick to have caught?"
- Note any recurring answers → these become the candidate "worth-noticing" criteria.

**What's already available to show:**
- 560-photo lab dataset (KMD space) — what kinds of moments are in there?
- Observation notes from using the prototype in the space

**Slide content:**
- 2–3 pull quotes from labmates (real words, not paraphrased)
- A photo of the lab space showing the kinds of moments that occur
- A short list of recurring "things I'd have wanted noticed" from interviews
- Frame: *"We went into the field first, to understand what noticing means in this space."*

**Visual:** Photo of the lab + 2 pull quotes in large text. Simple.

---

## Slide 6 — Proposed Method (30s)

**Headline:** Notice Delegation — the architecture

**The concept in one diagram (left to right):**

```
[Context — plain language]
        ↓
   VLM Compiler
        ↓
[Watch Spec — which relations, when]
        ↓
  Cheap CV Layer  ←—— Theory-grounded relational vocabulary (11 social-science relations)
        ↓ (when satisfied)
  VLM Confirmer + Narration
        ↓
  Robot: orient → nod → report
        ↓
  [Feed — async report to absent owner]
```

**Key design choices to name (small text below diagram):**
- VLM runs on **context change**, not every frame → economical
- Vocabulary is **literature-grounded** (Tomasello, Argyle, Hall, Goffman…), not learned
- Criterion is **yours, rewritable mid-run** (hot-reload context.txt)
- Perception runs on a USB webcam (high fps, needed for motion detection); pan-tilt via serial —
  no wireless overhead at this stage

**What NOT to say:** don't list the 11 relations. Don't explain gaze.py. Keep it conceptual.

**Visual:** Clean pipeline diagram. Can make an SVG — just confirm the visual style you want (minimal/
line-art / Cassie's existing SVG style from pantilt_assembly_v2.svg).

---

## Slide 7 — Prototyping: 1st Cycle (30–60s)

**Headline:** Make → try → revise

**What's built (one sentence to orient the audience):**
USB webcam (high fps + resolution, needed for motion detection) + pan-tilt via serial →
attention_system.py: context → compiled plan → continuous relation detection → VLM confirm → feed card.

**Main visual: a video clip (~45s)**
One full turn of the prototype, edited as:
1. **Zoom out** — show the whole scene: rig, people, space
2. **Live run** — one cycle: sweep → relation detected (overlay shows) → robot stops → VLM confirm → nod → story burst published to feed
3. **Zoom into the feed card** — show the resulting strip + VLM narration

> *(Shoot this as a screen-recording + room-camera combo, or just screen-record the
> attention_system.py UI + overlay while someone walks into frame. ~1 min raw, cut to 45s.)*

**Below the video (small text):** rig photo + one screenshot of the plan panel (the compiled watch-spec)
to show the "legible taste" side of the loop.

**Don't explain the code. Let the video do it.**

---

## Slide 8 — Discussions ① — What we learned (30s)

**Headline:** What the first cycle taught us

**Make → try → revise (3 honest beats) — moved here from Prototyping:**

| Tried | Broke | Learned |
|---|---|---|
| Fire on ANY relational change (config-surprise gate) | Relation explosion — "a functional list, not an experience" | Need a *designed*, small vocabulary — the choice of what to notice is itself the design problem |
| Per-frame VLM scoring | Too slow, too expensive, opaque | VLM belongs as compiler (per context-change) + confirmer (per event), not on the hot path |
| Single-shot report | Too little context to reconstruct why it mattered | Story burst (N-shot strip) makes the moment legible in retrospect |

**Additional findings:**
- **Delegation interface is coherent:** typing "watch for collaborations forming" produces a sensible,
  readable plan. The loop — context → compiled spec → legible behavior — holds.
- **Short glances > long stares** (confirms Admoni): orient + nod reads as "I noticed"; sustained staring
  reads as malfunction. → *nod is the signal, not the stare.*

**Limitations (honest):**
- Room-scale gaze: MediaPipe falls off at distance → open technical risk (CoMotion or WoZ as paths).
- Gate false-fires: approach/depart relation fires while sitting → threshold still needs tuning.
- No real user data yet: reactions so far are our own; the labmate study is next.

---

## Slide 9 — Discussions ② — Hypotheses + Next Steps (30s)

**Headline:** New hypotheses → next study

**Three hypotheses generated by the first cycle:**

- **H1 (Acceptance):** Steerable taste → higher acceptance than fixed criteria, because the criterion is
  *yours* — you can blame the noticing, not the robot.
- **H2 (Legibility):** Orient + nod → people are more likely to recognize that *something was noticed* vs
  silent capture.
- **H3 (Interpretability):** Story bursts → users agree more often with the robot's judgment ("yes, that
  was worth noticing") vs single-frame reports.

**Next steps — two tracks:**

**Track A — validate the concept (study):**
1. **Real fieldwork now:** lab observation + short interviews with labmates (do this week, before the talk)
2. **Controlled study:** steerable taste vs fixed × legible movement vs none — measure with Admoni's
   detection-accuracy method + user agreement rate ("did you agree this was worth noticing?")
3. **WoZ option** for room-scale gaze — fake the hard perception to isolate the interaction question

**Track B — deepen the HRI design (the robot as social agent):**
- **Movement design:** what does it mean for a robot to "notice"? Design the specific kinematics —
  the scan glide, the moment of stopping, the nod cadence. Admoni: short glances, not long stares.
- **Feedback modalities:** sound (beep/tone at the moment of noticing), future: voice narration as
  the robot reports ("something's happening at the whiteboard")
- **Voice / language interaction:** ASR → context update is one pipeline step; the interaction design
  is the real work — how does a person *talk* to their sidekick to reshape what it watches for?
- **Long-term appropriation:** how does the taste change over days/weeks of use? Do people lean in
  or stop caring?

**Close (say aloud):** "Notice Delegation is a first step. What we're really asking is: can you hand
the act of noticing to something that speaks your taste back in actions — and trust it to be you, watching?"

---

## Summary: slide count + timing

| Section | Slide(s) | Time |
|---|---|---|
| Introduction | 1 | 30s |
| Literature Review | 2 | 1 min |
| Research Goal | 1 | 30s |
| Fieldwork | 1 | 30–45s |
| Proposed Method | 1 | 30s |
| Prototyping | 1 | 45s |
| Discussions ① | 1 | 30s |
| Discussions ② | 1 | 30s |
| **Total** | **9 slides** | **~5 min** |

---

## What to make / capture before the talk

| Asset | How | Priority |
|---|---|---|
| Lab photo (candid, moments) | Go shoot in the KMD lab | HIGH |
| Labmate interviews (3–5 people, 5 min each) | Do this week, real quotes | HIGH (gap) |
| Rig photo (clean) | Photograph the pan-tilt setup | HIGH |
| **Demo video (~45s)** | Screen-record attention_system.py UI + room camera; one full turn: sweep → detect → nod → feed card. Cut: zoom out → run → zoom into feed. | HIGH |
| Feed card screenshot | From video or live run | MEDIUM |
| Plan panel screenshot | Show the compiled watch-spec in the UI | MEDIUM |
| 2×2 positioning diagram | I can make this as SVG | MEDIUM |
| Pipeline diagram (Slide 6) | I can make this as SVG | MEDIUM |

---

## Novel concept — the one-liner to repeat

> **Notice Delegation:** a placed sidekick you tell what's worth a second look — it watches,
> and reports the moments you would have missed. The "worth noticing" is yours, in plain language,
> rewritable.

**Pre-empt the reviewer's pushback:**
- *"Isn't this lifelogging?"* → No. Lifelogging records everything; the burden of meaning stays on you.
  Notice Delegation flips it: the agent carries the judgment, compiled from your words.
- *"Isn't this a smart camera?"* → No. A camera captures; this agent **notices** — it selects, confirms,
  narrates, and reports. The criterion is yours, not a fixed aesthetic model.
- *"Why not just use a VLM per frame?"* → Uneconomical + opaque. Our architecture keeps VLM off the
  hot path; it compiles taste and confirms events, while cheap structured CV does the continuous watching.
