#!/usr/bin/env bash
# build_mastering_env.sh — assemble a self-contained runtime folder for the
# "Mastering Suno AI Music in Ableton" course.
#
# SCOPE DECISION (see context.md §2 and PHASED_PLAN.md Phase 1 for the full
# reasoning): this course's learner is a total DAW novice, not just a
# mastering novice -- never used a DAW, no music theory, has never touched
# Ableton. They need help finding their way around Ableton's UI, not just
# audio-mastering judgment. So, unlike the original version of this script,
# this runtime IS a hybrid:
#
#   INCLUDED  -- the click-demonstration primitives (automate_ableton_task.py
#                + its hard deps), the control_catalog.json ground-truth
#                reference (consulted on-demand/narrowly by scripts, never
#                bulk-loaded into the agent's own context), and take_shot.sh
#                for ad hoc screenshot capture.
#   EXCLUDED  -- orchestrate.sh. That script wraps the fixed --task registry
#                in a screenshot-per-action pipeline that writes numbered
#                PNGs to LABS/<lab_dir>/ -- built for the sibling
#                click-automation course's pre-planned, provable lesson
#                steps. This course's tutoring is live and conversational,
#                not a pre-scripted task list, so that pipeline doesn't fit.
#
# IMPORTANT CAVEAT (as of this decision): automate_ableton_task.py's write
# primitives (set_checkbox_by_id / set_slider_by_id / set_combobox_by_id)
# are generic, but the ONLY way to invoke them today is through the fixed
# --task CLI menu (arm_track, solo_one, set_tempo, ...) -- none of which
# touch device parameters like an EQ Eight band. Live device-parameter
# demonstration (e.g. notching a band) is NOT yet possible through this
# runtime until the generic control-invocation interface (PHASED_PLAN.md
# Phase 2) is built. Until then, SUNO_MASTERING_AGENT_POLICY.md's tooling
# section should be read as describing what EXISTS, not a claim that every
# device control is already reachable.
#
# WHITELIST, not blacklist — same policy as build_runtime_env.sh: only files
# listed in FILES[] below ever leave this repo.
#
# Usage:
#   ./build_mastering_env.sh [target_dir]
#   target_dir defaults to a sibling folder: ../suno-mastering-course
#
# Point OpenCode's working directory at <target_dir> for the mastering
# course. Re-run any time SUNO_MASTERING_AGENT_POLICY.md or the whitelisted
# docs/scripts change — straight overwrite of those, but mastering_progress.md
# in the target is never touched once it exists (session log, not a build
# artifact), and LABS/ / scripts/dumps/ raw dump files are preserved if
# pre-existing, same as build_runtime_env.sh's policy.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-$SCRIPT_DIR/../suno-mastering-course}"

# --- The whitelist -----------------------------------------------------
# Everything the mastering-instructor agent needs. Per the Phase 1 scope
# decision above: the mastering curriculum docs/setup guide, PLUS the
# click-demonstration layer (minus orchestrate.sh) and the on-demand
# catalog reference -- NOT the fixed screenshot-per-action pipeline that
# belongs to the sibling click-automation course.
FILES=(
  "docs/suno-mastering-course-breakdown.md"   # authoritative lesson spec
  "docs/suno-mastering-curriculum.md"         # leaner 6-module operating version
  "docs/opencode-ableton-mcp-setup.md"        # ableton-mcp-extended setup — the
                                               # only external dependency this
                                               # course has; included so the
                                               # target folder is buildable
                                               # without the main repo for reference
  "take_shot.sh"                              # ad hoc screenshot capture (window
                                               # restore/focus/maximize) for the
                                               # vision-agent fallback described in
                                               # PHASED_PLAN.md Phase 4 -- NOT bundled
                                               # with orchestrate.sh's per-action
                                               # pipeline, which stays excluded
  "scripts/automate_ableton_task.py"          # click-demonstration primitives
                                               # (set_checkbox_by_id / set_slider_by_id
                                               # / set_combobox_by_id). CAVEAT: only
                                               # reachable today via the fixed --task
                                               # CLI (arm/solo/tempo) -- device-param
                                               # demonstration (e.g. EQ Eight) needs
                                               # PHASED_PLAN.md Phase 2's generic
                                               # interface, not yet built.
  "scripts/dump_ableton_pywinauto.py"         # hard dep of automate_ableton_task.py
  "scripts/keyboard_shortcuts.py"             # hard dep of automate_ableton_task.py;
                                               # also the Level-2 fallback lookup --
                                               # note groove_pool_toggle is a
                                               # PERMANENTLY blocked entry in here,
                                               # see the file itself, do not override
  "scripts/dumps/control_catalog.json"        # ground-truth "does this control
                                               # exist / is it safe" reference.
                                               # Consult narrowly/on-demand (e.g. one
                                               # grep for one device) -- never load
                                               # this whole file into the agent's own
                                               # conversation context
)
# Optional whitelist -- unlike FILES[] above, a missing entry here is a
# warning, not a FATAL. docs/live12-manual-en.pdf is local-only reference
# material (see .gitignore), so it legitimately may not exist on every dev
# checkout. Copied through when present so the mastering agent can consult
# it as ground truth per SUNO_MASTERING_AGENT_POLICY.md's tooling section.
OPTIONAL_FILES=(
  "docs/live12-manual-en.pdf"
)
POLICY_SRC_NAME="SUNO_MASTERING_AGENT_POLICY.md"
POLICY_DEST_NAME="AGENTS.md"
# Same dev-name/runtime-name split as build_runtime_env.sh, and for the same
# reason: an assistant auditing THIS dev repo must not misread the mastering
# instructions as being directed at itself. Only in the runtime folder is it
# renamed to AGENTS.md, where OpenCode auto-loads it for the agent under test.
# -------------------------------------------------------------------------

mkdir -p "$TARGET"
echo "[build] target: $TARGET"

policy_src="$SCRIPT_DIR/$POLICY_SRC_NAME"
if [ ! -f "$policy_src" ]; then
  echo "[build] FATAL: policy file missing from dev repo: $POLICY_SRC_NAME" >&2
  exit 1
fi
cp -f "$policy_src" "$TARGET/$POLICY_DEST_NAME"
echo "  copied: $POLICY_SRC_NAME -> $POLICY_DEST_NAME"

for f in "${FILES[@]}"; do
  src="$SCRIPT_DIR/$f"
  if [ ! -f "$src" ]; then
    echo "[build] FATAL: whitelisted file missing from dev repo: $f" >&2
    exit 1
  fi
  mkdir -p "$TARGET/$(dirname "$f")"
  cp -f "$src" "$TARGET/$f"
  echo "  copied: $f"
done

for f in "${OPTIONAL_FILES[@]}"; do
  src="$SCRIPT_DIR/$f"
  if [ ! -f "$src" ]; then
    echo "  skipped (not present in dev repo, optional): $f"
    continue
  fi
  mkdir -p "$TARGET/$(dirname "$f")"
  cp -f "$src" "$TARGET/$f"
  echo "  copied (optional): $f"
done

# mastering_progress.md is a runtime session log, not a build artifact — copy
# the template only if the target doesn't already have one going, so a
# re-run of this script never clobbers real session history.
progress_target="$TARGET/mastering_progress.md"
if [ ! -f "$progress_target" ]; then
  cp -f "$SCRIPT_DIR/docs/mastering_progress.md" "$progress_target"
  echo "  created: mastering_progress.md (template)"
else
  echo "  preserved: mastering_progress.md (existing session log untouched)"
fi

echo "[build] done. $((${#FILES[@]} + 1)) files synced."
echo "[build] take_shot.sh creates its own output directory per-call (e.g. a"
echo "        session-log folder you choose) -- nothing pre-created here."
echo "[build] Point OpenCode's working directory at: $TARGET"
