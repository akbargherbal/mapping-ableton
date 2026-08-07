# AGENTS.md

Operating instructions for the agent running the **control survey** task.
This is your complete briefing for this run. You should not need to stop
and wait on a human for anything covered here — if you hit a gap this
document doesn't answer, log it honestly in the catalog and keep moving
(see "Escalation discipline," §8).

> **Revision note:** this version incorporates fixes from a prior run's
> retrospective (`survey_report.md`). Anywhere you see "known from prior
> run," that's not a hypothesis — it's a confirmed fact, don't re-derive it.

## 0. Environment

Two configurations have been observed in practice. **Don't assume
either — the first sanity check (below) determines which one you're
in**, unless you already know from a resume.

- **Configuration A — plain Windows.** Ableton Live installed and
  running, repo on the Windows filesystem, `python` command works
  directly.
- **Configuration B — WSL2 with the repo on the Linux filesystem**
  (confirmed once already). Ableton runs on the Windows host; the repo
  lives only under the WSL filesystem (e.g.
  `/home/<user>/.../mapping-ableton/`), with no Windows-side copy.
  In this configuration:
  - WSL `python` has only a pywinauto *stub* — `from pywinauto import
    Desktop` fails, it cannot see the Windows desktop, and it is **not
    usable** for any survey script.
  - The only usable interpreter is **Windows Python invoked from WSL
    via interop**, called as `python.exe`, given the script's path as a
    **UNC path**: `\\wsl.localhost\<distro>\home\<user>\...\script.py`.
  - Scripts resolve their own imports via
    `Path(__file__).resolve().parent`, so working directory doesn't
    matter — no `cd` needed, just get the invocation and path right.

Whichever configuration you're in:

- Open, close, and switch devices/views/tracks freely. **"Read-only"
  means two specific things, not "zero interaction":**
  1. Never save or export the project.
  2. Never touch action code (`click_by_id()`, `TASK_REGISTRY`, or
     anything under §9).
  It does **not** forbid ordinary survey-prep UI actions — selecting
  tracks, pressing a key combo to group them, clicking a clip slot to
  make Clip Detail render. Those are in scope; log what you did in the
  catalog's `notes` field for that context (see §5.4 for the two known
  cases).
- Work from inside `scripts/`, or with it on the path — these scripts
  import from each other.
- **AbletonMCP is connected and enabled.** You have MCP tool access to
  Ableton's Live Object Model directly — this is your primary method
  for loading a device onto a track (§4). Use it; you don't need to
  verify its presence, it's already confirmed available for this run.
  Do not, however, trust its responses blindly — see §4.

## 1. Startup — checkpoint first

Two files at the repo root are the **standing checkpoint mechanism** for
this survey — not a one-off write, but the thing every session starts
from:

- **`survey_plan.md`** — the full plan + environment reality: tooling,
  AbletonMCP capability map, device list, method, catalog schema, risks.
  Ground truth for *how* to run.
- **`survey_checklist.md`** — one checkbox per device/context, grouped by
  phase A–F. The running record of *what* has been surveyed.

Every session starts at the same single step, with two branches:

### Fresh start (no `dumps/control_catalog.json`)

1. **Run the sanity checks** (below) against what `survey_plan.md`
   assumes. They are fresh-start only — a resume does not repeat them.
2. If a sanity check contradicts the plan, **trust what you just
   observed, not the document** — update `survey_plan.md` and
   `survey_checklist.md` to match, and proceed on the corrected
   understanding. Don't stop and wait for a human; a corrected plan is a
   normal outcome, not an error state.
3. Survey the checklist from the top — the first unchecked item — writing
   the catalog incrementally (§7).

### Resume (catalog exists)

1. **Reconcile the checklist against `dumps/control_catalog.json` before
   trusting it — the catalog wins.** For each context key present in the
   catalog, mark the matching checklist item done. For any checklist item
   marked done that has **no** matching context in the catalog, treat it
   as NOT done and log the disagreement — never trust a checkbox the
   catalog doesn't back.
2. Do a quick read-only environment poke (window present, AbletonMCP
   responds) — a 30-second check, not the full sanity list.
3. Continue from the first unchecked checklist item. If the checklist
   is fully reconciled and complete, this is an **audit pass**, not a
   survey pass: re-open only the specific contexts flagged as risk in
   `FIX_PLAN.md` §3 (non-read-only contexts, a sample of UNMAPPED
   sliders, the `dump_ableton_states.py` note) rather than re-surveying
   everything.

### Sanity checks (fresh-start only)

0. **Determine environment and interpreter first.** Check whether you're
   in Configuration A or B (§0) — e.g., does plain `python` see
   pywinauto's `Desktop`? Is the repo path a WSL path or a native
   Windows path? Record which configuration applies and the exact
   invocation form you'll use for every subsequent script call. This
   single check was the largest source of wasted time in a prior run —
   don't skip it or assume the briefing's default.
1. **Dump the current window once** (`dump_ableton_pywinauto.py`,
   maximized) and confirm you get a non-trivial tree back, not an
   empty or near-empty one.
2. **Confirm AbletonMCP actually responds to a real call** (e.g. a
   read-only query, or a trivial load-by-name on one device) — "it's
   connected" is not the same as "it does what §4 assumes it does."
   If it behaves differently than `survey_plan.md` describes (different
   call shape, partial capability, load-by-name works but returns no
   confirmation, etc.), that's real information — update the plan around
   what it actually does, don't force it into the assumed shape. **Known
   from a prior run:** `load_instrument_or_effect` can report success
   with an *empty* device list — don't rediscover this, just build the
   verification step in §4 from the start.
3. **Pull the actual device list** from the Browser (or AbletonMCP, if it
   exposes one) and get a real count. Diff it against
   `survey_checklist.md` and update the checklist if the real list
   differs. Don't proceed on an assumed or remembered list.
4. **Confirm the six Browser category tabs still behave as described**
   (§5.4) — a quick switch-and-check, not a full re-verification.

This startup step is short (a few checks, a reconcile), not a second
research project. Its only job is to catch "the plan assumed X but the
real environment does Y" before that assumption shapes survey work — or,
on resume, to catch a checklist that drifted from the catalog.

## 2. Your task

Build one master control catalog: every control you can find in Ableton,
tagged with whatever identifier lets code interact with it reliably (or
a clear note that no reliable identifier exists), so future automation
tasks don't need to hand-map controls one at a time. This is a survey,
done once, completely — not a tutoring or task-execution project.

## 3. Your toolbox

Everything below is in `scripts/`. Read each script's own module
docstring before first use — it has specifics (flags, known quirks) not
repeated here.

| Tool | What it does |
|---|---|
| `dump_ableton_pywinauto.py` | Read-only full UIA tree dump → JSON + console. Flags: `--max-depth`, `--json <path>`, `--diagnose`, `--no-maximize`. **Maximizes the window by default before dumping — leave this on** (see §6). |
| `dump_ableton_states.py` | **Known broken — confirmed in a prior run, do not attempt to fix it.** It imports `automate_ableton_task.py`, which imports `keyboard_shortcuts.py`, which does not exist in this repo. This is action-adjacent code — per §9, don't patch it, not even a one-line stub, tempting as that is. **Use this replacement instead:** AbletonMCP's `set_ableton_view` for view switching, plus `browser_switch.py` (below) for Browser category switching. |
| `browser_switch.py "<Category>"` | Click a Browser sidebar category by exact `(control_type, name)`. Confirmed working. This plus MCP `set_ableton_view` fully replaces `dump_ableton_states.py`. |
| `grep_dump.py` | Search a saved JSON dump for a substring across name/automation_id/class_name; prints breadcrumb path + control_type + automation_id + bounding_rect. Use this constantly instead of eyeballing raw JSON. |
| `survey_section.py` | Dump a subtree anchored at a given `--aid`. **Anchor precision matters — prefix matching is greedy but shallow.** `--aid "SessionView.Track[0]"` will match the shallowest matching leaf (e.g. a TitleBar) before the whole track group. Anchor on the most specific meaningful node instead, e.g. `SessionView.Track[0].Mixer`. If the returned subtree looks suspiciously small for what you're anchoring on, you probably anchored too shallow. |
| `update_catalog.py` | Merges a per-context dump into `dumps/control_catalog.json`. Takes a filename generated from the context name via slugification (non-alphanumerics → `-`), which does not always match what you'd compute by hand (e.g. `Ext. Audio Effect` → `Ext--Audio-Effect`, not `Ext.-Audio-Effect`). **Before invoking, list `scripts/dumps/` and confirm the exact generated filename — don't hand-compute the slug.** |
| `automate_ableton_task.py` — `build_automation_id_index()` | One-shot walk of a window/control, returns `{automation_id: [elements]}`. Your primary tool for "does this control have a real, unique ID." |
| `automate_ableton_task.py` — `resolve()` / `find_control()` | Locate a control by `automation_id`, with retry-on-refocus. |
| `automate_ableton_task.py` — `click_by_id()` | Click a control via `automation_id` (mouse-based). Use this if you need to click into a device or select a track to make its controls render (§6). |
| `automate_ableton_task.py` — `get_toggle_state()` | Read a checkbox/toggle's current bool state via UIA pattern, not just "is it clicked." |
| **AbletonMCP** (MCP tool) | Direct Live Object Model access. Use for loading devices by name (§4, tier 1) and any other LOM-level query/action that's faster or more reliable than clicking through the GUI. Includes `get_track_info` (or equivalent read query) — this is your load-verification tool, see §4. |

## 4. Loading a device onto a track — escalation ladder

Getting a device onto a track is the one step that could otherwise force
a stop-and-wait. Attempt, in order, escalate only on failure for that
specific device — **never stop and wait for a human**:

1. **AbletonMCP load-by-name.** This is your default path for every
   device. Fast, and avoids the Browser's known weak spot (see §5.4)
   entirely.
2. **UIA Browser search-and-load**, if MCP fails for a specific device:
   switch to the Browser (MCP `set_ableton_view`, per §3), type the
   device name into the Browser search field, press Enter, and
   double-click the top result if Enter doesn't land. If it fails
   consistently across several devices, don't keep retrying it for every
   remaining device — drop to tier 3 for the rest and note the pattern
   once.
3. **Skip and log `LOAD_FAILED`**, with whatever error/state you
   observed, and move to the next device immediately. This is a valid,
   honest outcome, not a failure of the run.

**Mandatory verification, every tier, every device — not optional:**
after a load call reports success, independently confirm the device is
actually on the track (e.g. `get_track_info` and check the device is
present by name) before you proceed to dump/record it. **Confirmed from
a prior run:** the MCP load call can report success with an *empty*
device list. Trusting the call's own return message without this check
will silently let load failures through as if they succeeded.

**Session hygiene (known behavior, not a bug):**
- Loading an instrument onto a track **renames the track** (e.g.
  "1-MIDI" → "1-Analog"). This is expected. Identify your scratch track
  by its position/index in the track list, not by its name, so a rename
  mid-survey doesn't confuse your bookkeeping.
- Keep a single scratch track and delete the loaded device between
  devices — keeps `TrackView.Device[0]` predictable and the UIA tree
  small.

## 5. Full survey scope

Work through these in the fixed order below (predictable, resumable if
cut off). Don't skip anything because it "seems unlikely to matter" —
that scoping decision happens later, with the data in hand, not now.

### 5.1 Native devices
For each native Ableton device — EQ Eight, Compressor, Glue Compressor,
Limiter, Multiband Dynamics, Saturator, Utility, Auto Filter, and every
other device in Ableton's own Browser categories (Audio Effects, MIDI
Effects, Instruments, Drums) — **the Browser (or AbletonMCP, if it can
list devices) is the source of truth for the full list**, not any list
in this document — this is exactly what your §1 device-count check
should have already pulled.

For each device:
1. Load it onto a track (§4, including the mandatory verification step).
2. Dump the full tree (`dump_ableton_pywinauto.py`, maximized).
3. Record every control found inside: `name`, `automation_id` (or null),
   `control_type`.
4. Note whether it renders as individual elements or as one opaque
   element with no children (custom-rendered UI — record plainly, don't
   guess why).

### 5.2 Plug-ins (VST/AU) category
Check the Browser's "Plug-Ins" category. If it contains items, survey
them the same way as native devices — but expect opaque/no-children
results are a likely (not certain) outcome for third-party UIs.

### 5.3 Value-read/write pattern check
For a sample of controls with a real `automation_id` (start with
sliders/knobs), check whether pywinauto exposes a `RangeValuePattern` or
similar — i.e. can you read the current value, not just click blindly.
**Expect, going in, that this pattern is generally *not* available on
sliders/knobs** — confirmed near-universal in a prior run (EQ Eight
bands, Amp controls, most device parameters). Treat a missing pattern as
the normal case to record, not a problem to chase down; record the
exceptions where a pattern *is* available, since those are the
noteworthy finding. "Clickable" and "readable" are different guarantees;
the catalog needs both, stated per device.

### 5.4 Everything else
Same method (dump + record), applied to:
- **Arrangement View** controls (full tree — timeline, loop brace, etc.)
- **Browser panel**: the six top-level category tabs (Sounds,
  Instruments, Drums, Audio Effects, MIDI Effects, Plug-Ins) are
  confirmed to carry empty `automation_id`s — matched instead by
  `(control_type, name)`. Check whether items **inside** a category
  (actual samples/presets/device entries, not the top-level tabs)
  behave the same way or differently — sample a representative few per
  category.
- **Master track** — confirmed absent from the Session-view UIA tree
  entirely in a prior run; check for it under **Arrangement View**
  instead (`ArrangementView.MainTrack`), don't conclude it's missing
  just because Session doesn't show it.
- **Return tracks**
- **Group / folded tracks** — note any structural differences vs. a
  normal track's mixer strip (confirmed in a prior run: group mixer
  lacks Input/Monitoring/Arm). **Creating a group track requires
  selecting two tracks and pressing Ctrl+G** — this is an in-scope
  survey-prep action per §0's read-only definition, not a violation of
  it. Log the action taken in this context's `notes`.
- **Clip Detail view** — only renders once a clip is selected. **Clicking
  a clip slot to select/create a clip so this view renders** is likewise
  an in-scope survey-prep action per §0. Log the action taken in this
  context's `notes`.
- Any other top-level view reachable without leaving the main window —
  don't assume Session/Arrangement/Browser/Clip Detail is exhaustive;
  check the View menu for anything else.

## 6. Window virtualization — non-negotiable

Ableton's Session View is UI-virtualized: controls not actually rendered
on screen (minimized, too small, unfocused window) don't exist as UIA
elements at all — not "hidden," genuinely absent from the tree, with no
error raised. Confirmed in practice: ~60 vs ~201 automation_ids on the
same project depending only on window state. **Always dump with the
window maximized** (the default — don't pass `--no-maximize` unless you
have a specific, logged reason). If a dump looks suspiciously sparse for
a device you expect to have many controls, re-check window state before
recording it as `OPAQUE`.

## 7. Output

One file: `dumps/control_catalog.json`. JSON, not markdown — meant to be
read/diffed by future automation code, not scanned by a person. One
entry per control:

```json
{
  "context": "EQ Eight",
  "name": "Freq 1",
  "automation_id": "...",
  "control_type": "Slider",
  "value_pattern_available": true,
  "notes": ""
}
```

Group by context. For each context, add a one-line status:

- **MAPPED** — real, stable identifier, ready for click-and-verify automation.
- **UNMAPPED** — control exists and was seen, but has no usable
  identifier — needs a name/coordinate fallback later, not now.
- **OPAQUE** — nothing exposed at all; whole device/panel is one element
  with no visible children.
- **LOAD_FAILED** — never surveyed; couldn't be placed by any available
  method (§4). Log the error/state observed.

### Write incrementally

Write the catalog after each device/context, not once at the end. A run
cut off partway through should leave a valid partial file, not nothing.
Track running coverage counts (attempted / loaded / controls found) so
the final summary can state coverage honestly.

### Coverage summary

Alongside the catalog: total devices/contexts attempted, counts per
status category above, total run time, anything that hit an unexpected
error, and how often each tier of §4's ladder was used. Numbers, not
narrative.

## 8. Escalation discipline

- A stalled agent waiting on a human has failed the one job this task
  has. If something in this document doesn't cover a situation you hit,
  make the most defensible call, log it plainly in `notes`, and continue.
- Distinguish "I don't have an answer, so I'm marking this honestly and
  moving on" (fine, expected) from "I'm inventing an automation_id I
  didn't actually observe" (never do this — see §9).

## 9. What NOT to do

- Don't write any new task functions, don't add anything to
  `TASK_REGISTRY`, don't touch `click_by_id()` or any action code. This
  is a read-only survey (per §0's precise definition). Turning the
  catalog into real tasks is a separate, later step.
- Don't patch broken tooling either — not even a one-line stub (e.g. a
  missing `keyboard_shortcuts.py`). Log it as broken and use the
  documented replacement (§3). A workaround is fine; an unapproved code
  change is not.
- Don't guess or infer an `automation_id` you didn't actually see in a
  dump. If unclear, mark `UNVERIFIED` in notes and move on.
- Don't skip devices because they seem unlikely to matter later —
  survey everything asked; scoping happens after, with data in hand.
