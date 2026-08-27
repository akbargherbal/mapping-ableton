# context.md — Project Digest

**Purpose of this file:** a standalone summary of what we're trying to do,
what's actually wrong with `SUNO_MASTERING_AGENT_POLICY.md` today, and what
to do next — so a new session doesn't have to re-derive any of this from
scratch. This file replaces the previous `context.md` entirely; that one
documented an earlier round of fixes (Phase 0–5 in the old `PHASED_PLAN.md`)
that are no longer the active problem. Read this file for *why*, then go to
`PHASED_PLAN.md` for *what's next*.

---

## 1. What we're actually trying to achieve

This repo hosts **two sibling AI-agent courses** that both teach inside a
real, running Ableton Live 12. This file is only about the **mastering
course** — teaching a total novice (never used a DAW, no music theory, has
never touched Ableton) how to master their own AI-generated (Suno) tracks.
The agent acts as a tour guide sitting at their shoulder, not a Socratic
tutor and not a silent auto-fixer.

The policy file the agent actually reads at runtime is
`SUNO_MASTERING_AGENT_POLICY.md` → shipped as `AGENTS.md`.

---

## 2. The actual problem this session identified

`SUNO_MASTERING_AGENT_POLICY.md` had grown to ~300 lines and was still
growing, and it was hard to even finish reading it in one pass. The cause
wasn't missing content — it was **historical narrative and redundant detail
baked into an operating document**:

- Cross-references to dev-only files the runtime agent never has
  (`PHASED_PLAN.md`, `README.md`, `context.md`, `.gitignore`, git
  "checkout" language).
- Internal build-plan bookkeeping leaking into prose the agent has to read
  every session (`"Phase 2, now built"`, `"Phase 4 wiring"`).
- **Investigation history standing in for a plain instruction.** Instead of
  "load devices through MCP," the file said "load devices through MCP
  because Browser drag-and-drop was surveyed in Phase E and found to have
  no automation_id on list items." The agent doesn't need the survey
  history to follow the rule.
- **The same crash re-explained three separate times** (in the tooling
  bullet, in the escalation rule, and again in a dedicated "Vision
  Fallback" section), each time with more forensic detail
  (`0xc0000409`, `ucrtbase.dll`, fault-bucket matching) — for a control
  (Groove Pool) that **isn't even part of this curriculum** and was never
  going to come up.
- An overspecified, numbered "Screenshot-and-Diagnose" procedure that
  asserted things about how the agent's own vision capability is invoked
  (`"you are the vision agent... not a second process"`) — narrating
  internal agent-routing that isn't this policy's business to describe at
  all, since that's OpenCode's concern, not this document's.
- Sections carrying detail the agent doesn't need to operate: exact
  frequency ranges and tool explanations in "Learner Profile" that just
  duplicate what's already authoritative in the curriculum docs, and a
  full "Progress Tracking" section built around a persistent session log
  the actual workflow doesn't use (sessions are stateless; the learner
  just starts a conversation with whatever track and symptom they're
  looking at that day).

**The deeper diagnosis, reached by the end of this session:** the crash
narrative in the policy file isn't the root problem — it's a symptom. The
`groove_pool_toggle` entry in `scripts/keyboard_shortcuts.py` is *callable
by design*, gated only by a boolean flag (`blocked=True`) and a generic
`allow_blocked=True` override that also serves ordinary, harmless
"not-built-yet" gaps (`monitoring_buttons`, `launch_selected_slot`). Because
the crash-risk action and the harmless gaps share one mechanism, guarding it
requires prose — comments, docstrings, and policy paragraphs all repeating
"please don't." **If a control shouldn't be reachable at all, the fix is to
not expose a call path for it, not to expose it and then write increasingly
detailed warnings not to use it.** (Division-by-zero analogy from this
session: don't hand someone a "0" button and then explain at length why
pressing it is a bad idea — don't offer the button.)

This reframes the actual fix as **code-level, not just prose-level**:
`SUNO_MASTERING_AGENT_POLICY.md` can only be permanently debloated once the
things it's currently narrating around no longer need narrating around.

---

## 3. Decisions made this session (current, supersedes anything earlier)

- **Groove Pool is not part of the mastering curriculum**, confirmed by
  grepping `docs/suno-mastering-course-breakdown.md` and
  `docs/suno-mastering-curriculum.md` — zero mentions. It only exists in
  this policy file because it's a shared-codebase safety concern inherited
  from the sibling click-automation course. It should not be a standing
  callout in the mastering policy at all once the code-level fix (below)
  removes the call path.
- **The Youlean LUFS screenshot workaround is genuinely needed** — LUFS/
  loudness is a real curriculum topic (`docs/suno-mastering-curriculum.md`,
  the loudness/limiting module) — but it should be one short instruction,
  not a multi-step procedure with a trigger taxonomy.
- **Code-level fix identified, not yet applied (deferred to next
  session):** delete the `groove_pool_toggle` entry from `SHORTCUTS` in
  `scripts/keyboard_shortcuts.py` entirely, so `load_shortcut(
  "groove_pool_toggle")` raises a plain `KeyError` ("this isn't a thing"),
  the same as any unknown label — not a special `ShortcutBlocked` exception
  carrying a paragraph of justification. The generic `allow_blocked=True`
  mechanism stays as-is for the legitimate, harmless gap entries; Groove
  Pool just stops being a member of that group.
  - **Explicitly out of scope:** `scripts/dumps/control_catalog.json` and
    `scripts/dumps/section_Groove-Pool.json`. These are static reference
    data, not executable gates — leave them exactly as they are. The
    `"status": "OPAQUE"` field and its crash-incident notes are fine to
    keep as historical record in the data file; the problem was only ever
    the *callable* guard plus the *prose* narrating it, not the data.
- **Escalation logic simplified and de-jargoned:** dropped the borrowed
  "Level 1/2/3/4" labels and internal exception class names
  (`LookupError`, `EscalationExhausted`, `UnsupportedControlType`) from the
  policy prose — those are implementation details, not something the agent
  needs to reason about in plain instructions.
- **"Already demonstrated once → don't demonstrate again" rule relaxed.**
  Previous wording was a hard rule. New instruction: keep demonstrating
  again if the learner actually asks to see it again; don't force them to
  do it solo just because the idiom came up once before.
- **"Learner Profile" section needs trimming**, not just leak-removal —
  domain specifics like exact frequency ranges and what `matchering` is
  belong in the curriculum docs (which are already the authoritative,
  detailed source) and shouldn't be duplicated in the policy file's
  persona summary.
- **"Progress Tracking" section removed entirely, along with
  `mastering_progress.md`** as a concept the policy prescribes. Sessions
  are stateless by design — the learner starts a session by just describing
  the track and the symptom ("this Suno track, 3/5 stars, starts fine but
  gets muddy after 2 minutes..."), not by consulting a log. This has a
  knock-on effect not yet resolved: `build_mastering_env.sh` currently
  creates and preserves `docs/mastering_progress.md` as a runtime artifact
  (see its own comments, lines ~147–155) — that build-script behavior needs
  to be revisited once the policy no longer references the file. Not done
  this session.
- **`KNOWN_ISSUES.md` is being repurposed.** Previously it only accepted
  *already-confirmed, already-fixed-or-permanent* problems, and explicitly
  excluded anything "already named in `AGENTS.md`" (see
  `docs/MASTERING_COURSE_KNOWN_ISSUES.md`, its "What does NOT qualify"
  section, which names Groove Pool as an example of something to **not**
  log because it's already documented elsewhere). That exclusion is now
  backwards: once the policy file stops pre-declaring things broken, this
  log becomes the **only** place such things get tracked — as an
  open investigation (suspected cause → confirm or refute → root cause →
  fix), not a settled-facts list. `docs/MASTERING_COURSE_KNOWN_ISSUES.md`
  itself needs a rewrite to reflect this; not done this session — see
  `PHASED_PLAN.md`.

---

## 3a. Decision made in a later session (2026-08-27): removed the sibling course's dead build path

`ABLETON_AGENT_POLICY.md` (a 13-byte `[PLACEHOLDER]`, never actually
written) and `build_runtime_env.sh` (its now-orphaned builder script) have
been **deleted**. They were themselves a small instance of the same
disease diagnosed in §2 above — a policy file that never got written, and
a build script whose only job was to copy that placeholder into a runtime
folder, both surviving purely as things other files cross-referenced ("same
policy as `build_runtime_env.sh`," "copied to `AGENTS.md` in
`../ableton-runtime`").

**Scope of this cleanup, explicitly:** only those two files. The rest of
the click-automation course's footprint — `orchestrate.sh`, `LABS/`,
`docs/course_outline.txt`, `docs/curriculum_map.md`,
`docs/control_catalog_usage_guide.md`,
`docs/ableton_ai_educational_risk_framework.md`, `docs/archived/v004/` —
was considered and deliberately **left in place** (a broader removal was
offered and declined). `README.md` was updated to note the deletion and
mark the click-automation course as currently unpackaged (no builder
script), rather than pretending it still has one. `build_mastering_env.sh`'s
comments that referenced `build_runtime_env.sh` by name were also cleaned
up so the mastering course's live build script doesn't point at a deleted
file.

This does not change anything in §3 above or the phases in
`PHASED_PLAN.md` — Groove Pool, `KNOWN_ISSUES.md`, and the
`SUNO_MASTERING_AGENT_POLICY.md` rewrite are unaffected and still the next
real work.

---

## 4. Where the plan lives

`PHASED_PLAN.md` (same folder) turns §3 above into a checkable, resumable
sequence, in dependency order: the code-level fix has to land before the
policy rewrite can actually stop narrating around it, and the Known-Issues
doc rewrite should land alongside the policy rewrite since they're meant to
work as one feedback loop (a suspected crash gets tried, gets logged if
confirmed, and the *policy* never needs to carry the story — only the log
does).
