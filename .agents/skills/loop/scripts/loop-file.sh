#!/bin/bash
# loop-file.sh - Execute a prompt file in a Ralph loop until completion
# Usage: loop-file.sh <prompt-file> [max-iterations] [completion-promise]

set -e

PROMPT_FILE="${1:-}"
MAX_ITERATIONS="${2:-10}"
COMPLETION_PROMISE="${3:-COMPLETE}"

if [ -z "$PROMPT_FILE" ] || [ ! -f "$PROMPT_FILE" ]; then
    echo "Usage: loop-file.sh <prompt-file> [max-iterations] [completion-promise]"
    echo ""
    echo "Arguments:"
    echo "  prompt-file         Path to markdown file with task (required)"
    echo "  max-iterations      Maximum loop iterations (default: 10)"
    echo "  completion-promise  Signal phrase for completion (default: COMPLETE)"
    echo ""
    echo "Example:"
    echo "  loop-file.sh task.md 10 DONE"
    exit 1
fi

# Check if ralph is installed
if ! command -v ralph &> /dev/null; then
    echo "Error: ralph CLI not found. Install with: npm install -g @th0rgal/ralph-wiggum"
    exit 1
fi

echo "Starting Ralph loop with prompt file..."
echo "  File: $PROMPT_FILE"
echo "  Max iterations: $MAX_ITERATIONS"
echo "  Completion promise: $COMPLETION_PROMISE"
echo ""

ralph --prompt-file "$PROMPT_FILE" \
    --max-iterations "$MAX_ITERATIONS" \
    --completion-promise "$COMPLETION_PROMISE" \
    --allow-all
