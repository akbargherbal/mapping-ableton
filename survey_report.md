# Survey Report — Ableton Control Catalog

Retrospective on running the Ableton control survey (2026-08-07) as an AI agent.
Honest account: what was planned, what actually happened, what went well, what went wrong,
and what I'd do differently. Companion to `survey_plan.md` and `survey_checklist.md`; the
data itself is in `dumps/control_catalog.json`.

---

## 1. The task, in one paragraph

Build one master control catalog for Ableton Live 12: every control discoverable in the UI,
tagged with whatever identifier future automation can use to interact with it reliably (or a
clear note that no reliable identifier exists). A read-only survey — 87 native devices plus
the main views/panels/tracks, one entry per control, written incrementally, with honest
MAPPED / UNMAPPED / OPAQUE / LOAD_FAILED statuses. AGENTS.md's core rules: never stop and
wait on a human, never invent an automation_id, trust what you observe over what a document
assumes.

## 2. What went well

- **The sanity checks earned their keep.** The very first step caught three plan-breaking
  reality gaps before a single device was surveyed: the WSL2 Linux `python` had no UIA
  backend at all (a native-Windows pywinauto `Desktop` was required), `dump_ableton_states.py`
  and `automate_ableton_task.py` were broken by a missing `keyboard_shortcuts.py`, and
  AbletonMCP was only half-functional. Had I trusted the documented toolbox, the whole run
  would have failed on device #1.
- **Trusting observation over the document was the right call repeatedly.** The document said
  "use `python`"; the only working interpreter was Windows `python.exe`. I logged the
  discrepancy and moved on instead of stopping to ask.
- **The core premise was validated before the long loop.** Loading EQ Eight and seeing real
  `TrackView.Device[0].Freq/.Gain/.Q` automation_ids proved that loaded devices do render
  usable UIA identifiers — then I committed to all 87 devices.
- **Building small read-only tooling was cheap and high-leverage.** Four scripts
  (`survey_device.py`, `survey_section.py`, `update_catalog.py`, `browser_switch.py`)
  reimplemented the helpers the broken modules were supposed to provide, and turned the
  per-device loop into a ~30-second mechanical step. The catalog merge recomputed statuses
  and counts from actual data, so it never drifted.
- **Incremental writing paid off dramatically.** Ableton crashed mid-survey (see below).
  Because the catalog and per-device dumps were written after every device, the crash cost
  nothing. This is the single best decision in the whole run.
- **Honest classification was maintained.** Every automation_id in the catalog was observed
  in a dump; OPAQUE was reserved for genuinely childless elements; the group-track gap and
  compact-view limitations were logged as documented gaps rather than papered over.
- **Completion.** 104 contexts, 3,797 controls, 0 LOAD_FAILED, all checklist items done,
  all phases A–F reached, in ~87 minutes of wall time (plus crash recovery).

## 3. What went wrong

- **The documented toolbox was partly fiction.** Two of the five pywinauto tools listed in
  AGENTS.md didn't import (`automate_ableton_task.py`, `dump_ableton_states.py` — missing
  `keyboard_shortcuts.py`, only stale `.pyc` files left). I had to reimplement
  `build_automation_id_index`, `get_toggle_state`, and browser navigation myself. Cost:
  maybe 30 minutes of tooling I didn't plan for.
- **Ableton crashed mid-survey.** During the Phase F Groove Pool step the window simply
  vanished — no close command was ever sent. Likely an app crash, possibly aggravated by the
  rapid UIA/keyboard automation. The user restarted it and asked whether the recovered
  session was needed (it wasn't — all state was in files). The most disruptive event, and the
  only one that required a human.
- **Compact device views are a real data-quality gap.** Compressor loads in a compact view
  (only ~17–34 controls, `ViewMode` radios, no Threshold/Ratio/Attack/Release). I could not
  find a reliable way to expand it (the `ExtendViewButton` is repurposed as "Sidechain
  Toggle"; clicking `ViewMode` radios and double-clicking the title did nothing useful). So
  several devices were cataloged in their default render only, with a note. The catalog is
  honest about this, but it's a genuine limitation.
- **Group-track creation failed.** shift-click + Ctrl+G, shift-arrow + Ctrl+G, and the
  context-menu "Group Tracks" all failed to produce a group in this environment (UIA
  selection extension didn't stick). I burned three attempts, then logged it as a documented
  gap per the escalation discipline instead of hammering it further.
- **An early classification bug would have poisoned the catalog.** My first status rule
  counted the device group node and its title-bar text as "controls with automation_id",
  which made every device look MAPPED. Caught on Amp, fixed to exclude scaffolding nodes,
  and re-derived. A reminder that aggregate statistics need a correctness check on a known
  case, not just trust in the script.
- **Rabbit holes cost time.** The Compressor expand investigation and the grouping attempts
  each ate several tool calls. In hindsight the expand investigation especially was
  over-invested: the plan's policy ("record what renders, note the limitation") was the right
  answer from the start, and the extra probing didn't change it.
- **MCP partial failure closed off a cross-check.** `get_device_parameters` (No module named
  'MCP_Server') and `get_session_info` (C++ signature error) were dead, so I could never
  cross-check the UIA control set against Live's LOM parameter list. The catalog is UIA-only
  by necessity.

## 4. Planned vs achieved

| Plan (survey_plan.md) | Actual |
|---|---|
| 47 Audio Effects, 15 MIDI Effects, 23 Instruments, 2 Drums, 0 Plug-Ins | Exactly that; all loaded and surveyed, 0 failures |
| Phases A–F in fixed order | Done; every phase reached and every checklist item checked |
| ~70–85 min | ~87 min of surveying + crash downtime |
| MCP tier-1 load for every device | Used for all 86 loads (tier 2 never needed, tier 3 never triggered) |
| Value-pattern check "feasible" | Confirmed, with a surprising shape: device sliders generally do NOT expose RangeValuePattern; checkboxes do expose TogglePattern. "Clickable" ≠ "readable" was the core finding |
| Predictable MAPPED/UNMAPPED/OPAQUE mix | 48 / 38 / 17. The OPAQUE set turned out to be exactly the native Max-for-Live devices — a clean, explainable pattern, not random |
| Tooling usable as documented | Mostly not; had to rebuild a small read-only toolchain. This was the biggest deviation between plan and reality |
| Resumability via catalog + checklist | Proven for real when Ableton crashed and the run resumed from files |

Under-delivered: compact-view device controls (not fully expanded), group/folded tracks
(documented gap), LOM cross-verification (impossible). Over-delivered: full coverage of the
Session/Arrangement/browser/clip-detail contexts, which were richer than expected.

## 5. Key findings that future automation should know

1. **Max-for-Live devices are opaque to UIA.** Every OPAQUE device is an
   `MxDeviceAudioEffect`/`MxDeviceInstrument` (Align Delay, LFO, Shaper, all DS-* drum
   synths, Envelope MIDI, Note Echo, etc.). Their controls are only reachable through the
   Live Object Model, not the accessibility tree.
2. **Device knobs/sliders are not value-readable.** No RangeValuePattern on most device
   sliders — automation can click them (by coordinate) but cannot read the value back via UIA.
   Transport, session/arrangement mixer faders, and clip-detail properties DO expose value
   patterns. The catalog records this per control.
3. **Real, stable ids exist and are patterned.** `TrackView.Device[N].<Param>` for the
   top-level device macros, `Band[N].Selector` for EQ Eight bands, `SessionView.Track[N].
   Mixer.<Field>`, `ArrangementView.ReturnTrack[N].Mixer.*`, `ClipDetailView.*`. These are
   the MAPPED backbone for click-and-verify automation.
4. **Browser entries carry no ids at all** — top-level tabs and items inside categories are
   all matched by (control_type, name).
5. **Window state changes what exists.** The same device rendered different node counts at
   different times (UI virtualization). Always dump maximized; treat sparse dumps with
   suspicion.

## 6. Lessons for next time

- **Check reality first, and let it change the plan.** Every significant problem in this run
  was caught by the sanity checks or the load tests; none was avoided by planning harder.
- **Persist after every unit of work.** The crash proved the incremental rule; without it the
  run would have lost everything.
- **Set a probe budget for UI-mechanics rabbit holes.** The expand-investigation taught me
  that if two attempts don't reveal a mechanism, log the limitation and move on — the plan's
  fallback policy was already correct.
- **Validate aggregate logic on a known case.** The MAPPED-everything bug was caught only
  because I inspected a known device (Amp) by hand. Do this once per new pipeline.
- **For a follow-up, try GUI-level techniques for the two gaps** (device expand, track
  grouping) — e.g. keyboard focus-and-Enter, or a human-in-the-loop once — and consider
  LOM-side parameter enumeration if the MCP server is fixed, to cross-check the UIA data.
- **Keep the human informed about crashes, not about every step.** The one time I needed a
  human, it was purely because the app died; the files carried the work.

## 7. Bottom line

The survey was delivered: a valid, honest, resumable catalog of 3,797 controls across 104
contexts, with the automation-usable identifiers separated from the ones that need
name/coordinate fallbacks. The plan survived contact with reality because the methodology —
check first, persist incrementally, classify honestly, never invent an id — was sound even
when the individual assumptions were wrong. The failures (broken tooling, a crash, compact
views, failed grouping) are all documented in the catalog's `coverage_summary.unexpected_errors`
and in `survey_checklist.md`, so the next run knows exactly what is trustworthy and what
still needs a human hand.
