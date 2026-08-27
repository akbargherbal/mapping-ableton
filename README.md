# Ableton Live 12 AI Tutor & UI Grounding Suite

An AI-agent-driven interactive tutoring and UI automation system for **Ableton Live 12**, built specifically to assist novice music creators (e.g., AI music generators using Suno/Udio) in learning how to edit, arrange, and polish music inside a professional Digital Audio Workstation (DAW).

---

## 💡 Core Philosophy & Purpose

### De-Intimidation Over End-to-End Automation

Ableton Live's interface is as complex as professional CAD or 3D modeling software. A novice creator's primary barrier isn't a lack of concepts—it's **procedural fear** when facing an unlabeled, dense grid of controls.

This system acts as a **procedural "sidecar" tutor** (a tricycle, not a self-driving bike):

- **Demonstrates Procedure, Not Just State**: Rather than silently altering Ableton's state via API calls behind the scenes, the agent moves the actual mouse cursor and interacts with UI controls (`pywinauto` / UI Automation) so the student absorbs the physical workflow.

### Two Sibling Courses

This repo hosts **two separate AI-agent courses** that both teach inside a real, running
Ableton Live 12, sharing the same click-automation code but built for different learners
and different curricula:

| | Click-automation UI-grounding course (this README) | Mastering course |
|---|---|---|
| Builder script | *(removed — no packaging path currently)* | `build_mastering_env.sh` |
| Runtime folder | `../ableton-runtime` (unbuildable until a builder script exists) | `../suno-mastering-course` |
| Policy file | *(removed — was a placeholder, never written)* | `SUNO_MASTERING_AGENT_POLICY.md` → `AGENTS.md` |
| Teaches | Ableton UI literacy — where things are, how to click | Mastering an AI-generated (Suno) track: EQ, compression, loudness, stereo |
| Curriculum reference | `docs/curriculum_map.md`, `docs/course_outline.txt` | `docs/suno-mastering-course-breakdown.md`, `docs/suno-mastering-curriculum.md` |

> `ABLETON_AGENT_POLICY.md` and `build_runtime_env.sh` were deleted
> (2026-08-27) — the former was a 13-byte placeholder that was never
> written, the latter its now-orphaned builder script. The
> click-automation course's reference docs (`docs/curriculum_map.md`,
> `docs/course_outline.txt`, `docs/control_catalog_usage_guide.md`, the
> code under `scripts/`, `orchestrate.sh`, `LABS/`) are untouched and still
> describe real, verified work — the course just has no packaged runtime
> build path right now.

The rest of this README documents the **click-automation UI-grounding course** above. If
you're working on the mastering course instead, start with `context.md` (the *why*) and
`PHASED_PLAN.md` (the *what's next*), not this file.

---

## 🏗️ System Architecture

The project bridges text-based AI agents with Ableton's graphical interface via a hybrid two-layer architecture:

```
                                    +───────────────────────────+
                                    |   AI Agent / Orchestrator |
                                    +─────────────┬─────────────+
                                                  │
                          ┌───────────────────────┴───────────────────────┐
                          │                                               │
                          ▼                                               ▼
            +───────────────────────────+                   +───────────────────────────+
            |       Visual Layer        |                   |      Semantic Layer       |
            |        (pywinauto)        |                   |   (ableton-mcp-extended)  |
            +───────────────────────────+                   +───────────────────────────+
            | • Moves physical mouse    |                   | • LOM direct queries      |
            | • Real UIA tree walks     |                   | • Device loading          |
            | • Pedagogical focus       |                   | • Ground-truth state      |
            +─────────────┬─────────────+                   +─────────────┬─────────────+
                          │                                               │
                          └───────────────────────┬───────────────────────┘
                                                  │
                                                  ▼
                                    +───────────────────────────+
                                    |   Ableton Live 12 Host    |
                                    +───────────────────────────+

```

### 1. Visual/Demonstrative Layer (`pywinauto` / Windows UIA)

Performs visible clicks, drags, and UI navigation using target `automation_id`s. This is the primary pedagogical interface that the student watches on screen.

### 2. Semantic/LOM Layer (`ableton-mcp-extended`)

A TCP socket bridge connecting the agent to Ableton's Live Object Model (LOM) via a custom Python Remote Script (`AbletonMCP`). Used for background verification, state reading, and heavy operations (such as loading native instruments/effects onto tracks).

### 3. UI Grounding & Control Catalog (`control_catalog.json`)

To prevent the agent from guessing visual pixel coordinates, the codebase includes a static, offline survey index (`scripts/dumps/control_catalog.json`) generated by probing Ableton's UI Automation tree. It maps native devices, mixer channels, view sections, and panels to stable `automation_id` strings.

---

## 🛡️ Multi-Tier Escalation Ladder

To uphold the **Non-Halt Imperative** (failures must never stall a student's session), deterministic UI actions fall through a 4-level escalation ladder, ordered by how directly the student can see and later repeat the action themselves — from most to least visible/learnable, with Human Instructions deliberately last because it's the most disruptive to the "learn by watching" flow, not the most trustworthy:

$$\text{Level 1: Mouse UI Click} \longrightarrow \text{Level 2: Keyboard Shortcut} \longrightarrow \text{Level 3: MCP/LOM Call} \longrightarrow \text{Level 4: Human Instructions}$$

1. **Level 1 (Mouse UI)**: Attempt explicit UIA element click via `automation_id`.
2. **Level 2 (Keyboard Shortcut)**: Consult `docs/ableton_keyboard_shortcuts.json` / `scripts/keyboard_shortcuts.py` for a verified factory shortcut keypress.
3. **Level 3 (MCP/LOM Call)**: Fall back to the AbletonMCP/LOM bridge (see the Semantic Layer in [System Architecture](#system-architecture)) to keep the lesson moving without guessing at pixels — invisible to the student, but preferable to stalling.
4. **Level 4 (Human Instructions)**: Last resort. Clear, spatial-unambiguous step-by-step instructions for the learner.

This is the policy target, matching `docs/ableton_ai_educational_risk_framework.md` (the authoritative source for the full ladder/fallback rationale — this README section is a summary, not the source of truth).

> **Implementation status:** `click_by_id()` in `scripts/automate_ableton_task.py` currently implements Levels 1, 2, and 4 — the Level 3 MCP/LOM fallback rung is **not yet wired into the deterministic escalation path**. Today, the AbletonMCP/LOM bridge is used as a separate, parallel capability by the agent layer (state reads, device loading), not as an automatic fallback inside `click_by_id()`. Wiring it in as a true Level 3 rung is an open build task, not yet done.

---

## ✍️ Write-back status by control type

Single source of truth lives in the `WRITE-BACK STATUS` block at the top of
`scripts/automate_ableton_task.py`; this is the same information, stated once here.

| Control type | Status | Write mechanism (all verified) |
|---|---|---|
| CheckBox | ✅ **Proven** | `set_checkbox_by_id()` — click + read-back verify + retry. Reference implementation. |
| Slider | ✅ **Proven** | `set_slider_by_id()` — double-click + type + Enter. ⚠️ **`RangeValuePattern.SetValue()` / `ValuePattern.SetValue()` is CONFIRMED to crash Ableton Live itself (twice, 2026-08-08) and is permanently disabled — never call it.** |
| ComboBox | ✅ **Proven** | `set_combobox_by_id()` — click-to-open + click-item on the `ChooserPopUp` menu. No pattern-based setter used. |

The currently proven write surface (the controls you can hand to a lesson and expect
to actually change) is listed in `docs/curriculum_map.md` → "Proven-write controls".
Exercised by `arm_track`, `solo_one`, `solo_tour`, `set_tempo`, `probe_toggle`, and
`idiom_demo`.

**Beyond the fixed `--task` menu:** `automate_ableton_task.py` also exposes a generic
invocation path — `call_control(window, automation_id, action, value=...)`, or
`--control <automation_id> --action <click|set> --value <v>` on the CLI — that dispatches
to whichever of the three write mechanisms above matches the control's *live* UIA type.
This lets an agent operate any control it looks up at runtime (e.g. a specific device
parameter) without a new named `--task` having to exist for it first. It's mutually
exclusive with `--task` and carries the same guardrails: only the three proven control
types above are supported, and `SetValue()` is never called. See `SUNO_MASTERING_AGENT_POLICY.md`
for the fuller write-up of this path (it was built for that course, but the code itself
lives here and either course's agent can use it).

---

## 🎬 Orchestration (screenshot-per-action)

`orchestrate.sh` runs **one single-action task** against live Ableton and takes a
screenshot after each `action_start` / `action_result` `EVENT:` line, so every click
gets its own image:

```bash
bash orchestrate.sh LABS/MOD_02_2026-08-09/creating-drum-loop arm_track --tracks 0
```

- Writes numbered, labeled PNGs into `LABS/<lab_dir>/` (e.g. `01_01_track_0_arm.png`),
  driven by a FIFO pipeline so the capture happens at the moment each step completes.
- Allowed tasks: `arm_track set_tempo probe_toggle probe_solo_transport
  probe_keyboard_activator read_solo_states solo_one`. `solo_tour` is excluded —
  use `solo_one` in a loop instead so each track gets its own screenshot.
- Real action requires the task to run `--live` (orchestrate.sh passes it itself —
  do **not** add `--live` to `TASK_ARGS` for the `solo_one` path).
- Runs a **drift check** first (`--list-tasks` schema version must match
  `EXPECTED_SCHEMA_VERSION`), and aborts before touching live Ableton on mismatch.
- `take_shot.sh` auto-restores a minimized window, brings it to front, and
  maximizes it before capturing — proven to recover from a minimized state.

---

## 📊 Current UI Survey & Catalog Status

The offline survey (`control_catalog.json`) provides verified technical grounding across **105 UI Contexts**:

| Survey Category                      | Status                        | Coverage Details                                                                                                                                                                                   |
| ------------------------------------ | ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Phase A (Native Devices)**         | ✅ **MAPPED**                 | **85/85** native Ableton instruments, audio effects, and MIDI effects mapped with stable `automation_id` parameters.                                                                               |
| **Phase B (Plug-Ins)**               | ✅ **MAPPED**                 | Verified 0 third-party plugins installed; category confirmed empty.                                                                                                                                |
| **Phase C (Value Patterns)**         | ✅ **MAPPED**                 | Probed UIA value patterns across 2,811 sliders and knobs (`RangeValuePattern` / `ValuePattern`).                                                                                                   |
| **Phase D (Arrangement View)**       | ✅ **MAPPED**                 | Timeline, loop brace, track header manager, arrangement controls, and master track.                                                                                                                |
| **Phase E (Browser Categories)**     | 🟡 **UNMAPPED**               | Top categories (Sounds, Instruments, Drums, Effects, Plug-Ins) sampled; item list items require dynamic text matching due to empty `automation_id`s. No reliable reference available yet — `docs/curriculum_map.md` marks Browser-dependent topics as honest gaps rather than guessing IDs. |
| **Phase F (Tracks & Special Views)** | ✅ **MAPPED**                 | Return tracks (A-Reverb, B-Delay), Group/folded tracks, Master track mixer, and Clip Detail view.                                                                                                  |
| **Phase G (Main Window Views)**      | ✅ **MAPPED** / 🛑 **OPAQUE** | File Manager, Undo History, Help View, Tuning System mapped. **Groove Pool & Info View marked OPAQUE** (Groove Pool triggers a known Ableton `ucrtbase.dll` crash—blocked from automated opening). |

---

## 📁 Repository Structure

```
.
├── AGENTS.md                   # Operating instructions for the agent driving this repo
├── SUNO_MASTERING_AGENT_POLICY.md # Mastering course policy (copied to AGENTS.md in ../suno-mastering-course)
├── context.md                  # Mastering course: project digest — read this first for *why*
├── PHASED_PLAN.md              # Mastering course: resumable implementation plan — *what's next*
├── build_mastering_env.sh      # Assembles the mastering-course runtime folder (whitelist)
├── orchestrate.sh              # Screenshot-per-action orchestration of a single task
├── take_shot.sh                # Capture the Ableton window (auto-restore/focus/maximize)
├── LABS/                       # Orchestration output (real screenshots from live runs)
├── docs/
│   ├── course_outline.txt      # 20-hour curriculum outline for AI creators (click-automation course)
│   ├── curriculum_map.md       # Lesson topic → automation_id reference layer (click-automation course)
│   ├── suno-mastering-course-breakdown.md # Authoritative mastering-course lesson spec (Lessons 1-10)
│   ├── suno-mastering-curriculum.md # Leaner 6-module mastering-course operating version
│   ├── mastering_progress.md  # Mastering-course session log template (date/track/lesson/rating)
│   ├── ableton_ai_educational_risk_framework.md # Risk/fallback policy (ladder + safety rules)
│   ├── control_catalog_usage_guide.md # Practical reference for using control_catalog.json
│   ├── opencode-ableton-mcp-setup.md  # Setup guide for OpenCode (WSL2) to Windows Ableton MCP
│   ├── ableton_keyboard_shortcuts.json # Windows/Mac default Ableton Live 12 shortcut index
│   ├── live12-manual-en.pdf   # Official Ableton Live 12 manual (local reference, not versioned — may be absent)
│   └── archived/v004/         # Phased plan, post-fix plan, survey docs, baseline, reports
└── scripts/
    ├── automate_ableton_task.py # Task automation, UIA click runner, and the generic
    │                             # --control/call_control() invocation path (see below)
    ├── dump_ableton_pywinauto.py # Core tree-walking and JSON window dumper
    ├── dump_ableton_states.py    # Automated multi-state/view dumper
    ├── update_catalog.py         # Catalog generator merging raw dumps into control_catalog.json
    ├── survey_value_patterns.py  # Phase C UIA value-pattern inspection tool
    ├── keyboard_shortcuts.py     # Programmatic lookup for Level-2 shortcut escalation
    ├── keyboard_shortcuts.md     # Human-readable shortcut reference
    ├── grep_dump.py              # Search utility for inspecting raw JSON UI dumps
    └── dumps/                    # Raw UI dumps & control_catalog.json (the survey index)
```

> **`scripts/dumps/` is the survey index, not repo-root `dumps/`.** All catalog paths
> below use `scripts/dumps/control_catalog.json`.

---

## ⚙️ Environment Setup

### System Requirements

- **OS**: Windows 10/11 (Native or WSL2 with Windows interop).
- **DAW**: Ableton Live 12+ Suite.
- **Python**: Python 3.10+ (must be executable as `python` or `python.exe`).

### 1. Python Dependencies

Install required packages into your Windows Python environment:

```bash
pip install pywinauto psutil "mcp[cli]>=1.3.0" python-dotenv
```

### 2. WSL2 Interop Configuration (If running from WSL)

When working within WSL2, Ableton runs on the Windows host while the repository can reside in WSL.

- **Interpreter Invocation**: Execute Windows Python from WSL using `python.exe`:
  ```bash
  python.exe scripts/dump_ableton_pywinauto.py
  ```
- **Directory Constraint**: Always run scripts from inside `scripts/` (or pass `--out-dir scripts/dumps`), as default dump outputs write relative to the current working directory.

### 3. AbletonMCP Control Surface Setup

1. Clone `ableton-mcp-extended` into your environment.
2. Copy the `AbletonMCP` folder from `AbletonMCP_Remote_Script/` to Ableton's Remote Scripts directory:
   `C:\Users\<User>\Documents\Ableton\User Library\Remote Scripts\AbletonMCP`
3. Launch Ableton Live 12 $\rightarrow$ **Settings** $\rightarrow$ **Link, Tempo & MIDI** $\rightarrow$ Set **Control Surface** to `AbletonMCP` (Input/Output set to `None`).

---

## 🚀 Quick Start & Diagnostic Commands

### Sanity-Check Window Reachability

To verify that `pywinauto` can locate and attach to the running Ableton Live window:

```bash
cd scripts
python.exe dump_ableton_pywinauto.py --no-print
```

### Probe Control Patterns for a Device

To check UI Automation value patterns (`RangeValuePattern` / `ValuePattern`) on a mapped device:

```bash
python.exe survey_value_patterns.py --json dumps/device_EQ-Eight.json
```

### Rebuild the Master Control Catalog

To re-flatten raw dump JSON files into the master catalog (`scripts/dumps/control_catalog.json`):

```bash
python.exe update_catalog.py --dumps-dir dumps
```

---

## 🛑 Critical Operating Rules & Safety Guardrails

1. **Window Virtualization**: Ableton's UI virtualizes elements—controls that are off-screen, minimized, or backgrounded do not exist in the UIA tree. **Always run automation and dumps with the window maximized and focused** (`ensure_window_ready()`).
2. **Fresh Tree Walks**: UI control handles must **never be cached** across actions or delays. Every click or read must execute a fresh tree walk (`resolve()`) to avoid stale-handle errors.
3. **Track-Selection Blindness Guard**: UIA cannot natively determine which track is currently focused in Ableton. Track-scoped shortcuts that rely on track selection (e.g., `S` for Solo, `C` for Arm) are flagged `blocked=True` in `keyboard_shortcuts.py` to prevent modifying the wrong track. Positional shortcuts (`F1`–`F8` for Track Activators 1–8) are unblocked.
4. **Groove Pool Safety Block**: Opening the Groove Pool panel (Ctrl+Alt+6) triggers an upstream stack overrun crash (`0xc0000409` in `ucrtbase.dll`) in Ableton Live 12. Automated scripts are strictly prohibited from toggling the Groove Pool panel.
5. **Host-Process Liveness Check**: every write path (`resolve()`, the universal chokepoint every click/set/verify goes through) checks the Ableton process is still actually running — via the OS, not by inferring it from a missing UIA control — before doing any work. If the process is confirmed gone, `AbletonProcessGone` is raised immediately and a distinct `host_crashed` event is emitted, instead of retrying or escalating against a dead window handle. See `get_ableton_pid()` / `is_ableton_alive()` / `require_ableton_alive()` in `scripts/dump_ableton_pywinauto.py`. Requires `psutil`.

---

## 📄 License & Attribution

This project is configured as an educational automation framework for Ableton Live 12.

- Uses `pywinauto` for Windows UI Automation.
- Extended from `uisato/ableton-mcp-extended` for Ableton LOM MCP bridging.
