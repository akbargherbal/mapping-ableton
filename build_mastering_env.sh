#!/usr/bin/env bash
# build_mastering_env.sh — assemble a self-contained runtime folder for the
# "Mastering Suno AI Music in Ableton" course, independent of the main
# mapping-ableton (click-automation) project.
#
# This course does NOT use the pywinauto/UIA click-automation stack at all —
# it runs entirely on ableton-mcp-extended (real device-parameter reads) plus
# the learner's own ears. So, unlike build_runtime_env.sh, nothing from
# scripts/automate_ableton_task.py, orchestrate.sh, take_shot.sh, or the UIA
# dump scripts is pulled in here. The two runtime folders this repo can build
# are deliberately siblings, not overlapping.
#
# WHITELIST, not blacklist — same policy as build_runtime_env.sh: only files
# listed in FILES[] below ever leave this repo.
#
# Usage:
#   ./build_mastering_env.sh [target_dir]
#   target_dir defaults to a sibling folder: ../suno-mastering-course
#
# Point OpenCode's working directory at <target_dir> for the mastering
# course, kept entirely separate from ../ableton-runtime (the click-
# automation runtime). Re-run any time SUNO_MASTERING_AGENT_POLICY.md or the
# whitelisted docs change — straight overwrite of those, but mastering_progress.md
# in the target is never touched once it exists (session log, not a build artifact).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-$SCRIPT_DIR/../suno-mastering-course}"

# --- The whitelist -----------------------------------------------------
# Everything the mastering-instructor agent needs, and nothing from the
# click-automation side of this repo.
FILES=(
  "docs/suno-mastering-course-breakdown.md"   # authoritative lesson spec
  "docs/suno-mastering-curriculum.md"         # leaner 6-module operating version
  "docs/opencode-ableton-mcp-setup.md"        # ableton-mcp-extended setup — the
                                               # only external dependency this
                                               # course has; included so the
                                               # target folder is buildable
                                               # without the main repo for reference
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

# mastering_progress.md is a runtime session log, not a build artifact — copy
# the template only if the target doesn't already have one going, so a
# re-run of this script never clobbers real session history.
progress_target="$TARGET/mastering_progress.md"
if [ ! -f "$progress_target" ]; then
  cp -f "$SCRIPT_DIR/mastering_progress.md" "$progress_target"
  echo "  created: mastering_progress.md (template)"
else
  echo "  preserved: mastering_progress.md (existing session log untouched)"
fi

echo "[build] done. $((${#FILES[@]} + 1)) files synced."
echo "[build] Point OpenCode's working directory at: $TARGET"
