# Interaction Design — Delegating to, and Reading, the Noticing Sidekick

Companion to `PROJECT_HANDOFF.md`. This doc designs the **HCI/HRI layer** that the
handoff calls weak: how a person *delegates* the act of noticing to the sidekick, and
how the sidekick *expresses* what it is doing back to the person. It also derives, from
that interaction, **why the body is a pan-tilt one-eye head** — the answer to "why are
you prototyping with this thing?"

Design intent: keep everything in service of **Notice Delegation**. Expression exists to
make delegation legible and trustworthy, not to make the robot a character. Disney-style
life is borrowed for *legibility and warmth*, but rationed hard so the agent stays a
**considerate observer**, not a needy pet. Last updated: June 2026.

---

## 0. The one design principle (read this first)

> **The robot has exactly two things to communicate: *where its attention is* and
> *what state of noticing it is in*. Every motion, light, and sound must serve one of
> those two. Nothing is decorative.**

This single rule keeps us on the right side of the Disney balance. Disney Research robots
(BlueDot, the "comprehensive cute" lineage) are charming because their motion is *legible*
— anticipation, follow-through, eye contact tell you what the character intends. But that
lineage also tends toward **constant, attention-grabbing animation**, which for a noticing
agent would be exactly wrong: a thing that fidgets for your attention cannot also be the
thing you delegate attention *to*. So we take Disney's **legibility** and refuse its
**busyness**. Stillness is the default and the personality.

Two channels carry the two messages, and keeping them separate is the core move:

| Channel | Carries | Why separate |
|---|---|---|
| **Head (pan-tilt)** | *Locus of attention* — where it is looking | This is the joint-attention organ. You must be able to read its gaze direction like you read a person's. |
| **LED antenna** | *Inner state / arousal* — searching, caught something, confused, resting | Affect that should NOT move the gaze. If state rode on the head, "I'm excited" and "I'm looking there" would collide. |

Sound is a **third, sparing channel** for the single most important event (a catch), because
the person is often not looking at the robot when it matters.

This head=attention / antenna=affect split is also the cheapest way to be expressive: it
lets a 2-DOF head plus one RGB LED cover the whole emotional range without adding joints.

---

## 1. The interaction loop

```
   ┌──────────────────────  DELEGATE  ──────────────────────┐
   │  person tells it, in plain words, what's worth noticing │
   │  + (optional) steers / corrects in the moment           │
   └─────────────────────────────────────────────────────────┘
                              │
                    READ-BACK (confirm understanding)
                              │
        ┌──────── the robot's own noticing loop ───────┐
        │   REST → SEARCH → ORIENT → NOTICE → REPORT    │
        └───────────────────────────────────────────────┘
                              │
   ┌──────────────────────  ACKNOWLEDGE  ───────────────────┐
   │  person sees the report later; marks "yes / not this"  │
   │  → feeds back into what it watches for                 │
   └─────────────────────────────────────────────────────────┘
```

Delegation is not a one-shot command; it is a **relationship of trust maintained over
time** — set it, watch it work, correct it, let it learn your taste. The three depths
below are the design of that relationship.

---

## 2. The delegation channel (human → robot)

Today delegation = editing `context.txt`, and the planner re-plans when the text changes.
That mechanism is right; what is missing is the **human-facing ritual** around it. We
design three *depths* of delegation, each heavier than the last, so the everyday case is
effortless and the rare case is possible.

### Depth 1 — Set the watch (the brief)
A single plain-language sentence: *"I'm away for a while; watch who comes to my desk and
what they do."* This is the existing `context.txt` → `planner.py` path. Two ways in,
matched to a *placed, mostly-silent* agent:

- **Type it** (phone/laptop web UI; `attention_ui.py` already exists) — the default,
  because the brief is something you compose deliberately, like leaving a note.
- **Say it** when you place it down — a "briefing" moment. Voice is for the *handoff*,
  not for ongoing control, so the robot never feels like a voice assistant you must talk at.

Design rule: **the brief is a note you leave, not a conversation.** You delegate and walk
away. That "place it, brief it, leave" gesture *is* the product.

### Depth 2 — Steer in the moment (correct without re-briefing)
When the robot is watching the wrong thing, you need a *lightweight nudge*, not a new
paragraph. Three minimal affordances, in priority order:

1. **"Not that" dismissal** — a single gesture/tap that means *this kind of moment isn't
   worth it*; it lowers the weight of whatever relation just fired (feeds the habituation
   gate the system already has). This is the most important steering act and must be
   one motion.
2. **Point-to-redirect** — you look/point at a region or object; the robot orients there
   and biases its watch toward it. This reuses the gaze/pointing relations (rows 1 & 4)
   *as an input device* — elegant, because the same perception that detects joint attention
   lets you establish joint attention *with the robot*.
3. **Tune the patience** — one physical control (a knob / two buttons) for *how eager*:
   from "only the obviously big stuff" to "tell me more". This maps to the cooldown /
   habituation threshold. A physical knob keeps the calm-vs-eager tradeoff in the person's
   hands, literally.

### Depth 3 — Teach by feedback (taste over days)
On each recorded moment the person marks **keep / not-this** (already implied by the
records UI). Aggregated, "not-this" marks down-weight relations or targets; "keep" marks
confirm them. Over a week the watch-spec drifts toward the person's actual taste **without
re-briefing**. This is the longitudinal hook the HRI study wants, and it is the concrete
sense in which the criterion is "yours, and rewritable."

### The read-back ritual (the trust hinge)
The biggest gap today: after you brief it, **you have no idea what it heard.** Before it
starts watching, the robot must *play back its understanding* so you can correct a
misread before you walk away:

- **On screen:** one line — *"Watching for: people approaching the desk, and handling
  things on it."* (the planner's watch-spec rendered to plain English).
- **On the body:** a short **orienting sweep** — it pans across the things it will watch
  (the desk, the door) and gives one settle-nod, as if to say *"these, got it."* This turns
  an opaque JSON spec into a legible, embodied promise. It is also the cheapest, most
  convincing demo of the whole concept: you say a sentence, and a head turns to look at the
  right things.

Read-back is itself a manipulable **study condition** (read-back vs none → trust/calibration).

---

## 3. The robot's expressive vocabulary (robot → human)

Organized by the **noticing state machine** (extends the current SCAN→WATCH loop). For each
state: head behavior, antenna behavior, sound, and the message. Keep the inventory small —
seven states, each unmistakable.

| State | Head (attention) | LED antenna (affect) | Sound | Message |
|---|---|---|---|---|
| **REST** | still, slightly down, servos relaxed | slow dim breathe (~6 s), warm white | — | "I'm here, off-duty, not watching you." |
| **LISTEN** (taking brief) | rises to level, faces you | gentle steady glow | soft rising chirp on start | "I'm taking this in." |
| **READ-BACK** | orienting sweep across watched targets + settle-nod | one confident pulse per target | — | "Here's what I'll watch — these, right?" |
| **SEARCH** (scanning) | slow, even pan-tilt sweep | slow cool breathe (calm, low arousal) | — | "On duty, nothing yet." |
| **ORIENT** (something rising) | smooth turn toward the candidate; *holds* | breathe quickens, brightens | — | "Something over here." |
| **NOTICE** (a catch) | quick settle on it + **single nod** | brief bright flutter, then hold | one short chirp (the only loud cue) | "Got one — worth noticing." |
| **WATCH/HOLD** (story open) | stays on the moment, micro-tracks | steady bright, slow pulse | — | "Still watching this unfold." |
| **CONFUSED/LOST** (tracking dropped) | small slow side-to-side scan | amber, irregular slow blink | — | "I lost it / I'm unsure." |

Design notes that keep this on the right side of cute:

- **One nod per catch, never repeated.** The nod is the signature gesture (dip-and-return,
  already in `rig.nod()`). Its scarcity is what makes it read as *acknowledgement* rather
  than tic. Anticipation + follow-through on that single nod (ease in, overshoot slightly,
  settle) is where we spend the "Disney" budget.
- **The antenna does the emoting so the head doesn't have to.** Arousal lives in light, not
  in extra wiggles. This is why we can stay expressive with only 2 DOF.
- **CONFUSED is a feature, not a failure.** A robot that *legibly admits* uncertainty
  (amber, hesitant scan) is trusted more than one that fakes confidence — and it invites a
  Depth-2 point-to-redirect. Honesty about perception limits is part of the personality.
- **Amber = "I'm unsure," never red.** Red reads as alarm/recording and would make a
  considerate observer feel like a surveillance camera. Palette stays warm white / cool
  white / amber.
- **Habituation has a body.** When a relation has fired too often and the gate mutes it,
  the antenna gives a *smaller, dimmer* acknowledgement and no sound — the robot visibly
  "stops being impressed" by the routine. This is the Gricean Quantity maxim (don't report
  the obvious) made physical, and it is the anti-overwhelm mechanism in plain sight.

### The anti-overwhelm budget (operational rules)
1. **Signal only on state transitions.** Within a state the robot is still. No idle
   animation loops.
2. **At most one sound per noticed moment**, and only for NOTICE. Everything else is silent.
3. **Idle is genuinely idle:** dim, low, relaxed servos (firmware already auto-relaxes).
   A resting robot is reassuring; a fidgeting one is not.
4. **Repeats fade.** Habituation lowers the cue intensity for recurring moments
   automatically.
5. **No face, no speech-out, no eyes-that-follow-you.** It looks where the *moment* is, not
   where *you* are. That restraint is what separates "considerate observer" from "thing
   staring at me."

---

## 4. Why the body is a pan-tilt one-eye head (form justification)

The form should be *derived* from the interaction, not chosen first. Here is the derivation,
which is the defensible answer to "why this prototype, not a robot arm / humanoid / OriHime
/ a static camera?"

### What Notice Delegation *requires* of a body
| Requirement (from the interaction above) | What it forces the body to have |
|---|---|
| **R1. Legible locus of attention** — you must read *where it is looking* at a glance | A single, directional regard — a "gaze" you can follow → **one eye + a head that aims** |
| **R2. Joint attention** — read it (relation #2) *and* establish it (point-to-redirect, read-back sweep) | The head must be able to **orient along a sharable vector** → pan-tilt |
| **R3. Acknowledgement** — a clear "I noticed" without saying anything | A legible head **nod** + an affect light |
| **R4. Honest non-action** — it *notices*, it does not *act on the world* | A body with **no manipulators, no locomotion** — it cannot grab, only look |
| **R5. Low social over-promise** — must not imply a full social peer it cannot be | **Minimal, abstract** form — not a face/person |
| **R6. Calm placed presence** — sits in a shared space, mostly still | Small, stationary, **relaxable** servos; quiet |

### Scoring the candidate forms against R1–R6
| Form | R1 gaze | R2 joint-attn | R3 nod | R4 non-action | R5 no over-promise | R6 calm | Verdict |
|---|---|---|---|---|---|---|---|
| **Pan-tilt one-eye head** | ✅ one clear regard | ✅ orients along a ray | ✅ tilt nod | ✅ can't act, only look | ✅ abstract, not a person | ✅ small, relaxes | **Best fit** |
| Robot arm | ⚠️ "gaze" ambiguous | ⚠️ points but reads as reaching | ⚠️ | ❌ reads as *will grab/act* | ⚠️ industrial | ⚠️ | Wrong affordance: implies *doing*, not *noticing* |
| Humanoid / android | ✅ | ✅ | ✅ | ❌ implies it can act | ❌ over-promises a social peer; uncanny | ❌ | Over-promise + cost; the "comprehensive cute" trap |
| OriHime-style telepresence | ✅ | ⚠️ | ⚠️ | ✅ | ❌ reads as *a remote person*, not an agent of yours | ✅ | Wrong concept: telepresence ≠ delegated autonomous noticing |
| Static camera / screen | ❌ no readable gaze | ❌ can't share attention | ❌ | ✅ | ⚠️ reads as **surveillance** | ✅ | Fails the social/legibility core; becomes a CCTV |

### The argument in one paragraph (use this when challenged)
> Notice Delegation needs a body whose **attention you can read and share**, that can
> **acknowledge**, and that is **honest about only watching** — not acting. A pan-tilt
> one-eye head is the *minimal* body meeting all of these: the single eye plus an aiming
> head gives a legible, sharable gaze (joint attention is literally the point); the tilt
> gives a nod; and the **absence of hands and wheels is not a limitation but the honest
> signal of the concept — it notices, it does not act.** Richer bodies (arm, humanoid,
> telepresence) don't add noticing ability; they add *action* affordances and *social
> over-promises* that fight the concept, plus uncanniness and cost. A static camera fails
> the other way: no readable gaze, so it can't do joint attention and reads as
> surveillance. The pan-tilt one-eye is therefore not a placeholder — **it is the form the
> concept argues for.** The one thing it is missing is a dedicated *affect* channel, which
> is exactly why the next prototyping step adds the **LED antenna** (Depth-0 of the
> expressive split above).

### What this implies for the eventual "real form" (the next decision)
- **DOF:** 2 (pan + tilt) is sufficient and *should not grow* — extra joints buy expression
  the antenna already provides, at the cost of legibility and calm. Resist arms.
- **The eye:** keep it singular and clearly the camera — the regard must be honest (it sees
  from where it looks).
- **The antenna (already on the rig):** an LED on a short stalk above the eye — see the
  current prototype photo, the cyan stalk-light. The stalk matters: secondary motion (a
  slight lag/settle of a flexible stalk) is the cheap Disney "life." Next step is only to
  drive it by *state* (RGB + patterns per §3), not just on/off.
- **Posture:** a slight resting down-tilt ("at ease") and a rise-to-level on LISTEN gives a
  whole personality from one axis.
- **Optional, only if a study needs it:** a base that can slow-rotate to "wake up / face
  you" — but evaluate whether the pan already covers it before adding a third axis.

---

## 4B. Form grammar — proving the *shape* (head, eye, antenna, neck, base)

§4 argued *body class* (pan-tilt one-eye, not arm/humanoid/cam). This section answers the
harder, more specific question — **why this exact shape, and why not more joints** (the
Pixar/Luxo-lamp challenge: a neck that leans in closer, or curls back to withdraw). The
goal here is a *proof*, not a preference: a single test that every part and every degree of
freedom must pass, then run each candidate feature through it.

### The sketch vs the prototype — and which one is right
Two reference images: the **prototype** (one camera lens = one eye, one stalk LED = antenna,
an aiming head on a planted base) and a **hand sketch** (two big eyes, a nose, a mouth-grille
— a *face*). They pull in opposite directions, and the concept decides the winner:

> The sketch reaches for **character** (a cute face). The concept demands **honesty** (the
> eye must *be* the sensor). When those conflict, honesty wins — so the prototype's single
> lens-eye is *more correct* than the friendlier sketch. The shape is unclear right now
> precisely because it is still half-pulled toward "face." Commit to the honest grammar and
> the shape becomes self-explaining.

### The admission test (the whole proof in one rule)
> **A part or degree of freedom is admitted only if it makes one of the two messages —
> *where attention is* or *what state it's in* — more legible, AND it does not (a) imply
> acting on / intruding into the world, (b) over-promise a social peer, or (c) merely
> duplicate a cheaper channel.**

That's it. "Legible-but-honest." Everything below is just turning the crank on this test.

### What passes — the form grammar (5 rules)
| Part | Carries | Why this shape (passes the test) |
|---|---|---|
| **One eye = the camera** | attention (honest gaze) | The eye must *be* the sensor, so "where it looks" literally equals "what it sees." A second/decorative eye would let the face point one way while the real sensor faces another — a *lie about its gaze* that breaks joint attention. One honest eye, not two. |
| **One antenna (stalk LED)** | state / life | Gives "a creature with attention" without a face. A flexible stalk adds living secondary-motion. This is the channel that rescues the bare lens from reading as a CCTV — the minimum that is both honest *and* warm. |
| **2 DOF head: pan + tilt** | attention locus | Fully spent encoding the gaze vector — the irreducible minimum for readable + sharable attention. Tilt doubles as the nod. Nothing wasted, nothing extra. |
| **A short neck (not articulated)** | — | Just enough to read as "a head that *turns to look*." A long, jointed neck would read as "a body that *reaches / leans / looms*" — an action affordance. Short on purpose. |
| **A planted, stable base** | honesty guarantee | Low, rooted, clearly not mobile: "I'm *placed*, I won't roam or follow you." The base makes the promise *it cannot come closer* physically visible. |

No mouth, no nose, no second eye: a mouth implies speech it doesn't have and pushes the
whole object toward "social peer" (fails test-b, the uncanny/over-cute trap). The expressive
load lives on antenna + head, never on a face.

### What fails — including the Luxo-lamp joints (the part you asked about)
| Proposed addition | What it would buy | Verdict via the test |
|---|---|---|
| **2nd eye / full face** (the sketch) | cuter, more "alive" | **Reject.** Fails (b) over-promise, and a decorative eye fails the *honest-gaze* requirement outright. |
| **Lean/extend neck to control distance** (get closer to inspect) | physical proximity to an object | **Reject — and this is the core answer.** A noticing agent does **not need** physical proximity (resolution is digital, it isn't manipulating anything). Worse, *moving closer to a person/object is itself a social action* — it is literally relation #7 "approach," the thing the robot is built to **detect in others**. If the robot approaches, it stops being an observer and becomes a participant; in a shared space a camera that leans into your zone reads as intrusion/surveillance, the opposite of "considerate." Fails (a) decisively, and (c) — arousal is already on the antenna. |
| **Curl back / retract into itself** ("off-duty", Luxo withdraw) | a legible "I've stopped watching" | **Reject for now (the closest call).** It *is* legible — but REST already says off-duty more cheaply: dim antenna + down-tilt + relaxed servos. Adding a withdraw-joint duplicates that (fails c) *and* imports the Luxo problem below. Keep as the **one** future joint worth a study *only if* field testing shows REST is not read as "off." |
| **Base yaw (slow rotate to wake / face the room)** | wider attention range | **Defer, don't reject.** This is the *only* candidate that still encodes pure attention-locus (not action), so if any joint is ever added, it's this one — and only if pan range provably can't cover the placement. Evaluate empirically first. |

### Why "borrow Luxo's joints" is the wrong instinct (name it explicitly)
Luxo Jr. is the patron saint of expressive articulation — but Luxo is a **performer**: its
entire purpose is to emote and to *act* (it hops, it nudges the ball). That is the exact
opposite stance from a **considerate background observer**. Borrowing Luxo's neck imports
Luxo's *neediness* — a body that articulates to perform aliveness is a body that demands you
watch *it*. Our agent must be watch-*able* on demand and ignorable by default. So we take
from animation only what survives the test — **legible gaze + one sparing nod + a living
antenna** — and we refuse the performing body. Restraint isn't a hardware budget; it is the
physical guarantee of the concept: *a body that literally cannot approach, reach, or perform
is the body you can comfortably delegate noticing to and then forget about.*

### The one-paragraph version (use when challenged on shape)
> Every part of this robot earns its place by one rule: does it make *where I'm looking* or
> *what state I'm in* more legible, without implying that I act on the world or that I'm a
> person? One honest eye (the sensor itself), one antenna for life, and two head axes for a
> sharable gaze pass that test exactly — nothing is missing and nothing is decorative. More
> joints fail it: a leaning/extending neck means *approach*, which is a social action the
> robot is meant only to *observe*, not perform; a retract-to-hide joint just duplicates what
> the resting pose and dimmed antenna already say; a face over-promises a peer it cannot be.
> The planted base and the un-jointed short neck aren't limitations — they are how the
> robot *physically guarantees* its central promise: it notices, it never intrudes. That is
> why this shape, and not a Pixar lamp, is the right body **for now**.

---

## 5. Hooks for the HRI / MDR1 study
The design above hands the study three clean, manipulable conditions:
1. **Legible movement vs muted** — orienting + nod + antenna ON vs a static camera that only
   logs. Tests whether *embodied legible attention* changes trust/usefulness (core claim).
2. **Read-back vs none** — does the embodied promise improve trust calibration and reduce
   "what is it even doing?" anxiety.
3. **Steerable taste vs fixed** — Depth-2/3 on vs a frozen brief. Tests the "yours and
   rewritable" claim — the differentiator from proactive/assistant robots.

Field-first (per MDR1): place it in the shared lab, brief it for real situations, watch real
reactions to the orienting/nod/antenna; the discussion is whether people *read* the cues as
intended and whether restraint reads as "considerate" or "dumb."

---

## 6. Concrete next prototyping steps
1. **Wire the LED antenna** (one RGB LED, e.g. WS2812 on a spare pin; extend
   `pantilt_r4.ino` with an `led <state>` command and `rig.py` with `set_state()`). Map the
   eight states in §3 to light patterns. Highest value / lowest cost.
2. **Build read-back:** render the planner watch-spec to one plain-English line in
   `attention_ui.py`, and add a `rig.readback(targets)` orienting-sweep + settle-nod.
3. **Add the "not-that" dismissal** as a single tap in the records UI → feed the habituation
   gate (Depth 2.1). One control, biggest steering payoff.
4. **Add the patience knob** (two buttons → cooldown/threshold) if hardware allows; else a
   UI slider.
5. **Refine the nod** with anticipation/overshoot/settle in `rig.nod()` (the one place to
   spend "Disney").
6. Then, with the interaction legible, run the field placement and decide the final
   enclosure/posture per §4.
