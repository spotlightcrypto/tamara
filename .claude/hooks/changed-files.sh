#!/usr/bin/env bash
# Stop hook: after each turn, surface the working-tree changes (modified / added
# / untracked) so the user sees what files changed. Prints a Claude Code
# `systemMessage` JSON object, or nothing when the tree is clean.
#
# Note: this reflects ALL currently-uncommitted changes, so it resets after a
# commit — it is not a strict per-turn diff.

git -C "${CLAUDE_PROJECT_DIR:-.}" status --short 2>/dev/null \
  | jq -Rsc 'if . == "" then empty else {systemMessage: ("Files changed (working tree):\n" + .)} end'
