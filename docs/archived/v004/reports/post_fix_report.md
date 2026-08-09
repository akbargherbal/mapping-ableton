# Post-Fix Report — README accuracy & project cleanup

**Date:** 2026-08-09
**Plan:** `POST_FIX_PLAN.md` (C1–C4)
**Goal:** make the repo's self-description honest again and remove accumulated cruft, without changing any runtime behavior.

---

## What changed

- `README.md`:
  - Repository-structure tree regenerated to match disk (removed ghost `docs/project_journal.md`, added `PHASED_PLAN.md`, `POST_FIX_PLAN.md`, `ABLETON_AGENT_POLICY.md`, `orchestrate.sh`, `take_shot.sh`, `build_runtime_env.sh`, `baseline/`, `reports/`, `LABS/`, `docs/curriculum_map.md`, `live12-manual-en.pdf`, `scripts/keyboard_shortcuts.md`).
  - Catalog path corrected everywhere: `dumps/control_catalog.json` → `scripts/dumps/control_catalog.json` (Architecture, tree note, Quick Start).
  - Added three sections: **Write-back status by control type** (CheckBox/Slider/ComboBox, with the `SetValue()` crash warning), **Orchestration** (`orchestrate.sh` screenshot-per-action, allowed tasks, `--live` note, drift check, `take_shot.sh` recovery), **Baseline & regression** (`baseline/` + `reports/` workflow).
  - Survey table Phase E row now cross-references `docs/curriculum_map.md` honest gaps instead of implying coverage.
  - Quick Start commands use `python.exe` (WSL interop) instead of bare `python`.
  - `ABLETON_AGENT_POLICY.md` tree comment now records it is an intentional placeholder.
- `docs/control_catalog_usage_guide.md`: replaced stale hardcoded commit (`fb6a71b`) with a relative reference to the live survey record.
- `.gitignore`: added `docs/live12-manual-en.pdf` and `LABS/**/.orchestrate_seq`.
- Deleted from tracking (kept on disk): `docs/live12-manual-en.pdf` (91 MB), 4× `LABS/*/.orchestrate_seq` (runtime seq counters).
- Deleted from disk: `scripts/__pycache__/`.
- `POST_FIX_PLAN.md`: added (the plan doc).
- **No runtime script content changed** (`automate_ableton_task.py`, `orchestrate.sh`, `take_shot.sh`, `build_runtime_env.sh` — untouched this pass).

---

## Acceptance criteria evidence

### C1

- `grep -rn "project_journal.md"` → only hits are in `POST_FIX_PLAN.md` (the plan's own record of the ghost reference), zero hits in README/docs.
- `grep -n "dumps/control_catalog" README.md` → all hits say `scripts/dumps/control_catalog.json`.
- Tree-vs-disk: every entry in the README tree block resolves to an existing path (checked by script); top-level sets match (README/.gitignore excluded as conventional self-omissions).
- `git diff` on `scripts/` → empty (no behavior change).

### C2

- Write-back status appears once, in one obvious place (the new README section), consistent with the module WRITE-BACK STATUS note in `automate_ableton_task.py`.
- `grep -n "SetValue" README.md` → only the crash warning ("CONFIRMED to crash Ableton Live itself ... permanently disabled — never call it").
- New commands verified runnable-as-written where they involve paths (`scripts/`, `python.exe`); the `--live`-in-`TASK_ARGS` caveat for `solo_one` is documented.

### C3

- `git ls-files | grep -E "\.pdf$|orchestrate_seq"` → nothing.
- `git status` shows only intended changes (`.gitignore`, README, usage-guide, deletions, new plan).
- `git check-ignore` confirms PDF + `.orchestrate_seq` + `__pycache__` are ignored.
- `bash build_runtime_env.sh /tmp/postfix-runtime` → identical to whitelist (8 files).
- No `__pycache__` remains on disk.
- **`ABLETON_AGENT_POLICY.md` left as placeholder by explicit human decision** (recorded in plan + README): runtime policy will be written once infrastructure is proven robust.

### C4

```
python3 -m py_compile scripts/automate_ableton_task.py   -> OK
bash -n build_runtime_env.sh orchestrate.sh take_shot.sh -> OK
--list-tasks vs baseline/baseline_task_list.json         -> IDENTICAL
build_runtime_env.sh output vs whitelist                 -> IDENTICAL (8 files)
```

---

## Notes / decisions

- **PDF handling:** untrack-but-keep on disk (not purged from history — that would require `git filter-repo` and was not done by default). Flagged as an option in the plan if the human wants history shrunk later.
- **Placeholder policy:** left as-is per human decision; documented in plan + README. This is the one load-bearing file (renamed to `AGENTS.md` in the runtime build), so it's tracked but intentionally empty of real content until the tooling landscape is settled.
- **`baseline/`, `reports/`, `LABS/`** remain in the dev repo as evidence; they are already excluded from the runtime whitelist by `build_runtime_env.sh`.
