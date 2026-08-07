# AGENTS.md

Operating instructions for the agent running the **control survey** task.
This is your complete briefing for this run. You should not need to stop
and wait on a human for anything covered here — if you hit a gap this
document doesn't answer, log it honestly in the catalog and keep moving
(see "Escalation discipline," §8).

## 0. Environment

- Windows 10/11, with Ableton Live installed, running, and one project
  open.
- Open, close, and switch devices/views/tracks freely — this is a
  read-only survey. You are not editing or saving the project.
- Use the `python` command. **Do not use `python3`.**
- Work from inside `scripts/`, or with it on the path — these scripts
  import from each other.
- **AbletonMCP is connected and enabled.** You have MCP tool access to
  Ableton's Live Object Model directly — this is your primary method for
  loading a device onto a track (§4). Use it; you don't need to verify
  its presence, it's already confirmed available for this run.

## 1. Before you start — write your plan

Everything in this document is a strong, considered starting point. It
is not ground truth. **Nothing here excuses you from checking reality
before you commit to a course of action.** Before you survey a single
device, do the following, in order:

1. **Run a handful of sanity checks** against what this document assumes:
   - Dump the current window once (`dump_ableton_pywinauto.py`,
     maximized) and confirm you get a non-trivial tree back, not an
     empty or near-empty one.
   - Confirm AbletonMCP actually responds to a real call (e.g. a
     read-only query, or a trivial load-by-name on one device) — "it's
     connected" is not the same as "it does what §4 assumes it does."
     If it behaves differently than described (different call shape,
     partial capability, load-by-name works but returns no confirmation,
     etc.), that's real information — update your plan around what it
     actually does, don't force it into the assumed shape.
   - Pull the actual device list from the Browser (or AbletonMCP, if it
     exposes one) and get a real count. Don't proceed on an assumed or
     remembered list.
   - Confirm the six Browser category tabs still behave as described
     (§5.4) — a quick switch-and-check, not a full re-verification.
2. **Write a short plan file** (`dumps/run_plan.md` or `.json` — your
   choice of format, but write it before starting the survey proper) that
   states: the device/context list you're about to work through and its
   order, which of this document's assumptions you just confirmed vs.
   which turned out different, and a rough time budget per phase (native
   devices vs. everything else in §5.4). This doesn't need to be long —
   a few lines per point is enough. Its purpose is to force the
   check-before-commit step to actually happen and leave a record of
   what you found, not to produce a polished document.
3. If a sanity check contradicts something this document states as fact,
   **trust what you just observed, not the document** — note the
   discrepancy in your plan file and proceed on the corrected
   understanding. Don't stop and wait for a human over this; a corrected
   plan is a normal outcome, not an error state.
4. Only after this — start the actual survey (§5).

This step is short (a few checks, a short file), not a second research
project. Its only job is to catch "the plan assumed X but the real
environment does Y" before that assumption quietly shapes 40 minutes of
survey work.

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
| `dump_ableton_states.py` | Automates view-switching + dump in one command. `--states session arrangement sounds instruments drums audio_effects midi_effects plugins`, or `--states all`. Detects the current view before switching, so it never toggles blind. |
| `grep_dump.py` | Search a saved JSON dump for a substring across name/automation_id/class_name; prints breadcrumb path + control_type + automation_id + bounding_rect. Use this constantly instead of eyeballing raw JSON. |
| `automate_ableton_task.py` — `build_automation_id_index()` | One-shot walk of a window/control, returns `{automation_id: [elements]}`. Your primary tool for "does this control have a real, unique ID." |
| `automate_ableton_task.py` — `resolve()` / `find_control()` | Locate a control by `automation_id`, with retry-on-refocus. |
| `automate_ableton_task.py` — `click_by_id()` | Click a control via `automation_id` (mouse-based). Use this if you need to click into a device or select a track to make its controls render (§6). |
| `automate_ableton_task.py` — `get_toggle_state()` | Read a checkbox/toggle's current bool state via UIA pattern, not just "is it clicked." |
| **AbletonMCP** (MCP tool) | Direct Live Object Model access. Use for loading devices by name (§4, tier 1) and any other LOM-level query/action that's faster or more reliable than clicking through the GUI. |

## 4. Loading a device onto a track — escalation ladder

Getting a device onto a track is the one step that could otherwise force
a stop-and-wait. Attempt, in order, escalate only on failure for that
specific device — **never stop and wait for a human**:

1. **AbletonMCP load-by-name.** This is your default path for every
   device. Fast, and avoids the Browser's known weak spot (see §5.4)
   entirely.
2. **UIA Browser search-and-load**, if MCP fails for a specific device:
   switch to the Browser (`dump_ableton_states.py`), type the device
   name into the Browser search field, press Enter, and double-click the
   top result if Enter doesn't land. This interaction is untried — you
   don't have prior evidence it works or fails. If it fails consistently
   across several devices, don't keep retrying it for every remaining
   device — drop to tier 3 for the rest and note the pattern once.
3. **Skip and log `LOAD_FAILED`**, with whatever error/state you
   observed, and move to the next device immediately. This is a valid,
   honest outcome, not a failure of the run.

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
1. Load it onto a track (§4).
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
State clearly, per device, whether this pattern is generically
available. "Clickable" and "readable" are different guarantees; the
catalog needs both.

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
- **Master track**
- **Return tracks**
- **Group / folded tracks** (note any structural differences vs. a
  normal track's mixer strip)
- **Clip Detail view**
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
  is a read-only survey. Turning the catalog into real tasks is a
  separate, later step.
- Don't guess or infer an `automation_id` you didn't actually see in a
  dump. If unclear, mark `UNVERIFIED` in notes and move on.
- Don't skip devices because they seem unlikely to matter later —
  survey everything asked; scoping happens after, with data in hand.
