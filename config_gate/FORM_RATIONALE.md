# Form Rationale — Why a Pan-Tilt One-Eye Head, and Not More

Companion to `INTERACTION_DESIGN.md` and `PROJECT_HANDOFF.md`. This doc answers the form
question directly: *what shape, how many joints, why this and not a Pixar-lamp / dog /
humanoid / arm* — and gives a **decision rule** you can defend in a review and reuse when
you finalize the enclosure. The current prototype (gray one-lens cube head + one RGB LED on
a stalk + 2-servo pan-tilt bracket) is treated as the hypothesis to prove, not assumed.

The argument has three parts: (1) a **verb test** that sorts the big robot archetypes,
(2) a **DOF-justification rule** that decides every joint, and (3) the **counterexample
rebuttal** (the Pixar lamp / telescoping idea) that the rule must survive. Last updated: June 2026.

---

## 1. The verb test — every body shape *speaks a verb*

Robot-appearance taxonomies sort bodies by how human-like they look — Fong et al. (2003):
**anthropomorphic / zoomorphic / caricatured / functional**; DiSalvo et al. (2002): a head
trades off **humanness / productness / robotness**. Those tell you how people *read* a form,
but not which form your *concept* needs. For that, sort archetypes by **kinematics**, because
a body's joints commit it to a dominant action — the verb a person reads the instant it
moves, before any behavior is programmed. Dragan & Srinivasa's legibility result is the
reason: people infer a mover's **goal from its motion** (action-to-goal). So the kinematics
*are* the first message, whether you intend them or not.

| Kinematic archetype | What its joints are organized to do | The verb people read | Appearance class (Fong) |
|---|---|---|---|
| **Head / gaze turret** (pan-tilt) | aim a regard | **"it looks / attends"** | caricatured–functional |
| **Legged / dog** (servo legs) | locomote, take posture | "it goes / roams / approaches" | zoomorphic |
| **Humanoid / torso** (arms + head) | do what a person does | "it is a someone" | anthropomorphic |
| **Arm / lamp** (serial reach chain, incl. Luxo/ELEGNT) | reach, point, translate toward things | **"it reaches / acts on"** | functional (expressive) |
| **Mobile base** (wheels) | drive through space | "it patrols / navigates" | functional |

Now state the concept's verb. **Notice Delegation's verb is *attend* — to look, to register, to
acknowledge — and explicitly *not to act on the world*** (`INTERACTION_DESIGN.md` R4:
"honest non-action"). Exactly one archetype's kinematics already speak that verb without
being told to: the **head / gaze turret**. Every other archetype speaks a *different* verb
that you would then have to spend design effort *suppressing*:

- A **dog/legged** body says "I roam" — but a noticing agent is **placed**, not roaming;
  mobility re-imports the surveillance reading (it decides where to be) and the approach verb.
- A **humanoid** says "I am a someone" — over-promising a social peer it cannot be (uncanny,
  costly), and implying it can *act*.
- An **arm/lamp** says "I reach toward things" — the manipulation/approach verb, which (see §3)
  is precisely the verb the concept must not have.
- A **mobile base** says "I patrol" — CCTV-on-wheels, the surveillance reading the concept
  works hardest to avoid.

**Conclusion of the verb test:** the pan-tilt one-eye head is not the *minimal* body by
accident or budget — it is the *only* archetype whose intrinsic kinematics **are** the
concept's verb. You are not fighting the form; the form already says "I look." That is the
defensible answer to "why this shape."

---

## 2. The DOF-justification rule — deciding every joint

Within the chosen archetype, decide each degree of freedom by a single test:

> **Add a DOF only if it (a) extends *where attention is* to a place the current joints can't
> reach, or (b) carries a *noticing-state* the antenna + motion-timing can't already carry —
> AND it does not import a new verb (reach / approach / roam).**

Two facts make (b) almost always answerable *without* new joints:

- **Affect rides on light + timing, not on extra joints.** The LED antenna carries arousal
  (your prototype already glows cyan for "on duty"), and ELEGNT shows the *same* motion can
  read calm or excited purely by **speed / sharpness / pauses** — high-arousal = quick sharp,
  calm = slow smooth. So you get the full emotional range from 2 DOF + 1 LED by modulating
  *how* the head moves, not by adding *where* it can move.
- **Perception doesn't need translation.** A room-scale camera with computational/optical
  attention doesn't need to physically move closer to see better (the handoff already
  resolved "no depth camera needed" — gaze is a 2D ray). So there is no *functional* reason
  to add a leaning or telescoping joint.

Applying the rule to candidate joints:

| Candidate DOF | Serves attention-locus? | Serves a state the antenna can't? | Imports a bad verb? | Verdict |
|---|---|---|---|---|
| **Pan** | ✅ aims regard horizontally | — | no | **Keep** |
| **Tilt** | ✅ aims vertically + gives the nod | ✅ the acknowledgement nod | no | **Keep** |
| **Lean-in / telescoping toward an object** | ❌ (zoom is optical) | ❌ (arousal = antenna/timing) | ❌ **"approach / reach"** | **Reject** (see §3) |
| **Retract / withdraw into base** | ❌ | ~ "going off-duty / giving privacy" — but head-down + antenna-dim already says this | mild | **Defer** — antenna+posture is cheaper |
| **Base yaw** (beyond pan range) | ✅ only if one placement must cover >120° | — | mild (toward "patrol") | **Defer** — first try repositioning / a second placed unit |
| **Legs / wheels** | ❌ | ❌ | ❌ "roam / patrol" | **Reject** — breaks "placed agent" |

Result: **2 DOF (pan + tilt) is the justified set *for the background watching job*.** Growth
is gated by the rule, not by ambition. **⚠️ See §7 — this rule is amended:** it was applied too
uniformly. More joints *are* justified for the **foreground engagement phases** (turning to
face you, recounting a story). §7–§8 supersede the "2 DOF is enough" conclusion.

---

## 3. The counterexample rebuttal — the Pixar lamp / telescoping idea

This is the strongest objection and must be met head-on, because Apple's **ELEGNT** (2025)
is exactly a Pixar-Luxo lamp with a **6-DOF arm** that leans, reaches, and retracts to
convey "attention, attitude, expression" — and it *works*. So why shouldn't the sidekick
get those joints to lean closer to an object or shrink back into itself?

Three reasons, in order of force:

**(1) The lamp's reach serves its *function*; yours doesn't.** A lamp's job is to put light
(or a projection) **onto a spot** — so translating toward the spot is functional; the
expressive lean is the *same motion* its job already requires. The sidekick's job is to
**perceive**, and a camera perceives the whole scene from where it sits without moving
closer. The lamp earns its reach joints functionally; a noticing camera does not. Borrowing
the lamp's joints would be borrowing its *form* without its *function* — decoration, which
§0 of the interaction doc forbids.

**(2) A lean-in joint makes the robot *perform the relations it is supposed to observe.***
This is the decisive, project-specific point. Your relation vocabulary already names
**approach (#7)** and **lean-in (#8)** as *human social signals the robot detects*. If you
give the robot a body that leans and approaches, it now **emits** those very signals — and
the figure/ground collapses: is that lean the robot *noticing*, or the robot *participating
in* the moment it should be quietly registering? A noticing agent must stay legibly on the
**observer** side of the relations it watches. Translational/approach DOF moves it across
that line. Pan-tilt + nod cannot be confused with approach or lean-in, so it keeps the robot
unambiguously an observer.

**(3) Legibility cuts against it.** Dragan's result: motion is read as **action-to-goal**.
A head that *orients* toward a thing reads as "attending to it." A body that *translates*
toward a thing reads as "going for it" — intent to act. For an agent whose whole promise is
"I notice, I don't act," translational motion is not just unnecessary, it actively
**mis-states the intent**. The antenna and the nod let you express arousal and
acknowledgement *without* ever generating an action-to-goal reading.

So the lamp is the right inspiration for **one** thing — *expressive timing on a
non-anthropomorphic body* — and the wrong inspiration for **kinematics**. Take ELEGNT's
lesson (modulate speed/sharpness/pauses for affect) and apply it to the pan-tilt head;
**reject** its reach joints. That is a precise, citable position, not a hand-wave: *same
expressive principle, different verb, therefore different joints.*

> **One-paragraph version for a reviewer:** "We considered an expressive multi-joint body in
> the Pixar-lamp lineage (cf. Apple's ELEGNT). We adopt its expressive-timing principle but
> reject its reach kinematics, for three reasons: a camera's function needs no translation
> to perceive (unlike a lamp's need to aim light); a leaning/approaching body would make the
> robot *emit* the approach and lean-in relations our system exists to *observe*, collapsing
> observer into participant; and translational motion reads as intent-to-act (Dragan's
> action-to-goal legibility), contradicting the concept's 'notices, does not act' promise.
> Pan-tilt is therefore the kinematic set whose every motion stays on the observer side."

---

## 4. The head itself — resist the face (a note on your sketch)

Your sketch gives the head **two big eyes, a nose, and a mouth grille**; the built prototype
has **one lens**. The taxonomy says keep the prototype's single eye and resist the sketch's
face:

- DiSalvo's dimensions: a mouth + two eyes + nose pushes the head toward **humanness**, which
  re-introduces the social over-promise the whole concept avoids — and invites the uncanny.
- A **single lens-as-eye is the most honest possible signal**: it sees *from exactly where it
  looks*, so its gaze direction is literally its perception direction. Two decorative eyes
  imply binocular human seeing the camera doesn't do, and a mouth implies speech it won't
  produce. Honesty about what it is = trust (and it keeps it on the "considerate observer,
  not surveillance" side).
- Character without a face comes from the **antenna + the legible nod + at-ease down-posture**
  — the same channels from `INTERACTION_DESIGN.md §3`. That is the caricatured-functional
  sweet spot: enough life to be warm, not enough to pretend to be a someone.

Recommendation: one honest eye (the lens), one expressive antenna, a readable head. The
googly-eyed face is the "comprehensive cute" trap; the prototype's restraint is more on-concept.

---

## 5. The decision rule, kept for when you finalize the form
When you build the "real" enclosure, run each proposed feature through this checklist:
1. **Verb check** — does this feature make the body say "look/attend," or does it import
   "reach / roam / be-a-someone"? If the latter, cut it.
2. **DOF rule** — does the joint extend attention-locus, or carry a state the antenna/timing
   can't? If neither, cut it.
3. **Honesty check** — does the feature imply a capability the robot lacks (binocular sight,
   speech, manipulation, mobility)? If yes, cut it.
4. **Restraint check** — does it animate when idle / beg attention? If yes, cut it
   (`INTERACTION_DESIGN.md §3` anti-overwhelm budget).

Anything that passes all four is on-concept; anything that fails is the form fighting the idea.

---

## 7. CORRECTION — attention is asymmetric in time (this amends §1–§2)

§1–§2 above made one wrong move: they applied "stay minimal / stay still" **uniformly across
time.** But the person's attention *to the robot* is not uniform. The interaction happens in
short, sharp **engagement phases** — you arrive, you brief it, you tiny-adjust it, you receive
a story — separated by long **background phases** where you are working and ignoring it. The
restraint argument is right **only for the background.** In an engagement phase the person is
looking straight at the robot, and there **more joints and more action genuinely raise
legibility** (Cassie's point — correct). So "more DOF = more legible" and "stay minimal" do
not conflict; they govern *different regimes*. Engagement itself is a known phased process —
initiation → maintenance → disengagement (Sidner & Rich) — so designing for phases is standard.

There is a second axis the earlier sections missed. **"Attend" has two targets:** the **scene**
(the watching job) and the **person** (engagement). §1–§3 only designed attending-to-scene
(pan-tilt at the room). Attending-to-*person* — turning to face you, looking between you and
the thing it caught, bowing to hand over a story — is a *different* expressive job and may
fairly want its own joints. This is the 2×2 the form should be designed against:

| | **Attend to SCENE** (the job) | **Attend to PERSON** (engagement) |
|---|---|---|
| **BACKGROUND** (you're working) | pan-tilt watch, antenna calm — **minimal** (the original rule, still right) | **nothing** — do not bid for attention |
| **FOREGROUND** (you're engaged) | show what it's watching: read-back sweep, recap a story's location | **turn to face you, gaze hand-off, bow/greet — RICH; here extra DOF earn their keep** |

The bottom-right cell is the one §1–§2 wrongly suppressed. **Jibo is the existence proof:** a
*stationary* tabletop robot with a **3-DOF body** whose extra axes exist for nothing but the
foreground — it turns to face you, looks between you and the tablet, strikes poses while
speaking — and never locomotes or reaches. Its joints raise engagement legibility while
staying fully on the "attend/engage" verb. That is exactly the move Cassie is asking for.

**The upgraded DOF rule** (replaces §2's): *Add a joint if it serves attending — to the scene
**or to the person** — in a way the existing joints + antenna + timing can't; it must (a) fall
still in the background, and (b) keep the verb "attend/engage," never "reach-for-object" or
"roam."* Note this rule **still rejects the lean-toward-an-object** of §3 (that is scene
*participation* = relations #7/#8) while it now **welcomes** a lean/turn **toward the person**
(that is engagement). The Pixar-lamp expressivity isn't banned — it is **redirected from the
object to the person.** That single distinction reconciles everything.

**New foreground stages to design for** (the "maybe more stages" intuition), mapped to the
engagement phases: **GREET** (you return / approach — it rises and faces you), **BRIEF**
(delegate), **STEER** (adjust — gaze hand-off between you and the target), **RECOUNT/DELIVER**
(it turns from the scene to you and recaps the caught moment — the receive-a-story stage made
embodied), **DISENGAGE** (you leave — it settles back to watching). These are where articulation
pays off; `INTERACTION_DESIGN.md §3`'s seven states were the *background/scene* half — this is
the missing *foreground/person* half.

---

## 8. A MENU OF RICHER FORMS (more ideas, all still on-concept)

The pan-tilt one-eye is a *floor*, not the answer. Here are fuller bodies that add foreground
articulation, each kept honest by §7's rule (still in background, verb = attend/engage). They
compose — pick a column or stack them.

**8a. Turning body — "desk owl" (head + body-yaw, ~3 DOF, Jibo-class).**
A head that pans/tilts to watch, on a trunk that **rotates to face you** in engagement. This
is the single highest-value addition: it unlocks the entire attend-to-*person* column. Watch
the scene with the head; pivot the whole body to GREET, to do gaze hand-off during STEER, and
to RECOUNT facing you. Background: trunk dead still, head watches. Verb stays "attend" (to a
person now), never reach. *Recommended first step.*

**8b. Articulated neck / bow — "the lamp that listens" (~3–4 DOF).**
Reclaims the Luxo silhouette Cassie likes, but the neck **bows toward the *person*** to hand
over a story ("here — I saw this") and **reclines** to rest/off-duty. Same expressive joint as
ELEGNT's reach, verb redirected from object to person. Serves RECOUNT and DISENGAGE vividly.
Risk: a bow toward the *scene* would re-trigger the §3 problem — so the bow must be
person-directed only.

**8c. Posture / height stalk — telescoping, done right.**
The extend/retract Cassie raised, anchored to *engagement level* not reach: it **rises to
"alert / attending you"** when you approach (a proxemic greeting — the robot performing
relation #5/#7 *toward you*, which is welcome, vs *toward the scene*, which isn't) and **sinks
to a low crouch** while quietly watching. Height encodes how engaged it is. Cheapest "alive"
signal after the antenna.

**8d. Expressive ear/antenna pair.**
Promote the single LED stalk to **two small perk/droop antennae** (one micro-servo each, or a
shared one). They **perk** on a catch and during engagement, **droop** at rest — carrying
attention-bid and affect with creature-legibility, no face required. Pure foreground/affect;
dead still in background. Lowest cost, high charm, zero verb risk.

**8e. Keep across all:** the **single honest eye** (§4) and the **acknowledgement nod**. None
of the above needs a second eye or a mouth.

**Suggested staging (make → try → make again):** add **8a body-yaw** first (it opens the whole
person column and is Jibo-proven) → then **8b bow** *or* **8c rise** for RECOUNT/GREET → then
**8d ears** if budget allows. Test each against §7: does it stay still while you're working?
does every motion still read as "attending you," not "reaching for that"? If yes, the extra
joints are buying legibility, exactly as Cassie argued.

> **Net position now:** the pan-tilt one-eye is the *minimum viable* noticing body and a fine
> MVP; it is **not** the ceiling. A *stationary, articulated* body (≈3–5 DOF) that turns to
> face you and gestures during the brief engagement phases — while going inert in the
> background — is very likely the *better* form, and stays fully on-concept because every
> added joint serves **attending to the person**, never reaching for the scene. The thing to
> reject was never "more joints"; it was "joints that make it act on the world or roam."

---

## 6. What this buys the paper / MDR1
- A **principled form story**: "form follows the concept's verb," with a taxonomy (Fong,
  DiSalvo), a legibility basis (Dragan), and a named counterexample handled (ELEGNT). This is
  exactly the kind of *reasoned design decision* MDR1's "proposed method + prototyping
  iteration" wants — and it pre-empts the "why this prototype?" attack.
- A clean **ablation/condition** if you want it later: pan-tilt-with-nod vs a static camera
  (does directed gaze change trust/legibility?) — and, if a reviewer pushes the lamp idea,
  you have the rebuttal rather than a defensive shrug.
- A **morphology positioning figure** (the verb table) that situates your choice against
  dog / humanoid / arm / mobile-base in one glance.

---

## Sources
- Fong, Nourbakhsh & Dautenhahn (2003), *A survey of socially interactive robots*, Robotics
  and Autonomous Systems — the anthropomorphic/zoomorphic/caricatured/functional taxonomy.
  https://www.cs.cmu.edu/~illah/PAPERS/socialroboticssurvey.pdf
- DiSalvo et al. (2002), robot-head design dimensions (humanness/productness/robotness).
- Dragan, Lee & Srinivasa (2013), *Legibility and Predictability of Robot Motion*, HRI —
  motion read as action-to-goal. https://www.ri.cmu.edu/pub_files/2013/3/legiilitypredictabilityIEEE.pdf
- Apple Machine Learning Research (2025), *ELEGNT: Expressive and Functional Movement Design
  for Non-Anthropomorphic Robot* (6-DOF Luxo-style lamp; affect via motion timing).
  https://machinelearning.apple.com/research/elegnt-expressive-functional-movement
- Breazeal / Jibo — stationary 3-DOF tabletop social robot; extra axes serve turn-to-face and
  gaze hand-off during engagement, never locomotion. https://spectrum.ieee.org/cynthia-breazeal-unveils-jibo-a-social-robot-for-the-home
- Sidner, Rich et al., *Recognizing engagement in human-robot interaction* — engagement as a
  phased process (initiation / maintenance / disengagement); non-verbal bids for attention.
  https://www.researchgate.net/publication/221473126_Recognizing_engagement_in_human-robot_interaction
