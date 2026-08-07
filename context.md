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
fails on a _specific_ device — not because MCP's overall availability is
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

- **Session 2**: Ran the agent's §1 recon step for real. It confirmed
  the environment (WSL2 + Windows Python for UIA, AbletonMCP
  connected-but-partial — `get_device_parameters`/`get_session_info`
  broken, load-by-name works), pulled the real device list (47 audio FX,
  15 MIDI FX, 23 instruments, 2 drum devices, 0 plug-ins), and found two
  of the four toolbox scripts (`automate_ableton_task.py`,
  `dump_ableton_states.py`) don't import at all (missing
  `keyboard_shortcuts.py`) — so surveying can't proceed on the toolbox
  as briefed without a small read-only replacement helper
  (`survey_device.py`, specced but not yet written). All of this was
  captured in `survey_plan.md` at the repo root; the agent stopped
  there, as instructed, without starting the actual survey.

  Before letting it continue, added a **cross-session checkpoint
  mechanism**, since a ~70–85 min survey with no memory between
  sessions risked losing completed work on any interruption (context
  limit, crash, deliberate stop, compaction — doesn't matter which):
  - **`survey_checklist.md`** (new, repo root): one checkbox per
    device/context pulled from `survey_plan.md` §6/§7, grouped by phase
    A–F. Ticked in the same step the agent writes that context's entry
    to `dumps/control_catalog.json` — near-zero extra cost since it's
    already touching disk at that point.
  - **`AGENTS.md` §1 rewritten** from a one-shot "write your plan"
    step into a standing **fresh-start / resume** dual branch. Resume
    reconciles the checklist against `dumps/control_catalog.json`'s
    actual keys first — **catalog wins on any disagreement**; a
    checklist box ticked with no matching catalog entry is treated as
    NOT done, never the reverse (false "not done" just costs a
    re-survey; false "done" would silently lose a control from the
    final map). The old sanity-check list was kept verbatim but scoped
    to fresh-start only, so resumes don't re-pay that cost every
    session.

  Note for later: `survey_plan.md` §1 ("write a short plan file... your
  choice of format") is now slightly stale — it describes the old
  one-shot behavior superseded by this checkpoint pair. Not worth a
  special session to fix; correct it next time `survey_plan.md` gets
  touched for another reason.

  Agent was then released to run the actual survey (§5 onward). As of
  this writing it's mid-run, into **Phase B (MIDI Effects)** — meaning
  Phase A (47 Audio Effects) completed without a `LOAD_FAILED`-driven
  stop. Next session: read `dumps/control_catalog.json` +
  `survey_checklist.md` to see actual Phase A/B results (coverage,
  any `UNMAPPED`/`OPAQUE`/`LOAD_FAILED` entries, whether
  `survey_device.py` ended up matching its §8 spec or drifted), decide
  whether anything about Phases C–F needs tuning before the agent gets
  there, and fix the `survey_plan.md` §1 staleness noted above if
  convenient.

- **Session 3** (review/QA session, no live Ableton access — this
  session works from a clone of the repo only, cannot run anything
  against a real Ableton instance): The survey finished in Session 2's
  continuation. Confirmed by reading (not re-running) the three
  hand-off docs:
  - `survey_report.md` — the agent's own retrospective (written on
    request at the end of Session 2: "what went well / wrong / planned
    vs achieved"). Claims: 104 contexts, 3,797 controls, 0
    `LOAD_FAILED`, 87 min wall time, all Phases A–F reached, all
    checklist items checked, one Ableton crash mid-Phase-F (recovered
    cleanly because of incremental writes), group-track creation never
    worked (3 methods tried), compact device views (e.g. Compressor)
    couldn't be expanded, MCP's `get_device_parameters`/
    `get_session_info` stayed broken all run so no LOM cross-check was
    ever possible.
  - `survey_plan.md` and `survey_checklist.md` — cross-checked against
    the report; consistent. All 104 checklist items are ticked; the
    plan's device counts (47/15/23/2/0) match what the report claims
    was surveyed.

  **QA pass on `dumps/control_catalog.json` itself** (static analysis,
  no Ableton needed — this is why it's doable from a plain repo clone):
  - Recomputed `coverage_summary` from the actual `contexts` dict
    instead of trusting the stored summary. `contexts_attempted` (104),
    `controls_total` (3797), `mapped` (48), `opaque` (17), and
    `load_failed` (0) all check out exactly.
  - **Found one real discrepancy: `coverage_summary.unmapped` says 38,
    actual count is 39.** Root cause: three UNMAPPED entries —
    `Group / Folded Tracks`, `View Menu (top-level views)`, and
    `Plug-Ins` — are documentation-style contexts with `node_count: 0`
    and `loaded_via: "none"` (no device was ever loaded for them; they
    record a gap, an enumeration, and a verified-empty category
    respectively). These don't fit the per-device merge path that
    `scripts/update_catalog.py` uses (its `status_for()` recomputes the
    summary from `cat["contexts"]` on every call, so if it had produced
    the final file, the count would be self-consistent). Working
    theory: at least one of these three was added to
    `control_catalog.json` by a different path (direct edit, or a
    merge call that didn't go through `update_catalog.py`'s recompute
    step) after the last time the summary was correctly regenerated.
    Net effect is cosmetic — the 39 UNMAPPED contexts themselves are
    all present, legitimate, and individually well-documented; only the
    one summary integer is stale by 1.
  - Verified the report's "all 17 OPAQUE devices are exactly the native
    Max-for-Live devices" claim by listing them: correct, no
    exceptions (Align Delay, Envelope Follower, LFO, Shaper;
    Envelope MIDI, Expression Control, MPE Control, Note Echo,
    Shaper MIDI; all 8 DS-\* drum synths).
  - Spot-checked a MAPPED device (`EQ Eight`, 81 controls) — ids look
    real and structurally sane (e.g.
    `TrackView.Device[0].TitleBar.ExtendViewButton`), and the
    MAPPED/UNMAPPED-relevant distinction between real per-control ids
    vs. device-group/title-bar scaffolding ids (the bug the report
    describes fixing) does hold up in the data.

  ### Verification plan (in progress — resume here)

  Goal: decide whether `dumps/control_catalog.json` is trustworthy
  enough to hand to the next project (the tutor / autonomous mixer)
  as-is, or needs a cleanup pass first. Static checks (no Ableton
  needed) go first; live checks (run via autonomous AI agent with
  AbletonMCP access) go last.
  - [x] Read `survey_report.md`, `survey_plan.md`, `survey_checklist.md`.
  - [x] Recompute `coverage_summary` from `contexts` and diff against
        the stored values → found the `unmapped` 38-vs-39 off-by-one above.
  - [x] Confirm the OPAQUE set is exactly the Max-for-Live devices.
  - [x] Spot-check one MAPPED device's control list for sane ids
        (`EQ Eight`).
  - [x] Root-cause the `unmapped` off-by-one. Confirmed: exactly 3
        contexts have `loaded_via: "none"` (`Group / Folded Tracks`,
        `View Menu (top-level views)`, `Plug-Ins`) — documentation-style
        entries with no device ever loaded, `node_count: 0`, and none of
        the per-device bookkeeping fields (`title_matched`/
        `expand_clicked`) populated the way real device merges have them.
        `update_catalog.py`'s `status_for()`/summary-recompute step always
        derives the summary fresh from `cat["contexts"]`, so a file it
        fully produced would be self-consistent — the stale `unmapped: 38`
        is consistent with at least one of these 3 having been added by a
        path that skipped that recompute (manual edit or a different merge
        call). Effect is cosmetic (all 39 UNMAPPED contexts are present and
        legitimate); the fix is a mechanical recompute-and-save, folded
        into the fix below rather than done standalone.
  - [x] Cross-checked all 104 catalog contexts against the 118 raw dump
        files in `scripts/dumps/`. Every context with `loaded_via: "mcp"`
        (101 of them) traces to a real source file — 85 to a
        `device_<slug>.json` (per-device loop, via `survey_device.py` +
        `update_catalog.py`) and the remaining 16 (Arrangement/Session
        View, Browser's 6 tabs, Master/Return tracks, Track Mixer, Clip
        Detail, Groove Pool) to a `section_<slug>.json` (via
        `survey_section.py`, for Phase F contexts that aren't a single
        loaded device). No orphan catalog entries; no missing dumps.
  - [x] Checked for duplicate `automation_id` values across the whole
        catalog: 72 ids are reused across ≥2 contexts. All are explained,
        none is a real conflict:
    - 20 are `TrackView.Device[0]*` — expected and by design: this
      prefix is a **slot-relative id** (whatever device currently
      occupies Track 3/Track 1's device slot), not a global identifier.
      Since every device was surveyed one at a time in the same slot,
      every device's controls legitimately reuse the same id shape.
      **This is an important usage note for downstream automation, not
      a bug**: code must confirm what's actually loaded before trusting
      a `TrackView.Device[0].*` id — it means "whatever's in the slot
      right now", not "this specific device's control forever."
    - 52 are `ArrangementView.*`/`SessionView.*`/`ContentBrowser*` ids
      that appear both in a broad panoramic section (e.g.
      `section_Arrangement-View`) and in a separately-surveyed
      zoomed-in child context (e.g. `Track Mixer (audio, Arrangement)`,
      `Master Track`, `Return Track A-Reverb`) covering the same real
      UI element, or shared Browser-toolbar controls (search field,
      history back/forward) that legitimately appear under all 6
      Browser tab contexts since that toolbar persists across tabs.
      Redundant but not conflicting — same id, same real element,
      recorded under two context names.
  - [x] Re-derived MAPPED/UNMAPPED/OPAQUE status per context from raw
        `controls` data (mirroring `update_catalog.py`'s `status_for()`
        rule: exclude the top-level device/section group's own id and any
        `.TitleBar.` id, then check if anything real remains) and diffed
        against the stored `status`. 2 mismatches found, investigated
        individually:
    - `Channel EQ` — re-derive said UNMAPPED, stored says MAPPED.
      **False alarm**: this device has a _second_, nested `Group` node
      (`TrackView.Device[0].Filter`, the X-Y Controller) that carries
      its own real automation_id distinct from the top-level device
      group. My re-derivation heuristic excluded all `Group`-typed
      controls, which was too blunt. Manually confirmed MAPPED is
      correct for `Channel EQ`.
    - **`Groove Pool` — likely a genuine misclassification.** Stored
      status is MAPPED, but its _only_ control with a non-null
      automation_id is `GroovePool` itself — the section's own
      top-level group id, with `view_state: null`, `node_count: 5`,
      and no other child carries an id. This is the identical
      signature to the 17 correctly-OPAQUE Max-for-Live devices (one
      self-referential id, nothing real underneath) — e.g. compare to
      `Align Delay` (`node_count: 1`, one control = its own group id →
      correctly OPAQUE). Working theory: `Groove Pool` went through
      `survey_section.py` → catalog merge without a `device_aid`
      equivalent being passed/excluded the way the per-device loop
      does, so its own id wasn't filtered out of the "real controls"
      count. Checked whether this pattern recurs elsewhere (searched
      all MAPPED contexts for "only real control is a Group whose id
      belongs to the top-level node") — **Groove Pool is the only
      occurrence**; not a widespread bug, just this one context.
  - [x] **Fix pass — done** (`dumps/control_catalog.json` edited
        directly, no re-survey needed since this was a classification/
        bookkeeping fix, not missing data):
    - `Groove Pool` reclassified `MAPPED` → **`UNMAPPED`** (not
      `OPAQUE`, after discussion — `OPAQUE` per this catalog's own
      schema means "the whole device/panel is one element with no
      visible children," which doesn't fit a 5-node tree; `UNMAPPED` —
      "seen, no usable id" — matches the schema better). `notes` field
      updated in place to explain the reclassification and its cause
      (see the field itself for full text).
    - `coverage_summary` recomputed from `contexts` (the source of
      truth) and rewritten: `mapped` 48→**47** (Groove Pool moved
      out), `unmapped` 38→**40** (the +1 off-by-one fix, +1 more from
      Groove Pool moving in), `opaque` unchanged at 17,
      `contexts_attempted`/`controls_total`/`load_failed` unchanged
      (104 / 3797 / 0). A note describing this fix was appended to
      `coverage_summary.unexpected_errors` so the change is visible
      inside the catalog file itself, not just here.
    - Nothing else in the catalog was touched — no `controls` arrays,
      no other context's `status`, no raw dump files. This was a
      minimal, targeted correction.
  - [x] **Autonomous AI Agent Verification Setup (`verification_mapping_ableton`)**:
        Created a dedicated, standalone repository `verification_mapping_ableton` packaged as `verification_mapping_ableton.zip` for an AI agent to run live verification unattended using AbletonMCP + pywinauto:
    - **`AGENTS.md`**: Tailored instructions directing the autonomous agent to cycle through all 21 verification targets sequentially without human intervention, utilizing AbletonMCP for device loading (`load_instrument_or_effect`) and view switching (`set_ableton_view`), then running `scripts/verify_context.py` to compare live UIA controls against `control_catalog.json`.
    - **`verification_targets.json`**: Machine-readable target specification covering 21 contexts (9 devices on Audio/MIDI tracks, 11 primary views/browser tabs, and 1 special check for `Groove Pool`).
    - **`scripts/verify_context.py`**: Verification helper script that walks the live UIA tree, compares observed `automation_id`s against expected catalog entries (excluding scaffolding nodes), and writes incremental results to `verification_report.json`.
    - **Curated Environment**: Contains only the required scripts (`dump_ableton_pywinauto.py`, `verify_context.py`, `browser_switch.py`, `survey_device.py`, `survey_section.py`, `grep_dump.py`), target specification, agent instructions, and `dumps/control_catalog.json`.
  - [ ] **Live verification execution — awaiting run**: The autonomous AI agent will execute `verification_mapping_ableton` against the running Ableton Live instance and produce `verification_report.json` and `verification_report.md`.
  - [ ] Once live-verification results are generated by the agent: read `verification_report.json` / `verification_report.md`, analyze any PARTIAL or MISSING findings, and write up the final QA verdict stating whether `control_catalog.json` is ready to hand to downstream projects.

  Next session: when the autonomous AI agent finishes running `verification_mapping_ableton`, inspect `verification_report.json` / `verification_report.md` to review live results and finalize the QA report.
