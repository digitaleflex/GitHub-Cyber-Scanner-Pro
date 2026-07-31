---
name: large-file-reader
description: Comprehensive toolkit for AI agents to read, analyze, and extract information from large files without overflowing context windows. Use when working with files too large to read entirely, analyzing codebases, extracting specific sections from logs, processing large datasets, or when semantic search is needed. Covers chunked reading, semantic grep, structured extraction, and intelligent file navigation strategies.
---

# Large File Reader

A comprehensive guide for efficiently reading and analyzing large files without exhausting context windows.

## Core Strategy

1. **Never read entire large files** - Always use targeted extraction
2. **Index before reading** - Understand file structure first
3. **Semantic over literal** - Use meaning-based search when possible
4. **Progressive disclosure** - Start broad, narrow down

## Quick Decision Tree

```
Is the file > 500 lines?
├── YES → Use chunked reading or semantic search
│   ├── Need specific pattern? → grep/rg with context
│   ├── Need meaning-based search? → mgrep (semantic)
│   ├── Need file structure? → Index first (grep -n)
│   └── Need specific lines? → sed -n 'START,ENDp'
└── NO → Safe to read directly
```

## Tool Reference

### 1. Semantic Search (mgrep) - RECOMMENDED FOR AGENTS

**Best for:** Natural language queries, finding code by intent, multimodal files

```bash
# Install
npm install -g @mixedbread/mgrep

# Login (or set MXBAI_API_KEY for headless)
mgrep login

# Index a project (run once, keeps synced)
mgrep watch

# Search semantically
mgrep "where is authentication configured?"
mgrep "database connection handling" src/
mgrep -m 20 "error handling patterns"           # Limit results
mgrep -a "how does caching work?"               # Get summarized answer
mgrep --agentic "yearly metrics 2020-2024"      # Multi-query refinement
mgrep --web --answer "how to use Redis streams" # Include web search
```

**Why mgrep is best for agents:**
- 2x fewer tokens than grep-based workflows
- Understands intent, not just patterns
- Works on code, PDFs, images
- Returns only semantically relevant chunks

### 2. Fast Pattern Search (ripgrep/rg)

**Best for:** Exact patterns, regex, speed on large codebases

```bash
# Basic search with context
rg "function_name" --context 5

# Search specific file types
rg "TODO" --type py --type js

# Case insensitive with line numbers
rg -in "error" src/

# Show only filenames
rg -l "deprecated"

# Count matches per file
rg -c "import" --type ts

# Search with regex
rg "def \w+\(.*\):" --type py

# Exclude directories
rg "pattern" --glob '!node_modules' --glob '!.git'

# JSON output for parsing
rg "pattern" --json
```

### 3. Line-Based Extraction (sed/awk)

**Best for:** Extracting specific line ranges, structured data

```bash
# Read specific line range
sed -n '100,200p' file.txt

# Read first N lines
sed -n '1,50p' file.txt

# Read last N lines (use tail)
tail -n 50 file.txt

# Read around a pattern (line number + context)
grep -n "pattern" file.txt | head -5  # Find line numbers first
sed -n '95,105p' file.txt              # Then extract range

# Extract every Nth line
awk 'NR % 10 == 0' file.txt

# Extract lines matching pattern with context
awk '/pattern/{for(i=1;i<=5;i++){getline; print}}' file.txt
```

### 4. File Structure Analysis

**Best for:** Understanding file organization before reading

```bash
# Count lines
wc -l file.txt

# Index key structures in code
grep -n "^class \|^def \|^function " file.py
grep -n "^## \|^### " README.md  # Markdown headings

# Find all function/class definitions
rg "^(class|def|function|const|let|var)\s+\w+" --line-number

# Get file type distribution
find . -type f | sed 's/.*\.//' | sort | uniq -c | sort -rn

# Directory structure
tree -L 2 --dirsfirst

# File sizes (find large files)
find . -type f -exec ls -lh {} \; | awk '{print $5, $9}' | sort -hr
```

### 5. Log File Analysis

**Best for:** Extracting relevant entries from large logs

```bash
# Filter by timestamp range
awk '$0 >= "2024-01-15" && $0 <= "2024-01-16"' app.log

# Filter by log level
grep -E "ERROR|WARN" app.log

# Last N errors with context
grep -B2 -A5 "ERROR" app.log | tail -50

# Unique error messages
grep "ERROR" app.log | sort -u

# Count by log level
grep -oE "(INFO|WARN|ERROR|DEBUG)" app.log | sort | uniq -c

# Extract stack traces
awk '/Exception|Error/{p=1} p; /^$/{p=0}' app.log
```

### 6. JSON/Structured Data

**Best for:** Extracting from large JSON files

```bash
# Pretty print with jq
cat large.json | jq '.' | head -100

# Extract specific keys
jq '.data[0:10]' large.json

# Filter and extract
jq '.items[] | select(.status == "active") | .name' data.json

# Count items
jq '.items | length' data.json

# Stream large JSON files (memory efficient)
jq --stream 'select(.[0][0] == "users")' huge.json
```

### 7. CSV/TSV Analysis

**Best for:** Large tabular data

```bash
# Preview structure
head -5 data.csv

# Count rows
wc -l data.csv

# Extract specific columns (csvkit)
csvcut -c 1,3,5 data.csv | head -20

# Filter rows
csvgrep -c status -m "active" data.csv

# Get column names
head -1 data.csv | tr ',' '\n' | nl

# Using awk for TSV
awk -F'\t' '{print $1, $3}' data.tsv | head -20

# Unique values in column
cut -d',' -f3 data.csv | sort -u | head -20
```

### 8. Binary/PDF Files

**Best for:** Extracting text from non-text formats

```bash
# PDF to text
pdftotext document.pdf - | head -200

# PDF with layout preservation
pdftotext -layout document.pdf -

# Extract specific pages
pdftk input.pdf cat 1-10 output first10.pdf

# Word documents
pandoc document.docx -t plain | head -200

# Using mgrep (handles PDFs natively)
mgrep "contract terms" documents/
```

## Workflow Patterns

### Pattern 1: Codebase Exploration

```bash
# 1. Get overview
tree -L 2 --dirsfirst
wc -l src/**/*.py

# 2. Find entry points
rg "if __name__" --type py
rg "main\(\)" --type py

# 3. Semantic search for functionality
mgrep "user authentication flow"
mgrep "database connection setup"

# 4. Read specific sections
sed -n '50,150p' src/auth.py
```

### Pattern 2: Log Investigation

```bash
# 1. Get log stats
wc -l app.log
grep -c "ERROR" app.log

# 2. Find error timeline
grep "ERROR" app.log | head -20
grep "ERROR" app.log | tail -20

# 3. Get context around specific error
grep -n "OutOfMemory" app.log
sed -n '1000,1050p' app.log

# 4. Extract unique errors
grep "ERROR" app.log | cut -d']' -f2- | sort -u
```

### Pattern 3: Large JSON Analysis

```bash
# 1. Understand structure
jq 'keys' data.json
jq '.[0]' data.json

# 2. Count and sample
jq 'length' data.json
jq '.[0:5]' data.json

# 3. Filter relevant data
jq '.[] | select(.type == "error")' data.json

# 4. Extract specific fields
jq '.[] | {id, name, status}' data.json
```

### Pattern 4: Multi-File Search

```bash
# 1. Find relevant files
rg -l "authentication" src/

# 2. Get context from each
for f in $(rg -l "authentication" src/); do
  echo "=== $f ==="
  rg -C3 "authentication" "$f"
done

# 3. Or use mgrep for semantic
mgrep "authentication implementation" src/
```

## Best Practices

### DO:
- Always check file size first: `wc -l file.txt`
- Use line numbers to navigate: `grep -n`
- Prefer semantic search (mgrep) for understanding intent
- Extract only what's needed
- Index before diving deep

### DON'T:
- Never `cat` or read entire large files
- Avoid piping through `head` or `tail` (causes buffering issues)
- Don't guess patterns - search first
- Don't load entire files into context

## Environment Setup

### Required Tools

```bash
# Core tools (usually pre-installed)
# grep, sed, awk, head, tail, wc

# Enhanced search
brew install ripgrep    # rg - fast grep
npm i -g @mixedbread/mgrep  # semantic search

# JSON processing
brew install jq

# CSV processing
pip install csvkit

# PDF processing
brew install poppler  # pdftotext
brew install pandoc   # document conversion
```

### mgrep Setup for Agents

```bash
# Option 1: Interactive login
mgrep login

# Option 2: API key (for CI/headless)
export MXBAI_API_KEY=your_api_key_here

# Start file watcher (keeps index updated)
mgrep watch

# Configure limits
export MGREP_MAX_FILE_SIZE=1048576  # 1MB
export MGREP_MAX_FILE_COUNT=1000
```

## Troubleshooting

### Context window still filling up?
- Reduce `-m` (max results) in mgrep
- Use narrower line ranges with sed
- Add more specific patterns to grep

### mgrep not finding results?
- Ensure `mgrep watch` is running
- Check `.mgrepignore` for excluded files
- Try rephrasing query semantically

### Slow searches?
- Use ripgrep instead of grep
- Exclude node_modules, .git: `--glob '!node_modules'`
- Index with mgrep for repeated searches

## Additional References

For advanced patterns, see:
- `references/advanced-patterns.md` - Complex extraction patterns
- `references/mgrep-guide.md` - Full mgrep documentation
