#!/bin/bash
# loop-task.sh - Execute a task in a Ralph loop until completion
# Usage: loop-task.sh "prompt" [max-iterations] [completion-promise]

set -e

PROMPT="${1:-}"
MAX_ITERATIONS="${2:-10}"
COMPLETION_PROMISE="${3:-COMPLETE}"

if [ -z "$PROMPT" ]; then
    echo "Usage: loop-task.sh \"prompt\" [max-iterations] [completion-promise]"
    echo ""
    echo "Arguments:"
    echo "  prompt              Task description (required)"
    echo "  max-iterations      Maximum loop iterations (default: 10)"
    echo "  completion-promise  Signal phrase for completion (default: COMPLETE)"
    echo ""
    echo "Example:"
    echo "  loop-task.sh \"Build a REST API. Output <promise>DONE</promise> when complete.\" 10 DONE"
    exit 1
fi

# Check if ralph is installed
if ! command -v ralph &> /dev/null; then
    echo "Error: ralph CLI not found. Install with: npm install -g @th0rgal/ralph-wiggum"
    exit 1
fi

echo "Starting Ralph loop..."
echo "  Prompt: ${PROMPT:0:50}..."
echo "  Max iterations: $MAX_ITERATIONS"
echo "  Completion promise: $COMPLETION_PROMISE"
echo ""

ralph "$PROMPT" \
    --max-iterations "$MAX_ITERATIONS" \
    --completion-promise "$COMPLETION_PROMISE" \
    --allow-all
