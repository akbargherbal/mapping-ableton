# PHASED_PLAN.md — Resumable Implementation Plan

Companion to `context.md` (read that first for *why*; this file is *what,
in what order*). This file replaces the previous `PHASED_PLAN.md` entirely
— that one tracked an earlier round of fixes (its own Phases 0–6) that are
now done and no longer the active problem. Each phase below has a
checklist, a definition of done, and its dependencies, so a future session
can jump straight to the first unchecked box.

**How to use this file:** check boxes off as work completes. Update
"Current Status" below at the end of every session, even a partial one.

---

## Current Status

> **Phase:** 0 not started (still the first real item below). Since this
> plan was originally written, one small out-of-band cleanup landed: the
> click-automation course's placeholder policy file
> (`ABLETON_AGENT_POLICY.md`) and its orphaned builder script
> (`build_runtime_env.sh`) were deleted, and references to them in
> `README.md` and `build_mastering_env.sh` were fixed up. See `context.md`
> §3a for the full writeup — it doesn't change anything about Phases 0–3
> below, just removed some dead weight the diagnosis in §2 also applies to.
> **Last updated:** this session — recorded the `ABLETON_AGENT_POLICY.md` /
> `build_runtime_env.sh` deletion. Phase 0 (Groove Pool code fix) itself is
> still not started.

---

## Phase 0 — Remove the Groove Pool call path at the code level
**Priority: first. Everything else in this plan assumes this is done —
the policy rewrite in Phase 2 can't stop narrating the crash until there's
nothing left to narrate around.**

**Goal:** a confirmed-crash action should have no callable path at all, not
a callable path plus warnings. Apply the "don't hand someone a 0 button"
principle from this session's discussion.

- [ ] In `scripts/keyboard_shortcuts.py`, delete the `groove_pool_toggle`
      entry from the `SHORTCUTS` dict entirely (currently lines ~123–141).
- [ ] Confirm `load_shortcut("groove_pool_toggle")` now raises a plain
      `KeyError` (unknown label), not `ShortcutBlocked` — there should be
      no special-cased exception or justification text left for this
      label, because the label shouldn't exist anymore.
- [ ] Grep the repo for any other place that could reach Groove Pool
      (`grep -rniI "groove" --include="*.py" --include="*.sh" .`) to
      confirm `keyboard_shortcuts.py` was the only door — same check the
      previous session's Phase 0 did, worth re-confirming after the edit.
- [ ] **Do not touch** `scripts/dumps/control_catalog.json` or
      `scripts/dumps/section_Groove-Pool.json`. Their `OPAQUE` status and
      crash-incident notes are fine as static historical data — this phase
      is only about removing the *callable* guard and its surrounding
      code comments/docstring justification, not about the data files.
- [ ] Remove or shorten the now-unnecessary justification comment inside
      `SHORTCUTS` and any docstring text in `load_shortcut`/
      `ShortcutBlocked` that exists specifically to explain the Groove Pool
      case — if the entry is gone, comments defending its existence should
      go with it. The generic `ShortcutBlocked`/`allow_blocked` mechanism
      itself stays, since it's still legitimately used by
      `monitoring_buttons` and `launch_selected_slot`.

**Definition of done:** `groove_pool_toggle` is not a valid label anywhere
in `SHORTCUTS`; no code comment anywhere still narrates the crash in detail
(a one-line "removed after a confirmed crash, see KNOWN_ISSUES.md" is fine
if useful for a future maintainer — a full incident report in a code
comment is what we're removing).

**Depends on:** nothing. Pure code change, no live Ableton needed to verify
the `KeyError` behavior (a plain unit-level check of `SHORTCUTS` and
`load_shortcut` is enough).

---

## Phase 1 — Rewrite `docs/MASTERING_COURSE_KNOWN_ISSUES.md`'s framing
**Priority: second. Should land before or alongside Phase 2, since the
policy rewrite will point to this doc as where crash/gap tracking now
lives — the doc needs to actually work that way first.**

**Goal:** turn this file from a "confirmed, permanent facts, don't
duplicate them" list into an **open investigation log** — suspected
crash/gap causes get tried, get logged with what's confirmed vs. still
unknown, and get a root-cause column that starts empty and fills in over
time, instead of arriving pre-solved.

- [ ] Remove the exclusion bullet under "What does NOT qualify" that
      currently says a "gap or OPAQUE area already named in `AGENTS.md`"
      (naming Groove Pool as its example) doesn't belong in this log —
      that's backwards now. Once the policy file stops pre-declaring
      things broken, this log is the *only* place they get tracked.
- [ ] Add a row (or a short "Under investigation" section above the table)
      for Groove Pool itself, written as an open question, not a settled
      fact: what's known (two crashes previously observed, same fault
      bucket, `0xc0000409` in `ucrtbase.dll`, before the code-level guard
      existed), what's *not* known (root cause — is it the specific
      toggle sequence, window state, something else entirely), and what
      the next confirm/refute step would be now that Phase 0 has removed
      the automated path (e.g. a deliberate, isolated manual test).
- [ ] Update the "Format" table's columns if needed so "Root Cause" can
      honestly be left blank/`Unknown` rather than implying every row
      already has one filled in.
- [ ] Leave the three-part bar ("structural, will recur, cheap to fix at
      the root") and the "ordinary teaching friction doesn't count" list
      as-is — those were never the problem, only the exclusion for
      already-documented gaps was.

**Definition of done:** this doc can accept "we suspect X crashes but
haven't confirmed why" as a valid row, and no longer tells someone not to
log something because it's already written up elsewhere in prose.

**Depends on:** Phase 0 conceptually (the Groove Pool row should reflect
that the automated path is now gone, not just blocked), but could be
drafted in parallel if convenient.

---

## Phase 2 — Rewrite `SUNO_MASTERING_AGENT_POLICY.md` (the real target)
**Priority: third. The actual deliverable this whole plan is in service
of.**

**Goal:** a policy file with no historical narrative, no redundant domain
detail, and no crash forensics — because Phase 0 removed the thing that
needed narrating around, and Phase 1 gave crash/gap tracking a proper home
outside this file.

- [ ] Remove the standalone Groove Pool "hard rule" callout entirely. With
      Phase 0 done, there's no automated path to warn against — if it's
      not part of the curriculum and not a callable action, the policy
      doesn't need to mention it at all. If the learner opens it manually
      and something happens, that's exactly what `KNOWN_ISSUES.md` (Phase
      1) is for, not this file.
- [ ] Remove the Browser-loading and Info-panel "no automation surface"
      justifications; keep only the plain instruction ("device loading
      goes through MCP") without the backstory of why clicking doesn't
      work. Confirm with the person whether clicking should still be tried
      first now (see the open question logged at the end of the previous
      session) or whether MCP-first stays the default.
- [ ] Relax the "already demonstrated once this session" rule per this
      session's decision: keep demonstrating again if the learner asks to
      see it again; only default to "invite them to do it themselves" when
      they haven't asked otherwise.
- [ ] Trim "Learner Profile" down to what actually changes how the agent
      should behave (novice, single stereo file / no stems, no paid
      plugins) and cut domain specifics that duplicate the curriculum docs
      (exact frequency ranges, what `matchering` does) — those live in
      `docs/suno-mastering-course-breakdown.md` /
      `docs/suno-mastering-curriculum.md` already.
- [ ] Remove the "Progress Tracking" section entirely. Sessions are
      stateless; the learner states their starting point conversationally
      each time. (Leaves an open question for Phase 3 below: does
      `mastering_progress.md` still get created by the build script if
      nothing in the policy references it?)
- [ ] Rewrite the Known-Issues Log section's framing to match Phase 1's
      new version of the doc: check it at the start of a session the same
      as before, but writing to it now includes "tried something and it's
      unconfirmed/still investigating," not just confirmed root-caused
      fixes.
- [ ] Re-verify the "When Something Doesn't Work" / escalation section
      still reads cleanly once the Groove Pool callout and the Browser
      justification are gone — it may compress further once those two
      cross-references are removed.
- [ ] Full read-through against the two prior in-conversation drafts from
      this session (not saved as files, only discussed) to make sure
      nothing legitimate got dropped along with the bloat — Role, Curriculum
      pointers, Global Rules, Lesson Loop, Verify/Don't Trust, and The
      Stems Trap were all confirmed fine as-is and shouldn't change.

**Definition of done:** a person can read the entire file in one pass
without hitting a place where it explains *why* a rule exists via incident
history instead of just stating the rule.

**Depends on:** Phase 0 (for Groove Pool) and Phase 1 (for where crash/gap
tracking now lives). Should not be started before both land, or the
rewrite will just reintroduce the same narrative it's trying to remove.

---

## Phase 3 — Reconcile `build_mastering_env.sh` with the policy changes
**Priority: fourth. Cleanup triggered by Phase 2, not urgent on its own.**

**Goal:** the build script's whitelist and generated files should match
whatever Phase 2 actually ships — no orphaned artifacts the policy no
longer references.

- [ ] Decide: since "Progress Tracking" is being removed from the policy
      (Phase 2), does `build_mastering_env.sh` still create/preserve
      `mastering_progress.md`? If the workflow is genuinely stateless now,
      this is dead weight; if there's still a reason to keep a lightweight
      record (e.g. for the person's own reference, not the agent's), say
      so explicitly rather than leaving the script and the policy
      disagreeing the way the original contradiction (documented in the
      old `context.md`) did.
- [ ] Confirm `KNOWN_ISSUES.md` seeding still points at the Phase 1
      rewritten `docs/MASTERING_COURSE_KNOWN_ISSUES.md` and that the
      "never overwritten once it exists" behavior (lines ~158–169) is
      still correct given the new framing.

**Definition of done:** running `build_mastering_env.sh` produces exactly
the files the rewritten policy actually references — nothing more, nothing
stale.

**Depends on:** Phase 2 (needs to know what the final policy actually
references before deciding what the build script should ship).
