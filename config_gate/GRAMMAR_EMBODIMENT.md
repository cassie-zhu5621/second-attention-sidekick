# Form Follows Grammar — The Robot as an Embodiment of Its Own Relational Vocabulary

The novelty doc. `FORM_DECISION.md` picked the craning-lean body; this doc says **why that
body is novel** — not as a shape (shapes are hard to make novel) but because it is bound to
the genuinely novel part of the project: the **relational grammar** (the 11-relation table +
the VLM-compiler planner). The move: **derive the form from the grammar**, so the robot
becomes *an agent that performs the same relations it perceives.* Last updated: June 2026.

> Note: the 11 relations will be revised from real-case questionnaires/fieldwork. The
> contribution here is the **coupling principle**, which survives any revision of the list:
> *whatever the grammar becomes, the body performs the bodily-performable subset of it.*

---

## 1. The idea — one vocabulary, used in both directions

The system already reads the scene as a set of **social-spatial relations** (gaze, joint
attention, pointing, lean-in, proxemics, F-formation, …). The insight is that those same
relations are not only things to *detect* — most of them are things a body can *do*. So:

> **The robot perceives the scene in the relational grammar, and expresses itself in the same
> relational grammar.** Its body vocabulary (gaze-at, eye-contact, lean-in, point, turn-to-face)
> is the *expressive twin* of the 11-relation perceptual table. Perception and expression are
> the **same code, run in two directions.**

This is what makes the form a contribution: it is no longer an arbitrary cute object onto
which behaviors are bolted; it is the **physical instantiation of the grammar.** The intelligence
(novel) and the body (otherwise unremarkable) become *one thing.*

### Why this is legible — and why that's not hand-waving (common coding)
This isn't just a neat symmetry. **Common coding theory** (Prinz; the Theory of Event Coding,
Hommel et al.) holds that perception and action share a *single representational code*, and
actions are coded by their *perceptual effects*. A key consequence: behavior built on a shared
code is read by **similarity, with no arbitrary rule-learning required.** Translated to our
robot: because the human already *perceives and produces* these relations (people gaze, lean,
point, take turns), a robot that *also* produces them is legible **for free** — the person
doesn't learn "blink-pattern X means Y," they just read a lean as interest, a gaze as regard.
Grounding the robot's expression in the *same* grammar it perceives is therefore the most
legible possible design, by construction. (`INTERACTION_DESIGN.md §0`'s "nothing is decorative"
becomes provable: every expressive act is a relation the system also perceives.)

---

## 2. The mapping — which relations the body can *perform*

Tier each relation by how directly a small placed gaze-head-+-lean-neck body can **perform**
it (not just detect it). This table *is* the form-derivation tool.

| # | Relation (perceived) | Robot performs it as… | Tier |
|---|---|---|---|
| 1 | **gazing-at** | head-ray orients to the noticed object (its core ORIENT/NOTICE) | **A — direct** |
| 3 | **eye-contact** | turns its eye *to you* — greeting / acknowledge / read-back | **A — direct** |
| 8 | **lean-in** | **the craning neck** — leans toward what it noticed = *interest* (the chosen form, now grammar-grounded) | **A — direct** |
| 4 | **pointing** (deixis) | whole-body lean = **bodily pointing**: "*that*, over there" | **A — direct** |
| 2 | **joint-attention** | it gazes at X → you follow → you + robot share regard on X (it *forms* joint-attn, not just detects it) | **A — direct** |
| 7 | **approach** | the lean is a bounded **micro-approach** toward the noticed (no locomotion) | **A — direct** |
| 6 | **F-formation** | an optional **turn-to-face** forms a momentary F-formation with you (the one grammar-grounded reason for a small base-yaw) | **B — analog** |
| 11 | **turn-taking** | gaze **hand-off** during steering: you point → it looks → it looks back | **B — analog** |
| 5 | **proxemic** | respects your zones; **rises** when you enter its zone (greeting) — placement/posture, not translation | **B — analog** |
| 9 | **hands-on** | no hands → the **dwell of regard** on an object is the attentional analog | **B — weak** |
| 10 | **gathering** | a scene property (headcount change) — it can *react* with posture but can't *perform* it alone | **C — detect only** |

**Read the Tier-A column as a parts list.** The relations the robot can perform directly need
exactly: a **gaze head** (pan-tilt → #1, #3), a **lean neck** (→ #8, #7, and bodily #4), and a
**single eye** (→ #3). That is the `FORM_DECISION.md` pick — *re-derived from the grammar
instead of from taste or from Mehrabian alone.* Optionally a **small turn-to-face** earns its
keep, but now for a principled reason: to perform **F-formation (#6)** and seal **joint-attention
(#2)** — not to imitate Jibo.

So the form decision and the grammar are now the same decision. *The body is the subset of the
grammar that a placed creature can speak.*

> **⚠️ Narrowed by §6–§7 (read those):** the robot does **not** re-enact person↔person relations
> (that flips the meaning). It performs only the **attentional primitive — directed regard
> toward the locus** — and *refers to* the relation it saw; the relation-type and participants
> live in the report. And every movement must change the captured result (§7), or it's cut.
> Treat §2 as "the perceptual grammar the body *points at*," not "gestures the body re-enacts."

---

## 3. The unified system story (one vocabulary, three loops)

This coupling cleans up the whole system into a single language spoken in three places:

- **Human → robot (steering):** you **point** / look (relation #4, #1) to redirect it —
  `INTERACTION_DESIGN.md §2` point-to-redirect. You steer *in the grammar.*
- **Scene → robot (perception):** the CV executor reads the 11 relations off the scene
  (`PROJECT_HANDOFF.md §3`). It perceives *in the grammar.*
- **Robot → human (expression):** it gazes, leans, makes eye-contact, points with its body
  (Tier A). It expresses *in the grammar.*

One vocabulary, three loops — input, perception, output all share the relational code. That is
a tidy, defensible system contribution, and it is the thing no shipped product has.

---

## 4. Novelty — stated for a reviewer

> Existing expressive robots **produce** social cues (Jibo gazes and leans; iCub/Pepper mirror
> affect) and other systems **perceive** social cues — but in all of them the perceived
> representation and the produced behavior are **separate, hand-authored mappings.** Our
> contribution is an agent whose **expression and perception are the same formal grammar**: the
> robot performs (a bodily-performable subset of) the *exact* 11-relation vocabulary it uses to
> watch the scene. We call this an **embodied common-coding of a social-spatial relational
> grammar.** It makes the form a contribution rather than a styling choice (the body *is* the
> grammar), it predicts legibility from theory (common coding: shared code → no arbitrary
> mapping), and it unifies steering, perception, and expression under one vocabulary. The form's
> novelty is therefore *inherited from* the project's genuinely novel intelligence, which is the
> right place for it to come from.

What this is **not**: a claim that the *shape* is new. A craning desk creature is not new. The
claim is that the *binding of body to perceptual grammar* is new — and that binding is what a
"why this robot?" challenge should be answered with.

---

## 5. Consequences

**For the form:** stop searching for a novel shape. Build the body that speaks the most Tier-A
relations: gaze head + lean neck + eye (+ optional turn-to-face for #6/#2). Done — and now
justified by the grammar.

**For the study (a sharp, falsifiable prediction common coding hands you):** relations the
robot performs that are **also in the perceptual grammar** should be read *faster and more
accurately* than equally-salient signals that are **not** grammar-grounded (e.g. an arbitrary
LED code for the same meaning). Test: same message ("I noticed that"), delivered as a
grammar-grounded **lean/gaze** vs an arbitrary **light/sound** code; measure comprehension
accuracy + time + "felt natural." Common coding predicts the grammar-grounded cue wins. If it
doesn't, the coupling buys legibility no more than styling would — an honest, publishable result.

**For the paper:** this reframes the form chapter from "I picked a robot" to "the form is the
embodiment of the contribution," and ties the (hard-to-novel) hardware directly to the
(genuinely novel) grammar — exactly the link Cassie identified as the way to make it novel.

**Living grammar:** when fieldwork revises the 11 relations, re-run §2's table — add any new
performable relations to the body's repertoire, drop any that leave. The *coupling* is the
invariant contribution; the specific list is the variable.

---

## 6. CORRECTION — refer, don't mime (this narrows §1–§2)

§1–§2 over-reached. "The robot performs the same relations it perceives" breaks on a fact
Cassie raised: **relations live between scene participants, not between the scene and the
robot.** Eye-contact, gaze, lean-in, F-formation usually happen **person ↔ person** (A looks
at B). If the robot *reproduces* such a relation to express that it saw it — e.g. it makes
eye-contact with *you* to report "I saw two people make eye-contact" — the **referent flips**:
the gesture now means "robot ↔ you," a completely different thing. Mimicry corrupts meaning.

**The fix — the body refers, it does not re-enact.** The robot has essentially **one expressive
act: directed regard** — orient (and gently lean) **toward the *locus* of the noticed event.**
It says *"I notice **something** over there,"* and points its attention at where. It never plays
the *role* of a participant in the scene's relation. The **kind** of relation (eye-contact?
hands-on? a gathering?) and **who** it was between are carried by the **storyboard + report**,
**not** by the body. Body = the *index finger*; report = the *sentence*.

So the §2 claim must be narrowed: the robot does **not** embody all 11 relations. It embodies
the **attentional primitive** — *directed regard* — that the gaze-family relations (#1 gaze,
#2 joint-attn, #4 point) are *built from*. Common coding still holds, but at the level of that
**one primitive**, not whole social relations: the human reads "it's attending to that"
because directed regard is a code we all share. **The robot is the embodiment of *attending
itself*, not a mime of social scenes.** That is cleaner, more honest, and more novel: *a
creature that embodies the act of noticing and refers to what it noticed.*

Two fixed deictic frames, nothing else:
- **robot → region/object** = "look *there*" (the noticing act; the common case).
- **robot → you** = "*you*" (greeting / read-back / acknowledgement only — a deliberate address,
  never a re-enactment of a scene relation).

This dissolves the semantic-confusion failure mode entirely, and it makes the movement minimal.

---

## 7. Movement must change the result — or it's theatre (the validity rule)

Cassie's second point is the sharper one: **if the storyboard + report come out the same no
matter what the robot did, the movement is unconvincing** — decoration that looks alive but
proves nothing (fine for an exhibition, fatal for a research/product claim). The cure is a hard
coupling:

> **Every visible movement is the outward signature of a real detection decision that changes
> the captured result.** No movement without a *receipt* in the report.

Concretely, tie the body to the executor so the two are faces of one act:
- **Orient direction → the framing of the storyboard.** Where it turned *is* the vantage/
  subject the keyframes are taken of. Look elsewhere ⇒ a different story is captured.
- **The interest-lean crossing a threshold → the capture trigger / a new keyframe.** The lean
  is not added on top of capture; it *is* the visible form of "this crossed worth-noticing."
- **Lean depth ∝ judged salience → shown in the report** (e.g. confidence / why-flagged). A
  bigger lean means a stronger call, and the report says so.

Two payoffs, both things Cassie asked for:
1. **Conviction.** The report is the *receipt* for the movement. You can demonstrate it live:
   steer it to a different target → the captured story changes. The motion is believable
   *because* it moves the output. (This is also the cleanest study: *does robot attention
   causally change the record?* — yes, by construction, and you can show the paired diffs.)
2. **Minimal & clean (anti-overwhelm).** Because motion only happens at *real* decision points
   — a genuine notice — it is naturally **sparse**. "No movement without a result-difference"
   is the rule that prevents the busy, overwhelming feel. It supersedes
   `INTERACTION_DESIGN.md §0`'s "nothing is decorative" with something testable: **nothing
   without a receipt.**

Design check to apply everywhere: *if I removed this movement, would the storyboard/report
change?* If no, cut the movement.

---

## 8. THE FINAL MINIMAL DESIGN — "a small creature curious about attention"

Pulling §1–§7 together into the answer to "what's the best form and movement":

**Form.** A small *placed* creature: a **single honest eye** (the lens — it sees from where it
looks) on a **pan-tilt gaze head**, with a **gentle craning lean**, and **one affect antenna**.
Nothing else. (No face, no hands, no wheels, optional tiny turn-to-face only for greeting.)

**Movement = one verb, in degrees** (referential, never mimetic):

| State | Motion | Couples to result |
|---|---|---|
| REST | still, slightly down, dim | (off) |
| SEARCH | slow even scan, calm antenna | — |
| ORIENT | smooth turn toward a rising candidate | sets the story's vantage |
| **NOTICE** | settle + **curious lean toward the locus** (depth ∝ interest) + one antenna flutter + (optional) one chirp | **triggers capture; depth → salience in report** |

That is the whole repertoire. Its personality is **curiosity about attention itself**: it
perks and leans when it catches *someone attending to something* — its interest is in
*noticing*, which is exactly the concept. Restrained, sparse, warm; it points, it doesn't
perform; and every lean leaves a receipt in the record.

**Why this is the best fit:** it is the minimal body that (a) embodies *attending* (the
concept), (b) refers without the meaning-flip of §6, (c) moves only when the result changes
(§7) — so it is convincing *and* clean — and (d) keeps the novelty in the right place: the
body is the embodiment of the noticing intelligence, not a costume on top of it.

---

## 9. Pan vs lean — what actually makes them different (refines §7–§8)

Fair worry: if you pan the head, the target can end up centered; if you lean toward it, the
target can *also* end up centered — so the **frames look similar** and the lean seems
redundant. The distinction has to be made real on two levels at once, or the lean is decoration.

### 9a. The optical difference: rotation has no parallax, translation does
- **Pan / tilt = rotation about the head's pivot.** The optical axis sweeps *angularly*; the
  camera's nodal point barely moves. This changes **which direction** it looks → it *selects a
  locus*. Crucially, rotation produces **no parallax**: near and far things shift **together**
  (this is the "rotate about the no-parallax point" fact used to shoot panoramas). The target
  gets centered but **not bigger**, and depth relationships don't change.
- **Lean / cran = translation of the nodal point toward the locus.** This changes **vantage,
  not direction**: the target grows (scale ↑), the angle lowers/comes "over" it, and — the
  signature — **parallax appears**: near things shift *more* than far things. A pan can never
  produce parallax; only a lean can. So even when both center the target, the lean's frame is
  measurably different: **closer, with motion parallax and a changed angle.**

That parallax is also the **objective test** that the two joints are doing different jobs
(useful for calibration and for the paper): pan a checkerboard scene → foreground/background
move together; lean → foreground slides against background. If your lean shows no parallax, the
neck isn't translating enough to matter — fix the mechanism or drop the joint.

### 9b. The semantic difference: *where* vs *how much*
Keep them on different questions, and make them **sequential, not interchangeable**:
- **Pan/tilt answers "where?"** — it is the SEARCH/ORIENT act, selecting the locus. (the question)
- **Lean answers "how much / how close?"** — it fires **only after** a locus is chosen, as the
  NOTICE/interest response: *commit, intensify, get the detail.* (the exclamation)

Because the lean only happens *after* a pan has selected something, the viewer never sees them
as two ways to do the same thing — they see "it looked over there (pan) … then leaned in
(interest)." Direction first, intensity second.

### 9c. The result difference (this is the receipt — §7): two shot *types*
Map the two motions to two **shot types**, the way film does:
- **Pan/tilt → the establishing / locating frame** (wide-ish: who, where, the gesture).
- **Lean → the push-in / detail frame** (close: the thing itself, confirmed).

Now the lean earns its keep on the **output**: it produces the *close, parallax, over-the-thing*
keyframe a pan alone cannot. Design rule (from §7): **if the lean doesn't yield a visibly
closer/parallax frame than the pan already gave, cut it** — it has no receipt.

### 9d. Cassie's reference idea — the lean for *relational* framing
Good instinct, and it gives the lean its strongest justification. The meaningful content of the
multi-party relations — **joint-attention (#2), pointing (#4), F-formation (#6)** — is the
**convergence geometry**: several people + the one thing they orient to. A single fixed frame
often can't hold *both* the people *and* their target well (the target may be off-axis, far, or
behind the sightlines). A **lean shifts the vantage** to better expose that convergence (a bit
of parallax disambiguates who's looking at what), and a **push-in** confirms the target.

Honest limit (state it, don't oversell): a small neck translates only a few cm, so it gives a
**modest** parallax + a detail push-in — it **cannot** teleport to the perfect angle on a
room-scale convergence. So the real win is *compositional, across panels*:

> **The storyboard stitches what one frame can't hold:** a **wide pan-frame** (the people + the
> pointing/gaze) **then** a **lean push-in** (the target they converged on). One camera can't
> show a joint-attention triangle in a single shot — but a *wide → push-in sequence* narrates
> it. Pan and lean become the two shot types your event-driven keyframe storyboard alternates
> to **tell a relation**. That is the lean's positive, provable effect on the result.

So: pan **selects and establishes** the relation; lean **confirms and details** it; the
**storyboard composes** them into a legible record of a moment no single fixed frame could
capture. The two joints are different in optics (parallax), in meaning (where vs how-much), and
in output (establishing vs detail) — three independent reasons they aren't the same move.

---

## Sources
- Prinz, W. (1997) & Hommel et al. (2001), *Theory of Event Coding* — perception and action
  share a common representational code; actions coded by perceptual effects; similarity-based
  (no arbitrary mapping). https://en.wikipedia.org/wiki/Common_coding_theory
- *Human Impression of Humanoid Robots Mirroring Social Cues*, HRI'24 companion — robots
  producing social cues (the production-only baseline we extend).
  https://dl.acm.org/doi/10.1145/3610978.3640580
- Admoni & Scassellati (2017), *Social Eye Gaze in HRI: A Review* — gaze/joint-attention as
  perceived and produced social cues. https://dl.acm.org/doi/pdf/10.5898/JHRI.6.1.Admoni
- Mehrabian (1971), *Silent Messages* — lean as the interest/immediacy cue (relation #8 / the
  robot's lean-in).
- Project internal: `PROJECT_HANDOFF.md §3` (the 11 relations), `FORM_DECISION.md` (the body),
  `INTERACTION_DESIGN.md §2` (steering in the grammar).
