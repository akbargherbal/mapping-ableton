# AGENTS.md

Operating instructions for the agent running the **control survey** task.
This file is about your environment and your task — not a claim about the
project's current behavior. Don't treat anything in the "Background" section
as something to re-verify; it's just why this task exists.

## Background (context only, not a task)

This repo already has working, general-purpose (not hardcoded) tools for
reading and clicking Ableton's Windows UI Automation (UIA) tree:

- `resolve()` / `click_by_id()` in `scripts/automate_ableton_task.py` — click
  any control given its `automation_id`. Not limited to any fixed list.
- `build_automation_id_index()` — one-shot full tree walk, returns
  `{automation_id: [elements]}` for whatever's currently on screen.
- `dump_ableton_pywinauto.py` — read-only, dumps the full UIA tree
  (control_type, name, automation_id) to JSON.

What's missing isn't the mechanism — it's the **map**. Only ~8 controls
(Session View mixer strip + transport) have ever been surveyed and confirmed
to carry real, stable `automation_id`s. Nobody has pointed these tools at
device chains (EQ Eight, Compressor, Limiter, etc.), other views, or browser
panels. This task is that survey.

## Environment

- Windows 10/11, with **Ableton Live installed and available to launch/use**.
- Open, close, and switch devices/views/tracks freely — this is a read-only
  survey, you are not editing or committing changes to any project.
- Use the `python` command. **Do not use `python3`** (stale interpreter on
  this machine).
- Work from inside `scripts/`, or with it on the path — some scripts import
  from each other.

## Your task: build one master control map

Goal: a single catalog file mapping every control you can find to whether
it's reliably clickable/readable, so future automation tasks don't need to
hand-map controls one at a time.

### 1. Survey native devices

For each native Ableton device (EQ Eight, Compressor, Glue Compressor,
Limiter, Multiband Dynamics, Saturator, Utility, Auto Filter, and the rest of
the built-in device list — check Ableton's own device browser for the
complete set, don't assume the list above is exhaustive):

1. Load the device onto a track.
2. Run `dump_ableton_pywinauto.py` (full tree, maximized window — window
   state affects what's visible, see the script's own docstring).
3. Record, per control found inside that device: `name`, `automation_id`
   (or confirm it's empty), `control_type`.
4. Note whether the device's controls appear as individual elements at all,
   or whether the whole device shows up as one opaque element with no
   children (this happens with some custom-rendered UIs — record it plainly
   if you hit it, don't guess why).

### 2. Check for a value-read/write pattern, not just click

For a sample of controls that do have a real `automation_id` (start with
sliders/knobs), check whether pywinauto exposes a `RangeValuePattern` (or
similar) — i.e. can you read the current value and not just click blindly.
If this pattern is available generically, say so clearly; it matters as much
as the ID itself, since "click it" and "know what it's now set to" are
different guarantees.

### 3. Survey everything else not yet mapped

Same method (dump + record), applied to:

- Arrangement View controls
- Browser panel — note: category `DataItem`s are **already confirmed** to
  have empty `automation_id`s (see `dump_ableton_states.py`). Don't
  re-litigate that; instead check whether items *inside* a category (actual
  samples/presets) behave the same way or differently.
- Master track, Return tracks, Group/folded tracks
- Clip Detail view

### 4. Output

Produce one file: `dumps/control_catalog.json`. JSON, not markdown — this
catalog is meant to be read and diffed by future automation code, not by a
human scanning prose. One entry per control:

```
{
  "context": "EQ Eight",              // device/view this was found in
  "name": "Freq 1",
  "automation_id": "...", // or null if empty
  "control_type": "Slider",
  "value_pattern_available": true,    // or false / not checked
  "notes": ""
}
```

Group by context. For each context, add a one-line summary: **MAPPED**
(real IDs, ready for click_by_id), **UNMAPPED** (blank IDs, needs a
name/coordinate fallback), or **OPAQUE** (no child elements exposed at all).

## What NOT to do

- Don't write any new task functions, don't add anything to
  `TASK_REGISTRY`, don't touch `click_by_id()` or any action code. This is
  a read-only survey. Turning the catalog into real tasks is a separate,
  later step.
- Don't guess or infer an `automation_id` you didn't actually see in a dump.
  If something's unclear, mark it `UNVERIFIED` in notes and move on.
- Don't skip devices because they seem unlikely to matter for mastering —
  survey what's asked; scoping decisions happen after, with the data in
  hand.
