# context.md

## What this project is

This repo runs one autonomous job: point an AI agent at a running Ableton
Live instance, with an hour (often less) and no human clicking anything for
it, and have it come back with a complete map of every control it could
find — device knobs, sliders, buttons, browser items, view controls —
tagged with whatever identifier lets code interact with it reliably (or a
clear note that no reliable identifier exists).

The output is one file: a control catalog. Nothing else. This is not a
tutoring project, not a task-execution project — it's a survey, done once,
so every later project (tutor, autonomous mixer, whatever) doesn't have to
re-discover the same ground by hand.

## Where this comes from

This grew directly out of `ableton-gui-grounding` (the parent project). That
project built real, working click-and-verify automation for a small,
hand-mapped set of controls — track arm, solo, mute, tempo, transport — 8
tasks total. Not because the mechanism was limited to 8, but because only
those 8 controls had ever actually been surveyed and confirmed to carry a
stable identifier. The click/verify machinery itself (`resolve()`,
`click_by_id()`, `build_automation_id_index()`) is already generic — it
takes any identifier string and acts on it. What was missing was the map.

Filling that map by hand, one control at a time, with a human clicking
through Ableton alongside the agent, doesn't scale and isn't the point.
This repo exists to do the survey itself, unattended, once, properly.

## The one hard requirement: no babysitting

Every design decision below serves this constraint. If a step in the survey
would normally require a human to click something first (most commonly:
placing a device onto a track before its controls can be surveyed), the
agent must have — and try — an automated way to do that step itself before
ever falling back to asking for help. A survey that stops and waits for a
person every few minutes has failed at the one job this repo has.

## What's available to the agent

- **A live Bash environment** on the same machine as Ableton — the agent
  can write and run its own scripts, not just invoke fixed ones.
- **The UIA scripts from the parent repo**: `dump_ableton_pywinauto.py`
  (read-only, general-purpose full tree dump — already proven to work
  independent of any fixed task list) and `dump_ableton_states.py` /
  `automate_ableton_task.py` for view-switching and indexing, if useful.
- **An MCP server** (`ableton-mcp-extended`, external to this repo) that
  talks to Ableton via its Remote Script / Live Object Model, not through
  clicking the GUI at all. This matters specifically for the "load a
  device onto a track" step: if the MCP/LOM side can load a device by name
  programmatically, that sidesteps the Browser entirely — and the Browser
  is the one part of the UIA side already confirmed to be unreliable
  (category items carry empty `automation_id`s; nothing about it is
  click-by-ID clean). Whether the MCP side actually has this capability,
  and how well it works, is unconfirmed and is itself part of what this
  survey needs to establish, not something to assume going in.

## Escalation strategy for the one blocking step: loading a device

Getting a device onto a track is the only step that could otherwise force a
stop-and-wait. The agent should attempt, in order, and only escalate on
failure:

1. **MCP/LOM load-by-name**, if the server exposes it — fastest, avoids
   the Browser's known weak spot entirely.
2. **UIA Browser search-and-load**: type the device name into the Browser
   search field, then press Enter or double-click the top result. This is
   a different interaction than clicking a category `DataItem` by ID (the
   thing already known to be shaky) — it hasn't been tried, and there's no
   evidence yet that it fails.
3. **Skip and log, never block.** If both fail for a given device, the
   agent records it as `LOAD_FAILED` in the catalog with whatever error it
   got, and moves on to the next device immediately. A gap in coverage is
   an acceptable, honest outcome. A stalled agent waiting on a human is not.

Once a device is loaded by whichever method worked, the actual survey step
(dump the tree, record every control's identifier and type, check for a
readable/settable value pattern) is already read-only and already proven
generic — no new invention needed there.

## Time budget and checkpointing

Budget is roughly one hour, sometimes less. The agent should:

- Work through devices/views in a fixed, predictable order (so a partial
  run is still useful and resumable, not a random subset).
- Write the catalog incrementally, after each device — not build
  everything in memory and write once at the end. A run that gets cut off
  at 40 minutes should still leave a valid, partial catalog file behind,
  not nothing.
- Track its own coverage as it goes: how many devices attempted, how many
  loaded successfully, how many controls found per device, so the final
  report can state coverage honestly instead of implying completeness it
  doesn't have.

## What "done" looks like

One catalog file (JSON — meant to be read by future automation code, not by
a person scanning prose), one entry per control found, each tagged with
whatever identifier exists and whether it's reliable:

- `MAPPED` — real, stable identifier found, ready for click-and-verify
  automation the same way the parent project's 8 tasks already work.
- `UNMAPPED` — control exists and was seen, but has no usable identifier
  (matches the Browser's known pattern) — needs a name-based or different
  fallback strategy later, not now.
- `OPAQUE` — nothing exposed at all; the whole device/panel is one
  element with no visible children (expected failure mode for some
  custom-rendered plugin UIs, possibly for some native devices too —
  unconfirmed until the survey actually hits one).
- `LOAD_FAILED` — never got surveyed at all because it couldn't be placed
  by any available method; logged honestly, not silently dropped.

Alongside the catalog, a short coverage summary (counts per category above,
total run time, anything that hit an unexpected error) — not a narrative
report, just the numbers needed to know how trustworthy the catalog is.

## What this project deliberately does not do

- Does not execute any real automation task against the surveyed controls.
  Reading and cataloging only.
- Does not assume MCP/LOM device-loading works — that's tested, not
  assumed, and the fallback exists precisely because it might not.
- Does not treat an incomplete run as a failure. A catalog covering most of
  Ableton with a handful of honest `LOAD_FAILED`/`OPAQUE` entries is a
  successful outcome. A catalog that silently pretends full coverage when
  it doesn't have it is the actual failure mode to avoid.
