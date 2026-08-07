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

- **Awaiting result of `ableton_click_proof.py`.** A standalone script
  (not part of either curated agent environment — a one-off proof
  requested directly by the maintainer) was handed off to run locally
  on the maintainer's Windows machine. It targets one real control from
  the catalog — `Auto Filter` → `Sidechain Toggle`
  (`TrackView.Device[0].TitleBar.ExtendViewButton`) — reads its
  toggle_state before a click, clicks it via pywinauto/UIA, reads the
  state after, and writes `ableton_click_proof_result.json` plus a
  printed trail. Purpose: end-to-end confirmation, on the maintainer's
  own machine, that a catalog `automation_id` resolves to a real live
  element and actually controls it (not just resolves in an agent
  session). Prerequisite given: load Auto Filter as the first device on
  a track and select that track before running.
  **Next session: read the maintainer's reported output (terminal trail
  and/or the result JSON) and confirm/deny the proof succeeded.** If it
  failed, the likely causes to check first are: script run under WSL
  Python instead of Windows Python, or Auto Filter not loaded as the
  first device on the selected track.

- If a downstream project (tutor, autonomous mixer) surfaces a stale or
  non-resolving `automation_id` outside the 21 verified contexts,
  that's the first place to look — not a contradiction of the "ready
  for handoff" verdict, but the expected edge of this project's scope.
