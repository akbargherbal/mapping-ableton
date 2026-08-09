# Phase 2 Report — Fix slider write-back

**Date:** 2026-08-09
**Goal:** replace the crash-confirmed `RangeValuePattern.SetValue()` path with the click+type pattern proven safe in `task_set_tempo`, generalized into a reusable helper, and turn `task_idiom_demo`'s Idiom 2 into a real write-and-verify.

---

## What changed

- `scripts/automate_ableton_task.py`:
  - Added `set_slider_by_id(window, auto_id, value, dry_run, label, verify=..., tolerance=0.01, max_attempts=2)` — a generic slider write helper using **double-click + type + Enter** only. It never calls `SetValue()` (the module's WRITE-BACK STATUS note and the helper's own docstring make this explicit). Verified write: after typing, the value is read back via `RangeValuePattern.CurrentValue` and compared to the target within a tolerance; retry once, then raise.
  - Added `_parse_slider_readback(raw)` — converts inconsistent Ableton read-backs (numeric e.g. `120.0` for Tempo vs display-string e.g. `"1.00 kHz"` for EQ Eight Freq) into a plain float in native units (kHz→Hz, MHz→Hz, etc.), returning None if unparseable. Needed because the default verify must handle both forms.
  - Added `import re` for the read-back parser.
  - Wired `set_slider_by_id` into `task_idiom_demo`'s Idiom 2: read original value → pick a mid-range target (1000 Hz unless already near it, else 500 Hz) → write+verify → restore original. Docstring updated to say Slider is now a real write, not read-only.
  - Updated the module WRITE-BACK STATUS note: Slider now "DISABLED SetValue() / proven click+type helper" instead of "DISABLED/DANGEROUS" — the click+type path is now proven; SetValue() remains forbidden.

No shell scripts changed. `task_set_tempo`, `probe_toggle`, and all CheckBox paths untouched (confirmed via `git diff` — the only `set_tempo` mentions in the diff are comments).

---

## Acceptance criteria evidence

### AC1 — Isolated single-control test completes without crashing, three separate runs in a row

Isolated test ran against `TrackView.Device[0].Freq` (EQ Eight band 1, loaded on a throwaway track for this purpose only). Each run: read original (10.0 Hz) → write 1000.0 Hz via `set_slider_by_id` → read back → restore original → read back. All three runs exited 0 with `RESULT: PASS`, no Ableton crash.

Run 1 (full output):
```
original Freq read: 10.0 Hz
Target value chosen: 1000.0 Hz (original=10.0 Hz)
  current value (RangeValuePattern, read-only): 10.0 Hz
  [click+type] IsolatedTest.Freq: set to 1000.0
EVENT: {"v": 1, "type": "action_start", "label": "IsolatedTest.Freq", "level": "L1"}
  [confirmed] IsolatedTest.Freq now verified (via click+type)
EVENT: {"v": 1, "type": "action_result", "label": "IsolatedTest.Freq", "level": "L1", "result": "success", "attempt": 1}
after-set readback: 1.00 kHz  parsed=1000.0
  current value (RangeValuePattern, read-only): 1.00 kHz
  [click+type] IsolatedTest.Freq.restore: set to 10.0
  [confirmed] IsolatedTest.Freq.restore now verified (via click+type)
restored readback: 10.0 Hz  parsed=10.0
RESULT: PASS
```

Runs 2 and 3 (tail):
```
===== RUN 2 =====
  [confirmed] IsolatedTest.Freq.restore now verified (via click+type)
restored readback: 10.0 Hz  parsed=10.0
RESULT: PASS
exit=0
===== RUN 3 =====
  [confirmed] IsolatedTest.Freq.restore now verified (via click+type)
restored readback: 10.0 Hz  parsed=10.0
RESULT: PASS
exit=0
```

### AC2 — `task_idiom_demo` demonstrates Idiom 2 as a real write-and-verify, not a read-only print

Live run with EQ Eight loaded (full Idiom 2 section):
```
=== Idiom 2: Turn a knob  (TrackView.Device[0].Freq) ===
  Original: 10.0 Hz -> target: 1000.0 Hz (via click+type, SetValue never called)
  current value (RangeValuePattern, read-only): 10.0 Hz
  [click+type] Freq slider: set to 1000.0
EVENT: {"v": 1, "type": "action_start", "label": "Freq slider", "level": "L1"}
  [confirmed] Freq slider now verified (via click+type)
EVENT: {"v": 1, "type": "action_result", "label": "Freq slider", "level": "L1", "result": "success", "attempt": 1}
  current value (RangeValuePattern, read-only): 1.00 kHz
  [click+type] Freq slider (restore): set to 10.0
  [confirmed] Freq slider (restore) now verified (via click+type)
EVENT: {"v": 1, "type": "action_result", "label": "Freq slider (restore)", "level": "L1", "result": "success", "attempt": 1}
```
Write landed (10 Hz → 1000 Hz confirmed) and restore landed (→ 10 Hz confirmed). Both are verified writes with `result:"success"`.

### AC3 — `grep -n "SetValue"` shows no live call path for sliders

```
$ grep -n "SetValue" scripts/automate_ableton_task.py
# every hit is a comment, a docstring warning, or the DISABLED probe_write_back
# task (whose test bodies return skip strings and never call SetValue())
```

All 23 hits are in comments (WRITE-BACK STATUS block), docstrings (`task_set_tempo` DANGER note, `probe_write_back` DANGER note, `set_slider_by_id` docstring), or the disabled `probe_write_back` task's skip-message bodies. `set_slider_by_id` itself contains zero `SetValue` references.

---

## Regression guard

Project state was returned to Phase 0 conditions before the re-run: EQ Eight track deleted, Track[0] Arm reset to off, Track[0] Monitoring reset to Auto (the `arm_track` run had left them on from earlier sessions), and confirmed `TrackView.Device[0].Freq` no longer resolves so `idiom_demo` skips Idiom 2 exactly as it did in the baseline.

Re-ran every Phase 0 baseline task + `--list-tasks`, diffing byte-for-byte:

```
=== probe_toggle ===          IDENTICAL to baseline
=== idiom_demo ===            IDENTICAL to baseline
=== arm_track ===             IDENTICAL to baseline
=== read_solo_states ===      IDENTICAL to baseline
=== solo_one ===              IDENTICAL to baseline
list-tasks IDENTICAL to baseline
```

Syntax: `python3 -m py_compile scripts/automate_ableton_task.py` → OK.

`task_set_tempo` untouched and confirmed working after the phase (same click+type path, same event shape):
```
$ python.exe scripts/automate_ableton_task.py --task set_tempo --bpm 123 --live
Task: set tempo to 123.0 BPM
  current value (RangeValuePattern, read-only): 120.00
  [confirmed] tempo now reads 123.00 (via click+type)
$ python.exe scripts/automate_ableton_task.py --task set_tempo --bpm 120 --live
  [confirmed] tempo now reads 120.00 (via click+type)
```

---

## Things that took more than one attempt / notes

- **The default verify initially failed on the Freq slider.** First isolated run: write sent, verify failed. Root cause: Ableton's read-back for Freq is a display string `"1.00 kHz"`, not a number — `float("1.00 kHz")` raised, so verification couldn't succeed even though the write probably landed. Fixed with `_parse_slider_readback()` (regex number + unit multiplier). This is the same "read-backs are inconsistent across controls" reality documented in `read_combobox_value`, now handled for sliders too.
- **A second diagnostic also revealed the type-in field is Hz-based.** Typing `2000` produced `2.00 kHz`, while typing `3.50` produced `10.0 Hz` — the field treats typed input as Hz, and values below the ~10 Hz minimum clamp to 10 Hz. The demo's target choice (1000 Hz unless already near it) avoids the low-end clamp. The original value got left at 10 Hz by that diagnostic and the isolated test restored to exactly what it read, so no state cleanup issue — the EQ Eight track was deleted afterward anyway.
- **Project-state cleanup for the regression guard:** the earlier `arm_track` runs had left Track[0] armed with Monitoring=In; these were reset (Arm off, Monitoring Auto) so the re-run would diff cleanly against the Phase 0 baseline.
- **Three-clean-runs requirement honored:** the tempo crash was reproduced twice on 2026-08-08, so the plan requires three consecutive clean isolated runs, not one. All three passed with exit 0.
