# The Channel Matrix — FINAL Design Spec

The canonical, finalized interaction spec. Lists **every channel** the sidekick has and **what
each one does at every interaction step (环节)**. Supersedes earlier drafts. Hardware is settled:
**CoreS3** (touchscreen + speaker + mic + IMU onboard) + **pan-tilt head** + **USB camera (the
eye)** + **one RGB-pixel antenna**; brain (VLM/CV + Whisper) on the laptop. Last updated: June 2026.

---

## 1. The channel roster — 7 channels (4 out, 3 in)

Each channel has **one job** (this is what keeps a cheap robot legible).

### Output — the robot expresses (4)
| # | Channel | Hardware | Its ONE job | Vocabulary |
|---|---|---|---|---|
| O1 | **Head / gaze** | pan-tilt servos | **WHERE attention is** | scan · orient · turn-to-you · point-to-thing · alternate · nod (tilt dip) · wake-sweep |
| O2 | **Antenna (LED)** | 1 RGB pixel (PL9823/NeoPixel) on the stalk | **STATE / affect** | color: warm=rest · cool=on-duty · amber=unsure · bright=caught · warm-pulse=approval · tempo: slow=calm/fast=eager |
| O3 | **Sound** | CoreS3 speaker | **rare EVENTS** (+ optional 1-line TTS) | rising chirp=wake · single chirp=catch/"hey" · descending chirp=sleep |
| O4 | **Screen** | CoreS3 touchscreen | **WHAT it sees/found** (readout — *never a face*) | live transcript · "Looking for: X" · the catch thumbnail · status |

### Input — the human acts on it (3)
| # | Channel | Hardware | Its ONE job | Vocabulary |
|---|---|---|---|---|
| I1 | **Vision** | USB camera (the eye) | **perceive** | detect the target · people · your point/gaze ray |
| I2 | **Voice** | CoreS3 mic + push-to-talk | **the spoken brief / redirect** | "watch for the blue bottle" / "no, the shelf" → Whisper → planner |
| I3 | **Touch** | CoreS3 touchscreen (or a button) | **discrete control** | push-to-talk · keep/not-this · eager↔calm · stop |

> Design rule: **Head=where · Antenna=state · Sound=events · Screen=what · Vision=perceive ·
> Voice=brief · Touch=control.** No channel does two jobs.

---

## 2. THE MATRIX — every channel at every step

Steps (环节): **1 Brief/Start · 2 Read-back · 3 Steer(point/fix) · 4 Set-personality · 5 Watch ·
6 Found-present(the bid) · 7 Found-away · 8 Judge(keep/not) · 9 Stop · 0 Confused.**

### A) Output channels

| Step | O1 Head / gaze | O2 Antenna (LED) | O3 Sound | O4 Screen |
|---|---|---|---|---|
| **1 Brief / Start** | wake-survey sweep → settle facing you + nod | LISTEN steady glow (mic open) → comes up to **cool** | tick on mic-open · **rising chirp** when armed | live transcript → **"Looking for: blue bottle"** |
| **2 Read-back** | sweep across what it'll watch + settle-nod | steady **cool** (confident) | — | the watch in plain text; highlight an example |
| **3 Steer (point/fix)** | **gaze-follow** your point → lock + nod; *(fix)* release wrong spot → glance to you → re-orient | amber blip (reset) → **bright flutter** on lock | — | locked target ("this?") · **amber "which one?"** if unclear |
| **4 Set personality** | one sample beat at the new tempo (snappy↔slow) | breathe **rate/brightness shift** (fast-bright↔slow-dim) | — | eager↔calm indicator |
| **5 Watch (idle)** | slow even scan; still at REST | calm slow breathe (cool / warm-dim) | — | live view dim — or off |
| **6 FOUND — present (bid)** | ①turn to **you** ②turn to **bottle**, hold ③**alternate** you↔bottle → settle+nod | **bright flutter** → steady bright | **single chirp** ("hey") · opt. 1-line TTS | **the catch, highlighted** ("see?") |
| **7 FOUND — away** | hold toward the spot (pending) → run bid on return | **slow pulse** = "show you" | — (no empty-room beep) | catch/pending; **phone** gets alert + keyframe |
| **8 Judge keep/not** | keep: small nod · not-this: small downward dip | keep: **warm pulse** · not-this: **amber dim** | — | the marked record updates |
| **9 Stop** | face you + nod → lower to rest → relax | cool → **warm dim** (off duty) | **descending chirp** | "off duty" / goes dark |
| **0 Confused/lost** | small hesitant side-to-side; look back to you | **amber** irregular blink | — | "lost it — point me?" / last view |

### B) Input channels

| Step | I1 Vision (camera) | I2 Voice (mic+PTT) | I3 Touch (screen/button) |
|---|---|---|---|
| **1 Brief / Start** | begins watching; grounds words to a seen example | **hold PTT, speak the brief** → Whisper → planner | (alt: type the brief) · hold PTT |
| **2 Read-back** | confirms it can see the target type | (correct by voice if it misheard) | (tap to correct) |
| **3 Steer (point/fix)** | **reads your pointing/gaze ray** → finds target | "no, the one on the shelf" (optional) | **"not-that" tap** · tap the target on screen |
| **4 Set personality** | (threshold change → more/fewer catches) | — | **eager↔calm slider/buttons** |
| **5 Watch (idle)** | **scanning for target & relations** (primary) | mic closed (until PTT) | idle |
| **6 FOUND — present** | **detected the delegated target** (trigger) | — | (you can tap keep/not → step 8) |
| **7 FOUND — away** | detected; keeps the spot | — | engage on return |
| **8 Judge keep/not** | — | — | **tap keep / not-this** (primary) |
| **9 Stop** | stops | "stop" (optional) | **press stop / pick it up** (primary) |
| **0 Confused/lost** | **tracking dropped** (trigger) | invites "it's over there" | invites a point/tap to re-steer |

---

## 3. How to read it / build it
- **A row** = the full multi-channel behavior of one moment (e.g. *Found-present* fires O1+O2+O3+O4
  together, triggered by I1).
- **A column** = everything one channel ever does → that's its driver/firmware spec (e.g. O3 Sound =
  exactly three chirps; I2 Voice = PTT→Whisper only).
- **Triggers vs receipts:** input channels (I1–I3) *start* a step; output channels (O1–O4) are the
  *receipt* (`GRAMMAR_EMBODIMENT §7`: no movement without a receipt — every output cell here
  corresponds to a real state/result change).
- **Minimal viable set:** O1 Head + O2 Antenna + O3 Sound + I1 Vision + I3 Touch already run the
  whole loop. **O4 Screen** and **I2 Voice** are the enrichments (both come "free" on the CoreS3:
  touchscreen + mic), so add them once the core loop works.

## 4. Hardware ↔ channel map (so wiring is unambiguous)
- O1 Head → pan-tilt servos (MG90S now / SCS0009 later; `CORES3_SERVO_MIGRATION.md`).
- O2 Antenna → 1 RGB pixel on a GPIO (`CAMERA_AND_PERIPHERALS.md`).
- O3 Sound → CoreS3 **built-in speaker** (`M5.Speaker`).
- O4 Screen → CoreS3 **touchscreen**.
- I1 Vision → **USB camera** into the laptop (MediaPipe).
- I2 Voice → CoreS3 **mic** → stream to laptop Whisper (`VOICE_CONTROL.md`).
- I3 Touch → CoreS3 **touchscreen** (PTT, keep/not, eager/calm, stop).

This table is the single source of truth — when a behavior changes, change the cell here; the other
docs (`INTERACTION_DESIGN`, `FIND_AND_SHARE`, `MASTER_FEEDBACK`, `GRAMMAR_EMBODIMENT`) point to it.
