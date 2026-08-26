# PHASED_PLAN.md — Resumable Implementation Plan

Companion to `context.md` (read that first for *why*; this file is *what,
in what order*). Each phase has a checklist, a definition of done, and its
dependencies, so a future session can jump straight to the first unchecked
box without re-reading the whole conversation history.

**How to use this file:** check boxes off as work completes. Update
"Current Status" below at the end of every session, even a partial one.

---

## Current Status

> **Phase:** 5 complete — all six original phases (0–5) done. A new Phase 6 was logged
> this session (design sketch only, not started).
> **Last updated:** this session — logged Phase 6 (screenshot coordinate annotation) as
> a new open item, and documented the WSL-Python-vs-`python.exe` split and the Ableton
> manual reference in `SUNO_MASTERING_AGENT_POLICY.md`. (Phase 2's one open item — a
> live-Ableton run of `call_control` — is still outstanding; see Phase 2 below.)

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

- [x] Decide: does `../suno-mastering-course` become a **superset** runtime
      (mastering curriculum + click-automation layer + on-demand catalog
      access), or does it stay separate and lean on a *different* set of
      tools (vision + MCP + generic primitives, minimal/no pywinauto task
      layer)? **Decided: hybrid.** Include the click-demonstration
      primitives (`automate_ableton_task.py` + hard deps), the catalog
      (on-demand lookup, never bulk-loaded), and `take_shot.sh`. Exclude
      `orchestrate.sh` — its screenshot-per-action pipeline is built for
      the sibling course's pre-planned, provable lesson steps, not live
      conversational tutoring.
- [x] Update `build_mastering_env.sh`'s `FILES[]` whitelist to match the
      decision. **Done** — added `take_shot.sh`,
      `scripts/automate_ableton_task.py`, `scripts/dump_ableton_pywinauto.py`,
      `scripts/keyboard_shortcuts.py`, `scripts/dumps/control_catalog.json`.
      Rebuilt `../suno-mastering-course` end-to-end and verified all 9
      files sync correctly, `mastering_progress.md` is still preserved
      across reruns, and the Phase 0 Groove Pool guard survives the copy
      intact (re-verified live in the built runtime).
- [x] Update `SUNO_MASTERING_AGENT_POLICY.md`'s opening "Role" section so
      it accurately states which tools the mastering agent actually has —
      no more mismatch between what the policy assumes and what the build
      script ships. **Done** — replaced the vague "pywinauto UIA layer"
      claim with an itemized "Available Tooling" section, including the
      honest caveat that device-parameter demonstration (e.g. EQ Eight)
      isn't possible yet until Phase 2's generic interface exists, and an
      explicit note that `orchestrate.sh` is NOT included.

**Definition of done:** the policy file and the build script agree on
which tools exist in the runtime. No aspirational references to tools that
aren't actually whitelisted.
**✅ Done.**

**Depends on:** nothing technical, just a decision. Should happen before
Phases 2–4 so they're not built into the wrong (or a not-yet-existing) folder.

---

## Phase 2 — Build the generic control-invocation interface
**Priority: third. The structural fix for the "memorize scripts" problem.**

**Goal:** let the agent call the already-generic write primitives
(`set_checkbox_by_id`, `set_slider_by_id`, `set_combobox_by_id`) with any
automation_id it looks up live, instead of only through the fixed
`--task {arm_track, solo_one, ...}` menu.

- [x] Add a general entry point to `automate_ableton_task.py` — sketched
      as `call_control(automation_id, action, value=None, dry_run=...)` —
      that dispatches to the correct proven-safe primitive based on the
      control's type (read that type from a live/narrow catalog lookup,
      not hardcoded). **Done** — `call_control()` reads `control_type`
      straight off the freshly-`resolve()`d live UIA element (not a
      hardcoded per-id table, and not blind trust in a possibly-stale
      catalog snapshot), then dispatches to `set_checkbox_by_id` /
      `set_slider_by_id` / `set_combobox_by_id` accordingly.
- [x] Add a matching CLI mode (e.g. `--control <automation_id> --action
      <set|click> --value <v>`) alongside the existing `--task` mode —
      don't remove `--task`, it's still fine for genuinely fixed sequences.
      **Done** — `--control`/`--action`/`--value` added; mutually
      exclusive with `--task` (argparse-level error if both given);
      `--value` is auto-typed (`"true"/"false"` → bool, bare number →
      float, else → string) since the CLI only ever hands over strings.
- [x] Guard rails carried over unchanged: still only the three proven
      control types; still never call `SetValue()`; unknown/untested
      control types (e.g. the `Text`-type EQ Eight band selectors found
      this session) should refuse with a clear "not yet validated" error,
      not attempt a guess. **Done** — `UnsupportedControlType` is raised
      for any control_type outside `{CheckBox, Slider, ComboBox}`, naming
      the Text-type band-selector case explicitly. `call_control()` calls
      the same three primitives verbatim (no new write path), so the
      permanently-disabled `SetValue()` prohibition is untouched.
- [x] Add a narrow, on-demand catalog lookup helper (e.g.
      `lookup_control(device_or_context, name_hint)`) that returns just the
      matching automation_id(s) + control_type — never load the full
      `control_catalog.json` into any agent context wholesale. **Done** —
      `lookup_control()` opens the catalog file itself and returns only
      the rows matching `name_hint` inside one named context; raises
      `LookupError` (with close-match suggestions) if the context itself
      isn't found, distinct from "found the device, no matching control."
- [x] Validate end-to-end on one real example: EQ Eight's Frequency slider
      (`TrackView.Device[0].Freq`), since it's already confirmed present
      and is a proven-safe control type (Slider). **Partially done, with
      an honest caveat:** `lookup_control("EQ-Eight", "freq")` was run
      against the real `control_catalog.json` and correctly returns
      `{"automation_id": "TrackView.Device[0].Freq", "control_type":
      "Slider", "name": "Frequency"}` — that part is a genuine, live-data
      check. But **this session's environment has no Windows machine, no
      running Ableton, and no `pywinauto`** (Linux sandbox), so
      `call_control()` itself could only be exercised against a hand-built
      mock UIA tree standing in for the real one (all three control types,
      `click` vs `set`, every guard-rail rejection, and the
      `UnsupportedControlType` path all passed against the mock). **A real
      `--control TrackView.Device[0].Freq --action set --value <hz> --live`
      run against a live Ableton project with EQ Eight loaded on the
      selected track is still outstanding** and should be the first thing
      whoever has that environment does before checking this box off as
      fully proven — the mock only proves the dispatch logic is sound,
      not that the live UIA write path behaves identically to
      `task_idiom_demo`'s already-proven Freq-slider round trip.

**Definition of done:** the sibilance scenario's "set the EQ band" step can
be executed by calling the generic entry point with a live-looked-up
automation_id — no new named `task_*` function required.
**Logic complete and mock-verified; live-Ableton confirmation still
outstanding (see caveat above).**

**Depends on:** Phase 1 (needs to know which runtime this ships in).

---

## Phase 3 — Write the explicit escalation decision rule
**Priority: fourth. The policy layer on top of Phase 2.**

**Goal:** replace the current vague "per the escalation ladder in the
README" reference in `SUNO_MASTERING_AGENT_POLICY.md` with a concrete rule
for this specific persona and this specific tool set.

- [x] Write a short decision procedure covering: when to physically
      demonstrate via the Phase 2 interface (visible click, the
      pedagogical moment), when to load/set invisibly via MCP (only where
      Level 1 is a *confirmed* gap, e.g. Browser drag-and-drop), when to
      ask the vision agent to look at the screen first, and when to fall
      back to plain human instructions (Level 4). **Done** — new
      "Escalation Decision Rule" section, six ordered steps (first-time
      demonstration → invite learner to repeat it → MCP-only for device
      loading → MCP read-back for verification → screenshot-before-
      improvising on any resolve failure or reported visual problem →
      Level 4 for genuine gaps), plus a quick-reference table.
- [x] Explicitly state the "show once, then invite the learner to try it
      themselves next time" pattern discussed this session, so the agent
      doesn't default to doing everything for the learner forever.
      **Done** — step 2 of the decision rule states this directly: once
      an idiom has been demonstrated once in a session, the next
      occurrence is the learner's to try, not a re-demonstration.
- [x] Fold this into `SUNO_MASTERING_AGENT_POLICY.md` directly (not a
      separate doc) since that's the file OpenCode actually loads as
      `AGENTS.md` at runtime. **Done** — inserted directly into that
      file, right after "Available Tooling" and before "Learner Profile."

**Definition of done:** a new contributor (or future agent) reading the
policy file alone can predict which tool the agent will reach for, for a
given kind of stuck moment, without guessing.
**✅ Done.**

**Depends on:** Phase 2 (there needs to be a real interface to write the
rule around).

---

## Phase 4 — Wire the vision agent into a first-class fallback
**Priority: fifth. Additive, not blocking.**

**Goal:** connect the already-existing screenshot pipeline
(`take_shot.sh`) to the vision agent so "this panel won't appear" /
"this view is hidden" has an actual tool behind it, not just narration.

- [x] Define the trigger: when a Phase 2 control lookup/click fails to
      resolve, or the learner reports something looks wrong, take a
      screenshot and hand it to the vision agent before improvising.
      **Done** — new "Vision Fallback: Screenshot-and-Diagnose" section
      in `SUNO_MASTERING_AGENT_POLICY.md` defines the trigger as any of:
      `call_control`/`click_by_id` raising `LookupError` /
      `EscalationExhausted` / `UnsupportedControlType`; the learner
      reporting something looks wrong/missing/hidden; or a value with no
      UIA/MCP surface at all (the LUFS case).
- [x] Define what the vision agent is asked to do with the screenshot:
      identify what's visible, flag if it matches a known OPAQUE/GAP area
      from the catalog (Groove Pool, Info View, Browser item selection),
      and suggest the next concrete step. **Done** — a 5-step procedure:
      take the screenshot (with a `LABS/mastering_<YYYY-MM-DD>/` +
      zero-padded `<seq>` naming convention, since this runtime doesn't
      have `orchestrate.sh`'s fixed per-lesson `lab_dir` scheme), look at
      it directly (clarified this is the agent's own multimodal read, not
      a second tool call — "vision agent" in `context.md` was never a
      separate process to wire up, just an unused capability), state
      what's visible before proposing anything, cross-check against
      Groove Pool / Info View / Browser-item-list before treating it as a
      new problem, then suggest one concrete next step.
- [x] Note the standing use case already flagged in the policy file: the
      Youlean LUFS meter has no queryable UIA/MCP surface — this is the
      first real candidate to wire up. **Done** — "Verify, Don't Trust"'s
      LUFS entry now points at this procedure instead of the old "ask the
      learner to read it" placeholder; the procedure itself spells out
      screenshot → read the number yourself → cross-check against the
      learner's own read, flagging any disagreement rather than silently
      picking one.

**Definition of done:** a stuck moment ("I don't see EQ Eight") triggers an
actual screenshot + vision read, not just the agent guessing in text.
**✅ Done** — as a defined procedure the policy file now requires; not
independently re-verified against a live Ableton session this session (no
Windows/Ableton available in this environment, same caveat as Phase 2).

**Depends on:** Phase 1 (runtime scope) but not Phase 2/3 — can be built
in parallel with those if convenient.

---

## Phase 5 — Deprecate stale docs
**Priority: least urgent. Housekeeping.**

- [x] Move or clearly mark `docs/curriculum_map.md` and
      `docs/course_outline.txt` as superseded, pointing readers to
      `docs/suno-mastering-curriculum.md` and
      `docs/suno-mastering-course-breakdown.md`. **Done, with a
      correction to the original framing:** these two files are NOT
      globally stale — `docs/curriculum_map.md` is still a live,
      accurate, actively-referenced (by `README.md`) reference for the
      *separate, sibling click-automation UI-grounding course*
      (confirmed by checking `docs/archived/v004/reports/phase5_report.md`,
      which shows `curriculum_map.md` was deliberately authored for that
      course's own phased plan). Blanket-deprecating them would have made
      `README.md`'s still-current "Proven-write controls" reference and
      Phase E note wrong. What was actually true (per `context.md` §3)
      is narrower: these files are stale *specifically as a curriculum
      source for the mastering course* — a future mastering-course
      session could plausibly stumble onto a file just called
      "curriculum_map.md" and mistake it for its own curriculum. Fixed
      that specific risk instead: added a scope-note banner to the top
      of both files pointing a reader who lands there for the mastering
      course to `docs/suno-mastering-course-breakdown.md` /
      `docs/suno-mastering-curriculum.md`, while leaving both files
      otherwise fully intact and still authoritative for the
      click-automation course they were actually written for.
- [x] Sanity-check nothing else in the repo (scripts, other docs) still
      treats the old files as authoritative **for the mastering course**.
      **Done** — grepped `docs/suno-mastering-curriculum.md`,
      `docs/suno-mastering-course-breakdown.md`, `docs/mastering_progress.md`,
      and `SUNO_MASTERING_AGENT_POLICY.md`: zero references to
      `curriculum_map` or `course_outline` in any of them already, so
      there was nothing else to fix on the mastering side. (Left
      `README.md`'s references alone, since those are correctly describing
      the click-automation course, not the mastering course.)

**Definition of done:** no live doc or script references the stale files
as current. **Rescoped to: no *mastering-course* doc or script treats
`curriculum_map.md`/`course_outline.txt` as its curriculum source** — the
click-automation course's own use of them remains current and correct on
purpose.
**✅ Done.**

**Depends on:** nothing. Safe to do whenever, including as a filler task
between other phases.

---

## Phase 6 — Annotate screenshots with the clicked element's location
**Priority: additive, not blocking. Logged this session as a design sketch — NOT started.**

**Goal:** instead of asking the learner to eyeball "the Frequency knob" (or whichever
control was just clicked) in a raw screenshot, draw a marker — a numbered circle or a
box — directly on the element's location, so the learner can see exactly what was
clicked without guessing.

**Why this is feasible (confirmed this session, not just assumed):**
- Every resolved pywinauto control already exposes `control.rectangle()` — screen-
  absolute pixel coordinates. This is already used today for diagnostics (see
  `task_probe_toggle` / `task_probe_solo_transport` in `automate_ableton_task.py`,
  which print `rect` after every click).
- `take_shot.sh` already computes the Ableton window's own screen-absolute rect
  (`GetWindowRect`) before capturing.
- So converting "where is this element in the screenshot" is simple arithmetic no new
  capability is required for:
  `image_x = element_rect.left - window_rect.Left` (same pattern for `y`).
- Drawing the marker itself is a small addition — either extend `take_shot.sh`'s
  existing PowerShell/System.Drawing capture step (no new dependency), or do it in
  `python.exe` with Pillow, whichever is easier to wire into `call_control`'s existing
  click flow.

**The real blocker — DPI awareness mismatch (must be resolved before this is trustworthy):**
- `take_shot.sh` explicitly calls `SetProcessDPIAware()` before capturing.
- `automate_ableton_task.py` (pywinauto) does **not** currently set any DPI awareness.
- If the two processes (`powershell.exe` capturing the screenshot, `python.exe` resolving
  the element) disagree on DPI awareness on a scaled display, their coordinate systems
  won't agree either — an annotation box computed from a mismatched rect will silently
  drift off the actual button. This has to be fixed by making both processes agree on
  DPI-awareness mode (most likely: make the pywinauto-driving `python.exe` process
  explicitly call `SetProcessDPIAware()` too, the same way `take_shot.sh` does, and
  confirm both report the same window rect for a shared reference point) before the
  annotation coordinates can be trusted — not an optional nice-to-have, a correctness
  requirement.

**Sketch of the work, not yet broken into checkable tasks:**
- [ ] Make DPI-awareness mode consistent between the `python.exe` process running
      pywinauto and the PowerShell process running `take_shot.sh` (likely: call
      `SetProcessDPIAware()` from the Python side too), and verify with a known
      reference point that both report the same screen coordinates before trusting
      annotation math.
- [ ] Extend the click flow (`call_control` and/or `click_by_id`) to optionally capture
      the resolved element's `rectangle()` at click time, not just log it.
- [ ] Add an annotation step — numbered circle or box drawn at the converted
      image-relative coordinates — either inside `take_shot.sh` (PowerShell/
      System.Drawing) or as a small `python.exe` + Pillow post-processing step.
- [ ] Decide the calling convention: does this become a new `take_shot.sh` argument
      (e.g. an optional `--mark x,y,label`), a separate annotate-in-place script run
      after the plain screenshot, or built into a future `call_control`-driven "click
      and show me" combined helper?
- [ ] Validate on one real example end-to-end (a known control, a known click, one
      annotated screenshot that visibly circles the right element) before relying on
      it in a live lesson.

**Definition of done:** a screenshot taken right after a `call_control`/`click_by_id`
call visibly marks the control that was just clicked, with coordinates confirmed
correct (not just computed) on a DPI-scaled display.
**Not started — design only.**

**Depends on:** Phase 2 (needs the generic control path to know which element to
annotate) and Phase 4 (extends the existing screenshot fallback). Safe to pick up
independently whenever someone has a live Ableton + Windows environment to verify the
DPI-awareness fix against.
