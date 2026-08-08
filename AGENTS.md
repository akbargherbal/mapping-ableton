# AGENTS.md

Operating instructions for the agent running the **control survey** task.

> **Design change from prior runs:** this survey used to be one long
> autonomous session that tried to cover everything in one go. That
> produced silent, unverifiable gaps (an entire Browser category with
> zero dump files, no record of why). This version splits the survey
> into **phases**, one phase per session, with a human picking the phase
> at the start and an objective, file-based check for "is this phase
> actually done" — not the agent's own judgment call.

## 0. Environment

Two configurations have been observed in practice. **Don't assume
either — the first sanity check (below) determines which one you're
in**, unless you already know from a resume.

- **Configuration A — plain Windows.** Ableton Live installed and
  running, repo on the Windows filesystem, `python` command works
  directly.
- **Configuration B — WSL2 with the repo on the Linux filesystem.**
  Ableton runs on the Windows host; the repo lives only under the WSL
  filesystem. In this configuration:
  - WSL `python`/`python3` has only a pywinauto *stub* — `from
    pywinauto import Desktop` fails, it cannot see the Windows desktop,
    and it is **not usable** for any survey script.
  - The usable interpreter is **Windows Python invoked from WSL via
    interop**, called as `python.exe`. **Use a plain relative path from
    inside the repo directory** — `python.exe scripts/script_name.py
    --args`. WSL interop resolves this automatically; no manual UNC
    path (`\\wsl.localhost\...`) is needed. Confirmed working directly
    against the real app. Only reach for a manual UNC path
    (`wslpath -w <file>` to generate it) if the plain relative form
    ever fails to resolve — treat that as the fallback, not the
    default.
  - Scripts resolve their own imports via
    `Path(__file__).resolve().parent`, so working directory doesn't
    matter for imports — but you still need to be in (or path
    relative to) the repo directory for the `python.exe script.py`
    form above to find the file.

Whichever configuration you're in:

- **Run every dump command from inside `scripts/`, not the repo root.**
  `dump_ableton_pywinauto.py` and `dump_ableton_states.py` both default
  to writing into a `dumps/` folder *relative to wherever the command
  is executed*, not relative to the script's own location. Since every
  "done" check in this document (§3, §4, all of Phase A–G) expects
  files under `scripts/dumps/`, running from the repo root without
  overriding `--out-dir` will silently write to the wrong place (a
  stray `dumps/` at the repo root) and the checklist will never find
  them. Confirm your current directory before any dump command:
  `cd scripts` first, or pass `--out-dir scripts/dumps` explicitly if
  invoking from elsewhere.

- Open, close, and switch devices/views/tracks freely. **"Read-only"
  means two specific things, not "zero interaction":**
  1. Never save or export the project.
  2. Never touch action code (`click_by_id()`, `TASK_REGISTRY`, or
     anything under §9).
  It does **not** forbid ordinary survey-prep UI actions — selecting
  tracks, pressing a key combo to group them, clicking a clip slot to
  make Clip Detail render. Those are in scope; log what you did in the
  catalog's `notes` field for that context.
- Work from inside `scripts/`, or with it on the path — these scripts
  import from each other.
- **AbletonMCP is connected and enabled.** You have MCP tool access to
  Ableton's Live Object Model directly — this is your primary method
  for loading a device onto a track (§5). Do not trust its responses
  blindly — see §5.

## 1. Every session starts the same way — pick one phase, then stop expanding scope

This is the core rule of this document. Read it before anything else:

1. **Run the environment sanity checks** (§2) — every session, not just
   the first. They're cheap (a few seconds) and catch "the machine
   changed since last time" before it wastes the rest of the session.
2. **Read `survey_checklist.md`** (create it from the template in §3 if
   it doesn't exist yet — that itself means this is the first session
   ever). For each phase, compute its real status by checking
   `scripts/dumps/` against that phase's expected file list (§4) —
   **don't trust a checkbox in the file itself; trust what's actually
   on disk.** A phase marked done with a missing expected file is not
   done — correct the checklist to match reality before proceeding.
3. **Show the human a one-line status per phase** (done / partial /
   not started, with counts — e.g. "Phase E (Browser): 2/6 categories
   have dump files") **and ask which phase to work on this session.**
   Do not guess, do not pick "the next incomplete one" automatically,
   do not start working before getting an answer.
4. **Work only that phase, to completion, this session.** If you
   finish it with time/turns to spare, **stop and report completion —
   do not roll into the next phase uninvited.** A session's job is one
   phase, done verifiably, not "as much as possible."
5. If something inside the phase blocks you (a device won't load, a
   control is genuinely ambiguous), handle it per the escalation rules
   in §9 — those are about *individual controls*, not about *which
   phase to run*. Never expand scope to "just quickly also cover X" to
   fill time.

## 2. Sanity checks (every session)

0. **Determine environment and interpreter first** (§0) — does plain
   `python` see pywinauto's `Desktop`? Is the repo path WSL or native
   Windows? Record the exact invocation form you'll use this session.
1. **Dump the current window once** (`dump_ableton_pywinauto.py`,
   maximized) and confirm you get a non-trivial tree back.
2. **Confirm AbletonMCP actually responds** to a real call (a
   read-only query, or a trivial load-by-name on one device) — "it's
   connected" isn't the same as "it does what §5 assumes." Known
   quirk: `load_instrument_or_effect` can report success with an
   *empty* device list — always verify independently (§5).
3. **Pull the actual device/category list** from the Browser (or
   AbletonMCP if it exposes one) and reconcile it against §4's phase
   tables below — if the real list differs, update this file's tables,
   don't proceed on a stale list.

## 3. `survey_checklist.md` — the single source of truth for progress

One row per phase. Regenerate the per-phase item counts from §4 rather
than hand-typing them.

```markdown
| Phase | Item | Expected dump file (scripts/dumps/) | Status | Last checked |
|---|---|---|---|---|
| A | EQ Eight | device_EQ-Eight.json | done | 2026-08-07 |
| A | Compressor | device_Compressor.json | not started | |
| E | Browser: Sounds | ableton_uia_*_sounds.json (latest) | not started | |
| E | Browser: Instruments | ableton_uia_*_instruments.json (latest) | not started | |
| ... | ... | ... | ... | ... |
```

Rules:
- A row is **done** only if its expected file exists AND is non-empty
  (`node_count` / `controls` array not empty) AND, for OPAQUE results,
  the notes field explains *why* (custom-rendered UI confirmed, vs.
  "window wasn't visible when this ran" — those are different findings
  and must be recorded differently; see §7).
- Never mark a row done from memory. Check the file.
- At the end of a session, update every row you touched — this file is
  what the *next* session (possibly a different one) reads at step §1.2.

## 4. The phases

Work through phases in this order across sessions (not within one
session — see §1). Each phase's "done" condition is a concrete file
check, not a judgment call.

### Phase A — Native devices
EQ Eight, Compressor, Glue Compressor, Limiter, Multiband Dynamics,
Saturator, Utility, Auto Filter, and every other device in Ableton's
own Browser categories (Audio Effects, MIDI Effects, Instruments,
Drums) — pull the full list from the Browser/AbletonMCP in §2.3, don't
assume this list is exhaustive.
**Done when:** one `device_<Name>.json` file per device on the pulled
list exists in `scripts/dumps/`, each non-empty or explicitly marked
OPAQUE with a reason.

### Phase B — Plug-ins (VST/AU)
Browser's "Plug-Ins" category, same method as Phase A. Opaque/no-children
results are a likely, not certain, outcome for third-party UIs.
**Done when:** one dump file per plug-in found in that category exists.

### Phase C — Value-read/write pattern sampling
For a sample of controls with a real `automation_id` (start with
sliders/knobs) across whatever Phase A/B already surveyed, check for a
`RangeValuePattern` or similar. Expect it to be largely absent on
sliders/knobs — that's a normal finding, not a gap; record the
exceptions clearly, since those are the useful ones.
**Done when:** every MAPPED context from Phase A/B has a
`value_pattern_available` field recorded (true or false), not blank.

### Phase D — Arrangement View
Full tree: timeline, loop brace, and whatever else renders.
**Done when:** `section_Arrangement-View.json` exists and is non-empty.

### Phase E — Browser panel (six categories, individually)
The six top-level tabs (Sounds, Instruments, Drums, Audio Effects,
MIDI Effects, Plug-Ins) are confirmed to carry empty `automation_id`s —
don't re-litigate that. What's required is sampling actual items
**inside** each category, one dump per category, not a single combined
"Browser Panel" dump.

**Tool:** `dump_ableton_states.py --states <category>`. Run **one
category per invocation** — do not use `--states all` for this phase.
Confirmed by direct testing: running multiple browser categories in one
`--states` call after a large category (Sounds/Drums, 1001 items each)
produces duplicate/stale dumps for every category after it — the
`goto_browser_category()` click apparently lands before the previous
category's 1001-item list finishes re-rendering, and the fixed
`time.sleep(0.3)` isn't enough to cover that. Single-category
invocations, and pairs that don't include a 1001-item category
mid-sequence, were confirmed to work correctly. Per §10, don't patch
the script for this — just invoke it one category at a time.

**File naming — do NOT expect fixed filenames.** Unlike Phase A/B
(which use `dump_ableton_pywinauto.py --json <fixed-path>`),
`dump_ableton_states.py` always writes through `default_json_path()`
with no override, producing a timestamped name:
`ableton_uia_<YYYYMMDD_HHMMSS>_<category>.json`. Never look for a file
literally named `browser_sounds.json` — it will never exist. To check
a category's status, glob `scripts/dumps/ableton_uia_*_<category>.json`
and take the most recent match by timestamp.

**Done when:** for each of the six categories (`sounds`, `instruments`,
`drums`, `audio_effects`, `midi_effects`, `plugins`), the most recent
matching `ableton_uia_*_<category>.json` file exists, is non-empty, AND
its printed tree contains a `Tree: "<Category Name> List, N Items"`
line whose name matches that category (not a leftover/stale name from
a different category — this is the actual regression seen when the
timing bug above is present). Five out of six, or six files that exist
but with wrong/duplicate content, is **not** done.

### Phase F — Tracks and special views
- **Master track** — confirmed absent from Session-view UIA tree in a
  prior run; check under **Arrangement View** instead
  (`ArrangementView.MainTrack`).
- **Return tracks** — survey *every* return track present in the
  project (query the actual count via AbletonMCP, don't assume one).
  If a return track has a device loaded, dump the device too, not just
  the mixer strip — an empty return-track mixer strip is a much
  thinner result than a loaded one and should be logged as such.
- **Group/folded tracks** — note structural differences vs. a normal
  track's mixer strip. Creating a group requires selecting two tracks
  and pressing Ctrl+G — in-scope survey-prep action, log it.
- **Clip Detail view** — only renders once a clip is selected; clicking
  a clip slot to make it render is in-scope, log it.
**Done when:** dump files exist for master track, every return track
found, at least one group-track example, and Clip Detail.

### Phase G — Anything else reachable from the main window
Check the View menu explicitly for views not covered by A–F (e.g.
Groove Pool). Don't assume Session/Arrangement/Browser/Clip Detail is
the full set of top-level views.
**Done when:** the View menu has been opened and every item in it is
either covered by an earlier phase or has its own dump file here.

## 5. Loading a device onto a track — escalation ladder

1. **AbletonMCP load-by-name** — default path for every device.
2. **UIA Browser search-and-load**, if MCP fails for a specific device.
   If it fails consistently across several devices, don't keep
   retrying per-device — drop to tier 3 for the rest and note the
   pattern once.
3. **Skip and log `LOAD_FAILED`**, with the observed error/state, and
   move to the next device. This is a valid, honest outcome.

**Mandatory verification, every tier:** after a load call reports
success, independently confirm the device is actually on the track
(`get_track_info` or equivalent) before dumping/recording it.
**Known quirk:** MCP load can report success with an *empty* device
list — always verify.

**Session hygiene:**
- Loading an instrument renames the track (e.g. "1-MIDI" → "1-Analog").
  Track it by position/index, not name.
- Keep a single scratch track; delete the loaded device between
  devices to keep `TrackView.Device[0]` predictable.

## 6. Window virtualization — non-negotiable

Ableton's Session View is UI-virtualized: controls not actually
rendered on screen (minimized, too small, unfocused window, or a panel
that closed during a view transition) don't exist as UIA elements at
all — not hidden, genuinely absent, no error raised. Confirmed in
practice: ~60 vs ~201 automation_ids on the same project depending
only on window state. **Always dump with the window maximized.** If a
dump looks suspiciously sparse (e.g. `node_count: 0`) for something you
expect to have content, **re-check window/panel state and re-dump
before recording it as OPAQUE** — a `node_count: 0` result is a strong
signal to re-check, not a finding to accept on the first try.

## 7. Distinguish two different kinds of "empty"

This matters enough to call out on its own, because it was a source of
silent data loss in a prior run:

- **Genuinely OPAQUE**: the device/panel is confirmed rendered and
  visible, and the UIA tree still returns nothing — a real
  custom-rendered-UI finding. Record as `OPAQUE` with a note confirming
  the panel was visibly open when dumped.
- **Capture failure**: the panel wasn't actually open/rendered at
  dump time (transition state, window not maximized, focus moved).
  This is **not** a finding about Ableton's UI — it's a failed dump
  that needs to be redone. Never record this as `OPAQUE`. Re-dump with
  the panel confirmed visibly open first.

## 8. Output

One file: `dumps/control_catalog.json`, built by merging the
per-context files in `scripts/dumps/` via `update_catalog.py`. JSON,
not markdown — meant to be read/diffed by future automation code.

> **Known gap:** `update_catalog.py` is referenced here but does not
> currently exist anywhere in this repo (confirmed by direct search).
> Don't assume it exists or try to call it. Until it's written, treat
> the per-context files in `scripts/dumps/` as the actual survey
> output, and flag catalog-merging as separate follow-up work — not
> something to invent or improvise mid-survey (see §10, don't add new
> tooling here).

Group by context. Per-context status:
- **MAPPED** — real, stable identifier, ready for click-and-verify.
- **UNMAPPED** — control seen but no usable identifier — needs a
  name/coordinate fallback later, not now.
- **OPAQUE** — confirmed rendered, no children exposed (see §7).
- **LOAD_FAILED** — never surveyed; couldn't be placed by §5.

Write incrementally, after each device/context. Update
`survey_checklist.md` (§3) alongside every write — the catalog and the
checklist should never drift apart.

### Coverage summary
Alongside the catalog: total contexts attempted, counts per status,
total run time (descriptive telemetry — not a target or a limit),
anything that hit an unexpected error, how often each tier of §5's
ladder was used.

## 9. Escalation discipline — within a phase, not across phases

- A stalled agent waiting on a human mid-phase over a single control
  or device has failed that phase's job. If something about *one
  control* isn't covered by this document, make the most defensible
  call, log it plainly in `notes`, and keep going within the phase.
- This does **not** override §1 — the choice of *which phase* to run is
  always a human decision at session start. Escalation-discipline
  applies to in-the-weeds decisions during a phase you were already
  told to run, not to expanding scope beyond it.
- Distinguish "I don't have an answer, so I'm marking this honestly and
  moving on" (fine) from "I'm inventing an automation_id I didn't
  actually observe" (never do this — see §10).

## 10. What NOT to do

- Don't write any new task functions, don't add anything to
  `TASK_REGISTRY`, don't touch `click_by_id()` or any action code. This
  is a read-only survey. Turning the catalog into real tasks is a
  separate, later step.
- Don't patch broken tooling — log it as broken and use a documented
  replacement if one exists.
- Don't guess or infer an `automation_id` you didn't actually see in a
  dump. If unclear, mark `UNVERIFIED` and move on.
- Don't skip devices/categories because they seem unlikely to matter —
  survey everything the phase asks; scoping happens later, with data
  in hand.
- Don't start a second phase in the same session because the first one
  finished early (§1.4).
- Don't mark a phase done without checking `scripts/dumps/` for the
  actual expected files (§1.2, §3).
