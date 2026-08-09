# Phased Infrastructure Remediation Plan

**Scope:** fix the issues surfaced in the infrastructure audit (Level 3 doc/code
mismatch, dangling `interaction_idioms.md` reference, broken slider/dropdown
write-back, unverified orchestration pipeline). Excludes curriculum, pedagogy,
and agent-narration work — those are superstructure and stay out of scope
until this plan is done.

**Ground rule for every phase:** nothing here may change behavior for a
capability that currently works. Each phase ends with a regression check
against a fixed baseline captured in Phase 0, not just a check that the new
thing works in isolation.

---

## Phase 0 — Baseline capture (no code changes)

**Goal:** have a concrete, reproducible record of what currently works,
before touching anything, so every later phase has something real to diff
against instead of a vague "did I break something?" feeling.

**Actions:**
1. Run `python scripts/automate_ableton_task.py --list-tasks` and save the
   output (`baseline_task_list.json`).
2. Run the currently-safe live tasks against a **throwaway/test Ableton
   project** and save full console + `EVENT:` output for each:
   - `probe_toggle`
   - `task_idiom_demo`
   - `arm_track`
   - `read_solo_states`
   - `solo_one`
3. Run `bash build_runtime_env.sh /tmp/baseline-runtime` and diff its file
   list against the current whitelist — confirms the build step itself is
   stable before Phase 1 touches its comments.

**Acceptance criteria:** a `baseline/` folder exists containing the task
list output and the saved run logs above. No code changed in this phase.

**Regression guard:** N/A — this phase *is* the regression guard for every
later phase.

---

## Phase 1 — Documentation decontamination (zero execution risk)

**Goal:** stop the repo from asserting things that aren't true. Pure text
changes, nothing that touches `--live` behavior, so regression risk here is
effectively zero — but it's still worth verifying nothing was accidentally
broken, since silent scope creep during a "just fix the docs" pass is exactly
how regressions sneak in.

**Actions:**
1. `README.md`: correct the escalation ladder diagram/table. Either:
   - (a) relabel it as a 3-level ladder (Mouse → Keyboard → Human
     Instructions) to match what `automate_ableton_task.py` actually does, or
   - (b) keep 4 levels documented, but explicitly mark Level 3 as
     **"not implemented in `automate_ableton_task.py` — available only as a
     separate AbletonMCP tool call at the OpenCode/agent layer, not part of
     the deterministic `click_by_id` ladder."**
   Pick (b) if you intend to eventually wire Level 3 into the ladder itself;
   pick (a) if you're formalizing "3 levels, MCP is a separate concern."
2. `scripts/automate_ableton_task.py`: fix or remove the `docs/interaction_idioms.md`
   reference in `task_idiom_demo`'s docstring. Either write the file (documenting
   the 6 idioms and which are proven vs. not) or replace the reference with
   an inline summary so the docstring stops pointing at nothing.
3. Add an explicit, visible status note near the top of `automate_ableton_task.py`
   (not buried in one function's docstring) listing write-back status per
   control type: CheckBox = proven safe, Slider = **confirmed to crash Ableton,
   disabled**, ComboBox = untested/unwired. This is currently discoverable only
   by reading two separate function bodies — it should be impossible to miss.

**Acceptance criteria:**
- README's ladder description matches what the code does, verifiably, by
  reading both side by side.
- `grep -rn "interaction_idioms.md" .` returns nothing (file created or
  reference removed).
- Write-back status is stated once, in one obvious place, for all three
  control types.

**Regression guard:** re-run every Phase 0 baseline task, diff console/EVENT
output byte-for-byte (docs-only changes should produce identical output).
`bash -n` all shell scripts, `python -m py_compile` the Python file.

---

## Phase 2 — Fix slider write-back (the actual blocker)

**Goal:** replace the crash-confirmed `RangeValuePattern.SetValue()` path
with the click+type pattern already proven safe in `task_set_tempo`, and
generalize it so it isn't tied to tempo specifically.

**Actions:**
1. Write a new, generic helper — e.g. `set_slider_by_id(window, auto_id,
   value, dry_run, verify=...)` — that uses double-click + type + Enter
   (the pattern already used for `Transport.Tempo`), not `SetValue()`.
   `SetValue()` must not be called anywhere in this helper.
2. **Isolated test first, throwaway project, one control.** Do not touch
   `Transport.Tempo` in this test (already covered) — pick a different,
   low-consequence slider (e.g. `TrackView.Device[0].Freq` on an EQ Eight
   loaded for this purpose only) and test the new helper against it alone,
   willing to lose the session if it crashes.
3. Only after that isolated test passes cleanly, wire the new helper into
   `task_idiom_demo`'s Idiom 2 (currently read-only), turning it from
   observe-only into an actual verified write.
4. Add a verify step (read back the value via UIA after typing) so success
   means "confirmed changed," not "keys were sent."

**Acceptance criteria:**
- The isolated single-control test completes without crashing Ableton,
  three separate runs in a row (not just once — the tempo crash was
  reproduced twice, so one clean run isn't enough confidence).
- `task_idiom_demo` demonstrates Idiom 2 as a real write-and-verify, not a
  read-only print.
- `grep -n "SetValue" scripts/automate_ableton_task.py` shows no live call
  path for sliders (only in disabled/documented-danger code, if kept at all
  for historical record).

**Regression guard:** re-run every Phase 0 baseline task unchanged — this
phase must not touch `task_set_tempo`, `probe_toggle`, or any CheckBox path.
Diff output against baseline. If `task_set_tempo` still uses its own
click+type implementation untouched, confirm it still behaves identically
before and after this phase (same BPM in, same BPM out, same event log
shape).

---

## Phase 3 — Fix dropdown (ComboBox) write-back

**Goal:** same treatment as Phase 2, applied to `Transport.GlobalQuantization`
or another safe ComboBox — currently "not wired up," not confirmed dangerous,
so this is lower-risk than Phase 2 but should still be proven in isolation
first rather than assumed safe by analogy.

**Actions:**
1. Investigate whether ComboBox selection can be done via click-to-open +
   click-item (Level 1 style) instead of `SetValue()`/`SelectionItemPattern`
   assumptions — mirror the "avoid the pattern that crashed on Slider"
   caution even though ComboBox hasn't crashed yet.
2. Isolated test on a throwaway project, single control, before wiring
   into anything else.
3. Wire into `task_idiom_demo`'s Idiom 3 once proven.

**Acceptance criteria:** same shape as Phase 2 — three clean isolated runs,
verified write via read-back, `task_idiom_demo` demonstrates all 3 idioms
as real writes.

**Regression guard:** re-run full Phase 0 baseline + Phase 2's new slider
test, confirm both still pass unchanged.

---

## Phase 4 — First real orchestration proof run

**Goal:** convert "should work" into "does work" for `orchestrate.sh` +
`take_shot.sh`, which currently have zero on-disk evidence of ever running
against live Ableton.

**Actions:**
1. Run `orchestrate.sh` end-to-end against one of the now-verified tasks
   (`arm_track` or the fixed `task_idiom_demo` from Phases 2–3) on a
   throwaway project.
2. Confirm a `LABS/` folder is created, correctly numbered/labeled, containing
   real screenshots (not zero-byte or error placeholders) for each
   `action_start`/`action_result` event.
3. Deliberately test one failure path — minimize the Ableton window before
   a step and confirm `take_shot.sh`'s auto-restore/focus/maximize logic
   actually recovers, not just that the happy path works.
4. Confirm the drift check (schema version comparison) actually fires
   correctly by temporarily bumping `EVENT_SCHEMA_VERSION` in a scratch copy
   and confirming `orchestrate.sh` detects and reports the mismatch.

**Acceptance criteria:** a real `LABS/` folder with real screenshots exists
and is committed (or at least kept) as evidence — this is the same kind of
proof `scripts/dumps/` already provides for the survey layer, now existing
for the orchestration layer too. The minimize/recover test and the drift
check test both produce the expected behavior, not just the happy path.

**Regression guard:** the tasks used here are the same ones validated in
Phases 0–3; if this phase reveals `orchestrate.sh` mishandles output from
the *newly fixed* slider/dropdown tasks specifically, that's a Phase 2/3
integration bug to fix there, not a reason to weaken this phase's criteria.

---

## Phase 5 — Lesson-to-catalog reference layer

**Goal:** the one piece of "prep" identified as genuinely worth doing next
— not a scripted recipe, a lookup reference: for a given curriculum topic,
which `automation_id`s / tasks are relevant. Deliberately last, since it's
only useful once Phases 1–4 mean the underlying actions it points to
actually work.

**Actions:**
1. For each `course_outline.txt` module, list candidate `automation_id`s
   from `control_catalog.json` and any matching `TASK_REGISTRY` entries.
   Stop at "here are the relevant controls" — no scripted sequence, no
   narration, no phrasing.
2. Explicitly flag topics that fall in the unmapped Phase E (Browser)
   territory as "no reference available yet" rather than guessing.
3. Store this as a simple, inspectable file (e.g. `docs/curriculum_map.md`
   or `.json`) — not code, so it's cheap to edit as the catalog or
   curriculum changes.

**Acceptance criteria:** for a sample of 3–4 modules, the reference
correctly lists real, verified `automation_id`s (spot-checked against
`control_catalog.json` directly) and honestly marks gaps rather than
papering over them.

**Regression guard:** this phase adds a new file only — verify no existing
script imports or depends on its absence in a way that would break (unlikely,
but check `grep -rn "curriculum" scripts/` first before assuming).

---

## Summary table

| Phase | Fixes | Risk if skipped | New capability unlocked |
|---|---|---|---|
| 0 | — | Can't detect regressions later | Baseline to diff against |
| 1 | False Level 3 claim, dangling doc ref, buried write-back status | Agent/human trusts a safety net that isn't there | Accurate self-description |
| 2 | Slider write-back (currently crashes) | Idiom 2 stays fake/read-only forever | Real "turn a knob" |
| 3 | Dropdown write-back (currently unwired) | Idiom 3 stays fake/read-only forever | Real "pick from a list" |
| 4 | Unproven orchestration pipeline | Lessons built on an unverified foundation | Proof the photography loop actually works |
| 5 | No curriculum↔catalog bridge | Agent improvises/guesses every lesson | Cheap reference, not a script |
