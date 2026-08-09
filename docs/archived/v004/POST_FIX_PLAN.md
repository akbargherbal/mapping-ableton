# Post-Fix Plan — README accuracy & project cleanup

**Status:** plan (not yet executed)
**Scope:** after the Phases 0–5 remediation (committed as `4fbbc13`), make the
repo's self-description honest again and remove accumulated cruft. Two work
streams: (A) `README.md` and related docs describe what now exists, (B) the repo
is cleaned of dead references, large/tracked junk, and stale claims.
**Ground rule:** docs/hygiene only — no changes to any script's runtime behavior.
Every phase keeps the Phase 0 baseline diffable as-is.

---

## Phase C1 — README repository-structure truth

**Problem:** README's tree (lines 93–118) describes a repo that no longer matches
disk. It references `docs/project_journal.md` (does not exist), omits files added
or used during remediation, and uses stale paths (`dumps/` vs `scripts/dumps/`).

**Actions:**
1. Regenerate the tree from `git ls-files` (source of truth), grouping by top-level
   dir, so it matches disk exactly.
2. Fix the catalog path everywhere: `dumps/control_catalog.json` →
   `scripts/dumps/control_catalog.json` (lines 59, 116, 173, 178).
3. Add the missing root entries: `PHASED_PLAN.md`, `orchestrate.sh`,
   `take_shot.sh`, `build_runtime_env.sh`, `ABLETON_AGENT_POLICY.md`,
   `docs/curriculum_map.md`, `baseline/`, `reports/`, `LABS/`.
4. Remove the ghost entry `docs/project_journal.md`; replace the stale
   `docs/` listing with the actual files on disk.
5. In `docs/control_catalog_usage_guide.md`, replace the hardcoded stale commit
   (`fb6a71b`) with a relative phrase (e.g. "the current survey pass") so the doc
   doesn't rot again.

**Acceptance criteria:**
- `grep -rn "project_journal.md" .` returns nothing.
- `grep -rn "dumps/control_catalog" .` returns nothing in `README.md` (all say
  `scripts/dumps/...`).
- Every path in README's tree exists on disk; every top-level file/dir on disk is
  in the tree (checked by a small script, not by eyeballing).
- No script behavior changed (`git diff` on `scripts/` empty).

---

## Phase C2 — README capability status (write-back + orchestration)

**Problem:** README predates Phases 2–4. It documents the survey/catalog layer but
says nothing about the now-proven write-back paths, the slider SetValue crash rule,
or the orchestration/screenshot loop.

**Actions:**
1. Add a "Write-back status by control type" subsection under the escalation-ladder
   section, mirroring the module-level WRITE-BACK STATUS note in
   `scripts/automate_ableton_task.py`: CheckBox = proven (click+verify),
   Slider = proven via click+type (`set_slider_by_id`) — **`SetValue()` confirmed
   to crash Ableton, never call it**, ComboBox = proven via click-to-open +
   click-item (`set_combobox_by_id`).
2. Link the proven-control set to `docs/curriculum_map.md` (the "Proven-write
   controls" table) and note which tasks exercise them (`arm_track`, `solo_one`,
   `set_tempo`, `idiom_demo`).
3. Add an "Orchestration" subsection: `orchestrate.sh <lab_dir> <task> [args]`
   drives one single-action task with a screenshot per `action_start`/`action_result`
   event into `LABS/`, with drift-check and `take_shot.sh` auto-restore/maximize.
   Note `--live` is required for real action and `solo_tour` is excluded.
4. Add a short "Baseline & regression" subsection: `baseline/` holds Phase 0
   snapshots; every phase re-runs them and diffs byte-for-byte.
5. Update the survey-status table (or add a footnote) so the Phase E (Browser)
   `UNMAPPED` row cross-references the honest-gaps section of `curriculum_map.md`
   rather than implying coverage exists.

**Acceptance criteria:**
- The three control types' write-back status appears once, in one obvious place,
  consistent with the module note (spot-check by reading both side by side).
- `grep -n "SetValue" README.md` shows the crash warning, not a usage instruction.
- README's new commands are runnable as written against the real layout
  (`scripts/` paths, `python.exe` for WSL interop — fix any bare `python` in
  Quick Start to match AGENTS.md §1).

---

## Phase C3 — Repo hygiene

**Problem:** tracked junk and runtime artifacts: a 91 MB binary PDF tracked in git,
`LABS/*/.orchestrate_seq` runtime state files committed, a `scripts/__pycache__`
dir on disk, and a placeholder shipped as the runtime agent policy.

**Actions:**
1. **`docs/live12-manual-en.pdf` (91 MB, tracked, referenced nowhere):** add
   `docs/live12-manual-en.pdf` to `.gitignore` and `git rm --cached` it so it stops
   being versioned. Keep the file on disk locally. (History still contains it —
   flag to the human if they want `git filter-repo` to purge it; not done by
   default.)
2. **`LABS/*/.orchestrate_seq` (runtime seq counter):** add `LABS/**/.orchestrate_seq`
   to `.gitignore`, `git rm --cached` existing ones. Screenshot PNGs stay tracked
   (they are Phase 4 evidence).
3. **`scripts/__pycache__`:** delete from disk (already gitignored, not tracked).
4. **`ABLETON_AGENT_POLICY.md` is a 13-byte `[PLACEHOLDER]`,** yet
   `build_runtime_env.sh` copies it as the runtime `AGENTS.md`. **DECISION (2026-08-09):
   leave as placeholder.** The human decided it stays a placeholder until the
   infrastructure is robust and the viable/dead-end paths for the tools are known —
   it is the runtime agent's policy and will be written at the end. Documented here
   and in the README; no content was invented.
5. **Survey-era docs** (`coverage_summary.md`, `survey_checklist.md`): keep (they
   are the survey layer's record) but ensure README's tree describes them
   accurately rather than as if current status.

**Acceptance criteria:**
- `git ls-files | grep -E "\.pdf$|\.orchestrate_seq"` returns nothing.
- `git status` shows only the intended changes; `.gitignore` covers both patterns.
- `bash build_runtime_env.sh /tmp/postfix-runtime` still runs and syncs the same
  expected file list (8 files) as the Phase 0 baseline.
- No `__pycache__` remains on disk.

---

## Phase C4 — Verification pass

**Actions:**
1. `bash -n` all shell scripts; `python3 -m py_compile` `scripts/*.py` (should be
   no-ops — nothing behavioral changed, but cheap to prove).
2. Re-run `python.exe scripts/automate_ableton_task.py --list-tasks` and diff
   against `baseline/baseline_task_list.json` → byte-identical.
3. Re-run `bash build_runtime_env.sh /tmp/postfix-runtime` and diff file list
   against the whitelist → identical.
4. Re-check README accuracy via the C1 acceptance script (tree vs disk) and the
   C2 spot-checks.

**Acceptance criteria:** all four checks pass; `git diff` shows changes only in
`README.md`, `docs/*`, `.gitignore`, and `git rm --cached` deletions — no change
to any runtime script content.

---

## Open questions for the human

1. **The 91 MB PDF:** untrack-but-keep (recommended) vs. purge from history via
   `git filter-repo` vs. move it out of the repo entirely. Untrack-but-keep is the
   default in C3.
2. **`ABLETON_AGENT_POLICY.md` placeholder:** **RESOLVED (2026-08-09)** — keep as
   placeholder; the human will write real runtime policy once infrastructure is
   proven robust. See C3 step 4.
3. **Should `baseline/` + `reports/` + `LABS/` live in this repo forever**, or be
   considered dev-artifacts that a future `build_runtime_env.sh` whitelist decision
   treats as out-of-scope for the runtime? (The whitelist already excludes them;
   the question is only about the dev repo.)

## Out of scope

- Any change to runtime script behavior (`automate_ableton_task.py`, `orchestrate.sh`,
  `take_shot.sh`, `build_runtime_env.sh` logic).
- Re-enabling disabled `SetValue()` paths, or relitigating the AGENTS.md safety facts.
- Curriculum, lesson narration, or agent-dialogue work.
