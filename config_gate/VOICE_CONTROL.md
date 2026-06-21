# Voice Control — What to Plug In (and What's Just Software)

How to talk to the robot instead of typing the brief on the web UI. The key fact up front:
**your laptop is already the brain, so almost all of this is software. The only thing you
physically add is a microphone.** Last updated: June 2026.

---

## 1. Bottom line — the plug list

| Add | What | Essential? | Notes |
|---|---|---|---|
| **USB microphone** | a small USB mic mounted on/near the robot | **Yes** — the one real addition | plug into the laptop; you talk *to the robot*, mic hears you |
| **Push-to-talk button** | momentary button → Arduino digital pin (you already have the Arduino) | Recommended | press → speak the brief → release. Privacy + no false triggers |
| **Small speaker** | USB or 3.5 mm speaker | Optional | only if you want it to *talk back* (TTS). The buzzer + screen/phone already cover read-back |
| **(Upgrade) USB mic array** | e.g. a 2-/4-mic array (ReSpeaker-style) | Optional | far-field pickup + **direction-of-arrival** → bonus: robot can turn to face whoever spoke |

Everything else — turning speech into text and into a watch-spec — **runs on the laptop you
already have. No new compute, no Raspberry Pi, no cloud required.**

---

## 2. The data path (it reuses what you've built)

```
 you speak  →  [robot: USB mic (+ push-to-talk button)]  →  USB  →  LAPTOP BRAIN
                                                                       │
                          speech-to-text (Whisper, local)  ───────────┘
                                       │  "watch for the blue bottle"
                                       ▼
                          planner.py  (same input as context.txt today)
                                       │  → watch-spec
                                       ▼
                          robot acts (antenna LISTEN → nod → "Looking for: blue bottle")
```

The crucial point: **voice doesn't change the brain.** Speech-to-text just produces the *same
plain-language brief* you currently type — it writes the text that `planner.py` already consumes
(`context.txt` path). The VLM planner was always built to take plain language; voice is a new
*input device* for it, nothing more.

- **Speech-to-text:** **Whisper** (e.g. `faster-whisper`) running **locally on the laptop** —
  offline, accurate, off-the-shelf (fits your "use existing models" approach). A cloud STT API
  works too but isn't needed.
- **No firmware change for STT.** The Arduino still only does servos/LED/buzzer. The mic talks to
  the *laptop*, not the Arduino. (The button is the only new Arduino input.)

---

## 3. Push-to-talk vs wake-word (pick PTT)
For a *camera* robot, an always-listening mic adds a real surveillance feel — the opposite of
"considerate observer." So:

- **Recommended: push-to-talk.** A physical button (on the robot) opens the mic only while held.
  Clear, private, no false triggers, and it makes a nice ritual: *press, speak your brief,
  release* — the embodied version of "leave it a note." Fits your existing "say it when you place
  it down" briefing moment (`INTERACTION_DESIGN §2`).
- **Optional: wake-word** ("Hey [name]") via a local engine (openWakeWord / Porcupine) on the
  laptop — convenient but always-listening; only add it if hands-free really matters, and tell
  users the mic is live.

---

## 4. Does it talk back? (optional, keep it sparse)
Your design is **mostly-silent** (buzzer for events; read-back on screen/phone). So spoken output
(TTS) is **optional** and slightly against the personality. If you want it:
- add a **small speaker**, use a local TTS (e.g. Piper) on the laptop, and keep it to *one short
  line* ("Got it — watching for the blue bottle"), not a chatty assistant.
- Otherwise, skip the speaker: confirm with the **antenna + nod + the screen/phone line**. That's
  the on-brand choice.

---

## 5. How voice fits the channels (a new LISTEN state)
Voice is an **input** on the delegate/steer stages of `CHANNEL_MATRIX.md`. Add one state:

| Stage | Head | Antenna | Buzzer | Screen |
|---|---|---|---|---|
| **LISTEN** (button held / wake-word fired) | turns to face you (it's being addressed) | **steady glow** = "mic open, I'm hearing you" | soft tick on open (optional) | shows the **live transcript** as you speak |

Then it flows into the existing **Brief → Read-back** rows: on release, STT → planner → it
**nods + shows "Looking for: blue bottle."** The steady-glow-while-listening is the key receipt —
you can *see* the mic is open and *see* it heard you (transcript), which also handles mis-hearing
gracefully (you see the wrong word and just repeat).

---

## 6. Minimal shopping list (to start today)
1. One **USB microphone** (a small omni/lavalier USB mic, or a USB mini conference mic for
   far-field). Mount it on the robot.
2. One **momentary push-button** + 2 wires to a spare Arduino digital pin (you have the board).
3. *(Later, optional)* a **USB mic array** for far-field + direction-of-arrival, and/or a small
   **speaker** for TTS.
4. Software: `faster-whisper` on the laptop; press-button → record → transcribe → write the brief
   into the planner input. (~a short script around what you already run.)

That's it — one mic and a button turn the typed brief into a spoken one, with no change to the
brain or the firmware's motor/LED/buzzer roles.

---

## 7b. Doing the speech-to-text "on the robot side" (talk to the robot, not the laptop)

You're right that *talking to the robot and seeing its screen* is more attractive than talking
at a laptop. The key insight: **"on the robot" is mostly about the *interaction locus* (mic +
screen on the robot, laptop hidden), not about *where the computation runs*.** You can get the
full "talk to the robot, it shows on its face" experience three ways:

| Path | Where STT runs | What's on the robot | Notes |
|---|---|---|---|
| **1 — Hidden laptop (recommended)** | laptop, as a local server | mic + small screen + WiFi/USB | You talk to the robot; the robot shows the transcript; **the laptop is just tucked away.** From your POV it *is* talking to the robot. Cheapest, most reliable. Do this for the study. |
| **2 — Raspberry Pi on the robot** | **on the robot** (faster-whisper on the Pi) | Pi + mic + screen | Truly self-contained voice+display: the robot hears, transcribes, shows it, then sends the *text* to the laptop VLM/CV brain over WiFi. Pi 4/5 runs small/base Whisper fine; Pi Zero 2 is marginal. More power/heat. |
| **3 — ESP32-S3 + small screen** | a **server** (laptop or cloud), audio streamed | ESP32 + mic + screen | ESP32 can't run free-form Whisper, but it can do **wake-word + capture**, stream the audio over WiFi to a STT server, and display the returned text. Good if you want the M5/ESP32 + screen ecosystem. |

**Important:** even in paths 2–3, the **heavy VLM/CV brain stays on the laptop** — a Pi/ESP32
can hear and display, but it won't run your perception/planner well. So the split is: *robot
does **talk + show** locally; laptop does **see + plan***. The text hops from robot → laptop.

**Recommendation:** for the demo/study, do **Path 1** — mic + a small screen on the robot, laptop
hidden/networked, STT running on the laptop. It gives the whole "talk to the robot, read its
screen" feeling now, with no new compute on the robot. Move to **Path 2 (Pi)** only when you want
it to work with the laptop fully out of the room. (Push-to-talk + the LISTEN-glow receipt from §3
apply in all paths.)

## 7. If you ever want it untethered (note for later)
Everything above assumes the **laptop is the brain** (your current setup). If you later want the
robot to run *without* a laptop, you'd move the brain onto a **Raspberry Pi** (can run Whisper +
your perception, has USB for the mic) — or stream I2S-mic audio from an **ESP32** to a server. Not
needed now; the laptop-brain path is by far the simplest.

---

## Cross-refs
`INTERACTION_DESIGN.md §2` (the brief / "say it when you place it down"), `CHANNEL_MATRIX.md`
(add the LISTEN row), `planner.py` (consumes the plain-language brief — unchanged by voice).
