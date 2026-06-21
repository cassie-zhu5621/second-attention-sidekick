# Camera (for low-latency MediaPipe) + Button/LED on the CoreS3

Concrete part picks. Two takeaways: **a wired USB (UVC) camera is the right call for fast,
stable, low-latency MediaPipe** (and latency is half software), and on the CoreS3 you barely
need external parts — its **speaker, mic, touchscreen, IMU are built in**. Last updated: June 2026.

---

## 1. Camera — yes, USB (UVC) is best for MediaPipe

**Why USB beats the alternatives for *latency*:**
- **USB UVC (wired)** = the camera streams straight into the laptop, **no network, no re-encode** →
  lowest, most *stable* latency (tens of ms). Best for MediaPipe.
- **WiFi / IP camera** (incl. the old M5 MJPEG, ESP32-CAM) = adds encode + network + decode delay
  and jitter → worse for real-time face/pose. (Fine only for a tidy *exhibit*, not for accuracy.)
- So for the study where MediaPipe quality matters, **wired USB UVC.**

**What MediaPipe actually needs (don't over-buy):** 30–60 fps, **720p is plenty** (Face/Pose run
great at 640×480–1280×720), MJPEG output, decent indoor low-light, a **modest FOV (~78–90°)** with
**low distortion** (ultra-wide fisheye hurts the gaze/pose geometry and your solvePnP ray). Higher
**fps (60)** helps more than higher resolution — it cuts motion blur for gaze.

**Specific models (型号):**
| Use | Pick | Why |
|---|---|---|
| **Quick dev / safest** | **Logitech C922** (720p@**60**) or **C920** (1080p@30) | plug-and-play UVC, the most OpenCV-proven webcams, low latency, ~¥6–10k |
| **Low-light / fast motion** | **Razer Kiyo Pro** (1080p@60, good in dim rooms) | better sensor; pricier |
| **Embed into the head (lens = the eye)** | **ELP USB module** (e.g. ELP-USBFHD01M, swappable lens — pick a ~90° low-distortion lens) or **Arducam IMX291 USB** (low-light, wide) | a **bare board + lens** fits the enclosure and *is* the honest single eye, unlike a big webcam shell |
| (only if fast tracking is critical) | Arducam **OV9281 global-shutter USB** (mono) | no motion skew on a moving head — but mono, niche; usually unneeded |

→ **Recommendation:** a **Logitech C922** for development now; switch to an **ELP/Arducam board
camera** when you build it into the head (so the lens reads as the eye). Avoid WiFi cams for the
MediaPipe path.

**Latency is half *software* — do these or the camera won't help:**
- Force **MJPEG**: `cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))` (lets USB do
  high fps).
- **Drop stale frames**: `cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)`, and/or grab in a **thread that
  keeps only the latest frame** (your existing MJPEG-grabber pattern — keep it).
- Set **resolution + fps explicitly** (don't accept defaults); on **macOS** use the AVFoundation
  backend (`cv2.CAP_AVFOUNDATION`).
- **Settle the head after a move** before judging a frame (you already wait for a fresh frame seq —
  keep that; it avoids motion-blurred gaze).
- Prefer **USB 3** port if the camera is USB3 (uncompressed higher-res headroom), but USB2 + MJPEG
  720p@60 is already fine.

---

## 2. Button + LED on the CoreS3 — most of it is already onboard

The CoreS3 connects peripherals through **Grove ports** (plug-in, 3.3 V logic). But check what you
*don't* need to add:

| Function | Best option | Add hardware? |
|---|---|---|
| **Push-to-talk button** | use the **touchscreen** as the button (zero hardware) — or an **M5Stack Button Unit** (Grove, plug-in) if you want a physical click | none / one Grove unit |
| **Buzzer / chirps** | the CoreS3's **built-in speaker** (`M5.Speaker.tone()`) | **none** |
| **Mic, screen, IMU** | **built in** | none |
| **LED antenna** | a **bare addressable RGB pixel** at the stalk tip (PL9823 5 mm / NeoPixel through-hole / SK6812) — **NOT** the packaged M5 LED Unit | **one** tiny part |

So the **only external part you really need is the LED antenna pixel.**

### ⚠️ Correction: don't use the packaged "M5 RGB LED Unit" for the antenna
The M5Stack **RGB LED Unit** is a WS2812 inside a **plastic Grove housing** — convenient on a
desk, but **far too bulky to embed in a thin, moving antenna**. For a glowing antenna *tip* on the
head you want a **bare addressable LED** soldered to thin wires (exactly like the single LED on a
wire you already have in the prototype — just upgrade it to an RGB pixel so it can do the
warm/cool/amber/bright palette).

**Pick (型号):**
- **PL9823 (5 mm through-hole)** — a WS2812-compatible pixel shaped like a classic 5 mm LED bulb;
  ideal "glow ball" for an antenna tip, cheapest, easy to diffuse.
- **Adafruit NeoPixel through-hole 5 mm**, or the tiny **NeoPixel Mini (3535) / Nano (2427)** SMD
  if you want it smaller.
- **SK6812** (a touch more tolerant of 3.3 V data than WS2812B).

**Wiring (one pixel at the stalk tip):**
- 3 **thin, flexible** wires down the stalk: **5 V (or ~4 V)**, **GND**, **DATA**.
- **DATA → a CoreS3 GPIO** (e.g. Grove Port B / an M-BUS pin); drive with `Adafruit_NeoPixel` /
  `FastLED` / `M5.dis`-style libs.
- **Power: one pixel ≈ 60 mA max** — small enough to run **from the CoreS3's 5 V**, common ground.
  (Servos no; a single LED yes.)
- **3.3 V-data caveat:** WS2812 wants data ≈0.7×VDD. At 5 V supply, 3.3 V data is *marginal* — for
  one short-run LED it often works; if it flickers, either **power the pixel at ~3.7–4.3 V** (then
  3.3 V data is safely above threshold) or use **SK6812** / a tiny level-shifter.
- **It's on a moving head:** use **stranded silicone 30 AWG** wire and leave a **service loop** so
  the pan/tilt flexing doesn't fatigue-break the joint. Add a frosted cap / ping-pong-style
  diffuser at the tip for a soft glow.

For the keep/not-this taps and eagerness control, the **touchscreen** covers them.

### Should you fix them on a breadboard? — No, not for the robot.
- A **breadboard is fine for a quick bench test**, but it's **unreliable on a moving robot or at an
  exhibition** — vibration and handling pop the jumper wires out. Don't ship on a breadboard.
- **Best: M5Stack Grove Units** (Button Unit, RGB LED Unit) — they **plug in with a Grove cable, no
  soldering, no breadboard**, and are robust. This is the tidy, exhibition-safe path and matches
  the CoreS3 ecosystem.
- **For a permanent custom build:** **solder** the LED (and button, if not a unit) to a small
  **proto/perfboard** or a cut Grove cable — solid joints, no loose wires.
- If you *do* breadboard a raw button: one GPIO with `INPUT_PULLUP`, button to **GND** (no resistor
  needed). A raw WS2812: data to a GPIO, its own **5 V** + **common ground**. But the **Grove units
  avoid all of this.**

---

## 2b. Audio — what the CoreS3 makes itself, and what the laptop makes

The CoreS3 has a **built-in speaker** (1 W, AW88298) and **dual mics** — so the **ears and the
mouth are already in the body**. The split is the same as everything else: **I/O on the body,
heavy compute on the laptop.**

| Sound | Made by | Embedded in the body? |
|---|---|---|
| **Chirps / beeps / tones** (the 3 event sounds) | **CoreS3 speaker, 100% onboard** — `M5.Speaker.tone(freq, ms)` | **yes** — nothing external |
| **Pre-recorded SFX** (a WAV) | CoreS3 plays a WAV from flash/SD | yes |
| **Spoken voice / TTS** ("found it") — *natural* | **synthesized on the laptop** (Piper / system / cloud TTS) → streamed to the CoreS3 → **played through its speaker** | **yes — the voice comes out of the robot's body**, even though the laptop did the synthesis |
| **Spoken voice — *robotic/retro*** | can run **on-device** (ESP8266SAM / esp-tts) — a SAM-style robot voice | yes, fully onboard (but low fidelity) |
| **Voice IN** (your brief) | mic is **onboard**; **Whisper runs on the laptop** | yes — you talk *to the robot* |

So: **chirps = entirely the CoreS3.** **Talking (natural TTS) = the CoreS3's speaker is the
mouth, but the laptop writes the words** (just like the mic is the ear and the laptop does the
listening). On-device you can only get a *robotic* voice — which, honestly, could even suit a
robot's character if you want a tiny retro "blip-voice," but keep speech sparse (the design is
mostly-silent; chirps + screen carry most of it).

**Enclosure note (so embedding it actually works):** when you put the CoreS3 inside a 3D-printed
body, **leave acoustic openings** — a small grille/holes **over the speaker** (so the chirp gets
out) and **a hole near the mic** (so it can hear you). Don't fully seal it. For a *loud
exhibition* hall you can add a bigger **external speaker** via I2S / an M5 Speaker module, but the
built-in 1 W is plenty for sparse chirps in a quiet room.

## 3. Net bill of materials for the CoreS3 side
- **Camera:** Logitech **C922** (dev) → ELP/Arducam board cam (final), **into the laptop via USB**.
- **CoreS3:** screen + mic + speaker + touchscreen + IMU = **already onboard** (button = touch,
  buzzer = speaker).
- **Add:** **one bare addressable RGB pixel** (PL9823 5 mm / NeoPixel / SK6812) at the antenna tip,
  on thin flex wire — **not** the packaged M5 LED Unit. Optional M5 **Button Unit** if you want a
  physical PTT (else the touchscreen).
- **No breadboard** in the robot — Grove plug-in units (or soldered perfboard for the final form).

---

## Cross-refs
`HEAD_AND_READOUT.md` (the camera *is* the eye), `CHANNEL_MATRIX.md` (LED/buzzer/button roles),
`VOICE_CONTROL.md` (mic + PTT — touchscreen or button), `CORES3_SERVO_MIGRATION.md` (Grove ports A/B/C).
