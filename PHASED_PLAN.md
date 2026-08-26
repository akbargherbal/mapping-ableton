# PHASED_PLAN.md — Resumable Implementation Plan

Companion to `context.md` (read that first for *why*; this file is *what,
in what order*). Each phase has a checklist, a definition of done, and its
dependencies, so a future session can jump straight to the first unchecked
box without re-reading the whole conversation history.

**How to use this file:** check boxes off as work completes. Update
"Current Status" below at the end of every session, even a partial one.

---

## Current Status

> **Phase:** 0 complete — ready to start Phase 1
> **Last updated:** this session — Phase 0 implemented and verified

---

## Phase 0 — Fix the Groove Pool guard
**Priority: most urgent. Safety fix, not a design change.**

**Goal:** close the gap between what the docs claim ("Groove Pool
automation is blocked") and what the code actually enforces (nothing).

- [x] Add a `"groove_pool_toggle"` entry to `SHORTCUTS` in
      `scripts/keyboard_shortcuts.py`, `blocked=True`, with a note citing
      the confirmed crash (`0xc0000409` in `ucrtbase.dll`), mirroring the
      shape of the existing `solo_selected_track` entry.
- [x] Grep the whole repo for any other place a Groove Pool shortcut or
      automation_id could be reached (`scripts/`, `orchestrate.sh`,
      `automate_ableton_task.py`) to confirm this is the only door in.
      **Result:** `grep -rniI "groove" --include="*.py" --include="*.sh" .`
      returns no hits outside `keyboard_shortcuts.py` — confirmed the only
      door in.
- [x] Confirm `load_shortcut("groove_pool_toggle")` raises by default
      (i.e. `allow_blocked=False` is the caller's default everywhere).
      **Result:** verified live — raises `ShortcutBlocked` with no args,
      only returns the key sequence (`^%6` / Ctrl+Alt+6) with an explicit
      `allow_blocked=True`.

**Definition of done:** calling the shortcut lookup for Groove Pool raises
unless a caller explicitly passes `allow_blocked=True` — same protection
class as the other blocked entries, not just a comment in a README.
**✅ Done.**

**Depends on:** nothing. Can be done first, in isolation, any session.

---

## Phase 1 — Decide the mastering runtime's real scope
**Priority: second. This is a decision, not code — but it blocks Phases 2–4.**

**Goal:** resolve the contradiction between `SUNO_MASTERING_AGENT_POLICY.md`
(assumes pywinauto + escalation ladder are available) and
`build_mastering_env.sh` (deliberately excludes them), now that the learner
persona is confirmed to be a total DAW novice, not just a mastering novice.

- [ ] Decide: does `../suno-mastering-course` become a **superset** runtime
      (mastering curriculum + click-automation layer + on-demand catalog
      access), or does it stay separate and lean on a *different* set of
      tools (vision + MCP + generic primitives, minimal/no pywinauto task
      layer)?
- [ ] Update `build_mastering_env.sh`'s `FILES[]` whitelist to match the
      decision (add or explicitly confirm exclusion of `orchestrate.sh`,
      `take_shot.sh`, `scripts/automate_ableton_task.py`,
      `scripts/dump_ableton_pywinauto.py`, `scripts/keyboard_shortcuts.py`,
      `scripts/dumps/control_catalog.json`).
- [ ] Update `SUNO_MASTERING_AGENT_POLICY.md`'s opening "Role" section so
      it accurately states which tools the mastering agent actually has —
      no more mismatch between what the policy assumes and what the build
      script ships.

**Definition of done:** the policy file and the build script agree on
which tools exist in the runtime. No aspirational references to tools that
aren't actually whitelisted.

**Depends on:** nothing technical, just a decision. Should happen before
Phases 2–4 so they're not built into the wrong (or a not-yet-existing) folder.

---

## Phase 2 — Build the generic control-invocation interface
**Priority: third. The structural fix for the "memorize scripts" problem.**

**Goal:** let the agent call the already-generic write primitives
(`set_checkbox_by_id`, `set_slider_by_id`, `set_combobox_by_id`) with any
automation_id it looks up live, instead of only through the fixed
`--task {arm_track, solo_one, ...}` menu.

- [ ] Add a general entry point to `automate_ableton_task.py` — sketched
      as `call_control(automation_id, action, value=None, dry_run=...)` —
      that dispatches to the correct proven-safe primitive based on the
      control's type (read that type from a live/narrow catalog lookup,
      not hardcoded).
- [ ] Add a matching CLI mode (e.g. `--control <automation_id> --action
      <set|click> --value <v>`) alongside the existing `--task` mode —
      don't remove `--task`, it's still fine for genuinely fixed sequences.
- [ ] Guard rails carried over unchanged: still only the three proven
      control types; still never call `SetValue()`; unknown/untested
      control types (e.g. the `Text`-type EQ Eight band selectors found
      this session) should refuse with a clear "not yet validated" error,
      not attempt a guess.
- [ ] Add a narrow, on-demand catalog lookup helper (e.g.
      `lookup_control(device_or_context, name_hint)`) that returns just the
      matching automation_id(s) + control_type — never load the full
      `control_catalog.json` into any agent context wholesale.
- [ ] Validate end-to-end on one real example: EQ Eight's Frequency slider
      (`TrackView.Device[0].Freq`), since it's already confirmed present
      and is a proven-safe control type (Slider).

**Definition of done:** the sibilance scenario's "set the EQ band" step can
be executed by calling the generic entry point with a live-looked-up
automation_id — no new named `task_*` function required.

**Depends on:** Phase 1 (needs to know which runtime this ships in).

---

## Phase 3 — Write the explicit escalation decision rule
**Priority: fourth. The policy layer on top of Phase 2.**

**Goal:** replace the current vague "per the escalation ladder in the
README" reference in `SUNO_MASTERING_AGENT_POLICY.md` with a concrete rule
for this specific persona and this specific tool set.

- [ ] Write a short decision procedure covering: when to physically
      demonstrate via the Phase 2 interface (visible click, the
      pedagogical moment), when to load/set invisibly via MCP (only where
      Level 1 is a *confirmed* gap, e.g. Browser drag-and-drop), when to
      ask the vision agent to look at the screen first, and when to fall
      back to plain human instructions (Level 4).
- [ ] Explicitly state the "show once, then invite the learner to try it
      themselves next time" pattern discussed this session, so the agent
      doesn't default to doing everything for the learner forever.
- [ ] Fold this into `SUNO_MASTERING_AGENT_POLICY.md` directly (not a
      separate doc) since that's the file OpenCode actually loads as
      `AGENTS.md` at runtime.

**Definition of done:** a new contributor (or future agent) reading the
policy file alone can predict which tool the agent will reach for, for a
given kind of stuck moment, without guessing.

**Depends on:** Phase 2 (there needs to be a real interface to write the
rule around).

---

## Phase 4 — Wire the vision agent into a first-class fallback
**Priority: fifth. Additive, not blocking.**

**Goal:** connect the already-existing screenshot pipeline
(`take_shot.sh`) to the vision agent so "this panel won't appear" /
"this view is hidden" has an actual tool behind it, not just narration.

- [ ] Define the trigger: when a Phase 2 control lookup/click fails to
      resolve, or the learner reports something looks wrong, take a
      screenshot and hand it to the vision agent before improvising.
- [ ] Define what the vision agent is asked to do with the screenshot:
      identify what's visible, flag if it matches a known OPAQUE/GAP area
      from the catalog (Groove Pool, Info View, Browser item selection),
      and suggest the next concrete step.
- [ ] Note the standing use case already flagged in the policy file: the
      Youlean LUFS meter has no queryable UIA/MCP surface — this is the
      first real candidate to wire up.

**Definition of done:** a stuck moment ("I don't see EQ Eight") triggers an
actual screenshot + vision read, not just the agent guessing in text.

**Depends on:** Phase 1 (runtime scope) but not Phase 2/3 — can be built
in parallel with those if convenient.

---

## Phase 5 — Deprecate stale docs
**Priority: least urgent. Housekeeping.**

- [ ] Move or clearly mark `docs/curriculum_map.md` and
      `docs/course_outline.txt` as superseded, pointing readers to
      `docs/suno-mastering-curriculum.md` and
      `docs/suno-mastering-course-breakdown.md`.
- [ ] Sanity-check nothing else in the repo (scripts, other docs) still
      treats the old files as authoritative.

**Definition of done:** no live doc or script references the stale files
as current.

**Depends on:** nothing. Safe to do whenever, including as a filler task
between other phases.
