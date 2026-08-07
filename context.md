# context.md

**Note:** this file is maintainer-facing background, kept in this
(fuller) copy of the repo for orientation. **The agent that runs the
actual survey does not have access to this file** — it works in a
separate, curated environment containing only `AGENTS.md` and the
handful of scripts it needs. If you're reading this to understand what
the agent knows or was told, read `AGENTS.md` instead; this file exists
to orient a human (or a new session) picking the project back up, not
for the agent.

This is a **checkpoint**, not a history. It describes where the project
stands right now. Resolved issues, superseded decisions, and closed
investigations have been pruned — if you need the reasoning behind a
past fix, it's in git history, not here.

## What this project is

This repo runs one autonomous job: point an AI agent at a running
Ableton Live instance, with an hour (often less) and no human clicking
anything for it, and have it come back with a complete map of every
control it could find — device knobs, sliders, buttons, browser items,
view controls — tagged with whatever identifier lets code interact with
it reliably (or a clear note that no reliable identifier exists).

The output is one file: `dumps/control_catalog.json`, a control
catalog. This is not a tutoring project, not a task-execution project —
it's a survey, done once, so every later project (tutor, autonomous
mixer, whatever) doesn't have to re-discover the same ground by hand.

It grew out of `ableton-gui-grounding`, the parent project, which built
real click-and-verify automation for a small, hand-mapped set of
controls (track arm, solo, mute, tempo, transport — 8 tasks). The
click/verify machinery itself (`resolve()`, `click_by_id()`,
`build_automation_id_index()`) is generic — what was missing was the
map. This repo fills that map.

## Current status: complete and verified — ready for downstream use

- **The survey ran to completion**: 104 contexts, 3,797 controls, 0
  `LOAD_FAILED`, all phases (A–F) reached. Recorded in
  `dumps/control_catalog.json`.
- **Static QA passed**: every context cross-checked against raw dump
  files (no orphans, no missing dumps); every duplicate
  `automation_id` explained (see "Known, expected id reuse" below);
  MAPPED/UNMAPPED/OPAQUE status re-derived from raw data and confirmed
  correct catalog-wide, with one deliberate reclassification (Groove
  Pool — see below).
- **Live verification passed**: a 21-context spot-check (9 devices, 11
  views/browser tabs, plus the Groove Pool special check), run via a
  separate standalone repo/agent (`verification_mapping_ableton`),
  came back **21/21 PASS** — all 417 expected `automation_id`s in that
  sample resolved against a live Ableton Live 12 instance. Full detail:
  `verification_report.json` / `verification_report.md` (kept outside
  this repo, in `verification_mapping_ableton`).
- **Verdict**: `control_catalog.json` is approved for handoff to
  downstream automation projects as-is. No further catalog edits are
  pending.

## What "done" means for the catalog

Each entry in `control_catalog.json` is tagged:

- `MAPPED` — real, stable identifier found, ready for click-and-verify
  automation.
- `UNMAPPED` — control exists and was seen, but has no usable
  identifier — needs a name-based or different fallback strategy later.
- `OPAQUE` — nothing exposed at all; the whole device/panel is one
  element with no visible children. (All 17 OPAQUE entries are native
  Max-for-Live devices — this is expected, not a gap.)
- `LOAD_FAILED` — never surveyed because it couldn't be placed by any
  available method. (Count: 0.)

Alongside the catalog, `coverage_summary` gives counts per category,
recomputed from `contexts` (the source of truth) rather than trusted as
stored.

## Known, expected id reuse (not bugs)

Duplicate `automation_id`s across contexts exist and are expected:

- `TrackView.Device[0].*` ids are **slot-relative** — they identify
  "whatever device currently occupies this slot," not one specific
  device permanently. Every device was surveyed in the same slot, so
  this id shape is legitimately reused across all of them. **Downstream
  automation must confirm what's actually loaded before trusting one of
  these ids** — it does not mean "this specific device's control,
  forever."
- Some `ArrangementView.*` / `SessionView.*` / `ContentBrowser*` ids
  appear in both a broad panoramic context and a separately-surveyed
  zoomed-in child context covering the same real UI element (or a
  Browser-toolbar control that persists across all 6 tab contexts).
  Same id, same real element, recorded under two context names —
  redundant, not conflicting.

## Groove Pool — special case

`Groove Pool` is classified `UNMAPPED`, not `MAPPED`, despite having one
recorded `automation_id`. Its only carried id is `GroovePool` itself —
the panel's own top-level group id — with no real child control ids
beneath it. This was confirmed both statically (raw dump inspection)
and live (subtree walk during verification): 5 nodes in the panel's
tree, exactly 1 (the group id itself) carries an automation_id. Any
future re-survey of this panel should expect the same result unless
Ableton's UI structure for Groove Pool changes.

## Known caveats for downstream consumers

- **Live verification covered 21 of 104 contexts** — a representative
  spot-check by design (see `AGENTS.md` in
  `verification_mapping_ableton`), not a full live re-walk of the
  catalog. The other ~83 contexts are validated only by the static
  pass above. This is expected residual scope, not a gap to close
  before handoff.
- **AbletonMCP endpoints mix 0-based and 1-based track indexing**
  inconsistently across calls (e.g. `get_chain_info` is 0-based;
  `delete_device` / `load_instrument_or_effect` / `get_track_info` are
  1-based; return tracks are reachable only via volume/pan-style
  endpoints, not `get_track_info`). This is an MCP-layer quirk, not a
  catalog defect, but will affect any automation built directly on
  these calls unless normalized first.

## Repo structure note

This (maintainer) copy of the repo may carry more files than any
curated agent environment built from it — test files, license, older
docs, etc. If you add something here intending an agent to use it, it
needs to be added to that agent's curated environment and to the
relevant `AGENTS.md` explicitly — being in this repo is not sufficient.

## Open items

- **DECISION PENDING: is the survey sufficient to unblock downstream
  projects, or does it need a second pass? Waiting on the maintainer to
  specify what those downstream projects (tutor, autonomous mixer,
  etc.) actually need to control.** This is the live question as of
  2026-08-07 -- next session should start here, by asking the
  maintainer for that requirements list, not by re-deriving the
  analysis below (already done, don't repeat it).

  **Background — where this question came from:** an earlier session
  had a dispute between the maintainer's claim ("every control has an
  id, an agent can theoretically operate Ableton like DOM elements")
  and a correction (only 865/3797 controls catalog-wide have a real
  `automation_id`, ~23%). The maintainer asked for this to be settled
  with data, not opinion, and specifically wanted to know: **is the
  uncovered 77% a genuine edge case, or is it the normal/default
  outcome?** The `ableton_click_proof.py` saga (see entry below) was
  the maintainer's way of stress-testing whether the mapped portion is
  even real -- it is (see PASSED entry below).

  **Analysis done this session (verified against control_catalog.json
  directly, figures are exact, not estimated):**

  The 23% figure hides a sharp split by *what kind* of control:

  - **Navigation/mixing layer -- essentially complete, genuinely an
    edge case when something's missing:** Session View 41/41 (100%),
    Clip Detail View 26/26 (100%), Master Track (Session) 5/5 (100%),
    Arrangement View 33/42 (79%), Track Mixer 6/8 (75%). This is
    exactly the layer `ableton_click_proof.py` exercised and it PASSED
    live. Track arm/mute/solo/volume/pan, transport, browser
    navigation -- solid, proven, not just on paper.

  - **In-device sound-shaping parameters (the sliders/knobs/combo
    boxes that actually shape the sound inside an effect or
    instrument) -- the gap here is the DEFAULT case, not an edge case,
    even inside contexts the catalog labels `MAPPED`.** Catalog-wide,
    only 249/632 (39%) of Slider/ComboBox controls inside `MAPPED`
    contexts have an automation_id. Worse, some devices are `MAPPED`
    status with ZERO controllable parameters: Auto Filter 0/11, Channel
    EQ 0/5, Chorus-Ensemble 0/9, Looper 0/7, Phaser-Flanger 0/19, Tuner
    0/1, Random 0/3, Drift 0/44. Auto Filter -- the very device used
    for the click-proof -- has NO mapped sound parameter; the one thing
    proven live (Sidechain Toggle) is UI chrome (expand/collapse the
    device view), not a parameter that shapes audio. Common everyday
    tools are similarly thin: Compressor 1/9, Delay 1/10, Echo 1/19,
    Limiter 1/5.

  **Why this matters for the decision:** `MAPPED` at the catalog's
  context level means "this device has at least one automation_id
  somewhere" -- often just the device's own group id or a chrome
  button -- not "this device's parameters are controllable." A
  downstream project that only needs navigation/mixing (arm a track,
  set volume, browse and load a device) can treat the survey as done;
  the click-proof result generalizes safely to that layer. A downstream
  project that needs to actually turn a filter cutoff or a compressor
  threshold cannot rely on the current catalog for most devices --
  that gap is systemic, not a rounding error, and would need either a
  second survey pass targeting device parameters specifically, or a
  different automation strategy (e.g. relative slider drag + read-back,
  rather than a stable id) accepted as this project's real answer for
  that 60%+ of parameters.

  **Next session action:** get the maintainer's actual list of what the
  downstream projects need to control, then give a direct
  done-or-not-done verdict per project against the numbers above (no
  new analysis needed unless the requirements point at data not already
  pulled here).

- **`ableton_click_proof.py` proof: PASSED (2026-08-07).** Ran on the
  maintainer's Windows machine against a live Ableton Live 12 instance
  with Auto Filter loaded as the first device on a selected track.
  `TrackView.Device[0].TitleBar.ExtendViewButton` ("Sidechain Toggle")
  resolved to a real live element, `toggle_state` read `0` before the
  click and `1` after -- end-to-end confirmation that a catalog
  `automation_id` both resolves and actually controls the real element,
  not just that a click landed. Full trail in
  `ableton_click_proof_result.json` (maintainer's machine).

  Getting there required three fixes to the original script, all now
  folded into the version the maintainer ran (worth keeping in mind for
  any future one-off pywinauto script written outside the two curated
  agent environments, since those already avoid these pitfalls):
  1. `descendants(auto_id=...)` doesn't work on current pywinauto
     (0.6.9) -- `auto_id` was dropped from `build_condition()`/
     `descendants()` and is now only wired into `find_elements()`/
     `child_window()`. Fix: pull elements unfiltered, filter by
     `.element_info.automation_id` in Python.
  2. Ableton's Session/Device views are UI-virtualized (see the
     `ensure_window_ready` lesson in `dump_ableton_pywinauto.py`) --
     restore/focus/maximize the window before walking the tree, or
     controls that aren't rendered on screen simply don't exist as UIA
     elements yet.
  3. **The one that actually mattered here:** `descendants()` calls
     `FindAll(TreeScope_Descendants, TrueCondition)` in one shot.
     Against Ableton's large tree this raised a COM error that
     pywinauto's `_get_elements()` silently swallows, returning `[]`
     with no exception and no warning -- indistinguishable from "found
     nothing" until a diagnostic pass counted total elements and saw
     zero. `dump_ableton_pywinauto.py` was already avoiding this by
     walking `.children()` manually, layer by layer, instead of calling
     `descendants()` -- the proof script just hadn't followed that
     pattern. Once it did, the tree walk saw 447 elements (229 with a
     non-empty automation_id) and the target resolved immediately.

  Net: no catalog defect, no environment misconfiguration on the
  maintainer's end -- the failure was entirely in the standalone
  script's use of a pywinauto API that's fragile against large trees.
  Nothing in `control_catalog.json` needs to change because of this.

- If a downstream project (tutor, autonomous mixer) surfaces a stale or
  non-resolving `automation_id` outside the 21 verified contexts,
  that's the first place to look — not a contradiction of the "ready
  for handoff" verdict, but the expected edge of this project's scope.
