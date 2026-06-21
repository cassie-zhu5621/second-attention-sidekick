# Version log

## v1 — perception + VLM planner + first robot loop  (June 2026)
Staged snapshot **before** the interaction-design pass and the larger hardware changes.

**What this version contains**
- Concept: **Notice Delegation** (master doc: `config_gate/PROJECT_HANDOFF.md`).
- VLM planner (`planner.py`, vocab v2.1) → 11 theory-grounded relations → CV executor
  (`relations.py`, `attention_system.py`) → records (storyboard + trace-narrated description).
- Robot: pan-tilt SCAN→LOOK→WATCH→nod (`rig.py`, firmware `pantilt_r4.ino` with red-LED breathe/flutter).
- Planner study (10 scenarios × 2 temps × 2 grammars × k5) + figures F1–F8 (`results/`, vocab v2.1).
- Docs: SYSTEM_MAP, grounding_map, relation_table, RELATED_WORK_hri, TITLE_ABSTRACT,
  MDR1_presentation_brief, plus the form/hardware/interaction design docs.

**v1 cleanup**
- Removed 3 superseded scripts (not used in the current system run): `robot_demo.py`,
  `attention_robot.py`, `run_perception.py` → all replaced by `attention_system.py --rig`.
  (Recoverable from git history.)
- Fixed dead references in SYSTEM_MAP / MDR1 brief / BRANCH_gaze_handoff.

**Tag this snapshot (run on your Mac — not in the sandbox):**
```bash
cd second-attention-sidekick
git add -A
git commit -m "v1: perception + VLM planner + first robot loop (pre-interaction redesign)"
git tag -a v1-perception -m "staged version before interaction design + hardware changes"
```

**Next stage**
- Interaction design (the steerable taste / see=teach loop, legible movement, reporting surface).
- Larger hardware changes (form / head / readout — see the design docs).
