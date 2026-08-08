# Project Journal

This document is the continuity thread for this project across working
sessions. It is not a spec and not fixed — it's a chronicle: what we've
figured out, what we've decided (and why), what's still open, and what got
deliberately parked for later. At the start of each session, review this
file (plus whatever other docs are pointed to) before diving into new
discussion, so we pick up from where we actually left off instead of
re-deriving things from scratch.

**How to use this file (for whoever — human or agent — is reading it at
the start of a session):**
- Read the whole thing, most recent entry last.
- Treat "Open threads" as the live to-do list of *ideas*, not code tasks.
- Treat "Parked" items as intentionally not-yet-relevant — don't resurrect
  them just because they're technically interesting.
- Add a new dated entry each session rather than editing old ones, unless
  something earlier turns out to have been wrong — in that case, note the
  correction in the new entry and leave the old one visible, so the
  journal keeps functioning as a real history.

---

## Session 1 — 2026-08-08

### The origin idea

The project started from a piece of wishful thinking: what if there were
a hands-on tutor sitting over your shoulder, moving the mouse and
clicking through Ableton for you, while you watched? OpenCode, connected
via an MCP server to Ableton, with Python/`pywinauto` doing the clicking
— tried on ~8 tasks, and it worked. The mouse moved with precision,
things got clicked, sounds happened. That result is what opened the door
to the current project.

### The first pivot: MCP-only wasn't enough

The very first version of this idea used *only* the MCP server (direct
semantic control of Ableton's Live Object Model). It failed for a
specific, important reason: **it only showed the aftereffects of an
action, never the action itself.** State changes correctly, but the
student never sees *how* — no mouse movement, no visible click, no
procedure to absorb.

This turned out to be diagnostic, not a minor UX complaint: it revealed
what the project actually is. The thing a beginner fears in Ableton
isn't "I don't know what this software does" — it's "I don't know what
to physically do with my hands in this intimidating, unlabeled grid of
controls." That fear lives entirely in the *procedure*, not the
*result*. So the pivot to UIA-based automation (`pywinauto`, real
`click_input()` calls that move the actual cursor) wasn't a technical
upgrade — it was a correction to match the tool to the actual problem.
MCP is being kept, not abandoned, for cases UIA can't handle (e.g.
semantic loads via `load_instrument_or_effect`) — but UIA is the layer
that carries the pedagogical point.

### What the JSON survey files (`scripts/dumps/`, `control_catalog.json`)
### actually are, and why

Underneath the mechanics, there's one problem: the agent is blind. It's
text-only, acting inside something almost entirely visual and spatial.
Without the survey, it has two bad options — guess (risky, live session,
wrong click), or have a human specify every element by hand (defeats the
point, and the human here doesn't know Ableton either).

The JSON catalog solves this by turning an unlabeled collection of
pixels into a set of *named, addressable things* — this object is
`TrackView.Device[0].Freq`, it's a Slider, it lives here. That's the
whole purpose. It's a grounding problem, not really an Ableton problem —
the same kind of problem any agent has acting in a world it can't
perceive directly.

**Who benefits, concretely:**
- *The agent* — acts with actual confidence instead of a plausible guess.
- *The student* — what they watch is real and repeatable, not an agent
  occasionally clicking the wrong thing while narrating past it with
  total confidence (which would be worse than no automation at all).
- *The project owner (not an Ableton or DAW expert)* — gets something
  reviewable. It's possible to sanity-check "does this list of Mixer
  controls make sense" without being able to judge "did the agent make
  the right call live," which isn't independently verifiable by someone
  without domain expertise.

**Coverage reality check (as of this session):** 85/85 native Ableton
devices are well-mapped with usable names. Transport and Mixer sections
are solid. Browser categories (loading sounds/instruments/plugins) are
still `UNMAPPED`. Session View data exists from an earlier survey pass
but isn't yet merged into the consolidated `control_catalog.json` (known
gap, already noted in `coverage_summary.md`).

The improvement priority going forward should be need-driven (what the
early course modules actually require), not "survey everything for
completeness" — the survey is a means, not the goal.

### What the project is actually for (the real reframe of this session)

The project is **not** trying to automate Ableton training end to end.
Some things are and will remain beyond what an AI agent can teach —
judgment calls, taste, "does this mix sound good" — those need a human,
and that's a given, not a gap to be engineered away.

The actual goal: **de-intimidation.** Ableton's UI is on par in
complexity with AutoCAD, 3ds Max, Photoshop, DaVinci Resolve — genuinely
intimidating to a newcomer. The project is a tricycle, not a self-driving
bike: let the student watch ~20 tasks, each performed a few times, until
they stop being afraid of the interface and start recognizing the
*pattern* of how the software wants to be used. The project has done its
job the moment the student becomes a pattern-recognizer of "how pros
think in Ableton" — not once they've mastered Ableton.

This reframe changes what counts as a *good* task to pick, later:

- Not "one task per topic in the course outline" (breadth-first coverage)
- But "tasks that share a recurring interaction idiom" — toggle a
  checkbox, drag a slider, open a device panel, navigate between two
  views — repeated across *different* devices/contexts. A student who's
  watched "open a device, find its main knob, drag it" on EQ, Compressor,
  and Reverb has learned something that transfers, because what they
  actually absorbed is the *grammar* of interacting with any device
  panel — not facts about those three specific devices.

This also suggests **effort should front-load toward early modules**
(navigation, audio basics, MIDI — where the specific fear being treated
actually lives), and get intentionally thinner in later modules
(Mixing, effects) where the interface stops being scary and what's left
is taste — which this project isn't trying to teach anyway.

### Status of the course outline

`docs/course_outline.txt` was generated on the fly with ChatGPT, purely
to have *something concrete to measure against* given the asymmetric
knowledge problem (project owner isn't a DAW/music expert). It is
explicitly **not fixed, not authoritative, and not a spec** — it's a
datum, raw material to mine for structure (modules → lessons/skills →
tasks), not a target to faithfully automate.

The atomic unit is confirmed as: **task = "click X button in Y panel."**
That granularity is correct and stays.

### Open threads (live — pick up next session)

1. **Name the 5–6 recurring interaction idioms** that show up repeatedly
   across Ableton's UI, using the course outline as raw material rather
   than a fixed spec. This was the concrete next step identified this
   session but not yet started (ran out of time).
2. Once idioms are named, map which existing survey coverage (85 mapped
   devices, Transport, Mixer) already supports demonstrating each idiom
   3-4 times across different skins/devices.
3. Decide how much of Modules 1–3 vs 4–7 the automated-tutor layer should
   actually attempt, given the front-loading argument above.

### Parked for later (technical — deliberately not decided yet)

A detailed architecture discussion happened this session covering four
independent axes — worth preserving, but explicitly *not* worth
revisiting until the project is past the "what is this for" stage:

- **Locator resolution timing** — resolve `automation_id`s at lesson
  *authoring* time (baked-in, safer, reviewable offline) vs at lesson
  *run* time (live catalog lookup, more flexible, riskier/ambiguous).
  Leaning: resolve at authoring time, re-validate cheaply at run time.
- **Agent improvisation vs fixed script** — fully scripted narration+
  action, vs agent freely deciding what to click, vs a hybrid (fixed
  step/order/target, generated narration only). Leaning: hybrid — keeps
  the risky part (which control gets touched) reviewable by a non-expert
  project owner, keeps the pedagogical part flexible.
- **Verification policy** — optimistic (click and assume), read-back
  after every step (slower, but doubles as a teaching beat: "let's
  confirm — yes, Solo is now on"), escalate-on-mismatch per the ladder
  already documented in `ableton_ai_educational_risk_framework.md`.
  Leaning: read-back + escalate, since it's consistent with the
  Non-Halt Imperative already designed into that framework.
- **UIA vs MCP as the default action path** — UIA-first (matches "watch
  the process" but is the fragile layer: window state, DPI, version
  drift) vs MCP-first-with-UIA-as-visible-demonstration-only (MCP is the
  source of truth for state, UIA click is cosmetic/pedagogical rather
  than load-bearing). Leaning: MCP-first is more realistic near-term
  given Browser categories are still unmapped and some UI chrome is
  noisy; UIA-as-primary only where coverage is already proven clean
  (native devices, Mixer, Transport).

None of these are decided. They're notes-to-self for when the project is
back in "build it" mode rather than "figure out what it is" mode.

---

<!-- Next session: add a new "## Session N — YYYY-MM-DD" entry below this line. -->
