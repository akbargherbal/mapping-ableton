# context.md — Project Digest

**Purpose of this file:** a standalone summary of what this project is trying to
do, what's actually wrong with it as of this session, and what to do next —
so a new session (or a tired future you) doesn't have to re-derive any of
this from scratch.

---

## 1. What we're actually trying to achieve

This repo hosts **two sibling AI-agent courses** that both teach inside a real,
running Ableton Live 12, but for two different problems:

| | Click-automation tutoring course | Mastering course (the one we're focused on) |
|---|---|---|
| Builder script | `build_runtime_env.sh` | `build_mastering_env.sh` |
| Runtime folder | `../ableton-runtime` | `../suno-mastering-course` |
| Policy file | `ABLETON_AGENT_POLICY.md` → `AGENTS.md` (currently a placeholder, `[PLACEHOLDER]`) | `SUNO_MASTERING_AGENT_POLICY.md` → `AGENTS.md` |
| Teaches | Ableton UI literacy (where things are, how to click) | Mastering an AI-generated (Suno) track: EQ, compression, loudness, stereo |

**The actual learner for the mastering course** (established mid-session,
correcting an earlier wrong assumption of mine): a total novice —
**never used a DAW, no music theory, has never touched Ableton before.**
They have ~600 self-generated Suno tracks (rated 1–5 stars) and want to
clean up / master them.

**What they want from the agent:** a **tour guide and instructor sitting at
their shoulder** — not a Socratic tutor who only asks questions, and not a
system that silently fixes things via API while the learner watches nothing
happen. When they say *"I hear a harsh 'ts-ts' sibilance, how do I remove
it?"*, the agent should help them figure out what's wrong, show them where
to click and how, and verify the fix in real numbers — the way a real
instructor standing next to them would.

---

## 2. What's problematic about `build_mastering_env.sh` right now

**Core contradiction found this session:**

- `SUNO_MASTERING_AGENT_POLICY.md` opens by stating the agent works via
  *"`ableton-mcp-extended`... **and** the pywinauto UIA layer (visible
  clicks, per this repo's escalation ladder in the README)."*
- But `build_mastering_env.sh`'s own header comment says the opposite:
  *"this course does **NOT** use the pywinauto/UIA click-automation stack
  at all"* — and its `FILES[]` whitelist accordingly excludes
  `orchestrate.sh`, `take_shot.sh`, `scripts/automate_ableton_task.py`,
  `scripts/dump_ableton_pywinauto.py`, `scripts/keyboard_shortcuts.py`, and
  `scripts/dumps/control_catalog.json`.

This split made sense under the **wrong assumption** that the mastering
learner already knows how to navigate Ableton and only lacks mastering
knowledge. Given the corrected persona (total DAW novice), the policy file
is the one describing the real need, and the build script's exclusion is a
real gap — a `../suno-mastering-course` runtime built today has no way to
help when "this panel won't appear" or "I don't see EQ Eight anywhere."

**Also found:** the mastering policy admits a second, related gap itself —
Youlean's LUFS meter has no queryable UIA/MCP surface, and the policy notes
*"if/when the vision-model tooling from the mapping-ableton project lands,
this is the first real use case for it"* — i.e., screen-reading for the
mastering course isn't wired up yet either.

---

## 3. What's problematic about our current approach (the deeper issue)

Early in this session the instinct was: *"user needs X, task X is missing
from `automate_ableton_task.py`, therefore go write task X."* This was
flagged, correctly, as **not how a real tutor works** — it turns the agent
into someone who memorizes scripts instead of someone who reasons and
adapts live to whatever's actually in front of the learner.

**The good news, discovered by reading the actual code:** the underlying
write primitives are *already fully generic*:

- `set_checkbox_by_id(window, auto_id, ...)`
- `set_slider_by_id(window, auto_id, value, ...)` — double-click + type +
  Enter, never `SetValue()`
- `set_combobox_by_id(window, auto_id, ...)`

None of these care what the `automation_id` is attached to. They work on
`Transport.Tempo` exactly as well as they'd work on
`TrackView.Device[0].Freq` (EQ Eight's Frequency slider — confirmed present
in `control_catalog.json` today).

**The actual bottleneck is the interface, not the capability:** the only
way to invoke these primitives today is through a fixed
`--task {arm_track, solo_one, solo_tour, set_tempo, ...}` CLI menu
(`argparse` `choices=[...]` in `automate_ableton_task.py`). Every new
teaching moment gets funneled into "add a new named task" instead of
"call the existing generic primitive with a newly-looked-up id." That's the
real thing to fix — not by writing more `task_*` functions, but by exposing
a general entry point (sketched as `call_control(automation_id, action,
value)` in this session) that the agent can drive live, combined with an
**on-demand, narrow lookup** into `control_catalog.json` (never bulk-loaded
into the agent's context — confirmed this is both wasteful and risks the
agent reasoning over stale `bounding_rect` pixel data it shouldn't use).

**Tool roles, clarified this session (audit against the sibilance scenario):**

| Tool | Role | Notes |
|---|---|---|
| `ableton-mcp-extended` (MCP/LOM) | Ground-truth read/verify; also the right way to **load a device**, since Browser drag-and-drop automation is a confirmed permanent gap (no automation_id on list items) | Legitimate Level-3 use, not a philosophy violation |
| `automate_ableton_task.py` primitives | Physically demonstrate a click/drag so the learner watches it happen — the actual pedagogical moment | Should be reachable generically, not just via fixed task names (see above) |
| `orchestrate.sh` / `take_shot.sh` | Screenshot after each action | Feeds both human review and the vision agent |
| Vision agent (OpenCode) | Diagnose *what's currently on screen* — hidden panels, missing views, reading meters with no UIA surface (e.g. Youlean LUFS) | The one tool that can answer "why is this stuck," not currently wired into a fallback rule anywhere |
| `control_catalog.json` | On-demand "does this control exist / is it safe" lookup | Correctly should never be force-fed into context |
| `keyboard_shortcuts.py` | Level-2 fallback + a teaching moment ("next time, press...") | Underused |
| `curriculum_map.md`, `course_outline.txt` | Old/stale | **Do not treat as authoritative** — use `docs/suno-mastering-curriculum.md` and `docs/suno-mastering-course-breakdown.md` instead |

---

## 4. Two concrete findings logged this session (not yet fixed)

1. ~~**Real bug — Groove Pool guard is not actually enforced in code.**~~
   **FIXED this session.** Added a `"groove_pool_toggle"` entry to
   `SHORTCUTS` in `scripts/keyboard_shortcuts.py`, `blocked=True`, noting
   this is a confirmed crash (not a coverage gap like the other blocked
   entries) and should not be casually unblocked even if the upstream
   Ableton bug is fixed. Verified: `load_shortcut("groove_pool_toggle")`
   raises `ShortcutBlocked` by default; a repo-wide grep confirmed
   `keyboard_shortcuts.py` is the only file that ever mentioned Groove
   Pool, so this was the only door that needed closing. See
   `PHASED_PLAN.md` Phase 0 for the verification detail.

2. **Design gap — task-name-only CLI interface.** Described in full in
   §3 above. Fix direction: add a generic invocation path so the agent can
   call the three proven-safe primitives directly with a live-looked-up
   `automation_id`, instead of requiring a new named task per scenario.

(For the record, the *other* crash risk — `SetValue()` on any Slider — **is**
properly guarded already: disabled in code, documented in three places in
`automate_ableton_task.py`, no action needed there.)

---

## 4a. Where the plan lives

The priority order below has been turned into a checkable, resumable
implementation plan: **`PHASED_PLAN.md`** (same folder as this file). It
breaks the work in §5 into six phases (0 through 5), each with its own
task checklist, definition of done, and dependencies, plus a "Current
Status" line at the top to update at the end of every session. If picking
this project back up later, read this file for *why*, then go straight to
`PHASED_PLAN.md` for *what's next*.

## 5. The way forward (in rough priority order)

1. **Decide the mastering runtime's real scope**, given the corrected
   novice persona: does `build_mastering_env.sh` need to become a superset
   that includes the click-automation layer + on-demand catalog access, or
   should the mastering agent lean primarily on vision + MCP + generic
   primitives (per §3) rather than the older task-based click layer?
2. **Fix the Groove Pool guard** (§4.1) — small, low-risk, unambiguous.
3. **Build the generic control-invocation interface** (§4.2) so new
   teaching moments don't require new code — this is the fix that actually
   stops the "memorize scripts" pattern.
4. **Write an explicit decision rule** for when the agent should: physically
   demonstrate (pywinauto), load invisibly (MCP, only where Level 1 is a
   confirmed gap like the Browser), narrate from a screenshot (vision), or
   defer to human instructions (Level 4) — today this is only asserted in
   prose ("per the escalation ladder"), not translated into a concrete
   runtime rule for this persona.
5. **Wire the vision agent into a first-class fallback**: if a pywinauto
   element can't be resolved, or the learner says a panel/view looks wrong,
   take a screenshot and diagnose before improvising.
6. Treat `docs/curriculum_map.md` and `docs/course_outline.txt` as
   deprecated; don't let a future session rediscover and re-trust them.
