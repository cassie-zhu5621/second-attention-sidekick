# Second Attention — Sidekick （Under Development）

A small **placed companion** that sits in a shared space, slowly **pans/tilts to look
around**, and captures interesting frames when it's **still** (observing) — skipping the blurry， boring ones
while it's moving (searching). Frames stream to a laptop over Wi-Fi and are saved as a
dataset. Stillness now; an "is an interesting moment?" brain comes later (laptop side).

```
  Arduino Uno R4 ──PWM──► 2× MG90S  (pan-tilt: glide = searching, 10s dwell = observing)
  M5 Unit CamS3-5MP ──Wi-Fi (MJPEG)──► laptop collector ──► dataset/ + web viewer
```

The two boards are **not wired together**. The camera just streams; the laptop reads the
stream, detects stillness, and saves only still frames.

## Repo layout

**`firmware/`** (Arduino)
| Path | What |
|---|---|
| `pantilt_r4/` | **Pan-tilt — LIVE mode.** Pure muscle: takes `pan,tilt` over USB serial from the laptop brain; auto-relaxes the servos when idle (no buzz/heat). Use this for the real-time loop. |
| `pantilt_sweep/` | **Pan-tilt — DATASET mode.** Autonomous: on power-up it sweeps a grid and dwells a few seconds at each spot (no laptop). Use this for collecting a dataset without scoring. *(Flash whichever matches the task; they're the same hardware.)* |
| `unitcams3_stream/` | Camera firmware (M5 CamS3-5MP) — MJPEG video stream. **One firmware for both cameras**; set `HOSTNAME` at the top per unit: the loop/eye camera = `sidekick-loop`, the dataset-collector camera = `sidekick-cam`. (That mDNS name is the *only* difference between the two cameras.) |

**`brain/`** (laptop, real-time)
| Path | What |
|---|---|
| `live_loop.py` | Search → notice → dwell state machine + web control panel (`localhost:8090`). worth = `taste.compose(dims, weights)`. |
| `live_brain.py` | VLM scores the 9 taste dimensions + an optional content `match`. |
| `voice_agent.py` | Laptop-mic wake word "hey potato" (VAD) → sets the taste/content. |
| `set_preference.py` | Type a preference into `preference.txt` (panel/voice share this file). |
| `taste.py`, `brain.py`, `session.py`, `loop.py`, `regress.py` … | The 9-dimension composer + offline tools (dataset will regress these weights). |

**`collector/`** (laptop)
| Path | What |
|---|---|
| `sidekick_collector.py` + `webui/index.html` | Dataset collector + black/white/acid-green viewer. |

`hardware/` — pan-tilt CAD (STL + scripts), LEGO camera mount, assembly diagram.
Runtime output (`dataset/`, `live_captures/`, `last_record.wav`) is git-ignored.

## Hardware

- **M5Stack Unit CamS3-5MP** (PY260 sensor) — the "eye". Powered by USB-C (charger / power bank).
- **Arduino Uno R4** + **2× MG90S** servos — the pan-tilt head. 5V signal is more reliable
  for MG90S than 3.3V. Power the servos from a **5V 2–3A** source, common ground with the R4.
- Camera clips to the tilt head via a **LEGO stud plate** (`hardware/lego_mount.py`).

Notes learned the hard way: the PY260 streams reliably at **UXGA (1600×1200)** with the
official web_cam firmware; hand-rolled `esp_camera_init` would init but not stream. 

## New environment / new location — what to (re)configure

⚠️ **Camera Wi-Fi — must edit + RE-FLASH.** The camera firmware has hard-coded Wi-Fi (no
captive portal). On a new network: open `firmware/unitcams3_stream/unitcams3_stream.ino`,
set `ssid` / `password`, set `HOSTNAME` (`sidekick-loop` = eye/loop camera, `sidekick-cam`
= collector camera), and **re-flash each camera**. This is the **only file with Wi-Fi** —
the pan-tilt firmwares are serial-only, nothing to change there.

**Arduino IDE settings (per flash):**
- Camera → Board **M5UnitCAMS3**, PSRAM **OPI PSRAM**, USB CDC On Boot **Enabled**.
- Pan-tilt → Board **Arduino Uno R4**.

**Laptop (once per machine):**
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-...        # the brain's VLM scoring needs it
```
- First voice run: macOS asks for **microphone permission** — allow it. If `sounddevice`
  fails to build, `brew install portaudio` then reinstall it.
- Cameras are found by mDNS (`*.local`) so there's no IP to set — but the laptop and cameras
  must be on the **same Wi-Fi**, and each camera serves **one viewer at a time**.

## Run

**Flash:** camera = `firmware/unitcams3_stream` (set `HOSTNAME`); pan-tilt = `firmware/pantilt_r4`
for the live loop, **or** `firmware/pantilt_sweep` for dataset collection.

### A. Dataset collection (no brain)
Pan-tilt on `pantilt_sweep` (auto-sweeps), collector camera = `sidekick-cam`. Then:
```bash
python3 sidekick_collector.py --camera http://sidekick-cam.local
```
Open **http://localhost:8000**, press **START** → still frames save to `dataset/`.

### B. Live brain loop (the demo)
Pan-tilt on `pantilt_r4` (R4 on USB), eye camera = `sidekick-loop` (on power). Two terminals:
```bash
python3 brain/live_loop.py      # search / notice / dwell + control panel at localhost:8090
python3 brain/voice_agent.py    # say "hey potato", then a preference
```
Open **http://localhost:8090** — live dimensions, weight tuning, threshold sliders, event sounds.
Type or speak the taste: "more story, less clutter" (tunes dimensions) or "animals" (content lean).

## License
TODO (e.g. MIT)
