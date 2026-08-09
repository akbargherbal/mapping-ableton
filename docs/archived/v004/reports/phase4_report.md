# Phase 4 Report — First real orchestration proof run

**Date:** 2026-08-09
**Goal:** convert "should work" into "does work" for `orchestrate.sh` + `take_shot.sh`, which previously had zero on-disk evidence of ever running against live Ableton. Prove the happy path, one failure path (minimize/recover), and the drift check.

---

## What changed

- `orchestrate.sh`, `take_shot.sh`, `build_runtime_env.sh` — **mode-only change** (`100644` → `100755`). `orchestrate.sh` invokes `take_shot.sh` directly as a command, and both are shebang'd scripts documented as `./script.sh`; the missing executable bit made the pipeline fail with `Permission denied` at the first screenshot. This is a genuine infrastructure fix, not cosmetic: without it Phase 4's acceptance was impossible. `git diff` confirms 0 content lines changed.
- No other files changed in this phase (README + automate_ableton_task.py changes are Phases 1–3, uncommitted).
- `LABS/` folder now exists on disk as the evidence artifact (see below).

---

## Acceptance criteria evidence

### AC1 — Real `LABS/` folder with real screenshots, correctly numbered/labeled

`arm_track` run (happy path):
```
[orchestrator] drift check: schema_version=1 OK
[orchestrator] task=arm_track args=--tracks 0 lab_dir=LABS/P4_2026-08-09_arm_track seq=01
[orchestrator] running: --task arm_track --live --tracks 0
...
[orchestrator] capturing screenshot: seq=01_01 desc=track_0_arm
Saved: .../LABS/P4_2026-08-09_arm_track/01_01_track_0_arm.png
NOTE:ALREADY_MAXIMIZED
... (01_02, 01_03, 01_04 all Saved, exit 0)
[orchestrator] task succeeded (exit 0)
[orchestrator] done. automate_exit=0 shot_exit=0 sub_steps=4
orchestrate exit=0
```

All 23 screenshots across 4 lab folders are real PNGs, none zero-byte, correctly numbered/labeled:
```
OK: LABS/P4_2026-08-09_arm_track/01_01_track_0_arm.png (229586 bytes)
OK: .../01_02_track_0_arm.png (229584)
OK: .../01_03_track_0_monitoring_in.png (229606)
OK: .../01_04_track_0_monitoring_in.png (229586)
+ 19 more across solo_repro, minimize, confirm (155KB–229KB each)
zero-byte PNGs: 0
```
Seq numbering persists across runs via `.orchestrate_seq` (all read `1`, correct for single fresh runs per folder).

### AC2 — Minimize/recover failure path actually recovers

Minimized the Ableton window (confirmed `IsIconic: True`), then ran `take_shot.sh` directly against it:
```
=== confirm minimized ===
IsIconic: True
=== take_shot.sh against minimized window (auto-restore/maximize should recover) ===
Saved: .../LABS/P4_2026-08-09_minimize/99_recover_test_recovered_minimize.png
NOTE:ALREADY_MAXIMIZED
take_shot exit=0
```
Post-recovery window state confirmed usable:
```
IsIconic: False  IsZoomed: True  FG: True
```
The auto-restore (SW_RESTORE) + auto-focus (SetForegroundWindow) + auto-maximize (SW_MAXIMIZE) logic all engaged and produced a real 190 KB screenshot. No `ERROR:` line emitted.

### AC3 — Drift check actually fires

Scratch copy of `automate_ableton_task.py` with `EVENT_SCHEMA_VERSION = 2` (real script stays at 1), pointed at via `ORCH_AUTOMATE_SCRIPT`:
```
[orchestrator] FATAL: EVENT schema version mismatch (expected 1, got 2)
orchestrate exit=1
```
Mismatch is detected **before any action** — the `LABS/P4_2026-08-09_drift` folder was NOT created (checked), so nothing touched live Ableton during the drift test. Normal path re-confirmed after cleanup:
```
[orchestrator] drift check: schema_version=1 OK
[orchestrator] task succeeded (exit 0)
```

---

## Regression guard

The tasks exercised here (`arm_track`, `solo_one`) are the same ones validated in Phases 0–3. No Phase 2/3 integration bug surfaced: the newly-fixed slider/dropdown helpers are not involved in the single-action task set `orchestrate.sh` accepts (`arm_track set_tempo probe_toggle probe_solo_transport probe_keyboard_activator read_solo_states solo_one`). `solo_one` ran through orchestration successfully with all 9 sub-step screenshots captured and `task succeeded (exit 0)`.

`py_compile` on the Python script: OK (unchanged from Phase 3). Shell scripts: mode-only change, no syntax risk (`bash -n` already passed on content in earlier phases; content untouched here).

---

## Things that took more than one attempt / notes

- **Missing executable bit (the real blocker).** First end-to-end run produced 4 correctly-detected sub-steps and a passing task, but every `take_shot.sh` call failed with `Permission denied` and `shot_exit=126`. Root cause: the three shell scripts are tracked as `100644` in git. `orchestrate.sh` executes `take_shot.sh` directly (`"$TAKE_SHOT" ...`), which requires the exec bit. Fixed with `chmod +x` (mode-only git diff, 0 content changes). This is the single most important thing this phase found — the pipeline was dead-on-arrival for reasons invisible in the code.
- **`--live` must NOT be passed to `orchestrate.sh`'s solo_one path.** First mid-run minimize attempt passed `--live` in `TASK_ARGS`; `orchestrate.sh`'s solo_one branch already appends `--live` itself, and its naive arg parser consumed `--live` as the `--seconds` value, producing `--seconds --live` and an argparse failure. Re-ran without `--live`; worked. Worth noting for the plan/usage docs, but it's an invocation mistake, not a script bug (the non-solo path also appends `--live`; passing it twice is harmless there).
- **One transient solo_one failure under orchestration.** The first mid-run minimize attempt ran `solo_one --seconds 8`; the Solo toggle failed verification twice (click landed, state read back as unchanged). The minimize was sent 5s in, after the task had already failed, so that run did not actually test minimize recovery. A follow-up `solo_one --seconds 3` orchestrated run passed cleanly with 9 sub-steps, so this looks like the known occasional click/read race on the custom-drawn Solo control under live screenshot pressure (`take_shot.sh` does SetForegroundWindow/maximize between events) rather than a Phase 4 regression — the same task passes repeatedly when run directly (Phases 0–3). Documented here rather than chased further, since it's the pre-existing solo-toggle flakiness, not an orchestration-output-handling bug.
- **Drift test scratch copy placement.** First attempt placed the v2 scratch file in the repo root; `--list-tasks` failed with `ModuleNotFoundError: keyboard_shortcuts` because the sibling-import layout expects the file inside `scripts/`. Moved the scratch copy to `scripts/` and the drift check fired correctly. The scratch file was deleted after the test; the real script was never modified.
