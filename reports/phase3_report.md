# Phase 3 Report — Fix dropdown (ComboBox) write-back

**Date:** 2026-08-09
**Goal:** same treatment as Phase 2, applied to `Transport.GlobalQuantization` — turn ComboBox selection from "not wired up" into a real, isolated-test-proven, verified write. Deliberately avoided pattern-based setters (`SetValue()` / `SelectionItemPattern`) in favor of the Level-1 click path a human uses.

---

## What changed

- `scripts/automate_ableton_task.py`:
  - Added `set_combobox_by_id(window, auto_id, item_name, dry_run, label, max_attempts=2)` — a generic ComboBox selection helper using **click-to-open + click-item only**:
    1. Click the closed ComboBox to open its dropdown (Ableton exposes it as a `Menu` control with `automation_id="ChooserPopUp"`, containing `MenuItem` children).
    2. Find the `MenuItem` whose name matches `item_name` (handling Ableton's `<name>, checked` suffix for the currently-selected item).
    3. Click it.
    4. Read the live value back via `read_combobox_value()` and confirm it matches `item_name`; retry once, then raise loudly.
    - Never calls `ValuePattern.SetValue()` / `SelectionItemPattern` — the helper's docstring and the module WRITE-BACK STATUS note both make this explicit.
    - On failure paths it closes any stray dropdown with `{ESC}` so a failed attempt doesn't leave the UI in an open-menu state.
  - Wired `set_combobox_by_id` into `task_idiom_demo`'s Idiom 3: read current quantization → pick a different target (`1/8` unless already there, else `2 Bars`) → write+verify → restore original. Docstring updated: all 3 idioms are now real writes.
  - Updated the module WRITE-BACK STATUS note: ComboBox is now "PROVEN SAFE via click-to-open + click-item", no longer "UNTESTED / NOT WIRED".

No shell scripts changed. No live path calls `SetValue()`.

---

## Investigation result (plan action 1)

A closed ComboBox has **no children in the UIA tree** (UI-virtualized). Clicking it opens a `Menu` control (`ChooserPopUp`) whose children are `MenuItem`s, e.g. `'None'`, `'8 Bars'`, ..., `'1/32'`, with the current selection rendered as `'1 Bar, checked'`. This confirmed the plan's hypothesis: ComboBox selection can be done entirely at Level 1 (mouse) with click-to-open + click-item, so no pattern-based setter (the thing that crashed on Slider) is needed or tested.

---

## Acceptance criteria evidence

### AC1 — Three clean isolated runs, verified write via read-back

Isolated test (scratch script, not wired into any task): read current (`'1 Bar'`) → open dropdown → click `'1/8'` → read back → restore `'1 Bar'` → read back. All three runs `RESULT: PASS`, exit 0, no Ableton crash.

Run 1:
```
current: '1 Bar' via ValuePattern
target item: '1/8'
  item found: '1/8' at (L295, T283, R381, B303)
after-set: '1/8' via ValuePattern
restoring to '1 Bar'...
  item found: '1 Bar' at (L295, T182, R381, B202)
after-restore: '1 Bar' via ValuePattern
RESULT: PASS
```
Runs 2 and 3: identical `RESULT: PASS`, exit 0.

### AC2 — `task_idiom_demo` demonstrates all 3 idioms as real writes

Live run (Idiom 3 section, the new part):
```
=== Idiom 3: Pick from a list  (Transport.GlobalQuantization) ===
  Current Quantization: '1 Bar' (via ValuePattern)
  Target: '1/8' (via click-to-open + click-item, no pattern-based setter)
  [click] Quantization dropdown: set to 1/8 (current: '1 Bar')
EVENT: {"v": 1, "type": "action_start", "label": "Quantization dropdown", "level": "L1"}
  [confirmed] Quantization dropdown now reads '1/8' (via click-item)
EVENT: {"v": 1, "type": "action_result", "label": "Quantization dropdown", "level": "L1", "result": "success", "attempt": 1}
  [click] Quantization dropdown (restore): set to 1 Bar (current: '1/8')
  [confirmed] Quantization dropdown (restore) now reads '1 Bar' (via click-item)
EVENT: {"v": 1, "type": "action_result", "label": "Quantization dropdown (restore)", "level": "L1", "result": "success", "attempt": 1}
```
Write landed (`1 Bar` → `1/8` confirmed) and restore landed (→ `1 Bar` confirmed). Idiom 1 (Metronome) and Idiom 2 (Freq, skipped — no device loaded on this baseline project) unchanged.

### AC3 — `grep -n "SetValue"` — no live call path for ComboBox (or anything)

All 26 occurrences of `SetValue` in the file are in comments, docstring warnings, or the disabled `probe_write_back` task's skip-message bodies. `set_combobox_by_id` contains zero `SetValue` / `SelectionItemPattern` references.

---

## Regression guard

The plan requires re-running the **full Phase 0 baseline** and **Phase 2's new slider test**, confirming both still pass.

Project state was reset before the clean re-run: EQ Eight track deleted, Track[0].Arm off, Monitoring back to Auto (the previous `arm_track` regression run had left them on — same state artifact seen in Phase 2, now expected each cycle).

Full Phase 0 baseline diff:
```
=== probe_toggle ===          IDENTICAL to baseline
=== arm_track ===             IDENTICAL to baseline
=== read_solo_states ===      IDENTICAL to baseline
=== solo_one ===              IDENTICAL to baseline
list-tasks IDENTICAL to baseline

=== idiom_demo ===            DIFFERS, but ONLY in the Idiom 3 section:
<   [read-only, via ValuePattern] Current Quantization: '1 Bar'
<   (ComboBox write-back isn't wired up yet -- read-only for now.)
---
>   Current Quantization: '1 Bar' (via ValuePattern)
>   Target: '1/8' (via click-to-open + click-item, no pattern-based setter)
>   [click] Quantization dropdown: set to 1/8 ... [confirmed] ... success
>   ... restore to '1 Bar' ... [confirmed] ... success
```
That diff is exactly the phase's own intended fix (Idiom 3 read-only → real write); nothing else changed. Idioms 1–2 output identical.

Phase 2 slider test re-run (EQ Eight reloaded for this purpose only, then track deleted):
```
original: 1.00 kHz  parsed=1000.0
[click+type] Phase3Regression.Freq: set to 1000.0
  [confirmed] Phase3Regression.Freq now verified (via click+type)
after-set parsed=1000.0
[click+type] Phase3Regression.Freq.restore: set to 1000.0
  [confirmed] Phase3Regression.Freq.restore now verified (via click+type)
restored parsed=1000.0
RESULT: PASS
```

Syntax: `python3 -m py_compile scripts/automate_ableton_task.py` → OK. No shell scripts changed.

---

## Things that took more than one attempt / notes

- **Closed ComboBox exposes no children** — first attempt to find list items inside the ComboBox control itself found nothing. The items only exist while the dropdown is open, as a sibling `ChooserPopUp` Menu. The helper therefore does a two-step resolution: open via click, then search the window for `ChooserPopUp` and its `MenuItem` children. This is the same UI-virtualization reality documented elsewhere in the repo (window must be maximized/focused, elements render on demand).
- **The currently-selected item is rendered as `'<name>, checked'`**, not the plain name. Matching strips/normalizes the `, checked` suffix so callers can pass plain names.
- **State artifact repeated from Phase 2:** each `arm_track` baseline re-run leaves Track[0] armed + Monitoring=In; the state had to be reset before the clean regression diff. Same as Phase 2, now understood as the expected per-cycle cleanup, not a code issue.
