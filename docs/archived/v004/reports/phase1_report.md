# Phase 1 Report — Documentation decontamination

**Date:** 2026-08-09
**Goal:** stop the repo from asserting things that aren't true. Pure text/comment changes; no `--live` behavior touched.

---

## What changed

- `README.md` — escalation ladder corrected from a 4-level ladder (with a "Direct MCP/LOM Call" tier) to the 3-level ladder `click_by_id()` actually implements: Mouse → Keyboard → Human Instructions. Added a blockquote explicitly stating MCP/LOM is a **separate parallel capability**, not a ladder tier, and pointing to the risk-framework doc for the broader policy.
- `scripts/automate_ableton_task.py`:
  - Added a prominent `WRITE-BACK STATUS BY CONTROL TYPE` comment block near the top of the module (after the docstring), stating per control type: CheckBox = proven safe (reference implementation, don't change its write mechanism), Slider = **confirmed to crash Ableton, disabled**, ComboBox = untested/unwired.
  - `task_idiom_demo`'s docstring: removed the dangling `docs/interaction_idioms.md` reference and replaced it with an inline summary of the 3 idioms actually demonstrated (toggle / slider / dropdown) plus write-back status per idiom.

No shell scripts changed. No test harness / write-path code changed.

---

## Acceptance criteria evidence

### AC1 — README's ladder description matches what the code does, verifiably, by reading both side by side

README (lines 66–73):

```
$$\text{Level 1: Mouse UI Click} \longrightarrow \text{Level 2: Keyboard Shortcut} \longrightarrow \text{Level 3: Human Instructions}$$

1. **Level 1 (Mouse UI)**: Attempt explicit UIA element click via `automation_id`.
2. **Level 2 (Keyboard Shortcut)**: Consult `docs/ableton_keyboard_shortcuts.json` / `scripts/keyboard_shortcuts.py` for a verified factory shortcut keypress.
3. **Level 3 (Human Instructions)**: Fall back to clear, spatial-unambiguous step-by-step instructions for the learner.

> **Direct MCP/LOM calls are NOT a ladder tier.** ... there is no Level 3 "Direct API" rung in `click_by_id()`. The AbletonMCP/LOM bridge ... is a **separate, parallel capability** ... not part of the deterministic `click_by_id()` escalation ladder.
```

Code (`scripts/automate_ableton_task.py`, `click_by_id` docstring, lines ~441–445):

```
NO MCP/LOM TIER HERE, on purpose. This project has no MCP/Remote
Script/MIDI bridge at all; padding in a 4th level for a direct
MCP/LOM call that could never fire here would be dead code, not a
real design. This ladder is scoped to what this file actually has:
3 levels.
```

Both agree: 3 levels, MCP is a separate concern. The plan offered choice (a) "3 levels, MCP is a separate concern" vs (b) "keep 4 levels documented with a not-implemented disclaimer" — the code's own docstring explicitly formalizes the (a) position, so (a) was chosen.

### AC2 — `grep -rn "interaction_idioms.md" .` returns nothing

```
$ grep -rn "interaction_idioms.md" . 2>/dev/null | grep -v "\.git/\|PHASED_PLAN.md\|baseline/\|reports/"
$ echo $?
1
```

Exit 1 (no matches). The only remaining mentions are inside `PHASED_PLAN.md` itself (the plan document, treated as read-only reference per AGENTS.md) and the Phase 0/1 report files, which are records of this work — not code references.

### AC3 — Write-back status stated once, in one obvious place, for all three control types

`scripts/automate_ableton_task.py` lines 74–96, immediately after the module docstring, before any imports:

```
# WRITE-BACK STATUS BY CONTROL TYPE  (single source of truth -- read this
# before writing to ANY control; individual function docstrings below give
# context, this block is the authority)
#
#   CheckBox  -> PROVEN SAFE. set_checkbox_by_id() uses click + verify +
#                retry. This is the ONE proven reference implementation;
#                do not change its write mechanism.
#
#   Slider    -> CONFIRMED TO CRASH ABLETON LIVE ITSELF. Calling
#                RangeValuePattern.SetValue() / ValuePattern.SetValue()
#                on a Slider killed Ableton twice on 2026-08-08 (once via
#                probe_write_back, once via task_set_tempo). Never call
#                SetValue() on a live Slider, for any reason. The only
#                proven-safe write path is double-click + type + Enter,
#                as implemented in task_set_tempo. DISABLED/DANGEROUS.
#
#   ComboBox   -> UNTESTED / NOT WIRED. No write-back path is implemented.
#                ComboBox SetValue() has no confirmed crash but also no
#                proven-safe path; treat as guilty until proven innocent,
#                same isolation discipline as the Slider fix.
```

---

## Regression guard

Re-ran every Phase 0 baseline task plus `--list-tasks` against the throwaway project (Ableton restarted fresh by the human, clean `Untitled` project), diffing byte-for-byte:

```
=== probe_toggle ===          IDENTICAL to baseline
=== idiom_demo ===            IDENTICAL to baseline
=== arm_track ===             IDENTICAL to baseline
=== read_solo_states ===      IDENTICAL to baseline
=== solo_one ===              IDENTICAL to baseline
list-tasks IDENTICAL to baseline
```

All 5 live baseline logs and the task-list JSON are byte-identical to Phase 0. Docs-only changes produced identical runtime output, as required.

Syntax checks:

```
$ python3 -m py_compile scripts/automate_ableton_task.py
py_compile OK
$ bash -n build_runtime_env.sh  →  OK
$ bash -n orchestrate.sh        →  OK
$ bash -n take_shot.sh          →  OK
```

---

## Things that took more than one attempt / notes

- **One restart needed for a clean regression check.** The first regression re-run attempt ran against the leftover project state from Phase 0's `arm_track` (track 0 still armed, monitor set to In). The human opted to run as-is and accept a documented diff, then chose to restart Ableton anyway for a clean byte-for-byte comparison. After the restart (fresh `Untitled`, no `*`), all five logs came back byte-identical. Final recorded result is the clean comparison above; no residual state diffs.
- **Choice (a) vs (b) for the ladder:** picked (a) — relabel to 3 levels — because `click_by_id()`'s own docstring already states the (a) position verbatim ("NO MCP/LOM TIER HERE... 3 levels"), so (b)'s "keep 4 levels with a disclaimer" would have contradicted the code's stated intent.
- **`docs/ableton_ai_educational_risk_framework.md` still contains the old 4-level formula** (line 19) including "Direct MCP/LOM Call", alongside its own caveat that the ladder "excludes non-existent tiers to prevent dead code" (line 17). This doc was NOT edited — Phase 1's explicit action targeted `README.md` only, and AGENTS.md says to treat the plan as read-only rather than expanding scope mid-execution. This is a known residual inconsistency to reconcile in a later phase or by explicit decision: the framework doc's formula contradicts both the code and the now-corrected README.
- **`TASK_REGISTRY["idiom_demo"]` description** still reads "3 of the 6 recurring interaction idioms"; the "6" enumeration exists nowhere else in the repo (only 3 are identifiable/documented). This is a registry string, not a dangling reference, and `--list-tasks` output was required to stay byte-identical to baseline, so it was left untouched here. Flagging for a future phase.
