> ⚠️ SUPERSEDED — the current consolidated master is **`config_gate/PROJECT_HANDOFF.md`** (read that
> first). Kept only for early gaze-branch history. (Note: robot_demo.py / attention_robot.py /
> run_perception.py mentioned below were removed in the v1 cleanup — use `attention_system.py --rig`.)

# Branch handoff — Gaze / Joint-Attention ("what we look at together")

This is the starting point for a NEW branch. Read this + the memory files; the code below already
exists and runs. Hardware is calibrated. The pivot and the next steps are at the bottom.

## The pivot (why this branch exists)
- **Old approach** (config-surprise gate): detect *all* geometric relations → scene graph → fire on
  generic structural change. Problem seen on real lab frames: relation **explosion**, unreadable,
  "a functional list", not an experience.
- **New approach**: hand-pick a SMALL set of relations that are **(a) easy to trigger reliably and
  (b) high theoretical grounding**; each becomes a SPECIFIC gate. At each scan pose the robot first
  asks "is THIS relation present?" → if yes, VLM confirms + narrates → robot **joins the attention**.
  The interaction is designed as an experience about *"what we look at together,"* not a relation dump.
- **Start with #5 gazing-at → #6 joint-attention** (more relations to follow, picked from the
  template table). Theory: gaze cueing (Friesen & Kingstone 1998), joint attention (Tomasello;
  Moore & Dunham 1995), HRI joint attention; ties to [[ref-media-equation]] (legible gaze = social
  cue) and "second attention" = attending to others' attention.

## The architecture decision (the "which is scientific" question — resolved)
- Detectors (YOLO-World / closed-YOLO / Grounding DINO) only **localize objects/phrases**; **none
  detects relations.** DINO fed a relational phrase still just localizes the nouns; it does NOT
  verify the relation — so DINO-as-relation-detector is unsound. DINO's real use = grounding rich
  noun phrases to better OBJECT slots.
- So: **detector fills object slots A/B; relation R is computed geometrically (cheap candidate) →
  VLM confirms (precision).** This is the existing gate→VLM split, now firing on a *designed* relation.
- **Pointing/attention relations need a DIRECTION primitive** (head/gaze ray, hand/arm vector) that
  object boxes can't give. Add a lightweight pose/gaze model (MediaPipe FaceMesh/Pose, or YOLO-pose).
- **No depth camera needed**: head-pose → 2D ray in the image plane; ray-hits-box and multi-ray
  convergence are 2D tests. Depth would only disambiguate front/back, which the VLM covers.
- Her template table's "trigger signal" column is already ray/geometry based (#4 hand-ray-hits-B,
  #5 head-orientation-ray-hit, #6 multi-ray-converge) → it already commits to the geometric path.

## What exists now (all in config_gate/, runnable on Cassie's Mac)
- **perceive.py** — `Detection`; `build_graph` (geometric relations near/on/inside; `inside` now
  whitelisted to real CONTAINER_TYPES so it no longer explodes); `StaticLatch` (latch immovable
  objects, stop flicker events). Detectors: `YoloWorldDetector` (open-vocab), `YoloDetector`
  (closed COCO-80, robust "place anywhere", misses instead of mislabels), `GroundingDinoDetector`
  (HF grounding-dino-tiny, accurate/clean but slow). Factory: `make_detector(kind, vocab, conf, device)`
  with kind ∈ {yoloworld, yolo, gdino}.
- **config_surprise.py** — `TemporalConfigGate` (structural-change + habituation). From the OLD
  approach; the new branch gates on a SPECIFIC relation instead, but reuse the habituation idea
  (don't re-fire the same attention).
- **judge.py** — `judge(jpeg, graph, taste, delta_added)` → {worth, why, note}; `ReportabilityTaste`
  (editable axes people/relevance/consequence/continuity, .nudge/.compose). Offline: SECONDATTN_OFFLINE=1.
- **viz.py** — `draw_overlay` neon overlay (boxes, relation lines, HUD).
- **rig.py** — `GimbalRig`: `move_to(pan,tilt)` over serial (firmware pantilt_r4.ino), `get_frame()`
  from M5 MJPEG (WiFi, fresh-frame-after-move), `nod()`. Convention: **+pan=right, +tilt=down, 0=level**.
  Calibration: `PAN_SIGN=-1`, `TILT_TRIM=30`, `TILT_LIMIT=45`. Standalone test in __main__.
- **rig_moves.py** — named motion test: level/right/left/up/down/nod.
- **cam_test.py** — pure M5 stream test + fps (no detection).
- **robot_demo.py** — SCAN→LOOK→REPORT→nod loop; PER-POSE memory (each heading its own gate+latch =
  spatial memory); **dwell-and-sample** (`--look-secs`, default 2.5s, several frames/pose so the gate
  gets enough samples). Flags: `--real`, `--serve` (reuses web_demo UI: live overlay + feed + taste
  box, in-memory thumbs), `--no-save` (test mode, no disk), `--detector`, `--offline`, `--worth`,
  `--threshold`, `--min-area`, `--k-pan/--k-tilt`, `--dwell`. `orient_target` uses +pan=right/+tilt=down.
- **web_demo.py** — fixed-camera web feed (the product surface). In-memory thumb store added.
- **depth.py** — optional Depth-Anything (NOT needed for this branch).
- **grounding_map.md** — references table (incl. the Media Equation row).

## System layout, camera, pan-tilt, architecture
See **`SYSTEM_MAP.md`** — full directory map, camera (M5 MJPEG) and pan-tilt (rig.py + firmware) wiring,
calibration values, and the two fixed contracts (Detector `.detect()` + rig `move_to`/`get_frame`).
The architecture is a working BASE, not frozen — refactor freely on this branch.

## Hardware + calibration (lab rig, measured)
- Camera: **M5 UnitCam S3**, MJPEG `http://<ip>/` (was `172.20.10.2` on phone hotspot — IP changes!),
  UXGA 1600×1200 ~2 fps, **ONE viewer at a time**.
- Servos: **Arduino Uno R4 + 2× MG90S**, firmware `firmware/pantilt_r4/pantilt_r4.ino` (TILT_MAX
  raised 125→135 for more down-look), serial `/dev/cu.usbmodem101` @115200, command `"dPan,dTilt\n"`
  relative to centre; board eases + auto-relaxes.
- pan is mirrored (`PAN_SIGN=-1`); camera mounted ~30° up (`TILT_TRIM=30`); usable down-look ~+12°.
- macOS serial gotchas: use `/dev/cu.*` (not tty.*); the VS Code **Serial Monitor** holds the port —
  close it or `lsof -t /dev/cu.usbmodem101 | xargs kill -9`. The `objc ... cv2/av dylib` warning is harmless.

## Run (current)
```bash
cd second-attention-sidekick/config_gate
python cam_test.py  --camera http://<ip>/                                   # camera only
python rig_moves.py --camera http://<ip>/ --port /dev/cu.usbmodem101        # rig motion
export ANTHROPIC_API_KEY=sk-...
python robot_demo.py --real --serve --no-save                               # full demo (test, no disk)
python run_perception.py --images <folder> --detector yolo|gdino|yoloworld  # offline detector A/B
```
Deps: ultralytics (yolo/-world), transformers (gdino, depth), anthropic (VLM), pyserial, opencv,
requests. **This branch will add: mediapipe** (head-pose/gaze ray).

## Next steps (this branch)
1. Add a **head-pose / gaze ray** primitive (MediaPipe FaceMesh or Pose) → per-person 2D gaze ray.
2. **gazing-at (#5)**: a person's ray hits object B's box within an angular tolerance → candidate.
3. **joint-attention (#6)**: ≥2 rays converge near a common target/region → candidate (stronger signal).
4. New gate = "is this relation present at this pose?" (replaces the generic structural gate for this
   branch); habituate repeated identical attention so it doesn't re-fire.
5. On candidate → VLM confirms + narrates → robot **orients to the gaze target (joins attention)** + nod.
6. Later: **click / touch to LOCK** a relation / an object set / relation+objects ("today just watch
   this group") = filter the gate to fire only on the selection.
7. Add more relations from the template table the same way (object slots + trigger signal + VLM confirm).

## Template table (19 relations) — axes & how to pick
Axes: 意外/surprise, 指向/pointing, 转变/transition, 不对称/asymmetry, 双重/duality, 拟人/anthropomorphism.
Pick by **(easy to trigger) × (high theory grounding)**. Config/surprise rows (co-occurrence, on/in,
stacked, at-edge, about-to-contact) = boxes + geometry only (fast, no pose). Pointing/attention rows
(reaching, gazing, joint-attention, looking-at, offering, eye-contact) = boxes **+ pose/gaze ray**
(the experiential heart of this branch).
