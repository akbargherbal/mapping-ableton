# Fix Plan — Next Survey Pass

Source: `survey_report.md` (run of 2026-08-07, 101/101 contexts, 0
LOAD_FAILED). This plan does not re-litigate what went well — it turns
every item in the report's §5 ("what went wrong") and §7 ("lessons")
into a specific change, mostly to `AGENTS.md`, so the next agent hits
none of these as *discoveries*. Everything here was already paid for
once; the point of a fix plan is to not pay for it twice.

No survey work is performed as part of this plan. Output of this plan
is (a) this document and (b) a rewritten `AGENTS.md`.

---

## 1. Scope decision for the next pass

The first pass already produced a complete catalog: 101/101 contexts,
0 LOAD_FAILED, 3,016 controls. Re-running the *entire* survey from
scratch would mostly re-confirm known-good results at real cost (~50
min of tool time) for little new information.

**Recommendation: the next pass is a resume/audit pass, not a fresh
survey**, using AGENTS.md's existing Resume branch (§1). Concretely it
should:

1. Reconcile checklist against the catalog (already-specified behavior).
2. Re-open only the contexts flagged as risk in this plan (see §3
   below — mostly UNMAPPED entries and the two non-read-only contexts)
   and confirm/extend their notes rather than re-surveying everything.
3. If the run is instead happening on a **different machine**, treat
   it as fresh-start — that's exactly the case the corrected §0/§1
   sanity checks (below) are for.

Either way, the same rewritten `AGENTS.md` is what gets used — it
doesn't assume which branch applies.

---

## 2. Pitfall → fix map

Each row: what happened → why it happened → the fix, and where it
lands in the rewritten `AGENTS.md`.

| # | What happened (report §3/§5) | Root cause | Fix | Lands in |
|---|---|---|---|---|
| 1 | Briefing assumed plain Windows; real env was WSL2 with the repo only on the Linux filesystem, `python` unusable, `python.exe` over a UNC path required | AGENTS.md §0 stated one assumed environment as fact instead of as "the common case, verify it" | Rewrite §0 to describe **both** known configurations (plain Windows, and WSL2-with-Linux-repo) and make interpreter/path selection a sanity-check output, not a precondition | New §0 + Sanity check 0 (new) |
| 2 | `dump_ableton_states.py` broken at import (missing `keyboard_shortcuts.py`); one of four toolbox entries dead on arrival, discovered mid-briefing | Toolbox table presented it as working without caveat | Mark it **known-broken** directly in the toolbox table with the exact error and the exact replacement (`AbletonMCP set_ableton_view` + `browser_switch.py`), so the agent never spends time discovering this itself | Toolbox table (§3) |
| 3 | MCP `load_instrument_or_effect` reports success with an empty "Devices on track" list — a load can silently fail while looking fine | Escalation ladder didn't require independent verification after tier-1 success | Add a **mandatory verification step** after every load, all tiers: call `get_track_info` (or equivalent) and confirm the expected device is actually present before proceeding. Not optional, not just "if suspicious" | §4 (escalation ladder) |
| 4 | Loading an instrument renames the track (e.g. "1-MIDI" → "1-Analog") mid-survey | Not documented as expected behavior; agent had to notice and adapt live | State it as an **expected, harmless side effect** up front, and recommend identifying the scratch track by index/position, not by name, since delete-by-name still worked but only by luck of no collision | New "Session hygiene" subsection (§4) |
| 5 | `survey_section.py --aid "SessionView.Track[0]"` matched the shallow TitleBar leaf instead of the whole track group | Prefix matching in the tool is greedy-but-shallow; not documented as a usage trap | Add explicit guidance in the toolbox entry: **anchor on the most specific meaningful node** (e.g. `SessionView.Track[0].Mixer`, not `SessionView.Track[0]`), and check the returned child count looks non-trivial before trusting it | Toolbox table (§3) |
| 6 | `Ext. Audio Effect` slugified to `Ext--Audio-Effect` (`.` → `-`); wrong filename fed to `update_catalog.py`, wasting a cycle | Agent assumed a mental slugification rule instead of checking the actual generated filename | Add a one-line rule: **before calling `update_catalog.py`, list `scripts/dumps/` and confirm the exact filename** — don't compute the slug by hand | Toolbox table (§3), near `update_catalog.py` |
| 7 | Two contexts (group-track creation, Clip Detail) needed real UIA interactions — Ctrl+G, clicking a clip slot — which pushed against the "read-only" framing | "Read-only" was stated without defining what it actually forbids | Redefine "read-only" precisely: **it means "never save/export the project and never touch action code (§9)," not "zero UI interaction."** Selecting tracks, grouping them, and clicking a clip slot to render Clip Detail are explicitly in-scope survey-prep actions, to be logged in `notes`, same as this run did | §0 (redefinition) + §5.4 (explicit callout for these two contexts) |
| 8 | Sliders almost never expose `RangeValuePattern`; "clickable" and "readable" are different guarantees, confirmed near-universal | §5.3 predicted this as a *possibility* to check, not a *near-certain* finding | Sharpen §5.3 from "check whether this is generically available" to "expect it's generally **not** available; record the exception, not the rule" — saves the next agent from treating every failed RangeValue read as a bug to chase down | §5.3 |
| 9 | (Process, not a specific error) Broken tooling was correctly left unpatched, workaround documented instead | This worked well — nothing to fix, but worth locking in as an explicit rule since it's easy for a future agent to "just fix the one-line import" | Keep §9 as-is; add one sentence to the toolbox note for `dump_ableton_states.py` explicitly forbidding the tempting one-line patch | Toolbox table (§3) |

---

## 3. Items for the audit pass specifically (not just AGENTS.md fixes)

If §1's resume/audit path is taken, these are the concrete things worth
re-opening, in priority order:

1. **The two non-read-only contexts** (group track, Clip Detail) —
   confirm their catalog `notes` field actually states what UI action
   was taken to produce them, per the new §0 definition. If the first
   pass didn't log this explicitly, add it now; don't re-do the action.
2. **A sample of UNMAPPED sliders** — spot-check a handful against the
   sharpened §5.3 expectation (RangeValue absent is normal now, not a
   signal of something broken) and confirm the catalog's per-context
   status note reflects that framing rather than reading as an
   unresolved question.
3. **`dump_ableton_states.py`** — leave broken, per §9, but confirm the
   catalog or plan has exactly one clear note about it (not scattered
   across multiple files) so a third pass doesn't rediscover it either.

No new devices, no new contexts, no re-running the 85 device loads —
those are done and clean (0 LOAD_FAILED).

---

## 4. What changes in `AGENTS.md`

Summary of structural edits (full rewritten file is the actual
deliverable, this is the diff-level summary):

- **§0 Environment** — replaced a single assumed environment with two
  known configurations + a rule to verify, not assume. Added a precise
  definition of "read-only" that permits minor UI prep actions but
  forbids saving and forbids touching action code.
- **New Sanity check 0** — "determine which environment/interpreter
  you're actually in" as the first sanity check, before the existing
  four, since this was the single biggest plan-vs-reality gap.
- **§3 Toolbox table** — `dump_ableton_states.py` marked known-broken
  with exact cause and replacement; `survey_section.py` gets an anchor-
  precision warning; `update_catalog.py` gets a "verify the actual
  filename first" note.
- **§4 Escalation ladder** — added mandatory post-load verification
  (`get_track_info`) as a non-skippable step after *any* tier succeeds,
  not just tier 1; added a short "session hygiene" note about track
  renaming and identifying the scratch track by position, not name.
- **§5.3** — reworded from "check whether available" to "expect
  generally unavailable; record exceptions."
- **§5.4** — explicit one-line callouts for group-track creation and
  Clip Detail confirming the specific permitted UI actions.
- Everything else (§1 startup/resume logic, §2 task statement, §6
  virtualization warning, §7 output schema, §8/§9 discipline) is
  unchanged — the report didn't surface problems with these, so they're
  left alone rather than churned for their own sake.

The rewritten file follows as `AGENTS.md` in this same location,
ready to replace the current one.
