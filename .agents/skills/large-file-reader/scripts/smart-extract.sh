#!/bin/bash
# smart-extract.sh - Extract relevant sections from large files
# Usage: smart-extract.sh <file> <pattern> [context_lines]

set -e

FILE="$1"
PATTERN="$2"
CONTEXT="${3:-5}"

if [ -z "$FILE" ] || [ -z "$PATTERN" ]; then
    echo "Usage: smart-extract.sh <file> <pattern> [context_lines]"
    echo ""
    echo "Examples:"
    echo "  smart-extract.sh app.py 'def authenticate' 10"
    echo "  smart-extract.sh server.log 'ERROR' 3"
    exit 1
fi

if [ ! -f "$FILE" ]; then
    echo "Error: File not found: $FILE"
    exit 1
fi

echo "=== Searching for: $PATTERN ==="
echo "File: $FILE"
echo "Context: $CONTEXT lines before/after"
echo ""

# Find matches with line numbers
MATCHES=$(grep -n "$PATTERN" "$FILE" 2>/dev/null | head -20)

if [ -z "$MATCHES" ]; then
    echo "No matches found for pattern: $PATTERN"
    exit 0
fi

MATCH_COUNT=$(echo "$MATCHES" | wc -l | tr -d ' ')
echo "Found $MATCH_COUNT matches (showing first 20)"
echo ""

# Extract each match with context
echo "$MATCHES" | while IFS=: read -r LINE_NUM REST; do
    START=$((LINE_NUM - CONTEXT))
    END=$((LINE_NUM + CONTEXT))
    
    # Ensure START is at least 1
    [ "$START" -lt 1 ] && START=1
    
    echo "--- Match at line $LINE_NUM ---"
    sed -n "${START},${END}p" "$FILE" | nl -ba -v "$START"
    echo ""
done
