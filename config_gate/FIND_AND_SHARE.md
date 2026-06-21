# Delegate → Find → Show You — the Core Sidekick Interaction

The focused interaction doc, per the professor's steer (June 2026). It narrows everything to
the **sidekick ↔ master** relationship around one moment: *you ask it to watch for a specific
thing, it finds that thing, and it shows you* — **"Cassie, come look at what I found."**

**Scope (deliberately small):**
- **Hardware is frozen** at the current **pan-tilt head + LED antenna + buzzer**. No new joints,
  no lean-neck, no base-yaw, no "vivid" character. The form-expansion docs (`FORM_RATIONALE §8`,
  `FORM_DECISION`, the lean/ears ideas) are **parked** — not needed for this.
- **In focus:** how it shows it *understood* your command; how it *redirects* to what you point
  at; and the **find-and-share** moment, in two cases — **you're present** vs **you're away**.
- **Out of focus (for now):** elaborate away-mode scene-watching and how it reacts to *other*
  people. Those stay quiet and minimal; the spotlight is on you and it.

---

## 1. The delegation receipt — "I understood you"

You give it a **specific target** in plain words: *"tell me when you see the blue bottle."*
Two things must be visible immediately so you trust it before you walk away:

1. **It understood the *what*.** On screen / phone: *"Looking for: a blue bottle."* (the open-
   vocabulary detector target). On the body: it **turns to you (eye-contact) + one nod**, antenna
   comes up to **cool "on duty."** If a blue bottle is already in view, it gives **one glance to
   it** — *"like this one?"* — the cheapest possible proof it grounded your words to the world.
2. **It can be redirected.** If you **point** at the thing (or a region), it **gaze-follows your
   point** to the target, lands, and **nods** ("that one"). If your point is ambiguous (no clear
   object on the ray), it goes **amber + looks back at you** = *"which one?"* — honest uncertainty,
   not a confident wrong guess.

That's the whole "it gets me" loop: *name it → it confirms → (optionally) point → it locks.*
All on pan-tilt + antenna; no new hardware.

---

## 2. The rule that keeps it from nagging: bid only for *delegated* finds

The robot notices many things, but it must not call you over for all of them — that would be
exhausting. So:

> **The "come look!" bid is reserved for the *specific things you delegated*** (you asked for
> the blue bottle → when it finds the blue bottle, it actively calls you). Everything else it
> notices stays **quiet** — logged for later, never an interruption.

This single rule makes the bid **meaningful** (it only ever means "the thing *you asked for* is
here") and keeps the sidekick calm rather than overwhelming. It's the master-side version of the
habituation gate.

---

## 3. FOUND IT — when you are **present**

This is **initiating joint attention** (IJA): the robot directs *your* attention to the thing.
The developmental/HRI literature gives the exact three beats (Mundy; Huang & Thomaz's "responding/
initiating/**ensuring** joint attention" on the Simon robot) — and all three are just *orienting
between you and the target*, so they run on the current pan-tilt:

1. **Attention-get — "Cassie!"** It turns **to you** (pan-tilt to your position), antenna **bright
   flutter**, **one chirp.** = "Hey — look up."
2. **Direct — "…there."** It turns **decisively to the blue bottle** and **holds**, antenna steady
   bright. The sharp, deliberate move *is* the deictic point (with a one-eye head, a committed
   turn-and-hold reads as "that, over there").
3. **Ensure — "you see it?"** It **alternates** gaze **you ↔ bottle** once or twice. When you look
   at it (or step toward it), it **settles + a warm nod** = "yes — that one." Joint attention
   achieved.

**If you don't respond:** one **gentle escalation** (brighter, a second chirp, repeat the
alternation), then **graceful give-up** — it logs the find and returns to watching, antenna back
to calm cool. *It never nags.* (A sidekick you can ignore without guilt is one you'll keep around.)

The emotional read of this sequence is exactly *"come look at what I found"* — delivered with a
turn, a light, and a chirp instead of words. (Optionally pair with a one-line TTS / phone buzz,
but the body alone carries it.)

---

## 4. FOUND IT — when you are **away**

Body language is wasted on an empty room, so the channel switches but the *intent* is the same —
get you to the thing:

1. **Reach you where you are — the phone alert.** Push a notification with the **keyframe**:
   *"Found it — a blue bottle on the shelf, just now. Come look?"* (+ the thumbnail, and the short
   storyboard if the moment is unfolding). This is the literal "come back and look."
2. **Hold the finding — the PENDING-SHOW state.** The robot keeps a "I have something to show
   you" posture: antenna **slow pulse**, and it keeps an eye on the spot so it can show you on
   your return. It is *visibly holding a finding for you.*
3. **Bridge back to present — the return bid.** The moment you **re-enter** (presence detected),
   it runs the §3 bid *at you*: turn-to-you → point to **where it found it** → ensure. If the
   bottle is still there, it shows the thing; if the moment passed, it points to the **location**
   and offers the **storyboard/clip** — *"it was right here; here's what happened."*

So "away" isn't a different behavior, it's the **same bid with a remote first step**: notify now,
then perform the embodied "here, look" when you're back.

---

## 5. Presence detection (kept honest and simple)
"Present vs away" = **is a person in view / seen recently** (the detector already finds people).
Telling *you* apart from *other* people needs face-ID or a worn tag — but per the professor we are
**not** focusing on the multi-person case, so for now assume the single-user lab (or "someone is
here" = you). Note it as a limitation; it doesn't block the prototype or the demo.

---

## 6. Build mapping (current rig) + how to show it works
- **Primitives:** `rig.look_at(you)` / `rig.look_at(target)` (pan-tilt to a stored direction),
  `rig.alternate(you, target, n)`, `rig.nod()`, antenna `set_state(color, tempo)` (flutter / cool /
  slow-pulse / warm), `beep()`; phone alert via the records/notification channel.
- **State machine:** `DELEGATE→confirm` · `WATCH` · on delegated-target detect → `FOUND`:
  `if present: BID(get→direct→ensure→[escalate]→resolve) ; else: ALERT + PENDING → on return: BID`.
- **Demo (cheap, convincing):** brief it "find the blue bottle," place a blue bottle in view →
  watch it confirm → walk away → get the phone alert → return → watch it call you over and point.
  That single run *is* the concept on film.

**Study hook:** the embodied bid vs a silent phone ping only — does the "come look" bid get you to
the thing **faster** and make it **feel like a sidekick** (vs a notification)? And does the
**ensure** step (check-back) matter for whether you actually look? (Huang & Thomaz found ensuring
improves joint-attention success.)

---

## Sources
- Mundy et al. (1986) & Mundy/Newell — **initiating vs responding joint attention** (IJA/RJA);
  IJA = directing another's attention via gaze-shift, pointing, showing, coordinated looking.
  https://link.springer.com/rwe/10.1007/978-1-4419-1698-3_853
- Huang & Thomaz (2011), *Effects of Responding to, Initiating and Ensuring Joint Attention in HRI*
  (Simon robot) — the attention-get → direct → **ensure** beats; ensuring improves success.
  https://sites.cc.gatech.edu/social-machines/papers/huang11-roman.pdf
- Admoni & Scassellati (2017), *Social Eye Gaze in HRI: A Review* — gaze for directing attention.
  https://dl.acm.org/doi/pdf/10.5898/JHRI.6.1.Admoni
- Project internal: `INTERACTION_DESIGN.md §2` (delegation/read-back/point-to-redirect),
  `PROJECT_HANDOFF.md §3` (open-vocab detection of the named target).
