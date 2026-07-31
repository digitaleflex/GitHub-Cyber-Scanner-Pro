#!/bin/bash
# code-indexer.sh - Index code structure for navigation
# Usage: code-indexer.sh <file_or_directory> [language]

set -e

TARGET="$1"
LANG="$2"

if [ -z "$TARGET" ]; then
    echo "Usage: code-indexer.sh <file_or_directory> [language]"
    echo ""
    echo "Supported languages: python, javascript, typescript, go, rust, java"
    echo ""
    echo "Examples:"
    echo "  code-indexer.sh src/main.py"
    echo "  code-indexer.sh src/ python"
    exit 1
fi

# Auto-detect language from extension if not provided
detect_language() {
    local file="$1"
    case "${file##*.}" in
        py) echo "python" ;;
        js|jsx) echo "javascript" ;;
        ts|tsx) echo "typescript" ;;
        go) echo "go" ;;
        rs) echo "rust" ;;
        java) echo "java" ;;
        rb) echo "ruby" ;;
        c|h) echo "c" ;;
        cpp|cc|cxx|hpp) echo "cpp" ;;
        *) echo "unknown" ;;
    esac
}

# Index patterns by language
index_file() {
    local file="$1"
    local lang="$2"
    
    echo "=== $file ==="
    
    case "$lang" in
        python)
            grep -nE "^class |^def |^async def |^@" "$file" 2>/dev/null || true
            ;;
        javascript|typescript)
            grep -nE "^export |^class |^function |^const \w+ = (async )?\(" "$file" 2>/dev/null || true
            ;;
        go)
            grep -nE "^func |^type |^var |^const " "$file" 2>/dev/null || true
            ;;
        rust)
            grep -nE "^pub fn |^fn |^pub struct |^struct |^pub enum |^enum |^impl |^pub trait |^trait " "$file" 2>/dev/null || true
            ;;
        java)
            grep -nE "^public class |^class |^public interface |^interface |public .* \w+\(" "$file" 2>/dev/null || true
            ;;
        ruby)
            grep -nE "^class |^module |^def " "$file" 2>/dev/null || true
            ;;
        c|cpp)
            grep -nE "^[a-zA-Z_][a-zA-Z0-9_]* \*?[a-zA-Z_][a-zA-Z0-9_]*\(|^struct |^class |^typedef " "$file" 2>/dev/null || true
            ;;
        *)
            echo "  (unknown language, showing function-like patterns)"
            grep -nE "^[a-zA-Z_].*\(" "$file" 2>/dev/null | head -20 || true
            ;;
    esac
    echo ""
}

if [ -f "$TARGET" ]; then
    # Single file
    if [ -z "$LANG" ]; then
        LANG=$(detect_language "$TARGET")
    fi
    index_file "$TARGET" "$LANG"
    
elif [ -d "$TARGET" ]; then
    # Directory
    echo "=== Code Index: $TARGET ==="
    echo ""
    
    # Find all code files
    find "$TARGET" -type f \( \
        -name "*.py" -o \
        -name "*.js" -o -name "*.jsx" -o \
        -name "*.ts" -o -name "*.tsx" -o \
        -name "*.go" -o \
        -name "*.rs" -o \
        -name "*.java" -o \
        -name "*.rb" -o \
        -name "*.c" -o -name "*.cpp" -o -name "*.h" \
    \) ! -path "*/node_modules/*" ! -path "*/.git/*" ! -path "*/vendor/*" ! -path "*/__pycache__/*" \
    | sort | while read -r file; do
        file_lang=$(detect_language "$file")
        if [ -n "$LANG" ] && [ "$file_lang" != "$LANG" ]; then
            continue
        fi
        index_file "$file" "$file_lang"
    done
else
    echo "Error: $TARGET is not a file or directory"
    exit 1
fi
