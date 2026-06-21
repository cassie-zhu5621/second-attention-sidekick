# The Head, and Where the "Screen" Goes

Resolves a contradiction I caused: I argued *against* a screen-face (Stack-chan's drawn eyes =
fake gaze) but kept saying "show it on screen." Those are two different screens. This pins down
what the head actually is. Last updated: June 2026.

---

## 1. "Screen" meant two different things — separate them

| | Screen-as-**FACE** | Screen-as-**READOUT** |
|---|---|---|
| What | drawn cartoon eyes (Stack-chan, Jibo) | text + the captured photo / storyboard |
| Purpose | pretend to be the robot's eyes | show you information |
| Verdict | **AVOID** — fakes gaze, breaks the honest eye | **fine** — but it lives on your **phone/laptop**, not the robot |

So the two organs are **physically separate and never the same thing**:

> **The EYE is the camera** (now your USB cam) — on the robot, on the pan-tilt, honest gaze.
> **The READOUT is a screen on your phone/laptop** — text and photos — *not a face on the robot.*

The head has **no screen.** A screen on the head would either (a) become a fake face, or
(b) compete with the eye for "where is it looking?" Both break the one thing that makes the
robot legible. Keep the head pure.

---

## 2. The head, concretely (you've basically already built it)

Your current prototype (the gray cube with the front lens + the cyan LED stalk on the pan-tilt)
**is already this head.** Formalize it:

- **Eye = the USB camera lens, single.** It is the real sensor *and* the gaze. To make its
  pointing legible as a gaze (so people read where it's looking), give the lens a simple
  **bezel / iris ring** — a shallow ring or hood around the lens so it reads as *an eye*. That's
  the only "face" styling allowed, and it's honest because it's framing the *actual lens*, not
  drawing fake eyes.
- **Antenna = the LED on a short stalk**, above/behind the eye = the affect/state channel (you
  already have this, glowing cyan).
- **Mount = the pan-tilt.** That's the whole head.
- **Nothing else:** no second eye, no mouth, no screen. One honest eye + one antenna.

That restraint is the design (`FORM_RATIONALE §4`, `GRAMMAR_EMBODIMENT`): a single real eye whose
direction you can trust, plus a light for mood. The USB cam just makes the eye *see better* —
same role, higher quality.

---

## 3. Where the readout actually lives — and why the robot needs no screen

Trace the two moments and you'll see a robot screen is **redundant**:

- **You're present.** The robot tells you with its **body**: turn-to-you → point-to-the-thing →
  antenna + chirp (the find-and-share bid, `FIND_AND_SHARE §3`). You then look at the *real
  thing*, not a screen. No display needed.
- **You're away.** The readout goes to your **phone**: the alert, the text *"Looking for: blue
  bottle"* / *"Found it"*, the keyframe photo, the storyboard (`FIND_AND_SHARE §4`,
  `INTERACTION_DESIGN §2` read-back line). The phone *is* the screen — and it's already where you
  are when you're away.

So every "on screen" line in the other docs means **the phone/laptop app** (`attention_ui.py` /
the records UI), never a face on the robot. The robot stays an honest eye + antenna; your phone
carries the words and pictures.

*(Optional, not required: a tiny status readout on the **base** — e.g. a small e-ink strip
showing "watching: blue bottle" — is acceptable **only** if it's clearly an instrument label on
the body, never on the head and never styled as eyes. The antenna color already covers
at-a-glance status, so this is a nice-to-have, not a need.)*

---

## 4. The one-line resolution
> The robot has **one screen-like surface and it's not on the robot: it's your phone.** On the
> robot there is **one eye (the camera) and one antenna (the light)** — nothing to read, only
> something that looks and something that glows. The eye sees; the phone shows.

---

## 5. Tiny build notes
- Mount the **USB cam as the front eye**; add a printed **bezel ring** so the lens reads as an
  eye and its aim is legible. Keep the lens the visual center of the head.
- Keep the **LED stalk** above it; that's the only other feature.
- All text/photo/storyboard UI → the existing **phone/laptop app**; the away-mode alert is a push
  notification with the keyframe.
- Result: the head you already have, minus any temptation to add a screen-face. Done.

---

## Sources / cross-refs
- `WHY_NOT_BUY.md` — the eye must be the camera (honest gaze); screen-face robots fake it.
- `GRAMMAR_EMBODIMENT.md` — the eye sees from where it looks; refer-don't-mime.
- `FORM_RATIONALE.md §4` — one honest eye, resist the face.
- `FIND_AND_SHARE.md` — present = body carries the message; away = phone carries it.
