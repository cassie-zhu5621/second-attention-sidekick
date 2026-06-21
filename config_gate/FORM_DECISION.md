# Form Decision — The Pick, Why It Fits the Concept, and How It's Novel

The convergence doc. `INTERACTION_DESIGN.md` designed the interaction; `FORM_RATIONALE.md`
opened the form space and §8 listed the menu. This doc picks one, proves it fits the concept,
and positions it against existing products for **novelty**. Last updated: June 2026.

> **Revision note (honest, for the research log):** an earlier draft of this doc picked **8a
> (head + body-yaw, "turn to face you")**. That was wrong, for two reasons Cassie raised:
> (1) it optimized for the *conversational recount* (face the person and tell them), which is
> exactly **Jibo's** territory — a famous existing product (HRI'24 workshop) → little novelty;
> (2) it under-valued **8b (the craning/leaning neck)**, which is *how a person physically
> finds an interesting thing* — and that, not conversation, is the heart of *noticing*. The
> corrected pick is below. This supersedes the 8a recommendation.

---

## 1. Re-strip the concept — the irreducible *embodied* act is the NOTICE, not the recount

Earlier I reduced Notice Delegation to "triadic attention" and then to *facing the person to
recount*. The recount matters — but in this system the recount is largely **asynchronous**:
you see the storyboard/record later, on a screen (`INTERACTION_DESIGN.md §1` loop). So the
recount does **not** need the body to turn and address you like a conversational robot. What
*does* need a body, in real time, is the **moment of noticing itself**: making *"oh — I just
noticed something over there"* legible, the instant it happens.

That is a different (and more on-concept) act. Its human form is well known: the **forward
lean / craning toward the thing** — the single most recognized nonverbal cue for **interest
and attention** (Mehrabian's *immediacy* cues; lean + nod = curiosity/interest). It is
literally "how people find an interesting thing," which is exactly Cassie's intuition. And it
does the joint-attention work by **initiation**: the robot cranes toward the thing → the
person *follows its lean/gaze to the thing* (responding joint attention / gaze-following). No
face-to-face needed; the deictic lean carries the triad in the object-directed direction.

So the form's headline job is to **embody curious noticing**, not to converse. That reframes
the whole pick.

---

## 2. The pick

> **Headline form: 8b — a craning / leaning neck** (a stalk that tilts and *extends/leans the
> head toward what it noticed*, and reclines to rest). It is the embodiment of *noticing as
> curiosity*: it leans in when it catches something, the way you crane toward an interesting
> thing. Add **8d expressive ears/antenna** for affect, keep the **one honest eye** and the
> **acknowledgement nod**. Pan + tilt remain (object-focus); the lean is the new headline DOF.

Demoted from the earlier draft: **base-yaw (8a)** is now *optional and secondary* — useful
only if a face-the-person recount proves necessary, and to be kept small because it pulls the
form toward Jibo. **8c rise-to-greet** stays an optional arousal/greeting layer.

Why this is the right pick, not just the liked one:

- **It is the concept made physical.** The project's novel core is *noticing*; the lean is the
  canonical cue for *noticing/interest* (Mehrabian). Form and concept are the same gesture.
- **It initiates joint attention.** A legible lean toward the catch makes the person follow it
  to the thing — the triadic loop, achieved by deixis rather than by facing-and-talking.
- **It expresses the affect the concept wants** — *curiosity*, restrained. A slow, gentle
  craning reads as a considerate, interested observer; a fast lunge would not. (Tune with
  ELEGNT's timing lesson: slow/smooth = calm interest, not excitement.)
- **It's legible from any viewer position** — unlike the pan-tilt's ambiguous side-glance, a
  lean *toward a thing* is readable whether you're in front, beside, or behind the robot,
  because its meaning is "that, over there," not "you."

### Resolving the earlier objection (this corrects `FORM_RATIONALE.md §3`)
§3 rejected a lean because it would make the robot "perform relations #7/#8 (approach/lean-in)
it is supposed to observe." That was **too coarse.** There are two different leans:

- **Social lean** — a person leaning *into another person's space* / joining an F-formation =
  relations #7/#8 between people. The robot must NOT do this (it would read as a participant).
- **Epistemic lean** — a small placed creature craning *toward a thing or region* to see it
  better = **deixis / curiosity**, not social participation. A desk-scale "curious looker"
  (think meerkat, bird, or Luxo Jr.) reads unmistakably as an *observer*, not as someone
  joining your conversation.

The corrected rule: **the lean is allowed and central when it is epistemic (toward the noticed
thing/region); it is forbidden when it intrudes into a person's personal space or a human
formation.** Same posture primitive, different referent → readable. So 8b is on-concept; the
old blanket ban was the error.

---

## 3. Novelty — why this isn't Jibo (or ELEGNT, or Astro)

The form must be *different from existing products*. Map the landscape on two axes: the
**embodied verb** (does the body *converse* or *notice*?) and the **target of attention** (the
*person*, or the *environment*?).

| Product | Embodied verb | Attention target | Lean? |
|---|---|---|---|
| **Jibo** | converse / companion | the **person** (turns to face & talk) | yes — *social* lean toward the speaker |
| **Vector / Cozmo** | play / react | self / person (desk pet) | no |
| **ElliQ** | converse / care | the person | no |
| **Amazon Astro** | patrol / fetch | the home (roams) | no — mobile periscope cam |
| **ELEGNT / Luxo** | illuminate / emote | a **task spot** | yes — *functional* reach to light it |
| **Security PTZ cam** | record | the environment | no — no expression |
| **→ This sidekick** | **notice (delegated)** | the **environment, on your behalf** | **yes — *epistemic* lean toward the noticed** |

The empty cell — **notices · the environment · for you · via an epistemic lean** — is unclaimed.
The differentiators are sharp:

- **vs Jibo:** Jibo's lean is *social*, toward the person it's talking to; ours is *epistemic*,
  toward the thing it noticed. Jibo embodies *conversation*; ours embodies *noticing*.
- **vs ELEGNT/Luxo:** the lamp's lean/reach is *functional* (aim light at a spot) or generic
  emotion; ours is *referential* — it means "I noticed *that*," steered by your delegated taste.
- **vs Astro / PTZ cams:** those watch the environment but **roam or just record** with no
  legible attention; ours is *placed* and makes its noticing *expressive and followable*.

**The novel contribution, named:** *the epistemic lean — a placed creature that visibly cranes
toward what it notices, on your behalf — as the embodiment of delegated noticing.* That is a
formal/interaction contribution no shipped product occupies, and it falls straight out of the
concept rather than being bolted on.

---

## 4. How to prove it — a discriminating study

Claim: *a craning/lean neck makes machine noticing more legible and more followable than gaze
alone.* Falsifiable, so test it. Built to discriminate (a condition where the lean should
clearly win or the claim fails).

**Conditions (the noticing cue, 3 levels, increasing embodiment):**
- **S — static eye** (LED/none; lower bound)
- **P — pan-tilt gaze** (current prototype; orients but doesn't lean)
- **L — craning lean** (the pick; orients *and* leans toward the catch)

**Discriminating manipulation — catch salience: obvious vs subtle/distant.** Prediction: S<P<L
everywhere, but the **L−P gap widens for subtle/distant catches**, where a small gaze rotation
is easy to miss and the lean is what makes "it noticed *that*" unmistakable. A benefit that
grows exactly where gaze-alone is weakest is the proof the lean does real work.

| Measure | How | Grounded in | Prediction |
|---|---|---|---|
| **Noticing legibility** | "did it just notice something? what?" — detection + referent accuracy | Admoni (attention perceived via gaze/posture) | L ≥ P > S; gap widens on subtle catches |
| **Attention-following** | does the person look where it leaned? accuracy + latency | Mutlu (referential cue narrows referents); gaze-following | L > P > S |
| **Curiosity / interest attribution** | rate "it seems curious / interested / noticing" | Mehrabian (lean = interest) | L > P |
| **"Noticing on my behalf" / connectedness** | short trust+engagement scale | Sidner & Rich | L > P > S |

**Cheap pilot (you already have P):** add one servo/linkage to make the head lean, film the
same catch at two saliences from a fixed viewpoint for S/P/L, run an 8–12 person video test of
the four measures before building any enclosure. If L doesn't beat P — especially on subtle
catches and attention-following — the lean isn't justified; say so (the honest, MDR1-friendly
result).

---

## 5. One-paragraph answer (reviewer / slide)
> The novel core of Notice Delegation is *noticing*, not conversation — so the body should
> embody noticing. The canonical human cue for noticing/interest is the **forward lean/cran**
> (Mehrabian's immediacy cues), and a placed creature that **cranes toward what it noticed**
> both expresses curiosity *and* initiates joint attention (you follow its lean to the thing).
> We therefore pick a **craning/leaning neck** over a conversational turn-to-face body. This is
> distinct from existing products: Jibo's lean is *social* (toward the speaker), ELEGNT/Luxo's
> is *functional* (aim light), Astro merely roams and records — none occupies *epistemic lean
> toward the noticed, on the user's behalf*. We prove it with a static/gaze/lean × salience
> study whose discriminating prediction is that the lean's advantage grows for subtle, distant
> catches where gaze alone fails.

---

## Sources
- Mehrabian (1971), *Silent Messages* — forward lean as an immediacy cue signaling interest/
  attention; lean + nod = curiosity. (Already your grounding for relation #8.)
  https://pmc.ncbi.nlm.nih.gov/articles/PMC7870468/ (immediacy/relational-message review)
- Admoni & Scassellati (2017), *Social Eye Gaze in HRI: A Review*, J-HRI — robot attention
  perceived via gaze/orientation. https://dl.acm.org/doi/pdf/10.5898/JHRI.6.1.Admoni
- Mutlu et al. — referential gaze narrows the referent set (faster/accurate object ID); basis
  for the attention-following measure.
- Jibo / Breazeal — conversational social robot; *leans toward the speaker* (the social lean we
  differentiate from). https://spectrum.ieee.org/cynthia-breazeal-unveils-jibo-a-social-robot-for-the-home
- Apple ELEGNT (2025) — Luxo-style lamp; functional reach + expressive timing (adopt the timing
  lesson). https://machinelearning.apple.com/research/elegnt-expressive-functional-movement
- Sidner & Rich — engagement as a phased process.
  https://www.researchgate.net/publication/221473126_Recognizing_engagement_in_human-robot_interaction
