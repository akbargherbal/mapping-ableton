# Coverage summary — Phase A (Native devices)

Session: 2026-08-07, first survey session ever.
## Totals
- Contexts attempted: **85** (23 instruments, 47 audio effects, 15 MIDI effects)
- Status counts: **MAPPED 85** (every dump contains `automation_id`s),
  UNMAPPED 0, OPAQUE 0, LOAD_FAILED 0
- Dump files: 85 `device_<Name>.json` in `scripts/dumps/`, all non-empty,
  20,346 automation_ids across all dumps

## Method
- Tier-1 (AbletonMCP `load_instrument_or_effect` by URI) used for **85/85**
  loads. Tier-2 (UIA Browser) used 0 times. Tier-3 (LOAD_FAILED) 0 times.
- Independent verification (`get_track_info`) run after every load. The
  documented quirk held: every load reported success with an empty device
  list, but independent verification confirmed the device in all 85 cases.
- Scratch tracks: track 1 (MIDI) for instruments + MIDI effects, track 3
  (audio) for audio effects. Device deleted between loads; no leftover
  devices at end of session.

## Errors / tooling issues
- `dump_ableton_pywinauto.py` console-print crashed with
  `UnicodeEncodeError` (cp1252) on a label containing `\u2044` — the JSON
  write happens *after* the print, so the crash prevented file writes.
  Worked around with the documented `--no-print` flag for every dump; no
  script changes made. Flagging as a known tooling wart (cp1252 console
  encoding), not fixed per §10.

## Catalog status
- `update_catalog.py` still does not exist (known gap in AGENTS.md §8). The
  85 per-context files in `scripts/dumps/` are the actual Phase A survey
  output. Catalog-merging into `dumps/control_catalog.json` is separate
  follow-up work.

# Coverage summary — Phase B (Plug-ins VST/AU)

Session: 2026-08-07.

## Finding
- **Zero third-party plug-ins installed.** The Browser's Plug-Ins category
  exists but renders an empty list (`Tree: "Plug-Ins List, 0 Items"` in
  `ableton_uia_20260807_234456_plugins.json`).
- Triple-confirmed, so this is a genuine finding, not a capture failure:
  1. `AbletonMCP list_external_plugins` (cached AND `refresh_cache=true`)
     → "No external plugins were discovered."
  2. `AbletonMCP get_browser_items_at_path("Plugins")` → empty `items`.
  3. UIA state dump of the Browser's Plug-Ins category → 0 items.

## Status
- Done-condition "one dump per plug-in found" satisfied vacuously (0 found).
- Recorded as **done** in `survey_checklist.md` with the evidence dump path,
  not silently skipped — the empty-category finding is the output.
- No loads attempted, no LOAD_FAILED (nothing to load). Tier usage n/a.
- Tooling: `dump_ableton_states.py --states plugins` also hits the cp1252
  `print_tree` crash; `--no-print` works there too.

# Coverage summary — Phase C (value-read/write pattern sampling)

Session: 2026-08-07.

## Result
- All **85** Phase A contexts probed; every dump now has a
  `value_pattern_available` field recorded (85/85 non-blank).
- **Finding contradicts the "largely absent" expectation:** Ableton's UIA
  sliders DO expose `RangeValuePattern`. All 2,811 Slider controls probed
  (across all 85 dumps, device + transport + mixer) exposed both
  `RangeValuePattern` and `ValuePattern`. `CurrentValue` reads work.
- The "absent" assumption held for non-slider controls: CheckBox, Group,
  Custom, DataItem, RadioButton, Text, MenuBar → no patterns. ComboBox
  and Edit expose only `ValuePattern` (2,234 + 1,368). Button: `ValuePattern`
  on 261/2,172 (no RangeValuePattern). ProgressBar: RangeValuePattern only.

## Notable caveat (the useful exceptions)
- On most *device* sliders, `CurrentMinimum`/`CurrentMaximum` return `nan`
  even though the pattern is present and `CurrentValue` is real — so
  RangeValuePattern confirms read/write capability but min/max range is
  often not exposed. 24 device sliders did return real min/max (the useful
  exceptions, e.g. Drum Buss DryWet 0–1, Beat Repeat FilterFreq 50–1000,
  Wavetable transpose −48–48). Full list in each dump's
  `value_pattern_stats.range_value_examples`.

## Method / tooling
- New read-only survey script `scripts/survey_value_patterns.py` (reuses
  `find_ableton_window`/`ensure_window_ready` from `dump_ableton_pywinauto`).
  Probes `iface_range_value`/`iface_value` (raise `NoPatternInterfaceError`
  when absent) on every control with a real `automation_id`, merges
  `value_pattern_available` + `value_pattern_stats` into each device dump.
- Load ladder: tier-1 (MCP load-by-URI) 85/85, all independently verified
  via `get_track_info`. 0 tier-2, 0 tier-3. Devices deleted after each
  probe; no leftovers.
- Note: pywinauto 0.6.9 exposes min/max as `CurrentMinimum`/`CurrentMaximum`
  on the RangeValue interface, not `Minimum`/`Maximum`.

# Coverage summary — Phase D (Arrangement View)

Session: 2026-08-08.

## Result
- `scripts/dumps/section_Arrangement-View.json` written and verified:
  271 nodes, 140 automation_ids (138 unique), 125 KB. Done-condition met.
- Dumped with window maximized and Ableton in Arranger view
  (`AbletonMCP set_ableton_view "Arranger"`), `dump_ableton_pywinauto.py
  --no-print`. The `Text "Timeline, 1, selected on 1-MIDI, Armed, Track 1 of 4"`
  node confirms the tree is the Arrangement view, not a stale Session dump.

## What's in it
- **Timeline/ruler**: timeline Text label; transport position sliders
  (`Transport.ArrangementPosition.Bars/Beats/Subdivisions`); GlobalRecord and
  ArrangementOverdub checkboxes.
- **Loop Brace**: `ArrangementView.ArrangerLoopBar` with "Arrangement Loop
  Start" (bar 3) and "Arrangement Loop End" (bar 7) groups.
- **Track Headers tree**: `ArrangementView.ArrangerHeaderManager` → Track[0..3],
  ReturnTrack[0..1], MainTrack TitleBar items.
- **Per-track Mixer groups**: `ArrangementView.Track[N].Mixer` with Input/Output
  ComboBoxes, Monitoring radio group, Activator/Solo/Arm, Volume+Pan sliders.
  Return tracks: no Input Type, add Pre/Post Toggle button + send sliders
  (unnamed, no automation_id). Main track: `MainTrack.Mixer` with Cue Out/Main
  Out, Volume/Pan, Preview-Cue Volume (unnamed).
- **Arrangement Controls**: `ArrangementView.SetDeleteLocator`, Prev/Next
  Locator buttons, `AutomationModeButton`, `LockEnvelopes`.
- **Zoom**: `IsWaveformVerticalZoomActiveView` checkbox + `WaveformVerticalZoomFactorView`
  slider; "Optimize Arrangement Height/Width" checkboxes (no automation_id).
- Notable: **Master track is reachable here as `ArrangementView.MainTrack`**
  (absent from Session view) — pre-stages part of Phase F. Device Detail /
  TrackView group also present.

## Method
- Single dump, no load ladder involved (no devices loaded). Window maximized
  before dump (default `ensure_window_ready`).

# Coverage summary — Phase E (Browser panel, six categories)

Session: 2026-08-08.

## Result
- Six dumps, one per category, all verified against disk: file exists,
  non-empty, and its list-marker line names the *correct* category (not a
  stale/duplicate from a neighboring category — the known regression from
  running multiple categories in one `--states` call). All six pass:

  | Category | Latest dump | List marker |
  |---|---|---|
  | Sounds | `ableton_uia_20260808_002115_sounds.json` | `Sounds List, 1001 Items` |
  | Instruments | `ableton_uia_20260808_002123_instruments.json` | `Instruments List, 23 Items` |
  | Drums | `ableton_uia_20260808_002131_drums.json` | `Drums List, 1001 Items` |
  | Audio Effects | `ableton_uia_20260808_002139_audio_effects.json` | `Audio Effects List, 47 Items` |
  | MIDI Effects | `ableton_uia_20260808_002147_midi_effects.json` | `MIDI Effects List, 15 Items` |
  | Plug-Ins | `ableton_uia_20260808_002155_plugins.json` | `Plug-Ins List, 0 Items` |

- Node counts 284–348 per dump; sizes 132–165 KB. Item counts match the
  Phase A device lists exactly (23 instruments / 47 audio / 15 MIDI; 1001
  library items for Sounds/Drums; 0 plug-ins).

## Method
- Ran **one category per invocation** of `dump_ableton_states.py --states
  <category> --no-print` (per AGENTS.md §4 Phase E — the multi-category
  timing bug makes combined invocations after a 1001-item category
  unreliable; `--no-print` works around the cp1252 `print_tree` crash).
- Category selection is by (control_type=DataItem, name) click since these
  sidebar nodes carry empty `automation_id`s; correctness verified after
  the fact from each dump's list-marker line (the script's own
  `goto_browser_category` explicitly logs this as unverified-until-dumped).
- Six categories confirmed empty `automation_id` on the item list (not
  re-litigated per §4); the per-item DataItems inside the lists were not
  individually probed — that's the scope of the sampling requirement.

# Coverage summary — Phase F (Tracks and special views)

Session: 2026-08-08.

## Result — all four done-conditions met, files verified on disk
| Item | Dump file | Verified |
|---|---|---|
| Master track (Arrangement) | `section_Master-track.json` | `ArrangementView.MainTrack.Mixer` subtree (5 automation_ids: Cue Out, Main Out, Volume, Pan + TitleBar) |
| Return track 0 — A-Reverb | `section_Return-track-0-A-Reverb.json` (mixer strip) + `section_Return-track-0-A-Reverb-device.json` (device) | Reverb device `TrackView.Device[0]`, 54 nodes |
| Return track 1 — B-Delay | `section_Return-track-1-B-Delay.json` (mixer strip) + `section_Return-track-1-B-Delay-device.json` (device) | Delay device `TrackView.Device[0]`, 52 nodes |
| Group track | `section_Group-track.json` | Full Session dump, 58 `SessionView.GroupTrack[0].*` ids |
| Clip Detail view | `section_Clip-Detail.json` | `ClipDetailView` subtree, 74 automation_ids |

## Key findings
- **Return tracks carry devices.** Both A-Reverb (Reverb) and B-Delay
  (Delay) have devices loaded; each device dumped from Device Detail after
  selecting the return-track header. Return-track mixer strips are *not*
  the whole story here — the loaded devices are richer.
- **Return-track devices expose almost no automation_ids.** The Reverb and
  Delay subtrees expose only the device root (`TrackView.Device[0]`) and
  title (`TrackView.Device[0].TitleBar.device_title`); every inner
  control (sliders, beat-division radio group, XY controllers) has an
  **empty** automation_id. Contrast with Phase A device dumps on session
  tracks, which expose full parameter ids (`TrackView.Device[0].DryWet`,
  `.Freq`, etc.). So device *controls* are effectively UNMAPPED when the
  device lives on a return track.
- **Master track**: confirmed reachable only under Arrangement View as
  `ArrangementView.MainTrack.Mixer` (Session view exposes no master strip).
  Controls: Cue Out + Main Out ComboBoxes, Volume/Pan sliders; Preview-Cue
  Volume slider present but unnamed.
- **Group track structure**: `SessionView.GroupTrack[0]` is a distinct
  prefixed namespace — group TitleBar (TreeItem), child Track[i].TitleBar +
  Track[i].Slot[j] (8 slots each), and a `GroupTrack[0].Mixer` with
  Stop/OutputType/OutputChannel/PeakLevel/Pan/Activator/Solo/Volume but
  **no Input Type** and **no Arm** (vs. normal tracks which have Input
  Type/Input Channel/Monitoring/Arm). Sends appear as `Mixer.Send[0..1]`
  (A-Reverb, B-Delay).
- **Clip Detail view**: `ClipDetailView` subtree renders only after a clip
  is selected. 74 automation_ids: Header (PowerSwitch), RegionProperties
  (Start/End/Loop position+length in Bars/Beats/Sixteenths, Set buttons),
  Signature, Groove (Commit/GrooveChooser), Key/Scale (InKey, ScaleRoot,
  ScaleName), and NoteTools/TransformationTools/GenerativeTools tab groups.

## Method / survey-prep actions (all logged)
- Created a temporary group: selected Session tracks 0+1 (Ctrl+click both
  TitleBars via pywinauto), pressed Ctrl+G. track_count 4→5. Dumped, then
  restored via right-click header → **"Ungroup Tracks"** context menu item
  (Ctrl+Shift+G keystroke did NOT ungroup reliably — menu item worked).
- Created a temp 4-bar MIDI clip on a MIDI track (MCP) to render Clip
  Detail, selected it, dumped, then deleted it (selected slot + Delete).
  Project restored to pre-Phase-F state: 4 session tracks + 2 returns,
  no clips, no group.
- Window maximized for every dump (default `ensure_window_ready`).
- Temp working dumps (`_f_*.json`) deleted after extraction; only the
  `section_*.json` deliverables remain.

# Coverage summary — Phase G (anything else reachable from the main window)

Session: 2026-08-08.

## Result — View menu opened and fully enumerated; every item either covered by A–F or dumped

The View menu was opened twice (via UIA click on the `View` MenuItem and
via Alt+V), all 42 items enumerated, and submenus (Zoom, Mixer Controls,
Arrangement Track Controls, Scene Tempo and Time Signature) expanded via
hover+Right-arrow. Newly-covered views each have their own section file:

| Item | Dump file | Finding |
|---|---|---|
| Help View (Ctrl+Alt+7) | `section_Help-View.json` | Custom "Lessons Start Page" web-view; only chrome ids (`LessonViewCloseButton`, `Back/Next/Home`) |
| File Manager | `section_File-Manager.json` | Custom "File Manager Start Page" web-view; `LessonView*` chrome + `ManageSet` |
| Undo History (Ctrl+Alt+Z) | `section_Undo-History.json` | Custom panel; only `LessonViewCloseButton` + one label ("New Live Set, current step") — list is custom-rendered |
| Groove Pool (Ctrl+Alt+6) | `section_Groove-Pool.json` | **OPAQUE** — panel renders as empty Tree, 0 ids; see crash note below |
| Tuning System | `section_Tuning-System.json` | Always-visible bottom bar; `TuningPool.DropAreaText` drop zone |
| Info View (`?`) | `section_Info-View.json` | **OPAQUE** — toggled on + control hovered, still nothing in UIA (custom canvas text) |

## Items already covered by A–F (not re-dumped)
Toggle Arrangement/Session View (Tab) → D/F; Clip View, Device View,
Toggle Clip/Device View, Expand/Hide Clip View, Arrange Clip View Panels
(x3), MIDI Note Editor, Envelopes Editor, Expression Editor → F (Clip
Detail / device chain); Browser, Full-Height Browser, Search in Browser,
Show Similar Files → E; Mixer, Mixer Controls, Scene Tempo and Time
Signature, Show Grouped Tracks, Show Selected Grouped Track → F; Overview,
Arrangement Track Controls, Automation Mode, Zoom to Time Selection,
Zoom Back from Time Selection, Fold to Notes, Fold to Scale, Show
Chains, Hide Chains, Zoom (submenu) → D/F.

## Items with nothing to survey in this project
- **Second Window** (Ctrl+Shift+W): no second window opened (no saved
  set to open in a second window — requires a saved project).
- **Plug-In Windows** (Ctrl+Alt+P): no-op; project has 0 plug-ins (Phase B).
- **Video Window** (Ctrl+Alt+V): no-op; no video clips in project.
- **Max for Live Window** (Ctrl+Shift+Alt+M): no-op; no M4L device loaded.
- **Full Screen** (F11): window display mode, not a surveyable view.

## CRASH INVESTIGATION (important)
Ableton Live crashed **twice** during this session — not because of any
close command. Both crashes are recorded in Windows Event Log
(Application log):

```
8/8 00:38:25 App Error  Ableton Live 12 Suite.exe  ucrtbase.dll 0xc0000409 (BEX64, stack buffer overrun)
8/8 00:39:41 App Error  Ableton Live 12 Suite.exe  ucrtbase.dll 0xc0000409 (BEX64)
```

- Both crashes carry the same fault bucket (type 5 / BEX64) and faulting
  module `ucrtbase.dll`, exception `0xc0000409` (`__fastfail`).
- **Both occurred immediately after opening the Groove Pool panel
  (Ctrl+Alt+6)** — the only correlated action in the session. View-menu
  navigation, submenu expansion, and every other view toggle ran fine.
- The dumps themselves were captured successfully *before* each crash
  (panel confirmed open), so the Groove Pool finding is genuine OPAQUE,
  not a capture failure. Ableton even generated its own crash-report
  banner ("Ableton Crash Report 2026-08-08 004023") shown in the Help
  View — corroborating evidence.
- **Action taken: do not re-open Groove Pool.** Recorded as OPAQUE per
  §7. This is an Ableton bug (BEX64 in ucrtbase on Groove Pool open),
  not a survey-tooling issue.

## Method / survey-prep actions (all logged)
- View menu opened via UIA click on the `View` MenuItem and via Alt+V;
  submenus expanded by hovering the parent item and pressing Right-arrow.
- Each uncovered view toggled via its View-menu shortcut, dumped with the
  real `dump_ableton_pywinauto.py` (automation_id extraction), then the
  relevant subtree extracted to `section_*.json`.
- Window maximized for every dump; Ableton verified alive after each
  toggle (post-crash, sanity dump re-run: 429 nodes, 216 automation_ids;
  session still 4 tracks + 2 returns + Master).
- Temp `_g_*.json` dumps deleted; only `section_*.json` deliverables
  remain.

## Remaining follow-up (not a phase)
- ~~`control_catalog.json` merge (`update_catalog.py`)~~ — **DONE 2026-08-08.** See below.

# Coverage summary — Catalog merge (§8 follow-up)

Session: 2026-08-08.

## Result
`scripts/update_catalog.py` written and run; output
`scripts/dumps/control_catalog.json` (6.6 MB):

| Context type | Count | Status |
|---|---|---|
| device:* (Phase A/B) | 85 | MAPPED |
| section:* (Phase D/F/G) | 12 | MAPPED |
| section:* (Phase G OPAQUE) | 2 | OPAQUE (Groove-Pool, Info-View) |
| browser:* (Phase E) | 6 | UNMAPPED |
| **Total** | **105** | 97 MAPPED / 6 UNMAPPED / 2 OPAQUE |

- **19,014 mapped controls** carry a real `automation_id` (each device
  entry also lists its unmapped controls, capped at 2000 per context for
  the 1001-item browser lists).
- All 85 device files + 14 section files + 6 browser categories on disk
  reconcile 1:1 with catalog contexts (verified — zero missing).
- `value_pattern_available` (Phase C) is carried through onto every
  device context.

## Catalog schema notes
- One `contexts` object keyed `device:<Name>`, `section:<Name>`,
  `browser:<category>`; each entry has `status`, `source`,
  `mapped_controls[]`, `unmapped_controls[]`, `automation_id_count`.
- **Browser categories are marked UNMAPPED** on purpose: the survey
  target (the item list) carries empty automation_ids; the mapped
  controls present in those dumps are window chrome (MenuBar, Transport)
  also covered by other contexts — noted in the entry.
- Only automation_ids actually observed in the dumps are recorded — no
  inferred identifiers (AGENTS.md §10). Script is read-only over dumps;
  it never talks to Ableton.
- Top-level `summary` gives context_count / by_status /
  total_mapped_controls, and any per-file read errors are surfaced under
  `summary.errors` (none in this run).

## Method
- Wrote `update_catalog.py` (glob device/section/browser dumps, flatten
  each UIA tree, de-dup mapped by automation_id, carry OPAQUE status +
  notes from the section files themselves).
- Run from `scripts/` so the output lands in `scripts/dumps/` per §0.







