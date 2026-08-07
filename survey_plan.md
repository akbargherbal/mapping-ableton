# Survey Plan — Ableton Live Control Catalog

Ground truth for *how* to run the control survey. Reconciles what
`AGENTS.md` assumed with what was actually observed during the
fresh-start sanity checks (2026-08-07). Where this document contradicts
`AGENTS.md`, **this document wins** — it reflects observed reality.

## 1. Task

Build one master control catalog (`dumps/control_catalog.json`): every
control findable in Ableton Live, tagged with whatever identifier lets
code interact with it reliably (or a clear note that no reliable
identifier exists). Read-only survey of a running Live 12 Suite with an
"Untitled" project open. Run once, completely, incrementally.

## 2. Environment reality (observed, 2026-08-07)

`AGENTS.md` assumes plain Windows. The real environment is **WSL2**:

- Host: Windows (DESKTOP-IVAHJ7J), distro **Ubuntu-22.04**, kernel
  `6.18.33.2-microsoft-standard-WSL2`.
- Ableton **Live 12 Suite** is running on the Windows host, project
  **"Untitled"** open, unsaved. Session: 4 tracks, 2 return tracks,
  Master. Track 1 is `1-MIDI` (MIDI). Track 1 currently holds an
  `EQ Eight` (`Eq8`) left over from sanity checks — survey or remove it
  when the run starts.
- Repo lives **only on the WSL filesystem** at
  `/home/akbar/Jupyter_Notebooks/OpenCode/mapping-ableton/`. There is no
  Windows-side copy. Windows tooling reaches it over the UNC path
  `\\wsl.localhost\Ubuntu-22.04\home\akbar\Jupyter_Notebooks\OpenCode\mapping-ableton\...`.

### Interpreter reality (contradicts AGENTS.md §0)

- `python` = WSL `/usr/bin/python` 3.12.13. **Has a Linux pywinauto
  stub — `from pywinauto import Desktop` fails. Cannot see the Windows
  desktop. NOT usable for the survey scripts.**
- `python3` = WSL 3.10.12. No pywinauto at all.
- `python.exe` = Windows Python 3.12.2
  (`C:\Users\DELL\AppData\Local\Programs\Python\Python312\python.exe`),
  reachable via WSL interop, **has full pywinauto and can drive UIA on
  the Windows desktop. This is the ONLY usable interpreter.**

**Correction to AGENTS.md:** every script invocation must be
`python.exe "<UNC-absolute-path-to-script>"`, e.g.:

```
python.exe "\\wsl.localhost\Ubuntu-22.04\home\akbar\Jupyter_Notebooks\OpenCode\mapping-ableton\scripts\dump_ableton_pywinauto.py" --diagnose
```

Scripts import each other via `Path(__file__).resolve().parent`, so
`sys.path` is correct regardless of the process working directory; no
`cd` gymnastics needed.

## 3. Tooling capability map

| Tool | Status (observed) | Notes |
|---|---|---|
| `dump_ableton_pywinauto.py` | **WORKS** | Maximized dump of current state = 392 nodes, 199 unique `automation_id`s. Pass `--json`/`--no-print` with an absolute UNC path to control output. |
| `dump_ableton_states.py` | **BROKEN — do not use** | Fails at import: `automate_ableton_task.py` line 118 does `from keyboard_shortcuts import ...` and `keyboard_shortcuts.py` does **not exist** in the repo. Per AGENTS.md §9 we do NOT patch task/action code. Use the two replacements below. |
| `browser_switch.py "<Category>"` | **WORKS** | Click a Browser sidebar category by exact `(DataItem, name)`. Verified this run: `Sounds` → subsequent dump shows `Tree: "Sounds List, 1001 Items"`. Replaces the browser half of `dump_ableton_states.py`. |
| MCP `set_ableton_view()` | **WORKS** | Switched `Arranger` and `Session` successfully (LOM-level, no Tab key). Replaces the view half of `dump_ableton_states.py`. |
| `survey_device.py "<Name>"` | **WORKS** | One loaded device → JSON survey. Validated on EQ Eight: `view_state=expanded`, 81 nodes, 38 with `automation_id`. Writes `scripts/dumps/device_<slug>.json` (gitignored). |
| `survey_section.py "<Context>"` | **WORKS** (untested this run) | For §5.4 non-device contexts. Same walk/probe machinery as `survey_device.py`. Select via `--aid <prefix>` or `--name <name> [--instance N]`. |
| `update_catalog.py <device_json>` | **WORKS** | Merges one survey result into `dumps/control_catalog.json` (repo root), recomputes coverage summary. Pure stdlib; run under either interpreter. Re-running the same slug overwrites that context. |
| `grep_dump.py` | **WORKS** (pure stdlib) | Search a saved dump JSON for substring across name/automation_id/class_name. |
| `automate_ableton_task.py` | **DO NOT USE** | Task/action code. Unusable anyway (missing `keyboard_shortcuts`). §9 forbids touching it. |
| **AbletonMCP** | **WORKS** | Confirmed: `get_session_info`, `get_browser_tree`, `get_browser_items_at_path`, `set_ableton_view`, `load_instrument_or_effect`, `list_external_plugins`. |

### AbletonMCP capability map

- **Load device:** `load_instrument_or_effect(track_index, uri)` — URI
  is the browser-tree form, e.g. `query:AudioFx#EQ%20Eight`. **Returns a
  success message but an EMPTY `Devices on track:` list — do NOT trust
  the load confirmation.** Always verify the device landed with
  `get_track_info(track_index)` (check `devices[].name` /
  `.class_name`). EQ Eight verified this way: `class_name = "Eq8"`.
- **Browser list:** `get_browser_tree()` top-level = Instruments, Sounds,
  Drums, Audio Effects, MIDI Effects, Clips, Current_project,
  Max_for_live, Packs, Plugins, Samples, User_library.
  `get_browser_items_at_path()` accepts those keys (`audio_effects`,
  `instruments`, `midi_effects`, `drums`, `plugins`, `sounds`, ...) and
  returns items with `uri`, `is_device`, `is_loadable`.
- **External plugins:** `list_external_plugins()` → **none discovered**;
  `get_browser_items_at_path("plugins")` → empty. Plug-Ins category has
  nothing to survey.
- **View switch:** `set_ableton_view()` supports Arranger, Session,
  Detail, Detail/Clip, Detail/DeviceChain, Browser. No "Overview".
- No native "load by device name" tool — load always needs the URI from
  the browser tree. No create-audio-track tool (only `create_midi_track`).

## 4. Device list (source of truth: AbletonMCP browser, pulled this run)

Browser = source of truth per AGENTS.md §5.1. Counts below are real.

- **Audio Effects** (`query:AudioFx`, 47 devices): Align Delay, Amp,
  Audio Effect Rack, Auto Filter, Auto Pan, Auto Shift, Beat Repeat,
  Cabinet, Channel EQ, Chorus-Ensemble, Compressor, Corpus, Delay, Drum
  Buss, Dynamic Tube, Echo, Envelope Follower, EQ Eight, EQ Three,
  Erosion, External Audio Effect, Filter Delay, Gate, Glue Compressor,
  Grain Delay, Hybrid Reverb, LFO, Limiter, Looper, Multiband Dynamics,
  Overdrive, Pedal, Phaser-Flanger, Redux, Resonators, Reverb, Roar,
  Saturator, Shaper, Shifter, Spectral Resonator, Spectral Time,
  Spectrum, Tuner, Utility, Vinyl Distortion, Vocoder.
- **Instruments** (`query:Synths`, 23 devices): Analog, Collision, Drift,
  Drum Rack, Drum Sampler, DS Clang, DS Clap, DS Cymbal, DS FM, DS HH,
  DS Kick, DS Snare, DS Tom, Electric, External Instrument, Impulse,
  Instrument Rack, Meld, Operator, Sampler, Simpler, Tension, Wavetable.
- **MIDI Effects** (`query:MidiFx`, 15 devices): Arpeggiator, CC Control,
  Chord, Envelope MIDI, Expression Control, MIDI Effect Rack, MIDI
  Monitor, MPE Control, Note Echo, Note Length, Pitch, Random, Scale,
  Shaper MIDI, Velocity.
- **Drums** (`query:Drums`): one device — **Drum Rack**. The other ~150
  entries are preset kits (`.adg`, `is_device: false`) — **out of scope
  as devices**; noted, not surveyed individually.
- **Plug-Ins** (`query:Plugins`): **empty**. `list_external_plugins`:
  none. One checklist item: confirm empty, log `OPAQUE`/none.
- Rack devices (Audio Effect Rack, Instrument Rack, MIDI Effect Rack)
  are already inside the category lists above — survey them where they
  appear. Their chain/parameter structure is a special case (nested
  chains) — record plainly if opaque or if chain internals render.

## 5. Method — per-device loop

Fixed order: Phase A (Audio Effects) → B (Instruments) → C (MIDI Effects)
→ D (Drums) → E (Plug-Ins) → F (everything else). See
`survey_checklist.md` for the running record.

Per device:
1. **Load (escalation ladder, tier 1 first):**
   - Tier 1 (default): MCP `load_instrument_or_effect(track_index, uri)`
     with the URI from §4. Verify with `get_track_info` — the load
     response's device list is unreliable (observed empty on success).
   - Tier 2 (only if tier 1 fails for a specific device): UIA Browser
     search-and-load — switch to Browser via MCP, `browser_switch.py` is
     only for category tabs, so tier 2 means clicking the device entry in
     the Browser item list and loading it onto the selected track. **This
     interaction is untried.** If it fails consistently, drop to tier 3
     for the rest and note the pattern once.
   - Tier 3: `LOAD_FAILED` — record the observed error/state in the
     catalog and move on immediately. Valid, honest outcome.
2. **Survey:** `survey_device.py "<Device Name>"` → writes
   `scripts/dumps/device_<slug>.json`. This walks the device subtree,
   records control_type/name/automation_id/bounding_rect per node, and
   probes UIA value/toggle/selection patterns. It performs exactly one
   interaction: expanding the device if the title-bar "Toggle Expanded
   View" checkbox is present and unchecked (§5 policy in AGENTS.md). It
   reports `view_state` = `opaque` | `compact` | `expanded`.
3. **Record:** `update_catalog.py scripts/dumps/device_<slug>.json
   --category <audio_effects|instruments|midi_effects|drums> --tier mcp
   [--class-name <class>]`. Merges into `dumps/control_catalog.json` and
   recomputes the coverage summary.
4. **Cleanup:** remove the device from the track (MCP `delete_device`)
   before loading the next, so the Device Detail panel renders exactly
   one device (`TrackView.Device[0]`) per survey and the tree stays
   predictable. (EQ Eight already on track 1 — survey it first or remove
   it.)

Track strategy: use track 1 (`1-MIDI`) for instruments and MIDI effects,
and for audio effects (Live 12 allows audio effects on a MIDI track's
device chain). If a specific load is rejected on a MIDI track, fall back
to an existing audio track if the session has one; if none exists and
MCP can't create one, log `LOAD_FAILED` with the reason.

### Virtualization (AGENTS.md §6) — non-negotiable

Window must be maximized/focused before every dump. `survey_device.py`
and `survey_section.py` call `ensure_window_ready(maximize=True)`
themselves. Never pass `--no-maximize` without a logged reason. If a
dump is suspiciously sparse, re-check window state before recording
`OPAQUE`.

## 6. Catalog schema (what the run actually produces)

`dumps/control_catalog.json`, written incrementally by `update_catalog.py`:

```
{
  "generated": <ISO timestamp>,
  "environment": "Ableton Live 12 Suite, WSL2 + Windows Python",
  "coverage_summary": {
    "contexts_attempted", "mapped", "unmapped", "opaque", "load_failed",
    "controls_total", "run_time_seconds", "load_tier_usage": {"mcp","uia_browser","failed"},
    "unexpected_errors": []
  },
  "contexts": {
    "<Device/Context Key>": {
      "status": "MAPPED|UNMAPPED|OPAQUE|LOAD_FAILED",
      "category", "loaded_via", "device_class", "view_state",
      "node_count", "controls_with_automation_id",
      "title_matched", "expand_clicked", "notes",
      "controls": [ { "name", "automation_id", "control_type",
                      "value_pattern_available", "patterns", "bounding_rect" } ]
    }
  }
}
```

Status derivation (`update_catalog.py::status_for`): `LOAD_FAILED` if the
survey returned an error; `OPAQUE` if `view_state == "opaque"` or no
child controls; `UNMAPPED` if controls render but none carry a usable
`automation_id` (TitleBar scaffolds and the device group itself are
excluded); else `MAPPED`.

**Value-pattern caveat:** `value_pattern_available` is currently
`bool(patterns)` — "any UIA pattern live (range/toggle/selection)", not
specifically RangeValue. Early data (EQ Eight): band sliders
`TrackView.Device[0].Band{N}.{Freq,Gain,Q,Selector}` carry real
automation_ids but expose **no** value pattern in the probe; checkboxes
(`Audition Mode`, `Analyze`) expose TogglePattern. So per-device §5.3
notes must state explicitly whether **RangeValue** is available, because
"clickable" and "readable" are different guarantees. Survey each
device's `patterns` and record the RangeValue-specific finding in
`notes`.

## 7. Write incrementally / coverage

- Write the catalog after **each** device/context (§5 step 3). A run cut
  off partway leaves a valid partial file.
- Track running counts: attempted / loaded / controls found. The
  `coverage_summary` block is the machine-readable tally; recompute from
  contexts (already done by `update_catalog.py`).
- Final coverage summary alongside the catalog: totals, per-status
  counts, total run time, unexpected errors, tier usage per §4 ladder.
  Numbers, not narrative.

## 8. Everything-else contexts (Phase F, §5.4)

Same dump+record method via `survey_section.py` (write to
`scripts/dumps/section_<slug>.json`, then `update_catalog.py`):

- **Session View** controls (transport, tempo, track mixer strips) — the
  automation_id scheme (`SessionView.Track[N].Mixer.*`, `Transport.*`)
  is already characterized in `automate_ableton_task.py`'s docstring;
  survey it as a section for the catalog.
- **Arrangement View**: timeline, loop brace, etc. Switch via MCP
  `set_ableton_view("Arranger")`, then `survey_section.py`.
- **Browser panel**: six top-level category tabs carry empty
  `automation_id`s — matched by `(control_type, name)` (confirmed
  working this run for `Sounds`). Check items **inside** a category
  (presets/devices): do they behave the same or differently? Sample a
  representative few per category.
- **Master track**, **Return tracks** (2 in the session), **Group /
  folded tracks** (note structural differences vs a normal mixer strip —
  no group tracks exist yet; create one to survey, or note absent).
- **Clip Detail view**: MCP `set_ableton_view("Detail/Clip")`; survey
  once a clip exists (create one via MCP if needed).
- **Other top-level views**: check the View menu for anything else
  (e.g. Overview in Live 12) reachable without leaving the main window;
  survey any that render.

## 9. Risks / known gaps

- `dump_ableton_states.py` broken (missing `keyboard_shortcuts.py`) —
  mitigated by MCP view switching + `browser_switch.py`. Logged as an
  environment gap, not to be fixed (§9).
- MCP load returns no device confirmation — always verify via
  `get_track_info`.
- Value-read pattern (RangeValue) appears device-dependent and often
  absent — §5.3 finding per device; don't assume readability.
- Browser items inside a category: behaviour (empty IDs vs stable IDs)
  not yet characterized — Phase F samples it.
- UI virtualization: window state can silently change the tree —
  always maximize, re-check sparse dumps before recording OPAQUE.

## 10. What NOT to do

Same as AGENTS.md §9: no new task functions, no `TASK_REGISTRY` changes,
no touching `click_by_id()` or any action code in
`automate_ableton_task.py`; never invent an `automation_id` not seen in a
dump (mark `UNVERIFIED` in notes); don't skip devices.

## 11. Escalation discipline

Same as AGENTS.md §8: make the most defensible call, log it plainly in
`notes`, keep moving. A corrected plan (this file) is a normal outcome,
not an error.
