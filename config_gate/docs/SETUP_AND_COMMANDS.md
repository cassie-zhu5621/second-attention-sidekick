# Setup & Commands

## 1. One-time setup on a new machine

### 1.1 Environment (covers everything incl. CoMotion)
```bash
# conda ToS (new conda versions, one-time):
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r

conda create -n sidekick -y python=3.10      # 3.10 REQUIRED (CoMotion pins torch 2.5.1)
conda activate sidekick

git clone <repo-url> && cd second-attention-sidekick
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-...              # put in ~/.zshrc
```
Auto-downloads on first run (no action needed): MediaPipe `.task` models (→
`config_gate/weights/`), YOLO `.pt` (ultralytics), Grounding DINO (HuggingFace, only
with `--detector gdino`).

### 1.2 CoMotion backend (optional — only for `--pose-backend comotion`)
```bash
git clone https://github.com/apple/ml-comotion ~/Projects/ml-comotion
# chumpy is ancient and breaks pip build isolation — install it FIRST, like this:
pip install --no-build-isolation \
  "chumpy @ git+https://github.com/mattloper/chumpy@9b045ff5d6588a24a0bab52c83f032e2ba433e17"
pip install -e ~/Projects/ml-comotion
pip install "scenedetect==0.6.4"             # 0.7 API-breaks CoMotion's shot detector

cd ~/Projects/ml-comotion
sed -i '' 's/^wget /curl -L -O /' get_pretrained_models.sh   # macOS has no wget
bash get_pretrained_models.sh                # ~2.2 GB checkpoints

# SMPL body model (manual, license-gated):
#   register at https://smpl.is.tue.mpg.de (academic), download SMPL v1.1.0 ("for
#   Python users" zip — the .pkl one, NOT npz variants), then:
mkdir -p src/comotion_demo/data/smpl
cp basicmodel_neutral_lbs_10_207_0_v1.1.0.pkl src/comotion_demo/data/smpl/SMPL_NEUTRAL.pkl
```

### 1.3 Hardware
- **M5 UnitCamS3-5MP**: Wi-Fi is hard-coded — edit ssid/password in
  `firmware/unitcams3_stream/unitcams3_stream.ino` and re-flash per network (Arduino IDE,
  board M5UnitCAMS3, PSRAM=OPI). IP changes per network; ONE viewer at a time.
- **Pan-tilt (Uno R4 + 2×MG90S + passive buzzer)**: flash `firmware/pantilt_r4/`.
  Wiring: PAN→D9, TILT→D10, BUZZER +→D8 −→GND, servo V+→external 5V, GND shared.
  macOS serial = `/dev/cu.usbmodem*`; CLOSE the VS Code Serial Monitor before running
  (or `lsof -t /dev/cu.usbmodem101 | xargs kill -9`).
- **USB webcam** (dev camera): plug in; it is `--camera 0` or `1` (order varies).
- macOS will ask camera permission for the terminal app on first run — allow it.

### 1.4 Per-session
```bash
conda activate sidekick
cd .../second-attention-sidekick/config_gate
export SIDEKICK_CAM=http://<m5-ip>/          # only when using the M5
```

## 2. Smoke tests (run these first, in order)
```bash
python cam_test.py --camera http://<ip>/     # M5 stream alive? Ctrl-C after (one viewer!)
python rig_moves.py --port /dev/cu.usbmodem101   # rig: moves + nod (beep BEFORE dip)
python gaze.py --camera 0 --detect           # MediaPipe rays + YOLO + 4 relations live
python comotion_pose.py --camera 0           # CoMotion skeleton probe (async; ~20s warmup)
```

## 3. The system — all run modes
```bash
echo "I'm away for a while; watch who comes to my desk." > context.txt

# static, MediaPipe (30fps dev default)
python attention_system.py --serve --save --plan-frame --camera 0
# static + CoMotion skeletons/ids (needs sidekick env)
python attention_system.py --serve --save --plan-frame --camera 0 --pose-backend comotion
# pan-tilt body (SCAN -> beep+nod+WATCH -> resume); M5 camera
python attention_system.py --serve --save --plan-frame --rig --port /dev/cu.usbmodem101
# no API key at all (fake planner/judge):
python attention_system.py --serve --offline --camera 0
# VLM double-checks before recording:
python attention_system.py --serve --save --confirm --camera 0
```
Web UI: http://localhost:8000 (live · THE PLAN · feed with full-strip links · context box
— typing re-plans). Flags reference: README table. Testing tip: `--cooldown 10`.

## 4. Per-relation tests (TEST_PLAN_system.md §2 — the detectability data)
```bash
# one relation at a time, deterministic (no API):
python attention_system.py --serve --camera 0 --cooldown 10 --spec-file test_specs/r9.json
# rows: r1 gazing / r2 joint-attn / r3 eye-contact / r4 pointing / r5 proxemic /
#       r6 f-formation / r7 approach / r8 lean-in / r9 hands-on / r10 gathering /
#       r11 turn-taking;  combo.json = executor semantics (§3: window/cooldown/then/not)
# Solo rows at home: r1 r3 r4 r7 r8 r9 r10. Two-person rows at the lab: r2 r5 r6 r11.
# Protocol: 5 staged positives + 5 negatives per row -> fill Hits/FA in the table.
```

## 5. Studies (planner / paper data)
```bash
python studies/planner_study.py                          # full: 10 scen × 2 temps × 2 grammars × k5
python studies/planner_study.py --scenarios guest --k 5  # targeted re-run (writes *_partial)
python studies/compare_plan.py --image scenes/roundtable.jpg \
    --context "this is our roundtable space for running regular meetings."   # LLM-vs-VLM ablation
python studies/make_report_figures.py --jsonl results/planner_study_claude-sonnet-4-6_vocab-v2.jsonl
# F7 (v1 vs v2 comparison) regenerates with:
python -c "import sys; sys.path.insert(0,'.'); sys.path.insert(0,'studies'); \
import make_report_figures as M; M.fig_v1v2( \
'results/planner_study_claude-sonnet-4-6_vocab-v1.jsonl', \
'results/planner_study_claude-sonnet-4-6_vocab-v2.jsonl', \
'results/figures/F7_vocab_v1_v2.png')"
```
Scenario texts live in `studies/planner_study.py` (`SCENARIOS` dict); every results
`.jsonl` row also carries its full context string.

## 6. Where outputs land
| Path | Content |
|---|---|
| `feed/` | comic-strip frames + thumbs, `attention_log.jsonl`, `relation_log.jsonl` (per-frame T/F) |
| `results/` | study jsonl/md + `figures/F1-F8` (committed = paper data) |
| `context.txt` | live context (edit while running → re-plan) |

## 7. Known benign noise (ignore)
`objc AVFFrameReceiver duplicate` (cv2/pyav dylib) · `landmark_projection NORM_RECT` ·
`clearcut uploader FAILED_PRECONDITION` (MediaPipe telemetry) · HF_TOKEN warning ·
`inference_feedback_manager` lines.
