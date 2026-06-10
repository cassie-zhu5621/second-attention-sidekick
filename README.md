# Second Attention — Sidekick (under development)

A small **placed companion** that watches a shared space *for* you — typically while you
are away. You tell it, in a sentence, what kind of moments matter today; it quietly
watches and records only those, like a considerate observer rather than a surveillance
camera. The research frame is **delegated noticing**: attending to other people's
attention ("second attention") on the owner's behalf.

## Architecture — VLM plans, CV watches

The VLM is a **compiler and auditor, not the runtime**: it never runs per frame.

```
 context (typed; + current frame with --plan-frame)
        │
        ▼
 VLM PLANNER (planner.py) ──► watch-spec JSON: combos over a fixed 11-row vocabulary
        │                      all / any / not / then + time window + "why" + "missing"
        │                      (= the "free" grammar, chosen by the preliminary study;
        │                       a "restricted" OR-of-ANDs arm — a strict subset — is
        │                       kept in planner.py for study reproduction)
        ▼
 CV EXECUTOR (relations.py + watch_exec.py)
   MediaPipe Face/Pose (people) + YOLO/GDINO (object slots)
   → per-frame TRUTH VECTOR over rows 1–11 (logged: relation_log.jsonl)
   → conjunction satisfied (persist + window) → MOMENT recorded → cooldown (habituation)
        │
        ▼
 records + web UI (attention_ui.py: live view · THE PLAN panel · feed · context box)
 optional: VLM confirm step re-checks the frame before recording (--confirm)
```

The vocabulary is **literature-grounded** (Hall, Kendon, Goffman, …) and versioned —
see `config_gate/relation_table.md`. A preliminary study (`planner_study.py`, results in
`config_gate/results/`) validated the context→spec mapping and drove vocabulary v1→v2.

## Quick start

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-...
cd config_gate

python cam_test.py --camera http://<m5-ip>/        # camera alive? (ONE viewer at a time)
echo "I'm away until 6pm; watch who comes to my desk." > context.txt
python attention_system.py --serve --save           # web UI at http://localhost:8000
```

Useful flags: `--camera 0` (laptop webcam) · `--plan-frame` (planner sees the scene) ·
`--spec-file test_specs/r9.json` (skip planner, deterministic testing) · `--offline`
(no API key, fake planner/judge) · `--confirm` (VLM double-checks before recording).

## Repo layout (detail: `config_gate/SYSTEM_MAP.md`)

| Path | What |
|---|---|
| `config_gate/attention_system.py` | **MAIN** — plan → watch → record loop, hot re-plan |
| `config_gate/planner.py` | VLM planner (context → watch-spec; two grammars) |
| `config_gate/relations.py` | relation engine: frame → truth vector rows 1–11 |
| `config_gate/watch_exec.py` | watch-spec executor (windows, persist, cooldown) |
| `config_gate/attention_ui.py` | web UI: live + plan + feed + context box |
| `config_gate/gaze.py`, `perceive.py`, `judge.py` | direction primitives · detectors · confirm judge |
| `config_gate/planner_study.py`, `compare_plan.py`, `make_report_figures.py`, `results/` | studies + paper data/figures |
| `config_gate/relation_table.md`, `TEST_PLAN_system.md` | vocabulary v2 · live-test record sheet |
| `config_gate/rig.py`, `cam_test.py`, `rig_moves.py` | hardware adapters (M5 + pan-tilt) |
| `firmware/` | `unitcams3_stream` (camera MJPEG) · `pantilt_r4` (**keep**: servo firmware for the motion phase) |
| `archive/` | retired generations (old structural gate, 9-dim brain, collector) |

Runtime output (`dataset/`, `feed/`, `weights/`, `*.pt`, `*.task`) is git-ignored;
`config_gate/results/` (study data + figures) IS committed — it is paper material.

## Hardware

- **M5Stack Unit CamS3-5MP** (PY260) — MJPEG at `http://<ip>/`, UXGA ~2 fps, one viewer.
  Hard-won notes: PY260 only inits at UXGA on the stock driver (a driver gap, not a sensor
  limit; community firmware unlocks VGA, XCLK is capped at 10 MHz physically). Wi-Fi is
  hard-coded in `firmware/unitcams3_stream/` — edit ssid/password and **re-flash** on a
  new network; the IP changes per network (`rig.py` `CAM_URL` is the single place to update).
- **Arduino Uno R4 + 2× MG90S** pan-tilt (`firmware/pantilt_r4/`), serial `"dPan,dTilt\n"`
  @115200; calibration constants live in `rig.py` (PAN_SIGN, TILT_TRIM). Static-camera
  operation does not need the rig.

## Status & future work

Working now: full VLM-first pipeline on a static camera, live-tested; preliminary
planner study (v1→v2 vocabulary revision closed-loop); figures F1–F8.

Planned, in order:
1. **Detectability mini-study** — staged pos/neg trials per relation row on the real rig
   (`TEST_PLAN_system.md` section 2 is the recording sheet).
2. **Scenario elicitation (v3)** — replace designed test scenarios with prompts collected
   from lab members (`elicitation_form.md`); re-run the planner study on them.
3. **Pan-tilt integration** — merge the SCAN → confirm → WATCH-at-pose loop
   (`attention_robot.py`) with the VLM-first executor; `firmware/pantilt_r4` is the
   motion reference.
4. **Voice interaction** — the typed context becomes speech (the context box is already
   the single entry point, so the plumbing is one ASR step), but turn-taking with a
   non-anthropomorphic device, confirmation feedback, and re-plan acknowledgement need
   real interaction design first — deliberately future work.
