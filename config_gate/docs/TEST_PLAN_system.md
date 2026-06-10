# System Test Plan & Record — attention_system.py, static M5, live API
*(record-bound file: fill in the tables as you test; this doubles as the detectability
mini-study data for the paper. Date: ____ Tester: ____ Camera IP: ____)*

Setup assumed: M5 UnitCamS3 @ UXGA ~2fps (static, no pan-tilt), `--serve` web UI on
localhost:8000, ANTHROPIC_API_KEY exported. One M5 viewer at a time.

```bash
python cam_test.py --camera http://<ip>/        # 0. stream alive? then Ctrl-C
python attention_system.py --serve --save       # planner mode (sections 1, 4, 5)
python attention_system.py --serve --save --spec-file test_specs/<name>.json   # section 2-3
```

---

## 1. Planner, live (context → spec)   [planner mode]

| # | Step | Expect | Pass | Notes |
|---|------|--------|------|-------|
| 1.1 | `context.txt` = "I'm working at my desk; notice when someone approaches or seeks my attention." | `[plan]` prints ≤3 entries, plausibly 7/5/3-flavoured; `why` coherent | ☐ | |
| 1.2 | Type "Watch my fragile prototype on the desk." into the web UI context box (or edit context.txt) | cyan re-plan banner next frame; new spec hands-on-flavoured (9); PLAN panel in browser updates (context, why, entries) | ☐ | |
| 1.3 | Nonsense context ("asdf qwerty") | planner still returns valid JSON (graceful), or violation warning printed — no crash | ☐ | |
| 1.4 | Check terminal for `MISSING` lines | note any vocabulary gaps named on real contexts | ☐ | |

## 2. Relations 1–11, staged T/F  [spec-file mode = deterministic]

Create one spec file per row, e.g. `test_specs/r9.json`:
`{"watch": [{"all": [9], "within_s": 2, "label": "test row 9"}], "single_ok": []}`
(same pattern for each id; row 7/10/11 use within_s 6).

Protocol per row: **5 staged positives + 5 staged negatives**, count hits / false alarms.
A trial = perform (or avoid) the action for ~5 s, watch the truth strip (`nT`) and panel.
NOTE: the sidekick's real operating condition is OWNER-ABSENT (it watches others for you).
Solo rows (1/3/4/7/8/9/10) may use yourself as the stand-in actor; two-person rows
(2/5/6/11) require a colleague — do them at the lab, which also tests the real condition.
In real use, write absence into the context ("I'm away until 6pm; watch …").

| Row | Stage POSITIVE (expect T) | Stage NEGATIVE (expect F) | Hits /5 | FA /5 | Knob if failing |
|----|---------------------------|---------------------------|---------|-------|-----------------|
| 1 gazing-at | look at a cup 1m away | look 30°+ past it | | | `tol_gaze` (12°) |
| 2 joint-attn | 2 people look at same object | look at different objects | | | tol; needs 2 faces detected |
| 3 eye-contact | look into the lens, incl. from frame edge | look straight ahead, not at lens | | | eye_contact tol (12°) |
| 4 pointing | extended arm at object | arm bent / at rest | | | `min_extension_deg` (140°) |
| 5 proxemic | 2 people stand <1.2m | stand ~3m apart | | | `ZONE_PERSONAL` (2.7 sw) |
| 6 F-formation | 2 people face each other, 1-2m | stand side-by-side facing camera | | | `tol_mutual` (25°) |
| 7 approach | walk toward camera 3-4 steps | stand still / sidestep | | | `approach_frac` (0.20), win 3s |
| 8 lean-in | lean torso >20° over desk | sit/stand upright | | | `lean_deg` (15°) |
| 9 hands-on | hold/touch cup ≥1.5s | hover hand 30cm above it | | | `sustain_s` (1.0), margin 0.1 |
| 10 gathering | 2nd person enters frame | both stay, move around | | | count window 1.5s, hold 5s |
| 11 handoff | A holds cup ≥1.5s, then B takes it ≥1.5s | A re-grabs the same cup | | | `sustain_s`; needs stable pids |

Per-row notes (flicker, distance effects, pid jumps): ______

**Distance limit (fills the M5 feasibility number):** step back until face/pose lost.
FaceLandmarker lost at ____ m; PoseLandmarker lost at ____ m; detector person box lost at ____ m.

## 3. Executor semantics, live  [spec-file mode]

`test_specs/combo.json`:
```json
{"watch": [
  {"all": [3, 5], "within_s": 4, "label": "close + looking at robot"},
  {"then": [7, 3], "within_s": 15, "label": "approach then eye-contact"},
  {"all": [3], "not": [9], "within_s": 4, "label": "eye-contact unless hands busy"}
], "single_ok": []}
```

| # | Step | Expect | Pass | Notes |
|---|------|--------|------|-------|
| 3.1 | Trigger 3 alone, then 5 alone (>4s apart) | neither entry fires (window not met) | ☐ | |
| 3.2 | Both within 4s | "close + looking" fires ONCE; banner + feed card | ☐ | |
| 3.3 | Hold the situation 30s | no re-fire (cooldown; panel shows orange) | ☐ | |
| 3.4 | Break it, redo after 60s | fires again | ☐ | |
| 3.5 | Walk in from 3m, then look at lens | `then(7→3)` fires; doing it in REVERSE order must NOT fire | ☐ | |
| 3.6 | Look at lens while handling the cup | "unless hands busy" does NOT fire; release cup, wait 4s, look again → fires | ☐ | |

## 4. Records & surfaces  [planner mode, --save]

| # | Check | Pass | Notes |
|---|-------|------|-------|
| 4.1 | Web UI: live overlay matches local window; entries panel updates ≤1s behind | ☐ | |
| 4.2 | Fired moment → feed card with thumb + label; `feed/frame_*.jpg` full-res on disk | ☐ | |
| 4.3 | `feed/relation_log.jsonl` rows ≈ frames seen; truth keys 1–11 present | ☐ | |
| 4.4 | record JSON contains the truth snapshot at fire time | ☐ | |
| 4.5 | `--confirm` run: VLM veto shows red banner, vetoed moment NOT in feed | ☐ | |

## 5. Sustained run (the boring critical one)

Run 30+ min in the real lab with a real context. Record:

- false fires (panel/feed moments you'd call wrong): ____ count, which entries: ____
- missed moments you'd call obvious: ____
- fps end-to-end (status line): ____ ; CPU temp/fan sane? ☐
- M5 stream drops & auto-reconnects survived: ____ count
- pid stability: does the same person keep one id across 30 min? ☐

## Outcome summary (for the paper / supervisor)

| Metric | Value |
|---|---|
| Rows passing ≥4/5 hits AND ≤1/5 FA | __ / 11 |
| Distance limits (face / pose / detector) | __ / __ / __ m |
| Executor semantics all pass (3.1–3.6) | ☐ |
| Thresholds changed from defaults | |
| Vocabulary gaps named by planner on real contexts | |
