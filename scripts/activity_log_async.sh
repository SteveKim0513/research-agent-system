#!/bin/bash
# Claude Code hook wrapper — reads stdin JSON, forks activity_log.py in the
# background, returns immediately. Prevents hook timeouts from blocking the
# user-facing turn. Logging failures never surface to the UI.
#
# Usage (from .claude/settings.json hooks):
#   bash $CLAUDE_PROJECT_DIR/scripts/activity_log_async.sh <subcommand>
#
# Subcommands forwarded to activity_log.py: on-prompt-submit | on-turn-end | on-bash-event

set -u

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SUBCOMMAND="${1:-}"

if [ -z "$SUBCOMMAND" ]; then
  exit 0
fi

# Drain stdin fast so the hook runtime can unblock.
INPUT="$(cat)"

# Fork into a detached subshell — shell exits immediately, logger runs orphaned.
(
  printf '%s' "$INPUT" | python3 "$SCRIPT_DIR/activity_log.py" "$SUBCOMMAND" >/dev/null 2>&1
) &

disown 2>/dev/null || true
exit 0
