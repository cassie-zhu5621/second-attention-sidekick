# Second Attention — Sidekick (hardware milestone)

A small **placed companion** that sits in a shared space, slowly **pans/tilts to look
around**, and captures frames when it's **still** (observing) — skipping the blurry ones
while it's moving (searching). Frames stream to a laptop over Wi-Fi and are saved as a
dataset. Stillness now; an "is this interesting?" brain comes later (laptop side).

```
  Arduino Uno R4 ──PWM──► 2× MG90S  (pan-tilt: glide = searching, 10s dwell = observing)
  M5 Unit CamS3-5MP ──Wi-Fi (MJPEG)──► laptop collector ──► dataset/ + ZZZ web viewer
```

The two boards are **not wired together**. The camera just streams; the laptop reads the
stream, detects stillness, and saves only still frames.

## Repo layout

| Path | What |
|---|---|
| `firmware/unitcams3_webcam/` | Camera firmware (M5 Unit CamS3-5MP). Streams MJPEG at `http://<cam>/`, mDNS name `sidekick-cam.local`. |
| `firmware/pantilt_r4/` | Pan-tilt firmware (Arduino Uno R4 + 2× MG90S). Button toggles a slow observe-sweep. |
| `sidekick_collector.py` | Laptop: reads the camera stream, stillness detection, saves dataset, serves the web viewer. |
| `webui/index.html` | Black / white / acid-green dataset viewer (live preview + capture grid). |
| `hardware/` | Pan-tilt CAD (STL + parametric scripts), LEGO camera mount, assembly diagram. |

## Hardware

- **M5Stack Unit CamS3-5MP** (PY260 sensor) — the "eye". Powered by USB-C (charger / power bank).
- **Arduino Uno R4** + **2× MG90S** servos — the pan-tilt head. 5V signal is more reliable
  for MG90S than 3.3V. Power the servos from a **5V 2–3A** source, common ground with the R4.
- Camera clips to the tilt head via a **LEGO stud plate** (`hardware/lego_mount.py`).

Notes learned the hard way: the PY260 streams reliably at **UXGA (1600×1200)** with the
official web_cam firmware; hand-rolled `esp_camera_init` would init but not stream. Servos
need an external 5V supply (USB bus browns out); ease the motion to avoid current spikes.

## Setup

### 1. Camera
Arduino IDE → Board **M5UnitCAMS3**, USB CDC On Boot **Enabled**, PSRAM **OPI PSRAM**.
Open `firmware/unitcams3_webcam/unitcams3_webcam.ino`, set your Wi-Fi `ssid`/`password`, upload.
It joins your Wi-Fi and streams at `http://sidekick-cam.local/` (mDNS) — no IP hunting.

### 2. Pan-tilt
Arduino IDE → Board **Arduino Uno R4**. Open `firmware/pantilt_r4/pantilt_r4.ino`, upload.
Wiring: PAN signal → D9, TILT → D10, servo V+ → external 5V, GND shared with R4, button D2↔GND.
Tap the button to start/stop the observe-sweep.

### 3. Laptop collector (the dataset + viewer)
Needs Python with `requests`, `Pillow`, `numpy`.
```bash
python3 sidekick_collector.py            # connects to sidekick-cam.local
# or:  python3 sidekick_collector.py --camera http://192.168.1.50
```
Open **http://localhost:8000**, press **START**. Frames save to `dataset/` only while the
view is still. The camera serves **one viewer at a time**, so don't also open its IP in a browser.

Tuning (flags): `--thresh` stillness sensitivity, `--min-gap` min seconds between saves,
`--poll` how often to check.

## License
TODO (e.g. MIT)
