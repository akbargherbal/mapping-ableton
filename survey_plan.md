# Ableton Control Survey — Master Plan + Discoveries

Session handoff document. Start here in any future session before touching the survey.
Everything in this file is based on what was **actually observed** on 2026-08-07 (sanity checks run
per AGENTS.md §1). Where reality differed from AGENTS.md, observed behavior wins and is marked
clearly.

---

## 0. TL;DR for the next session

- Environment is **WSL2** (Linux shell) + Windows 10/11 host running **Ableton Live 12 Suite**,
  project "Untitled - Ableton Live 12 Suite" open.
- **All UIA work must run under the Windows Python**, never the WSL `python`:
  ```
  PYEXE=/mnt/c/Users/DELL/AppData/Local/Programs/Python/Python312/python.exe
  $PYEXE dump_ableton_pywinauto.py --no-print --label <name>
  ```
  (`--no-print` is MANDATORY — console `print_tree` crashes on cp1252 Unicode before the JSON is
  written. WSL `python` has a Linux pywinauto with NO UIA backend.)
- **AbletonMCP is connected but partial** (see §3). Loading devices via MCP works and is the tier-1
  path. `get_device_parameters` and `get_session_info` are broken — all control data comes from UIA
  dumps.
- **`automate_ableton_task.py` and `dump_ableton_states.py` are broken** (missing
  `keyboard_shortcuts.py`). Only `dump_ableton_pywinauto.py` imports cleanly. The next session must
  write one small read-only helper (`survey_device.py`, spec in §8) before surveying.
- Loaded devices DO render controls in UIA under `Device Detail > TrackView.Device[0]` with real
  automation_ids — the survey premise is validated. Some devices render a COMPACT subset by default
  (see §5 view-state policy).
- **The survey has NOT started yet.** No `dumps/control_catalog.json` exists. Begin at §7 Phase A.

---

## 1. Environment & tooling reality (observed)

| Tool | Status | Notes |
|---|---|---|
| `dump_ableton_pywinauto.py` | ✅ works (via `$PYEXE`) | Use `--no-print`. Default maximize is fine. Writes `scripts/dumps/` JSON. |
| WSL `python` | ❌ no UIA | Linux-flavored pywinauto 0.6.9; `from pywinauto import Desktop` fails (only defined under win32). |
| Windows `python.exe` (`$PYEXE`) | ✅ full UIA | pywinauto 0.6.9, `Desktop(backend='uia')` sees Ableton (ProcessId 50212, title "Untitled - Ableton Live 12 Suite"). |
| `grep_dump.py` | ✅ works (any python) | Pure stdlib; use on saved dumps. |
| `automate_ableton_task.py` | ❌ import fails | `import keyboard_shortcuts` → ModuleNotFoundError (only stale `.pyc` remains). `build_automation_id_index`, `resolve`, `get_toggle_state`, `click_by_id` NOT importable. |
| `dump_ableton_states.py` | ❌ import fails | Imports the broken module above; browser/view switching helpers unavailable. |
| AbletonMCP | ✅/❌ partial | See §3. |

Ableton window: 432 nodes / 214 automation_ids on default state (sanity dump
`scripts/dumps/ableton_uia_20260807_103304_sanity.json`). Window spans NEGATIVE screen coords
(x −1634..−11) — it lives on a secondary/left monitor in a virtual desktop; clicks still land.

## 2. Sanity-check outcomes (AGENTS.md §1)

1. ✅ UIA dump produces a non-trivial tree (see §1).
2. ✅ AbletonMCP responds to real calls; **load-by-name works but its confirmation field is empty** —
   verify each load via `get_track_info`. Call shapes that differ from AGENTS.md are listed in §3.
3. ✅ Device list pulled from the MCP Browser (full list in §6). Plug-Ins = 0 items.
4. ✅ Six Browser category tabs confirmed as `DataItem` nodes with **empty automation_id**; category
   switching verified working (after clicking "Audio Effects", dump shows
   `Tree: 'Audio Effects List, 47 Items'`).

## 3. AbletonMCP capability map (tested this session)

**Works:**
- `get_browser_tree(category_type=...)` — top-level categories only.
- `get_browser_items_at_path(path)` — full item list per category with loadable URIs
  (e.g. `query:AudioFx#EQ%20Eight`). This is the device-list source of truth.
- `load_instrument_or_effect(track_index, uri)` — loads the device. **Returns empty
  "Devices on track:" field even on success** → verify with `get_track_info`.
- `get_track_info(track_index)` — devices + state. Use to confirm loads.
- `get_arrangement_info()` — tracks/tempo/clips.
- `set_ableton_view(view)` — switches Session/Arranger/Browser/Detail views (verified Session).
- `delete_device(...)` — verified (deletes, reports remaining count).
- `list_external_plugins(...)` — returns none on this machine.

**Broken (do not rely on; log if needed):**
- `get_session_info` — `C++ signature error (None.None(Song) vs TPyHandle<ASong>)`.
- `get_device_parameters` — `No module named 'MCP_Server'`.

Consequence: **no LOM parameter enumeration** → every control in the catalog comes from UIA dumps.

## 4. Survey method (per-device loop, Phases A–D)

Target tracks: **audio effects → Track 3 (audio)**; **instruments / MIDI effects / drum devices →
Track 1 (MIDI)**. Keep exactly one device on the track at a time.

1. MCP `delete_device` on the target track (ignore if empty).
2. MCP `load_instrument_or_effect(uri)`.
3. Verify via MCP `get_track_info` → device listed? If not: tier 2 (UIA Browser search — untried,
   note it), else tier 3 → mark `LOAD_FAILED`, log, next device. **Never stop for a human** (§8).
4. Run `survey_device.py` (spec §8): maximize → walk `TrackView.Device[0]` subtree → probe live
   controls for value patterns → write `scripts/dumps/device_<slug>.json`.
5. Merge into `dumps/control_catalog.json` **incrementally** (after EVERY device) + update
   `dumps/run_coverage.json`.
6. Record value-pattern availability per control (§5.3 of AGENTS.md): RangeValuePattern
   (`get_range_value()`), TogglePattern (`get_toggle_state()`), SelectionItem.

## 5. Render / view-state policy (honest, documented in notes)

Observed: **EQ Eight** loads fully expanded (bands, EqDisplay, globals). **Compressor** loads in a
COMPACT view (~17 nodes: `ViewMode` radios, `Lookahead/Envelope/Makeup/Model`; Threshold/Ratio/
Attack/Release/DryWet NOT exposed). Clicking Compressor's `ExtendViewButton` (a.k.a. "Sidechain
Toggle") and `ViewMode` radios did **not** expand it. Double-clicking the device title collapses
further. No reliable expand mechanism was found for compact devices.

Policy per device:
- Dump the device **as loaded** (no clicks). Record everything present.
- If `TitleBar.ExtendViewButton` is a CheckBox named **"Toggle Expanded View"**, click once and
  re-dump (captures devices that load collapsed but have an expand affordance).
- Compact-rendering devices → record the exposed set, note "compact view only; remaining parameters
  not exposed in default render". Controls that ARE exposed get MAPPED/UNMAPPED normally.
- Subtree empty / 1 node → status `OPAQUE`.

## 6. Device list (from MCP Browser, this session)

Load URIs follow the pattern `query:<Cat>#<URL-encoded name>` with Cat = AudioFx / MidiFx / Synths /
Drums. Re-pull anytime via `get_browser_items_at_path`.

**Audio Effects (47)** — `query:AudioFx#…`
Align Delay, Amp, Audio Effect Rack, Auto Filter, Auto Pan, Auto Shift, Beat Repeat, Cabinet,
Channel EQ, Chorus-Ensemble, Compressor, Corpus, Delay, Drum Buss, Dynamic Tube, Echo, Envelope
Follower, EQ Eight, EQ Three, Erosion, External Audio Effect, Filter Delay, Gate, Glue Compressor,
Grain Delay, Hybrid Reverb, LFO, Limiter, Looper, Multiband Dynamics, Overdrive, Pedal,
Phaser-Flanger, Redux, Resonators, Reverb, Roar, Saturator, Shaper, Shifter, Spectral Resonator,
Spectral Time, Spectrum, Tuner, Utility, Vinyl Distortion, Vocoder.

**MIDI Effects (15)** — `query:MidiFx#…`
Arpeggiator, CC Control, Chord, Envelope MIDI, Expression Control, MIDI Effect Rack, MIDI Monitor,
MPE Control, Note Echo, Note Length, Pitch, Random, Scale, Shaper MIDI, Velocity.

**Instruments (23)** — `query:Synths#…`
Analog, Collision, Drift, Drum Rack, Drum Sampler, DS Clang, DS Clap, DS Cymbal, DS FM, DS HH,
DS Kick, DS Snare, DS Tom, Electric, External Instrument, Impulse, Instrument Rack, Meld, Operator,
Sampler, Simpler, Tension, Wavetable.

**Drums (2 devices surveyed)** — `query:Drums#Drum%20Rack`, `query:Drums#Drum%20Sampler`.
The rest of the Drums category is ~200 preset `.adg` kits that load INTO Drum Rack — skip
individually, note in catalog.

**Plug-Ins: 0 found** (browser empty + `list_external_plugins` none). Record once as an empty
category; nothing to survey (§5.2).

## 7. Phase order (fixed, resumable)

1. **A — Audio Effects** (47) → Track 3. ≈25–30 min
2. **B — MIDI Effects** (15) → Track 1. ≈8 min
3. **C — Instruments** (23) → Track 1. ≈14 min
4. **D — Drums devices** (2) → Track 1. ≈2 min
5. **E — Plug-Ins** (0) — record empty, no loop.
6. **F — §5.4 contexts** ≈20–30 min:
   - Arrangement View (`set_ableton_view("Arranger")` + dump).
   - Browser: each of the 6 category tabs + representative items inside (samples/presets/devices) —
     compare automation_id presence vs top-level tabs (empty).
   - Master track; Return tracks; Group/folded tracks (create temp tracks via MCP, survey, delete —
     additive/reversible; note as survey state, not saved project edits).
   - Clip Detail view (create a temp MIDI clip via MCP, dump, delete).
   - View-menu sweep for any other top-level view.

Total ≈ 70–85 min. Resume from `dumps/run_coverage.json` if cut off.

## 8. Helper script spec — `scripts/survey_device.py` (MUST BE WRITTEN BEFORE SURVEYING)

Read-only, UIA-only, imports ONLY from `dump_ableton_pywinauto.py` (it imports cleanly). Does NOT
call MCP, does NOT touch action code / TASK_REGISTRY / `click_by_id` (AGENTS.md §9). Reimplements
the few helpers lost with the broken modules (DFS walk by automation_id, toggle read, RangeValue
probe). Behavior:
1. `find_ableton_window()` + `ensure_window_ready(maximize=True)`.
2. Walk the live tree; collect every node whose `automation_id` starts with `TrackView.Device[0]`;
   for each, record control_type, name, automation_id, and whether `get_range_value()`,
   `get_toggle_state()`, or selection indicators are available.
3. If `TrackView.Device[0].TitleBar.ExtendViewButton` exists and reads as unchecked with name
   "Toggle Expanded View", click once, wait ~0.6 s, re-walk (per §5 policy).
4. Write `scripts/dumps/device_<slug>.json` with: device name, node count, view-state flag
   (expanded/compact/opaque), and the control list.

The next session can verify it on one known device (EQ Eight — expect ~20 nodes with
`TrackView.Device[0]` prefix + ~20 more children without ids, and the `Filter Mode`/`Filter
Activator`/`EqDisplay` slider pattern) before looping all devices.

## 9. Output schema (AGENTS.md §7)

`dumps/control_catalog.json` (JSON, written incrementally):

```json
{
  "generated": "ISO timestamp",
  "environment": "Ableton Live 12 Suite, WSL2 + Windows Python",
  "coverage_summary": {
    "contexts_attempted": 0,
    "mapped": 0, "unmapped": 0, "opaque": 0, "load_failed": 0,
    "controls_total": 0,
    "run_time_seconds": 0,
    "load_tier_usage": {"mcp": 0, "uia_browser": 0, "failed": 0},
    "unexpected_errors": []
  },
  "contexts": {
    "EQ Eight": {
      "status": "MAPPED",
      "category": "audio_effects",
      "loaded_via": "mcp",
      "view_state": "expanded",
      "controls": [
        {"name": "Freq", "automation_id": "TrackView.Device[0].Freq",
         "control_type": "Slider", "value_pattern_available": true, "notes": ""}
      ]
    }
  }
}
```

Status per context: **MAPPED** (stable ids ready to automate), **UNMAPPED** (seen, no usable id),
**OPAQUE** (no children exposed), **LOAD_FAILED** (never placed; log error/state).

Raw dumps → `scripts/dumps/` (gitignored). Coverage counters → `dumps/run_coverage.json`.

## 10. Known decisions / risks (logged, honest)

- `get_session_info` + `get_device_parameters` broken → catalog parameter data is UIA-only.
- Compressor-style compact devices: expand mechanism unknown → recorded as a documented limitation,
  NOT an error state; status reflects what was exposed.
- WSL `python` is useless for UIA → everything UIA runs under `$PYEXE`; Linux `python` only for
  stdlib JSON merge/parse.
- Temporary tracks/clips for §5.4 are additive and deleted after; survey-side state only, nothing
  saved to the project.
- No automation_id is ever invented — every id in the catalog was observed in a dump
  (AGENTS.md §9). Doubtful entries get `UNVERIFIED` in notes.

## 11. Escalation (AGENTS.md §8)

Never stop to wait on a human. Load failures escalate MCP → UIA Browser search (untried; note
pattern once) → skip+log. Uncovered situations → make the most defensible call, log plainly in
`notes`, continue.
