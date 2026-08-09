# AGENTS.md

Operating instructions for the agent running the **infrastructure
remediation** work defined in `PHASED_PLAN.md`.

> **You are not the tutor agent and not the survey agent.** This workspace
> is a deliberately narrow export of the `mapping-ableton` dev repo,
> containing only what's needed to execute `PHASED_PLAN.md`. It does not
> contain curriculum, pedagogy, or narration work — that is explicitly out
> of scope. If you find yourself designing lesson content or agent dialogue,
> stop; that is a different project phase, not this one.

## 0. The one rule that overrides everything else

**No regression.** Every phase in `PHASED_PLAN.md` must leave every
currently-working capability behaving identically to before. This is not
a nice-to-have alongside "fix the bug" — it is co-equal with it. A phase
that fixes its target issue but changes behavior of something that already
worked has failed that phase, even if the primary fix looks correct.

This is why Phase 0 (baseline capture) comes first and is mandatory before
any other phase, and why every later phase's acceptance criteria includes
re-running the Phase 0 baseline and diffing output.

## 1. Environment

- This project's automation only runs against a real Windows Ableton Live
  installation via UI Automation (`pywinauto`). Two configurations are
  possible:
  - **Plain Windows**: `python` works directly.
  - **WSL2 with the repo on the Linux filesystem**: WSL's own
    `python`/`python3` cannot see the Windows desktop. Use **Windows Python
    invoked from WSL via interop**, called as `python.exe`, with a plain
    relative path from inside the repo directory (e.g. `python.exe
    scripts/automate_ableton_task.py --task idiom_demo --live`). Confirm
    which configuration you're in before the first `--live` run of a
    session — don't assume.
- Every `--live` run in this plan (Phases 0, 2, 3, 4) must run against a
  **throwaway/test Ableton project**, never a real project you or the user
  cares about. Phases 2 and 3 specifically involve write paths that have
  already crashed Ableton once (see §3) — treat this as non-negotiable, not
  a suggestion.
- Always run `--dry-run` (the default; `--live` is opt-in) at least once
  before the first `--live` invocation of any task you're touching this
  session, to confirm the task's logic reaches the point you expect before
  it does anything real.

## 2. Every session starts the same way

1. **Confirm Phase 0 (baseline) exists and is populated.** If
   `baseline/baseline_task_list.json` and the saved run logs listed in
   `PHASED_PLAN.md` §Phase 0 don't exist yet, that is this session's only
   job — do not start any later phase without a baseline to diff against.
2. **Read `PHASED_PLAN.md` and determine the current phase** by checking
   each phase's acceptance criteria against what's actually true on disk —
   same principle as this repo's survey process: trust the file, not a
   memory of what you did last session.
3. **State the phase you're about to work on and its acceptance criteria,
   plainly, before starting.** Don't silently begin.
4. **Work only that phase, to completion, this session — including its
   regression check.** If you finish early, stop and report; do not roll
   into the next phase uninvited. A phase isn't done until its regression
   guard has actually been run, not just its own new acceptance criteria.
5. **Phases are strictly ordered.** Do not attempt Phase 2 or 3 before
   Phase 1 is done, and do not attempt Phase 4 before Phases 2–3 are done.
   The plan's ordering is deliberate (see `PHASED_PLAN.md`'s own reasoning,
   e.g. Phase 5 is last because pointing students at unfixed controls would
   be actively harmful) — don't reorder it for convenience.

## 3. Non-negotiable safety facts — do not relitigate these

These are established, not open questions. Do not attempt to "test whether
this is still true" as a way of second-guessing them — the cost of being
wrong is a host-application crash, not a caught exception.

- `RangeValuePattern.SetValue()` / `ValuePattern.SetValue()` on a Slider
  **is confirmed to crash Ableton Live itself**, reproduced twice
  (2026-08-08, once via `probe_write_back`, once via `task_set_tempo`
  directly). **Never call this method on a live Slider control, for any
  reason, including "just to confirm."**
- The only proven-safe write path for a Slider is **double-click + type +
  Enter** (simulated keyboard entry), as already implemented in
  `task_set_tempo`. Phase 2 generalizes this pattern — it does not invent
  a new one.
- ComboBox write-back has no confirmed crash but also no confirmed safe
  path yet. Treat it with the same isolation discipline as the Slider fix
  (single control, throwaway project, willing to lose the session) even
  though it hasn't failed yet — "hasn't crashed" and "proven safe" are not
  the same claim.
- CheckBox write-back (`set_checkbox_by_id`) already works and is already
  hardened with verify+retry. **Do not modify this function's write
  mechanism** while working on Phases 2–3 — it is the one proven reference
  implementation; changing it without cause risks the exact regression
  this whole plan exists to prevent.

## 4. Stop conditions — when to halt and report instead of continuing

- **Any live write test crashes Ableton, at any point, even once.** Do not
  retry. Do not attempt a "safer" variant in the same session. Stop, document
  exactly what was called and against which control, and report to the
  human before touching that control type again. The project's own history
  (§3 above) is exactly this scenario played out once already — don't repeat
  it by being confident the second time.
- **A regression check fails** — any Phase 0 baseline task produces
  different output after a change than before it, and the difference isn't
  explained by the phase's own intended fix. Stop and resolve before moving
  to the next phase, don't note it as a "known issue" and continue.
- **A phase's acceptance criteria can't be verified from disk.** Same
  principle as this repo's survey work: a claim of "done" that can't be
  checked against an actual file/log/diff is not done.

## 5. What NOT to do

- Don't touch `ABLETON_AGENT_POLICY.md` or anything related to curriculum,
  lesson narration, or student-facing conversation design — explicitly out
  of scope for this plan (see `PHASED_PLAN.md`'s stated scope).
- Don't expand Phase 5 into an actual lesson script or dialogue design. Its
  acceptance criteria is a reference lookup, not a curriculum.
- Don't re-enable the disabled `SetValue()` test paths in
  `automate_ableton_task.py`'s write-back test harness "to double check" —
  they're disabled for a documented reason (§3).
- Don't skip Phase 0 because it feels like process overhead. It is the only
  thing that makes every other phase's "no regression" claim checkable
  rather than asserted.
- Don't mark a phase done from your own judgment — check it against the
  concrete acceptance criteria and regression guard written for that phase
  in `PHASED_PLAN.md`.

## 6. Reporting

At the end of each phase, write `reports/phase<N>_report.md` containing:
- What changed (files touched, one line each).
- The regression-guard diff output (or explicit confirmation of "identical
  to baseline").
- The phase's own acceptance-criteria evidence (paste the relevant command
  output, don't summarize it away).
- Anything that took more than one attempt, and why — this is useful
  history for whoever reads this later, the same way this project's other
  docs preserve "confirmed twice on 2026-08-08" instead of just stating the
  current rule.

Do not include speculative next-phase planning in a phase report — that
belongs in `PHASED_PLAN.md` itself, which this agent should treat as
read-only reference, not a document to silently rewrite mid-execution. If
the plan itself needs to change based on something discovered during
execution, say so explicitly to the human rather than editing it unilaterally.
