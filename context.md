# context.md

**Note:** this file is maintainer-facing background, kept in this
(fuller) copy of the repo for history and rationale. **The agent that
runs the actual survey does not have access to this file** — it works in
a separate, curated environment containing only `AGENTS.md` and the
handful of scripts it needs. If you're reading this to understand what
the agent knows or was told, read `AGENTS.md` instead; this file exists
for humans revisiting the project later, not for the agent.

## What this project is

This repo runs one autonomous job: point an AI agent at a running Ableton
Live instance, with an hour (often less) and no human clicking anything
for it, and have it come back with a complete map of every control it
could find — device knobs, sliders, buttons, browser items, view
controls — tagged with whatever identifier lets code interact with it
reliably (or a clear note that no reliable identifier exists).

The output is one file: a control catalog. Nothing else. This is not a
tutoring project, not a task-execution project — it's a survey, done
once, so every later project (tutor, autonomous mixer, whatever) doesn't
have to re-discover the same ground by hand.

## Where this comes from

This grew directly out of `ableton-gui-grounding` (the parent project).
That project built real, working click-and-verify automation for a
small, hand-mapped set of controls — track arm, solo, mute, tempo,
transport — 8 tasks total. Not because the mechanism was limited to 8,
but because only those 8 controls had ever actually been surveyed and
confirmed to carry a stable identifier. The click/verify machinery itself
(`resolve()`, `click_by_id()`, `build_automation_id_index()`) is already
generic — it takes any identifier string and acts on it. What was missing
was the map. Filling that map by hand, one control at a time, doesn't
scale and isn't the point. This repo exists to do the survey itself,
unattended, once, properly.

## The one hard requirement: no babysitting

Every design decision serves this constraint. If a step in the survey
would normally require a human to click something first (most commonly:
placing a device onto a track before its controls can be surveyed), the
agent must have — and use — an automated way to do that step itself
before ever falling back to asking for help. A survey that stops and
waits for a person every few minutes has failed at the one job this repo
has.

## Device loading: resolved

Earlier drafts of this project's docs treated MCP/LOM access as an
unconfirmed possibility to be checked at runtime. That's resolved now:
**AbletonMCP is connected and confirmed available** and is the agent's
primary method for loading a device onto a track (see `AGENTS.md` §4).
The UIA Browser search-and-load path and the honest `LOAD_FAILED` log
still exist as tiers 2 and 3 of that same ladder, for the case where MCP
fails on a *specific* device — not because MCP's overall availability is
still in doubt.

## Time budget and checkpointing

Budget is roughly one hour, sometimes less. The agent:

- Writes a short plan first, grounded in a few real sanity checks against
  the actual environment (device count, MCP behavior, window state) —
  not just proceeding on this document's or `AGENTS.md`'s assumptions
  untested. See `AGENTS.md` §1.
- Works through devices/views in a fixed, predictable order, so a partial
  run is still useful and resumable, not a random subset.
- Writes the catalog incrementally, after each device — not build
  everything in memory and write once at the end. A run cut off partway
  through should still leave a valid, partial catalog file behind.
- Tracks its own coverage as it goes, so the final report states
  coverage honestly instead of implying completeness it doesn't have.

## What "done" looks like

One catalog file (JSON — meant to be read by future automation code, not
by a person scanning prose), one entry per control found, each tagged
with whatever identifier exists and whether it's reliable:

- `MAPPED` — real, stable identifier found, ready for click-and-verify
  automation the same way the parent project's 8 tasks already work.
- `UNMAPPED` — control exists and was seen, but has no usable identifier
  — needs a name-based or different fallback strategy later, not now.
- `OPAQUE` — nothing exposed at all; the whole device/panel is one
  element with no visible children.
- `LOAD_FAILED` — never got surveyed at all because it couldn't be
  placed by any available method; logged honestly, not silently dropped.

Alongside the catalog, a short coverage summary (counts per category
above, total run time, anything that hit an unexpected error) — not a
narrative report, just the numbers needed to know how trustworthy the
catalog is.

## What this project deliberately does not do

- Does not execute any real automation task against the surveyed
  controls. Reading and cataloging only.
- Does not treat an incomplete run as a failure. A catalog covering most
  of Ableton with a handful of honest `LOAD_FAILED`/`OPAQUE` entries is a
  successful outcome. A catalog that silently pretends full coverage
  when it doesn't have it is the actual failure mode to avoid.

## Repo structure note

This (maintainer) copy of the repo may carry more files than the agent's
actual working environment — test files, license, older docs, etc. that
were deliberately excluded when curating what the agent gets, precisely
so the agent isn't left guessing what an unrelated file is for. If you
add something here intending the agent to use it, it needs to be added
to the agent's environment and to `AGENTS.md` explicitly — being in this
repo is not sufficient.

## Session log

- **Session 1**: Reviewed and rewrote `AGENTS.md` from scratch against
  the actual code (found and resolved a contradiction between this file
  and `automate_ableton_task.py` over MCP availability — now resolved,
  see above). Curated the agent's environment down to
  `automate_ableton_task.py`, `dump_ableton_pywinauto.py`,
  `dump_ableton_states.py`, `grep_dump.py`, and `AGENTS.md`; excluded
  `keyboard_shortcuts.{py,md}`, `test_orchestrate.py`,
  `test_phase0_events.py` as not needed for a read-only survey; kept
  `LICENSE` in the maintainer repo for unrelated reasons. Added a
  mandatory "write your plan first, grounded in sanity checks against
  the real environment" step to `AGENTS.md` (§1) so the agent doesn't
  execute on untested assumptions from either document. Next session:
  review results of the actual survey run and tune `AGENTS.md` based on
  what the agent actually found.
