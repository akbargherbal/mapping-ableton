# Phase 5 Report — Lesson-to-catalog reference layer

**Date:** 2026-08-09
**Goal:** the one piece of "prep" worth doing next — a cheap, inspectable lookup reference mapping each `course_outline.txt` module to candidate `automation_id`s from `control_catalog.json` and matching `TASK_REGISTRY` entries. No scripted sequence, no narration, no phrasing; honest gaps marked, not papered over.

---

## What changed

- `docs/curriculum_map.md` — new file only. Per-module reference (Modules 1–7) listing relevant `automation_id`s with explicit write/read-status tags, a "Proven-write controls" table (the verified automation surface), and an "Honest gaps" section. Written as Markdown (inspectable/editable, not code), per the plan.

No script or shell file changed.

---

## Acceptance criteria evidence

### AC1 — For a sample of 3–4 modules, the reference correctly lists real, verified automation_ids (spot-checked against control_catalog.json directly)

All 52 backticked automation_ids in the map were spot-checked against `control_catalog.json`. Wildcards/`[N]`/`[M]`/`.*` forms in the reference use index placeholders deliberately (reference-doc convention); every concrete form was verified present:

```
$ python3 <<'PYEOF'
... (load control_catalog.json, collect all automation_ids, check concrete forms) ...
missing concrete forms: none — all present
```

Modules spot-checked against the catalog directly (IDs listed exist in the file, not guessed):
- Module 3 (Quantization): `Transport.GlobalQuantization` → present, write=proven via `set_combobox_by_id` (Phase 3).
- Module 5 (EQ Eight): `TrackView.Device[0].Freq` → present, write=proven via `set_slider_by_id` (Phase 2).
- Module 6 (Mixer): `SessionView.Track[0].Mixer.Volume`, `.Pan`, `.Send[0]`, `.PeakLevel`, `SessionView.ReturnTrack[0].Mixer.*`, `SessionView.GroupTrack[0].Mixer.*` → all present.
- Module 4 (Arrangement): `ArrangementView.AutomationModeButton`, `.LockEnvelopes`, `.SetDeleteLocator`, `.Track[0].Header.AddAutomationLane` → all present.

### AC2 — Phase E (Browser) topics honestly flagged as "no reference available yet"

`browser:sounds`, `browser:instruments`, `browser:drums`, `browser:audio_effects`, `browser:midi_effects`, `browser:plugins` are all `UNMAPPED` in the catalog (confirmed by direct inspection). The map marks Browser, Packs, and Browser Sounds as **gap**, and the Honest-gaps section states: "Do not guess item-level IDs."

### AC3 — Stored as a simple, inspectable file, not code

`docs/curriculum_map.md` — plain Markdown, cheap to edit as the catalog or curriculum changes.

---

## Regression guard

The plan's guard: "this phase adds a new file only — verify no existing script imports or depends on its absence."

```
$ grep -rn "curriculum" scripts/
(exit 1 — no matches)
```

No script references the curriculum map or depends on its prior absence. The new file is additive only. No live Ableton interaction occurred in this phase (nothing to regression-diff).

---

## Notes

- **Write/read status tags are the honest core of this reference.** Each ID is tagged `write=proven` (CheckBox/Slider/ComboBox verified in Phases 2–3), `write=none` (readable/referenceable but no verified write path), or `gap` (not in catalog). The "Proven-write controls" table makes the boundary explicit: only 7 controls have a verified write path today, and the map points students only at those for hands-on automation.
- **"6 recurring interaction idioms" wording persists in `TASK_REGISTRY["idiom_demo"]`'s description** (flagged in Phase 1 too) — left untouched here because `--list-tasks` output must stay byte-identical to the Phase 0 baseline. The map's Module 5/6 rows implicitly reflect the 3 actually-implemented idioms. Still a candidate for a future cleanup if the baseline is ever regenerated.
- **No restarts / no live runs were needed** this phase; it is a pure reference-lookup deliverable.
