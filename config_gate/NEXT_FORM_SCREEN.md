# Next Form — Investigating a Screen on the Robot

You're right, and I was too absolute. The honest rule was never "no screen" — it was **"no
screen that fakes a face."** A screen that shows *what the robot sees / what it found* is a
different animal, and the HRI literature says it's a recognized **transparency** technique that
*raises* perceived competence and trust. So a small screen can be both **more intuitive** and
**more on-concept**, not a compromise. This doc investigates the options for the next form.
Last updated: June 2026.

---

## 1. The corrected rule

> **A screen is bad only when it pretends to be a *face* (drawn eyes faking gaze). A screen that
> shows *what it perceives* — the live view, the catch, what it's watching for — is good: it
> makes the robot's *attention legible*, which is exactly Notice Delegation made visible.**

Why this is on-concept, not a concession: the whole project is *delegated attention made
legible*. A "window into what it's attending to" is the most direct possible way to show that.
Research on co-located HRI transparency finds that displaying what a robot perceives (camera
stream, detections, attention/saliency) **increases perceived competence** and supports
"mutual understanding." So the user's intuition — *a screen is more intuitive* — is supported.

The only thing that's still banned is the **Stack-chan/Jibo drawn-eyes face**, because that
fakes gaze (`WHY_NOT_BUY.md`). Showing the *real* view is the opposite of faking — it's
radical honesty about where attention is.

---

## 2. Four form options

| | What the screen shows / where | Intuitive? | Honest gaze? | On-concept? | Verdict |
|---|---|---|---|---|---|
| **A — No screen** | nothing on robot; readout on phone | ◐ (need phone) | ✅ | ✅ minimal | safe **study baseline** |
| **B — Viewfinder eye** | the eye *is/holds* a small screen showing the **live view / the catch**, head still pans-tilts | ✅✅ "see what I see" | ✅ head bears gaze; screen shows what's seen | ✅✅ attention made visible | **recommended next form** |
| **C — Body/base readout** | camera-lens eye on top (gaze); a **separate** small screen on the body/base shows text + the captured photo | ✅ glanceable | ✅ eye and readout separate | ✅ | strong, **safe** alternative |
| **D — Face screen (drawn eyes)** | cartoon eyes on a front display | ◐ cute | ❌ fakes gaze | ❌ | **rejected** (it's a Stack-chan) |

### B — the "viewfinder eye" (the interesting one)
Make the eye a **small screen showing the camera's live feed**, framed like a *viewfinder /
camera-obscura window*, not cartoon eyes. The camera is still the sensor; the head still
pans-tilts (so *where it looks* stays legible from orientation); the screen adds *what it sees*.
When it catches the blue bottle, the eye-window **shows the bottle, highlighted** — so the
find-and-share moment becomes literal: it turns to the thing **and its eye shows the thing**,
*"come look — see?"* This is honest (it displays real perception), intuitive (you read the find
at a glance), novel (a creature whose eye is a little window into its attention), and grounded
(a transparency display). It is arguably **more** on-concept than no screen.

### C — the safe split
Keep the **lens as the eye** on the pan-tilt head (gaze), and put a small screen on the
**body/base** showing text ("watching: blue bottle") + the captured photo. Clean separation:
head = honest eye, body = readout. Lower risk than B (no chance the screen reads as a face),
slightly less magical.

---

## 3. Cautions for whichever screen you add
- **Don't let it become a face.** No eyes/eyebrows/mouth drawn on it. It shows *the view* or
  *the readout*, never a cartoon visage. (That's the line between B and D.)
- **Keep the gaze on the head, not the screen.** *Where it looks* must still read from head
  orientation (pan-tilt). The screen carries *what*, not *where*.
- **Stay a creature, not a gadget.** A screen pulls toward "device." Keep it small, let the
  **antenna + the gaze movement** still carry the life, so it doesn't become a tablet on a stick.
- **Privacy of a live feed.** A screen showing raw video of people can feel surveillant — the
  opposite of "considerate observer." Mitigation: the eye-window mostly shows a calm/abstracted
  view, and *sharpens to the actual catch* (the object) at the find moment, rather than always
  streaming faces. Worth a design pass.
- **Professor's freeze still holds for the *current* study.** Hardware is frozen for the study
  you're running now → **Option A (or the current rig)** is the minimal baseline. **B/C is the
  *next* iteration** — propose it as the next prototyping cycle, not a change to the current one.

---

## 4. Recommendation
- **For the study you're running now:** keep it minimal — **A** (eye = camera, antenna, phone
  readout). Don't add hardware mid-study.
- **For the next form (what you're investigating):** **B, the viewfinder eye** — it's the most
  intuitive *and* the most on-concept, because it turns the screen into a window on the robot's
  attention, which is the whole idea. If B feels risky to build or reads too "screen-y" in
  mockups, fall back to **C** (separate body readout). **Never D.**

## 5. A clean way to *test* the screen (turns the debate into data)
Compare **A vs B vs C** on the find-and-share moment: when it finds the blue bottle, does a
screen (B/C) make people **understand the find faster** and **trust** it more than body+antenna
alone (A)? Does the **viewfinder eye (B)** beat a **body readout (C)** on "it feels like it's
showing me"? Measures: comprehension time, trust/competence rating, "felt like a sidekick."
Prediction (from the transparency literature): B ≥ C > A on competence/understanding — but
watch the privacy/"creature vs gadget" ratings, where A might win. That tradeoff *is* the
finding.

---

## Sources
- *A Literature Survey of How to Convey Transparency in Co-Located HRI* (2023) — screens to
  present what the robot perceives; transparency and trust. https://www.mdpi.com/2414-4088/7/3/25
- *Here's Looking at You, Robot: The Transparency Conundrum in HRI* (IEEE) — perception-display
  raises perceived competence; transparency tradeoffs. https://ieeexplore.ieee.org/document/10309653/
- *Should robots display what they hear?* (2024) — displaying robot perception reshapes mutual
  understanding. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12511783/
- Project internal: `WHY_NOT_BUY.md` (the eye must be honest — drawn-eyes face is the only ban),
  `HEAD_AND_READOUT.md` (eye vs readout), `FIND_AND_SHARE.md` (the show-me moment a screen aids).
