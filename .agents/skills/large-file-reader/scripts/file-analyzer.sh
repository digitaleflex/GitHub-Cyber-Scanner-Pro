#!/bin/bash
# file-analyzer.sh - Analyze file structure and provide reading strategy
# Usage: file-analyzer.sh <file_path>

set -e

FILE="$1"

if [ -z "$FILE" ]; then
    echo "Usage: file-analyzer.sh <file_path>"
    exit 1
fi

if [ ! -f "$FILE" ]; then
    echo "Error: File not found: $FILE"
    exit 1
fi

# Get file info
FILENAME=$(basename "$FILE")
EXTENSION="${FILENAME##*.}"
LINES=$(wc -l < "$FILE" 2>/dev/null || echo "0")
SIZE=$(ls -lh "$FILE" | awk '{print $5}')
SIZE_BYTES=$(stat -f%z "$FILE" 2>/dev/null || stat --format=%s "$FILE" 2>/dev/null)

echo "=== File Analysis ==="
echo "File: $FILE"
echo "Size: $SIZE ($SIZE_BYTES bytes)"
echo "Lines: $LINES"
echo "Type: $EXTENSION"
echo ""

# Determine strategy
if [ "$LINES" -lt 100 ]; then
    echo "Strategy: SAFE TO READ ENTIRELY"
    echo "  → File is small enough to read directly"
elif [ "$LINES" -lt 500 ]; then
    echo "Strategy: MODERATE - Consider chunked reading"
    echo "  → Read in chunks of ~100-200 lines"
    echo "  → Use: sed -n '1,200p' $FILE"
elif [ "$LINES" -lt 2000 ]; then
    echo "Strategy: LARGE - Use targeted extraction"
    echo "  → Index first: grep -n 'pattern' $FILE"
    echo "  → Extract sections: sed -n 'START,ENDp' $FILE"
    echo "  → Consider: mgrep for semantic search"
else
    echo "Strategy: VERY LARGE - Use semantic search or streaming"
    echo "  → mgrep 'query' (semantic search)"
    echo "  → rg 'pattern' $FILE (fast pattern search)"
    echo "  → Never read entire file"
fi

echo ""
echo "=== File Preview (first 20 lines) ==="
head -20 "$FILE"

echo ""
echo "=== Structure Hints ==="

case "$EXTENSION" in
    py)
        echo "Python file - Key structures:"
        grep -n "^class \|^def \|^async def " "$FILE" 2>/dev/null | head -20 || echo "  (no classes/functions found)"
        ;;
    js|ts|jsx|tsx)
        echo "JavaScript/TypeScript file - Key structures:"
        grep -n "^export \|^class \|^function \|^const \|^interface " "$FILE" 2>/dev/null | head -20 || echo "  (no exports/classes found)"
        ;;
    java)
        echo "Java file - Key structures:"
        grep -n "^public class \|public interface \|public void \|public static " "$FILE" 2>/dev/null | head -20 || echo "  (no classes/methods found)"
        ;;
    go)
        echo "Go file - Key structures:"
        grep -n "^func \|^type " "$FILE" 2>/dev/null | head -20 || echo "  (no functions/types found)"
        ;;
    rs)
        echo "Rust file - Key structures:"
        grep -n "^pub fn \|^fn \|^struct \|^enum \|^impl " "$FILE" 2>/dev/null | head -20 || echo "  (no functions/structs found)"
        ;;
    md)
        echo "Markdown file - Sections:"
        grep -n "^## \|^### \|^#### " "$FILE" 2>/dev/null | head -20 || echo "  (no headings found)"
        ;;
    json)
        echo "JSON file - Top-level keys:"
        head -1 "$FILE" | python3 -c "import sys,json; print('\n'.join(json.load(sys.stdin).keys() if isinstance(json.load(open('$FILE')), dict) else ['(array)']))" 2>/dev/null | head -10 || echo "  (could not parse)"
        ;;
    log|txt)
        echo "Log/Text file - Sample patterns:"
        grep -oE "(ERROR|WARN|INFO|DEBUG|\d{4}-\d{2}-\d{2})" "$FILE" 2>/dev/null | sort | uniq -c | sort -rn | head -10 || echo "  (no common patterns)"
        ;;
    *)
        echo "Generic file - Line distribution:"
        echo "  First 10 lines, middle 10 lines, last 10 lines available"
        ;;
esac
