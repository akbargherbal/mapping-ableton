# Session Prompt — Next Survey Pass (Resume/Audit)

Paste this as the opening message when starting a new agent session.

---

Read `AGENTS.md` in full before doing anything else — it's the current,
authoritative briefing and has already been rewritten to incorporate
lessons from the prior run. This is a **resume/audit pass, not a fresh
survey**: the catalog already has 101/101 contexts and 0 LOAD_FAILED.
Do not re-survey anything that's already complete.

**Other docs in this repo, and how to treat each one:**

- `AGENTS.md` — current instructions. Follow this. Wins on any conflict.
- `survey_checklist.md` — the running record of what's been surveyed.
  **Read this and reconcile it against `dumps/control_catalog.json`**
  as your first real step (an item only counts as done if a matching
  context exists in the catalog, not just a checked box).
- `dumps/control_catalog.json` — the actual deliverable. Source of
  truth over the checklist.
- `FIX_PLAN/FIX_PLAN.md` — why AGENTS.md looks the way it does, and the
  specific short list of things this pass should re-open. Read §3.
- `survey_plan.md` — **historical**, superseded by AGENTS.md §0. Only
  useful now for run-specific facts AGENTS.md doesn't carry (exact
  hostname, WSL path, prior session state). Not authoritative.
- `survey_report.md` — **historical**, fully absorbed into
  `FIX_PLAN/FIX_PLAN.md`. No need to read it to do this pass; it's kept
  for provenance only.

**What to actually do, in order:**

1. Sanity check 0 (AGENTS.md): confirm which environment/interpreter
   you're actually in and record it before running any script.
2. Reconcile `survey_checklist.md` against `dumps/control_catalog.json`.
3. Re-open only these, per `FIX_PLAN/FIX_PLAN.md` §3:
   - The two non-read-only contexts (group-track creation, Clip
     Detail) — confirm their `notes` field documents the UI action
     taken to produce them. If missing, add the note; don't redo the
     action.
   - A sample of UNMAPPED sliders — spot-check a handful and confirm
     the status note reflects "RangeValue absent is expected," not an
     open question.
   - `dump_ableton_states.py` — confirm there's exactly one clear note
     that it's known-broken (not scattered across files). Do not
     attempt to fix it.
4. Do not touch any action code (§9 of AGENTS.md), do not save/export
   the project, and do not re-run the 85 device loads — those are done
   and clean.

If anything in `AGENTS.md` doesn't match what you observe, log it in
the catalog/notes rather than silently working around it — that's what
feeds the next fix pass, the same way this one was built from
`survey_report.md`.
