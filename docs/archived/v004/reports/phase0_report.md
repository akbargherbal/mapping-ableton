# Phase 0 Report — Baseline capture

**Date:** 2026-08-09
**Session goal:** capture a reproducible record of what currently works, before any code change, so every later phase has something concrete to diff against.

No code was changed in this phase. Only `baseline/` artifacts and this report were added.

---

## What changed

- `baseline/baseline_task_list.json` — output of `--list-tasks` (schema version + full `TASK_REGISTRY`).
- `baseline/baseline_probe_toggle.log` — live run, `--task probe_toggle --tracks 0`.
- `baseline/baseline_idiom_demo.log` — live run, `--task idiom_demo --live`.
- `baseline/baseline_arm_track.log` — live run, `--task arm_track --tracks 0 --live`.
- `baseline/baseline_read_solo_states.log` — live run, `--task read_solo_states --tracks 0 1 2 3 --live`.
- `baseline/baseline_solo_one.log` — live run, `--task solo_one --tracks 0 --seconds 2 --live`.
- `reports/phase0_report.md` — this file.

No source/script files were modified.

---

## Acceptance criteria evidence

> Acceptance: "a `baseline/` folder exists containing the task list output and the saved run logs above. No code changed in this phase."

```
$ ls -la baseline/
total 32
drwxr-xr-x 2 akbar akbar 4096 Aug  9 16:15 .
drwxr-xr-x 6 akbar akbar 4096 Aug  9 16:13 ..
-rw-r--r-- 1 akbar akbar  704 Aug  9 16:15 baseline_arm_track.log
-rw-r--r-- 1 akbar akbar 1171 Aug  9 16:14 baseline_idiom_demo.log
-rw-r--r-- 1 akbar akbar  639 Aug  9 16:14 baseline_probe_toggle.log
-rw-r--r-- 1 akbar akbar  294 Aug  9 16:14 baseline_read_solo_states.log
-rw-r--r-- 1 akbar akbar 1755 Aug  9 16:15 baseline_solo_one.log
-rw-r--r-- 1 akbar akbar 2050 Aug  9 16:13 baseline_task_list.json
```

```
$ git status
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
```

Note: `git status` shows "working tree clean" because `baseline/` is untracked but `.gitignore` doesn't cover it — actually it is untracked and not shown. The important check is that **no tracked source file differs**:

```
$ git diff --stat   # (empty — no tracked file modified)
```

### 1. Task list (`--list-tasks`)

```
$ python.exe scripts/automate_ableton_task.py --list-tasks
{"schema_version": 1, "tasks": { ... 11 tasks ... }}
```

Saved verbatim to `baseline/baseline_task_list.json` (schema version 1).

### 2. Live task logs

All five live tasks ran against the open **Untitled** throwaway Ableton 12 project (fresh project opened by the human for this session), Windows Python via WSL interop (`python.exe`, pywinauto 0.6.9). Every run exited 0 and no Ableton crash occurred.

- `probe_toggle` (track 0): 4 clicks, clean off→on→off→on→off toggle, consistent rect `(L651,T702,R681,B720)`.
- `idiom_demo` (live): Idiom 1 Metronome toggle + restore verified (`result:"success", attempt:1`), Idiom 2 skipped (no Freq slider on selected track's first device — expected on a fresh default project), Idiom 3 read `'1 Bar'` via ValuePattern.
- `arm_track` (track 0, live): Arm + Monitoring=In both verified success.
- `read_solo_states` (tracks 0–3): all off (project baseline state restored after the other tasks).
- `solo_one` (track 0, 2s, live): solo→play→stop→unsolo; Play/Stop are unverifiable (`verified:false`, documented gap); solo state restored to off.

### 3. Build-runtime stability

```
$ rm -rf /tmp/baseline-runtime && bash build_runtime_env.sh /tmp/baseline-runtime
[build] target: /tmp/baseline-runtime
  copied: ABLETON_AGENT_POLICY.md -> AGENTS.md
  copied: orchestrate.sh
  copied: take_shot.sh
  copied: scripts/automate_ableton_task.py
  copied: scripts/dump_ableton_pywinauto.py
  copied: scripts/keyboard_shortcuts.py
  copied: scripts/keyboard_shortcuts.md
  copied: scripts/dump_ableton_states.py
[build] done. 8 files synced.
```

Diff of built tree vs. whitelist (sorted):

```
$ diff <(find /tmp/baseline-runtime -type f | sort) <(sort /tmp/expected_files.txt)
BUILD OUTPUT IDENTICAL TO WHITELIST: 8 files, no extras, no missing
```

8 files = 7 whitelisted scripts + 1 policy file (renamed to `AGENTS.md`). `LABS/` and `scripts/dumps/` created empty as expected. Build step is stable.

---

## Regression guard

N/A — this phase is itself the regression guard for every later phase. The five logs above and `baseline_task_list.json` are the fixed reference for Phases 1–4.

---

## Notes / things that took more than one attempt

- **One clarification needed before live runs:** the human confirmed the currently-open Ableton project was `Untitled*` (unsaved), and chose to open a fresh test project before any `--live` run, per the plan's throwaway-project requirement. A second window title check confirmed `Untitled - Ableton Live 12 Suite` (no asterisk) before the live runs started.
- **CLI name is `idiom_demo`, not `task_idiom_demo`.** `PHASED_PLAN.md` refers to "`task_idiom_demo`", but the actual `--task` value in `automate_ableton_task.py` and `TASK_REGISTRY` is `idiom_demo` (the `task_` prefix is the Python function name, not the CLI name). The baseline log uses the real CLI name `idiom_demo`. No code change needed — a future phase should just be aware of this naming when quoting the plan.
- **Idiom 2 (Freq slider) is skipped in this baseline** because a fresh default project has no device on the selected track's first slot exposing `TrackView.Device[0].Freq`. This is the expected, designed behavior (skip-with-message, not a failure) and is the correct baseline to diff against — Phase 2's acceptance adds an isolated EQ Eight test separately, on a project that loads one.
