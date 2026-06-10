# System map — files, camera, pan-tilt, architecture

The current built system: where every file lives, how the camera and pan-tilt connect, and what the
architecture rests on. This is a working BASE, not frozen — refactor freely on top of it.

## Directory map (repo root: second-attention-sidekick/)
```
firmware/                                  # microcontroller code (Arduino IDE)
  unitcams3_stream/unitcams3_stream.ino    # CAMERA: M5 UnitCam S3 — streams MJPEG over WiFi
  pantilt_r4/pantilt_r4.ino                # PAN-TILT: Uno R4 + 2x MG90S, serial "dPan,dTilt"; TILT_MAX=135
  pantilt_sweep/pantilt_sweep.ino          #   (alternate sweep firmware)
config_gate/                               # the live system (everything runs from here)
  # === THE VLM-FIRST SYSTEM (current; relation_table.md architecture) ===
  attention_system.py# MAIN: context -> VLM plan -> CV watch -> record; web UI; hot re-plan;
                     #   --plan-frame (situated planning) / --spec-file (deterministic tests)
  planner.py         # VLM planner: context (+frame) -> watch-spec JSON (2 grammars, validation)
  relations.py       # RelationEngine: frame -> truth vector over vocabulary rows 1-11
  watch_exec.py      # WatchExecutor: all/any/not/then + time windows + persist + cooldown
  attention_ui.py    # web UI for THIS pipeline: live + THE PLAN panel + feed + context box
  gaze.py            # direction primitives: head-pose / arm rays; rows 1-4 + neon draw helpers
  perceive.py        # Detection + detectors (yolo/yoloworld/gdino) + make_detector() factory
  judge.py           # back-end VLM judge (confirm step) + ReportabilityTaste
  # --- studies & paper artifacts (run from config_gate/: python studies/<script>.py) ---
  studies/planner_study.py   # preliminary study: scenarios x temps x grammars
  studies/compare_plan.py    # LLM-vs-VLM ablation: text-only vs text+frame
  studies/make_report_figures.py  # regenerates results/figures/F1-F8
  results/           # study jsonl/md + figures (COMMITTED: paper data)
  test_specs/        # canned watch-specs r1-r11 + combo (per-item live testing)
  scenes/            # still frames for plan ablations
  # --- hardware adapters ---
  rig.py             # GimbalRig: move_to() serial + get_frame() M5 MJPEG; calibration; nod()
  cam_test.py        # camera-only stream test;  rig_moves.py  # named motion test
  # --- previous-generation demos (still runnable; deps of attention_robot) ---
  attention_demo.py  # fixed-cam relations->gate->VLM (also: frame_source / publish helpers)
  attention_robot.py # rig: scan -> confirm -> STOP & WATCH at pose -> resume
  robot_demo.py      # OLD generic structural gate on the rig (+ orient_target helper)
  web_demo.py        # old web feed (taste box); config_surprise.py / viz.py: its gate + overlay
  run_perception.py  # batch detector A/B on saved frames
  # --- docs/ ---
  docs/SYSTEM_MAP.md           # THIS file
  docs/relation_table.md       # vocabulary v2 (11 rows) + grammars + grounding (paper-bound)
  docs/TEST_PLAN_system.md     # live test record sheet (= detectability mini-study data)
  docs/TEST_PLAN_gaze.md       # earlier gaze-branch checklist
  docs/BRANCH_gaze_handoff.md  # the gaze branch: concept pivot + history
  docs/grounding_map.md        # references / theory grounding (incl. Media Equation)
  docs/elicitation_form.md     # Google-Form text for the scenario elicitation round
archive/old_gate/                          # retired config-surprise experiments & docs
```

## Camera (RGB only — no depth)
- **M5 UnitCam S3**, firmware `firmware/unitcams3_stream/unitcams3_stream.ino`.
- Streams **motion-JPEG at `http://<ip>/`** over WiFi. **ONE viewer at a time.**
- Resolution **UXGA 1600×1200, ~2 fps** (ESP32 limit). IP changes with the network (was `172.20.10.2`
  on a phone hotspot). Get the IP from the M5's boot serial print, or the hotspot's device list.
- Read it with the MJPEG reader (see `cam_test.py` / `rig.py` `_MJPEGGrabber`). Do NOT use
  `cv2.VideoCapture(url)` — it buffers stale frames.
- Quick check: `python cam_test.py --camera http://<ip>/`

## Pan-tilt (servos over USB serial)
- **Arduino Uno R4 + 2× MG90S**, firmware `firmware/pantilt_r4/pantilt_r4.ino`.
- Wiring: PAN→D9, TILT→D10, servo V+→external 5V, GND shared, R4 on USB.
- Serial **115200**, command `"dPan,dTilt\n"` (degrees relative to centre); the board eases to target
  and auto-relaxes when idle. `TILT_MAX` raised 125→135 for more down-look.
- Laptop side = `rig.py` `GimbalRig`: `move_to(pan,tilt)` (serial) + `get_frame()` (M5 MJPEG) + `nod()`.
- **Convention everywhere: +pan = RIGHT, +tilt = DOWN, 0 = level.**
- Calibration measured on the lab rig: `PAN_SIGN=-1` (pan was mirrored), `TILT_TRIM=30` (camera mounted
  ~30° up), `TILT_LIMIT=45` → usable down-look ~+12°.
- macOS gotchas: use `/dev/cu.*` (not `tty.*`); the VS Code **Serial Monitor** holds the port — close it
  or `lsof -t /dev/cu.usbmodem101 | xargs kill -9`. The `objc ... cv2/av dylib` warning is harmless.
- Quick check: `python rig_moves.py --camera http://<ip>/ --port /dev/cu.usbmodem101`

## Architecture — the only fixed contracts
Everything else is swappable. The system depends on just two interfaces:
1. **Detector**: `.detect(image) -> List[Detection]`  (Detection = label, box, score).
   Implementations: `YoloWorldDetector` (open-vocab), `YoloDetector` (closed COCO-80, robust),
   `GroundingDinoDetector` (accurate, slow). Pick via `make_detector(kind, vocab, conf, device)`.
2. **Rig**: `move_to(pan, tilt)` + `get_frame()`  (`GimbalRig` for hardware, `MockRig` for tests).

Keep those two contracts and you can rebuild the rest — gate, scan loop, relation logic, detector,
UI are all free to change. (e.g. the gaze branch replaces the generic structural gate with a
relation-specific one without touching the detector or rig.)

## Run cheatsheet
```bash
cd second-attention-sidekick/config_gate
python cam_test.py  --camera http://<ip>/                                  # camera only
python rig_moves.py --camera http://<ip>/ --port /dev/cu.usbmodem101       # rig motion
export ANTHROPIC_API_KEY=sk-...
python robot_demo.py --real --serve --no-save                              # full demo (test, no disk)
python run_perception.py --images <folder> --detector yolo|gdino|yoloworld # offline detector A/B
```
Deps: ultralytics (yolo/-world), transformers (gdino, depth), anthropic (VLM), pyserial, opencv,
requests, mediapipe (gaze branch).
