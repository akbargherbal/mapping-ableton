# KNOWN_ISSUES.md — Mastering Course Friction Log

**Purpose:** a lean record of *systemic* snags — cases where a bad assumption
baked into `AGENTS.md`, the scripts, or the docs cost real time or nearly
caused a wrong action, and would keep costing it in future sessions if left
alone. This is not a session diary and not a bug tracker for one-off
glitches.

**This file stays short.** If it's growing fast, the bar below isn't being
applied strictly enough — go re-read it before adding the next row.

---

## What qualifies (all three must be true)

1. **It's structural, not circumstantial.** The cause lives in `AGENTS.md`,
   a script, or a doc in this folder — not in a particular track's audio, a
   particular learner mistake, or a one-off environment hiccup (e.g. Ableton
   was slow to launch that one time).
2. **It will recur** unless something in this folder changes. Ask: *if the
   next session hits this exact situation again, will the same thing go
   wrong?* If no, it doesn't belong here.
3. **Fixing it at the root is cheap relative to what it costs left alone.**
   A five-minute wording fix in `AGENTS.md` that prevents a recurring
   10-minute detour every session clears the bar. A one-time fluke does not,
   no matter how annoying it was in the moment.

## What does NOT qualify — do not log these

- Ordinary teaching friction: the learner was confused, needed a concept
  re-explained, or disagreed with an ear-only judgment call.
- A single track's audio being unusually noisy, quiet, or weird — that's
  the material, not the agent.
- A gap or OPAQUE area already named in `AGENTS.md` or
  `scripts/dumps/control_catalog.json` (e.g. Groove Pool — permanently
  blocked, confirmed crash; Browser drag-and-drop — no automation_id on
  list items; Info View — OPAQUE). Those are already-known, already-
  documented limitations — don't duplicate them here.
- A mistake you made once and immediately corrected, with no reason to
  think it'll happen again.

## Format

One row per **distinct root cause**. If the same root cause shows up again,
don't add a new row — bump `Times Seen` and `Last Seen` on the existing one.

| Date First Seen | Times Seen | Last Seen | Symptom | Root Cause / Bad Assumption | Root Fix (what to change, and where) | Status |
|---|---|---|---|---|---|---|
| _(no entries yet)_ | | | | | | |

**Status** is one of: `Open` (not yet fixed) · `Fixed` (root fix applied —
keep the row, don't delete, so the history of what was wrong survives) ·
`Wontfix` (considered, deliberately not worth fixing — say why in Root Fix).
