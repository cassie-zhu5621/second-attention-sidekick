# Hardware Architecture — Mic, Screen, Controller, Servos

Answering: where do mic + screen connect, is Arduino enough, and is the SCS0009 servo plan
sound. Plus a positioning note on MIT's Stochastic Parrot. Last updated: June 2026.

---

## 0. Quick verdict
- **One correction:** the mic does **not** go through the Arduino. An Arduino can't do
  speech-to-text. **Mic → laptop (USB); the command is *born on the laptop* (Whisper), not on
  the board.** The board never recognizes the command; it only *displays* what the laptop
  decided and drives the motors/LED/buzzer.
- **Is Arduino "good enough"?** For *dumb muscle + a small text screen*, yes — but once you add
  **serial-bus servos (SCS0009)** + screen + maybe audio, an **ESP32 is the more comfortable
  controller**, and the **cleanest** option is to let the **laptop drive the bus servos directly
  via a USB servo adapter** and keep a small MCU only for LED/buzzer/button/screen.
- **SCS0009 reality:** good upgrade for *position feedback + active hold*, but it's **300°**
  (position mode), **not 360° with feedback**, its torque ≈ MG90S, and a **tethered USB camera
  will tangle** if the pan rotates freely. Details below.

---

## 1. The corrected data flow (who is the brain)

```
            ┌──────────────── LAPTOP = BRAIN ────────────────┐
 you speak  │  Whisper (speech→text)  →  planner.py (VLM)     │
   │mic     │        │"look for blue bottle"                  │
   ▼  USB   │        ▼                                        │
 [USB mic] ─┼──────► command text ──► watch-spec ──► CV/VLM   │
            │                                   │             │
            └───────────────┬───────────────────┼─────────────┘
                            │ USB serial (commands DOWN)       ▲ USB serial
                            ▼                                  │ (button/knob UP)
                ┌─────────── MCU = DUMB MUSCLE ───────────────┐
                │  servos (gaze) · LED antenna · buzzer ·      │
                │  small OLED shows "Looking for: blue bottle" │
                └──────────────────────────────────────────────┘
```

**The key idea you had inverted:** intelligence and audio live on the **laptop**. The MCU is
"muscle + a display relay." So:
- **Mic → laptop (USB).** Whisper turns speech into the same plain-language brief you type today
  → `planner.py` (unchanged). The board is not involved in hearing you.
- **Screen text flows the *other* way:** laptop decides "Looking for: blue bottle" → sends that
  string **down** the serial to the MCU → MCU prints it on a small OLED. (Or the laptop drives
  the screen directly.) The board doesn't generate the text; it shows what the brain sends.
- **The MCU only sends *up*** simple inputs: the push-to-talk button, the eagerness knob.

(Why not capture audio on the board and stream it up? An Uno R4 is poor at audio; a USB mic into
the laptop is far simpler. Only an ESP32 + I2S mic could stream audio — unnecessary here.)

---

## 2. Controller — three clean options (pick by taste)

| Option | Servos | LED/buzzer/button/screen | Verdict |
|---|---|---|---|
| **A — Laptop drives bus servos via USB adapter** (FEETECH/Waveshare bus-servo adapter) + small MCU for the rest | laptop → USB adapter → SCS bus | small ESP32/Uno over USB | **Recommended** — offloads the fiddly half-duplex servo protocol from the MCU; laptop already computes the gaze targets |
| **B — One ESP32 does everything** | ESP32 UART2 → SCS bus | same ESP32 (WS2812, buzzer, button, I2C OLED) | **Good** if you want one board; ESP32 > Uno R4 here (more UARTs, 3.3 V logic, display libs, room for I2S mic later) |
| **C — Uno R4 does everything** | Serial1 + half-duplex transceiver → SCS bus | Uno R4 pins | **Works but fiddly** — the half-duplex bus on a single extra UART is the awkward part; weakest of the three |

**Is Arduino good enough?** Technically yes (Option C), but for *combining serial servos + screen
(+ future audio)* the **Uno R4 is the weak link**, not because it lacks power but because the
serial-bus-servo wiring (half-duplex TTL) is awkward on it. **Prefer A (laptop drives the bus
servos) or B (ESP32).** Both make "combine all these things" easy.

---

## 3. SCS0009 — the good, and four things to check

**Why it's the right *direction* (real upgrades over MG90S):**
- **Position feedback (10-bit magnetic encoder):** the servo *knows and reports its angle*. That
  is genuinely valuable for you — the robot can command an **absolute gaze angle**, read it back,
  and you can log "where it looked" (honest gaze, read-back sweep, aim-at-the-bottle all get
  easier and more precise).
- **Active hold:** it *holds* position against load (fixes the MG90S "can't hold the head" sag),
  and reports load/temperature/voltage.
- **Daisy-chain (TTL, up to 253 IDs, 1 Mbps):** pan + tilt on one bus, fewer wires.

**Four things to check before you commit:**
1. **It's 300°, not 360° with feedback.** SCS0009 gives **~300° in *position* mode**; full
   continuous rotation is only the **"motor/wheel" mode, which has *no* absolute position**. For
   *gaze* you need position mode → so plan for **~300° pan**, not a precise 360. (If you truly
   need 360° *with* position, look at a single-turn 360° servo like the **STS3215** instead.)
   300° is plenty for a desk sidekick anyway.
2. **Torque ≈ MG90S.** SCS0009 = **2.3 kg·cm stall / 0.75 kg·cm rated** — similar to MG90S. The
   win is *active hold + feedback*, **not** brute torque. If the head physically **sagged** on
   MG90S, verify SCS0009 actually holds it; if the head is heavy, **size up** to a bigger bus
   servo (e.g. STS3215 ≈ 19–30 kg·cm) and/or **balance the tilt axis** (put the pivot near the
   head's center of mass / add a small counterweight) — balancing helps more than raw torque.
3. **Tethered USB camera + rotation = cable tangle.** If the pan rotates freely the **USB cable
   will wrap**. Options: **bound the pan** to ~300° with a cable service loop (simplest), use a
   **slip ring** for true continuous rotation, or a **wireless camera**. Don't design for endless
   spinning with a wired cam. (This is also why 300° is fine — you don't want unlimited pan with a
   tether anyway.)
4. **Power.** Bus servos want a clean **6 V** supply (stall ~1 A each). **Don't** run them off the
   Arduino's 5 V / USB — use a **separate 6 V supply, grounds common** with the MCU.

---

## 4. MIT "Stochastic Parrot" — inspiring, and useful for positioning
It's an **"AI Cohabitant"**: a physical agent framed as a *roommate / house-pet* with its **own
personality and narrative**, acting **autonomously, ambiently, continuously** — explicitly
**reversing the subservient assistant dynamic** (it isn't waiting for commands; it observes,
learns, and "subtly participates" on its own rhythm).

- **Why it's inspiring / helpful:** it gives you an **academic umbrella + citation** for the move
  you've already made — a *placed, ambient, non-assistant presence that observes*. Use it to
  justify "this is **not** a voice-assistant," which reviewers respond well to.
- **How you differ (state this clearly, it sharpens your novelty):** the Stochastic Parrot's
  contribution is **characterful autonomy** — the AI's *own* narrative/agenda. Yours is the
  opposite vector: **delegated, steerable noticing** — the criterion of what's worth attention is
  **the user's**, given in plain words and **rewritable**, and the robot **reports** it. So:
  *Cohabitant = the AI's own attention/personality; your sidekick = the user's attention,
  delegated and embodied.* Both are ambient placed presences; the **delegation + the relational
  grammar** is what's yours. Add it to `RELATED_WORK_hri.md` as a near-neighbor in the
  "ambient/cohabitant" cluster, differentiated on *delegation & steering*.

---

## 5. Decision summary / shopping
- **Mic:** USB mic → **laptop** (not the board). Whisper on the laptop. Push-to-talk button → MCU.
- **Controller:** **either** let the **laptop drive the SCS bus servos via a USB bus-servo
  adapter** + a small ESP32/Uno for LED/buzzer/button/OLED (cleanest), **or** one **ESP32** for
  everything. Uno R4 works but is the awkward choice for serial-bus servos.
- **Servos:** SCS0009 is a good upgrade for **feedback + hold**; plan **300° pan** (not 360),
  verify torque vs your head weight (size up to STS3215 if it sags), **bound rotation or add a
  slip ring** for the USB cam, **separate 6 V supply**.
- **Screen:** small OLED for text driven by the MCU (laptop sends the string), **or** the phone/
  laptop carries the readout. The camera *viewfinder* screen needs the laptop or a Pi/ESP32, not
  an Uno.

---

## 6. Cheaper than a Pi 4/5 — and better for exhibitions

If the on-robot board **only handles servos + voice I/O + screen + LED** (the brain stays on the
laptop), you **don't need a Pi at all** — a **Pi is overkill**. The right cheap board is an
**ESP32-S3 (~$5–15)**, and there's a ready-made variant that bundles exactly what you need.

**It comes down to one question: does speech-to-text run *on the robot* or on the laptop?**

| | STT on the **laptop** (recommended) | STT **on the robot** (untethered) |
|---|---|---|
| Board on robot | **ESP32-S3** — *no Pi needed* | a Linux SBC (Pi-class) |
| What it does | servos (bus UART) + mic (on-chip **wake-word**, NPU) + **streams audio over WiFi** to the laptop's Whisper + drives screen + LED/buzzer | runs Whisper locally, then sends text to the laptop brain |
| Cost | **~$5–15 bare**, or the **ESP32-S3-BOX-3 (~$45)** = dual-mic array + **LCD screen** + RGB LEDs in one unit (a ready voice+screen front end) | **Pi Zero 2 W ~$28** (tiny-Whisper but **~5 s** latency — slow); Pi 5 is snappy but pricier |
| Verdict | **cheapest + fastest + most robust** | only if no brain machine is in the room; cheap = slow |

So: **ESP32-S3 replaces the Arduino+Pi idea entirely** for the "servo + voice" board. The
**ESP32-S3-BOX-3** is especially tidy — it's literally a smart-speaker devkit (mics + LCD + LEDs),
so it can be your voice + screen module out of the box, with the ESP32 also driving the servo bus.

### Why ESP32 (not a Pi) is *better for exhibition*
- **Instant-on, no crashes.** An ESP32 has no OS / no SD card, so it boots in a second and can't
  suffer SD-card corruption — the #1 cause of dead Pi exhibits after days of power-cycling.
- **Auto-recovers from power cuts.** Visitors and cleaners will unplug things; an MCU just
  re-runs and reconnects. A Pi needs a clean shutdown and a longer boot.
- **Hidden brain box.** For a multi-day exhibit, don't tie up your laptop — run the VLM/CV +
  Whisper on a cheap **mini-PC (Intel N100, ~$150)** or NUC, tucked out of sight, 24/7. (If your
  VLM is an API call, the local compute is light anyway — mostly the CV.)
- **Cut the camera tether.** A wired USB camera limits pan (cable tangle, §3) and looks messy at
  a booth. For exhibition consider a **WiFi/IP camera** (or ESP32-CAM) so the head can rotate
  freely and there's one less wire — trading some image quality/latency for tidiness. (Keep the
  USB cam for the high-quality study; the WiFi cam is the exhibit option.)
- **Clean power.** Separate 6 V servo supply + a powered USB hub; design so a power-cycle brings
  everything back unattended.

**Bottom line:** on the robot, use an **ESP32-S3** (or the **ESP32-S3-BOX-3** for mics+LCD+LEDs in
one). Keep Whisper + the VLM/CV on a **hidden laptop or N100 mini-PC**. Reach for a **Pi only if
you insist on running speech-to-text on the robot itself** — and accept it'll be either slow
(Zero 2) or pricier (Pi 5). For a robust, cheap, tidy exhibit, ESP32 + hidden mini-PC wins.

## 7. ESP32-S3 vs Pi Zero 2 W — and can the M5Stack CoreS3 be the board?

**They're different *categories*, not two versions of the same thing:**

| | **ESP32-S3** | **Pi Zero 2 W** |
|---|---|---|
| What it is | a **microcontroller** (no OS) | a tiny **Linux computer** |
| CPU / RAM | dual-core 240 MHz, ~512 KB + up to 8 MB PSRAM | quad-core 1 GHz, 512 MB RAM |
| Runs | Arduino / ESP-IDF, bare-metal — **no Python/Linux, can't run Whisper** | full Linux, Python, OpenCV, **Whisper tiny (slow, ~5 s)** |
| Boot / reliability | **instant-on, no SD card, can't corrupt, real-time** | ~20–30 s boot from SD, **SD-corruption risk**, not real-time |
| Power | very low (tens of mA) | higher (≈0.5–1 W+) |
| Best at | **servos, sensors, LED, mic capture + stream, screen** | **computing** (STT/CV) — at the cost of robustness |

**Which is better — for *your* robot board?** The board's job is servos + voice I/O + screen +
LED, and the **brain is the laptop**. That is exactly the ESP32's strength and the Pi's weakness
(Linux can't do precise servo timing and is fragile under exhibition power-cycling). So
**ESP32-S3 is better for your case.** A Pi Zero 2 W only wins if you *must* run speech-to-text
**on the robot** with no laptop in the room — and even then it's slow. They're often used
*together* in big robots (Pi = brain, MCU = motors), but since your laptop is the brain, you only
need the MCU.

### Yes — the M5Stack CoreS3 is an excellent fit (it IS an ESP32-S3, integrated)
The CoreS3 is an **ESP32-S3** with, built in: a **2" touchscreen**, **dual microphones + speaker**,
a 0.3 MP camera, IMU, SD, RTC, and Grove/M-BUS ports. It's essentially the all-in-one version of
the ESP32-S3-BOX I recommended — so it can be your on-robot board directly:
- **Screen** → the readout / live transcript / the catch thumbnail (a *readout*, **not** a drawn
  face — keep the honest eye on the USB camera, `HEAD_AND_READOUT.md`).
- **Dual mics** → voice capture (better far-field, possible direction-of-arrival), **push-to-talk
  via the touchscreen**; stream audio over WiFi to Whisper on the laptop.
- **Touchscreen** → also gives you the keep/not-this taps and the eagerness control for free.
- **Speaker** → optional one-line TTS; **Grove** → WS2812 LED antenna + buzzer.
- **Servos** → drive the SCS serial bus from a **Grove UART + a bus-servo adapter**, *or* let the
  **laptop drive the servos via a USB adapter** and use the CoreS3 only for voice/screen/LED.
- **Bonus:** battery + tidy enclosure + instant-on = **exhibition-friendly**.

**Two caveats:** (1) the CoreS3's **own camera is only 0.3 MP** — keep your high-quality **USB
camera on the laptop** for perception; don't use the CoreS3 cam as the eye. (2) Like any ESP32 it
**can't run Whisper** — it streams audio to the laptop. **Power the servos from a separate 6 V
supply**, not the CoreS3.

**Bottom line:** if you have a CoreS3, use it — it covers screen + voice + LED (and optionally the
servo bus) in one robust, exhibition-ready unit, with the USB camera + Whisper + VLM/CV on the
hidden laptop/mini-PC.

---

## Sources
- M5Stack **CoreS3**: ESP32-S3 (240 MHz, 16 MB flash / 8 MB PSRAM), 2" 320×240 cap-touch IPS,
  0.3 MP GC0308 cam, **dual mics + 1 W speaker**, IMU, microSD, RTC, 2× Grove + M-BUS.
  https://docs.m5stack.com/en/core/CoreS3 · https://www.cnx-software.com/2023/05/05/60-m5stack-cores3-esp32-s3-iot-controller-comes-with-2-inch-display-vga-camera-multiple-sensors/
- *Best Home Assistant Voice Satellites 2026* / CNX Software — **ESP32-S3-BOX-3** (dual-mic array,
  LCD, RGB LEDs, on-chip microWakeWord NPU) streams audio to **server-side Whisper** (Wyoming);
  **Pi Zero 2 W ~$28** runs tiny-Whisper but slow (~5 s); Pi 5 fast but pricier.
  https://www.smarthomeexplorer.com/guides/best-home-assistant-voice-satellite-2026 ·
  https://www.cnx-software.com/2025/08/30/esp32-s3-audio-board-smart-speaker-devkit-dual-mic-array-lcd-camera-rgb-leds/
- FEETECH **SCS0009**: 4–7.4 V, 2.3 kg·cm stall / 0.75 rated, **300°** + continuous motor mode,
  10-bit magnetic feedback, TTL serial 1 Mbps daisy-chain.
  https://www.seeedstudio.com/Feetech-SCS0009-Servo-p-6535.html ·
  https://evelta.com/scs0009-6v-2-3kg-300deg-serial-bus-servo-motor/
- MIT Media Lab, **The Stochastic Parrot: a physical AI Cohabitant** — characterful, autonomous,
  ambient; reverses the assistant dynamic.
  https://www.media.mit.edu/projects/the-stochastic-parrot/overview/
- Project internal: `VOICE_CONTROL.md` (mic→laptop→Whisper→planner), `CHANNEL_MATRIX.md`,
  `RELATED_WORK_hri.md` (add the cohabitant neighbor).
