# Robot → Master — Feedback for the Six Delegation Actions

The **master-side** counterpart to the robot↔scene work (`INTERACTION_DESIGN.md §3`,
`GRAMMAR_EMBODIMENT.md`). Those designed how the robot *refers to the scene*. This designs how
the robot *acknowledges you*, the person who delegates — the foreground/engagement frame.
Last updated: June 2026.

---

## 0. The one principle: every master action gets a receipt

On the scene side the robot must **never address people** — it only *refers* to a locus
(`GRAMMAR_EMBODIMENT §6`). The master side is the **opposite frame**: here the robot **should
look at you**, because you are talking to *it*. The rule:

> **Every action you take gets an immediate, legible acknowledgement — a *receipt* — so you
> always know your input landed.** Without it, delegation is an act of faith ("did it hear
> me?"). The receipt is what makes the robot feel trustworthy rather than oblivious.

Receipts are built from the **same small vocabulary** as everything else — no new channels:
- **eye-contact (relation #3, the deliberate "robot → you" frame)** = "I register *you*."
- **gaze-follow / orient** = "I'm acting on what you indicated."
- **the nod** = "got it" (acknowledgement; the scarce signature gesture).
- **antenna** = state/affect (warm=at-ease, cool=on-duty, amber=unsure/reset, bright=caught,
  warm-pulse=approval); **antenna tempo** also carries *temperament*.
- **sound, very sparse**: rising chirp = waking/start, descending chirp = sleeping/stop. Nothing else.

And each receipt is tied to a **real change in the task** (the `§7` rule), so the
acknowledgement is never empty theatre — see the last column of the table.

---

## 1. The six actions

| # | Master action | Robot feedback (head / body) | Antenna | Sound | Message | Ties to result |
|---|---|---|---|---|---|---|
| 1 | **START** (place + brief, press go) | **wake-survey**: one slow full sweep of the space it will watch, then **settle facing you + eye-contact + single nod** (this *is* the read-back) | dim→**cool** comes up ("on duty") | rising chirp | "I've taken in the room — on it." | begins capture; the sweep = the watched field |
| 2 | **FIX wrong direction** | **visible release**: break off the wrong locus, a quick **glance back to you** (eye-contact = "my mistake"), then **turn to the corrected direction** + small nod | brief **amber** blip (reset) → back to cool | — | "Not that — *this*. Got it." | changes the captured vantage |
| 3 | **POINT at** (you point/look at a target) | **gaze-follow**: eye-contact to acknowledge you → **track along your point** to the target → settle + slight curious lean + nod. *If no clear target on the ray:* amber + look back at you = "which one?" | cool; **bright flutter** when it locks the target | — | "Following your point… that one." | sets the watch target |
| 4 | **SET personality** active ↔ calm | **show the temperament immediately**: one sample beat at the new tempo — *active* = quicker, snappier scan; *calm* = slow, smooth scan | breathe **rate/brightness** shifts (fast-bright ↔ slow-dim) | — | "This is how eager I'll be now." | changes notice threshold → more/fewer stories |
| 5 | **JUDGE the result** — **keep** | a small **affirmative nod** toward the record / you; pleased | **warm pulse** | — | "Noted — more like this." | reinforces that pattern in the taste model |
| 5 | **JUDGE the result** — **not-this** | a small **downward settle** (a brief abashed dip); visibly *lowers interest* | **amber dim** | — | "Okay — less of that." | down-weights that pattern (habituation) |
| 6 | **STOP task** (stop / pick it up) | **power down attention**: return to **face you + eye-contact + single nod** ("done"), head lowers to at-ease, servos relax | **cool → warm, dim** (off-duty) | descending chirp | "Off duty — no longer watching." | ends capture (privacy receipt) |

---

## 2. Notes on the tricky ones

**START / the 360 (your idea).** A full sweep is the perfect "I'm waking and taking in the
whole space I'll watch" gesture — legible and done **once**, so it reads as a boot ritual, not
a fidget. It also *is* the read-back from `INTERACTION_DESIGN §2`: sweep the field, then settle
on you and nod. *Hardware honesty:* a literal 360° needs the optional **base-yaw** joint; with
pan ±60° alone it can only sweep its reachable field. So either (a) add base-yaw and the 360
becomes a genuine "scan the room awake," or (b) approximate with a wide pan sweep (a partial
"look around"). The base-yaw is justified here for the *same* reason it's justified for
F-formation (`FORM_RATIONALE §8a`) — facing/surveying the whole space — not for reaching.

**FIX.** The important beat is the **visible release of the wrong target** — the master must
*see it let go* of where it was looking. A correction that produces no visible abandonment
feels ignored. The quick glance back to you before re-orienting is the "my mistake" backchannel.

**POINT.** This is the prettiest one because it runs the **grammar in both directions at once**:
the robot *detects* your pointing (#4) / gaze (#1) and *responds* by gaze-following to form
**joint attention (#2) with you**. Build the **ambiguity case** — if your ray doesn't land on a
clear object, it must say "which one?" (amber + look back) rather than silently guessing. Honest
uncertainty here builds far more trust than a confident wrong lock.

**SET personality.** Temperament is **not** a new behavior — it's a *modulation* of the existing
motion (ELEGNT's lesson: speed/sharpness/pauses carry arousal) plus the **notice threshold**.
Active = faster motion + lower threshold (leans at smaller things → more stories); calm = slower
+ higher threshold (only the big stuff). So the knob's effect is felt in the body *and* visible
in the result (more/fewer captures) — a continuous trait with a continuous receipt. No sound,
because it's a state, not an event.

**JUDGE.** Keep the bodily feedback tiny — the screen/records UI does the real marking; the body
just gives the **emotional backchannel** of a creature whose taste is being shaped (a little more
interested, or a little less). This is where the "it's learning what I care about" relationship
becomes felt rather than abstract.

**STOP.** For a *watching* agent this is trust-critical: the master must be able to see it
**actually stop**. The visible "power-down" (face you, nod, dim to warm, relax, descending
chirp) is the privacy receipt — the bookend to START's rising chirp. Never let it stop silently.

---

## 3. Why this stays on-concept (and minimal)

- **Same vocabulary, opposite frame.** Scene side = refer to a locus, never address people;
  master side = address you (eye-contact), because you're the one talking to it. The two frames
  never collide because they're triggered by different events (a scene catch vs. your action).
- **The nod stays scarce.** It appears only as a genuine "got it" (start, fix, point, stop) — a
  few times per session — so it never degrades into a tic.
- **Antenna carries most of the master-side affect** (approval pulse, reset blip, temperament
  tempo), keeping the head free to mean only "where my attention is."
- **Every receipt has a result-tie** (last table column), so none of it is empty animation —
  it obeys the `GRAMMAR_EMBODIMENT §7` "no movement without a receipt" rule.

**Engagement-phase mapping** (`FORM_RATIONALE §7`): START = GREET+BRIEF, FIX/POINT = STEER,
SET = a STEER trait, JUDGE = the ACKNOWLEDGE loop, STOP = DISENGAGE. These six *are* the
foreground/person half that the scene-side seven states (`INTERACTION_DESIGN §3`) didn't cover.

---

## 4. For the build / study
- Wire the receipts onto the existing primitives: `rig.nod()`, an `rig.eye_contact(master_dir)`
  (pan/tilt to a known master position), `rig.set_state(color, tempo)` for the antenna, and the
  two chirps. The temperament knob writes the cooldown/threshold *and* the antenna tempo from one
  control.
- **Study hook:** receipts present vs absent → does immediate acknowledgement improve the
  master's *trust* and *sense of being understood*, and reduce re-issued commands ("did it hear
  me?")? Predict yes — receipts are the master-side analog of the read-back trust effect.
