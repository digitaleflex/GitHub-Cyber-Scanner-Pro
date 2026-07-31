# Advanced Extraction Patterns

## Complex grep Patterns

### Multi-pattern search (AND logic)
```bash
# Lines containing both patterns
grep "pattern1" file | grep "pattern2"

# Using ripgrep
rg "pattern1" file | rg "pattern2"
```

### Multi-pattern search (OR logic)
```bash
grep -E "pattern1|pattern2|pattern3" file
rg "pattern1|pattern2|pattern3" file
```

### Inverted match (NOT)
```bash
grep -v "exclude_pattern" file
rg -v "exclude_pattern" file
```

### Complex regex examples
```bash
# Function calls with specific arguments
rg "authenticate\([^)]*admin[^)]*\)"

# Import statements for specific modules
rg "^(import|from)\s+.*?(auth|security)"

# Error messages with error codes
rg "ERROR.*\[E\d{4}\]"

# URLs in code
rg "https?://[^\s\"\']+"

# Email addresses
rg "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
```

## AWK Advanced Patterns

### Field extraction
```bash
# Print specific columns
awk '{print $1, $3, $NF}' file

# Custom delimiter
awk -F',' '{print $2}' file.csv
awk -F':' '{print $1}' /etc/passwd
```

### Conditional processing
```bash
# Print lines where field > value
awk '$3 > 100 {print}' file

# Print lines matching pattern
awk '/ERROR/ {print $0}' logfile

# Count lines matching pattern
awk '/ERROR/ {count++} END {print count}' logfile
```

### Aggregations
```bash
# Sum a column
awk '{sum += $2} END {print sum}' file

# Average
awk '{sum += $2; count++} END {print sum/count}' file

# Group by and count
awk '{counts[$1]++} END {for (k in counts) print k, counts[k]}' file
```

### Window functions
```bash
# Running total
awk '{sum += $1; print $0, sum}' file

# Difference from previous line
awk 'NR>1 {print $1 - prev} {prev = $1}' file
```

## SED Advanced Patterns

### Multi-line operations
```bash
# Join lines (remove newlines)
sed ':a;N;$!ba;s/\n/ /g' file

# Delete empty lines
sed '/^$/d' file

# Delete lines matching pattern
sed '/pattern/d' file
```

### In-place substitution
```bash
# Replace and backup
sed -i.bak 's/old/new/g' file

# Multiple substitutions
sed -e 's/foo/bar/g' -e 's/baz/qux/g' file
```

### Range operations
```bash
# Print between patterns
sed -n '/START/,/END/p' file

# Delete between patterns
sed '/START/,/END/d' file

# Replace only in range
sed '/START/,/END/s/old/new/g' file
```

## JSON Processing with jq

### Navigation
```bash
# Nested access
jq '.data.users[0].name' file.json

# Array slicing
jq '.items[0:5]' file.json

# All values of a key
jq '.users[].email' file.json
```

### Filtering
```bash
# Select by condition
jq '.items[] | select(.status == "active")' file.json

# Multiple conditions
jq '.items[] | select(.age > 21 and .country == "US")' file.json

# Null handling
jq '.items[] | select(.email != null)' file.json
```

### Transformation
```bash
# Create new objects
jq '.users[] | {name: .name, email: .email}' file.json

# Add computed fields
jq '.items[] | . + {full_name: "\(.first) \(.last)"}' file.json

# Group by
jq 'group_by(.category) | map({category: .[0].category, count: length})' file.json
```

### Aggregation
```bash
# Count items
jq '.items | length' file.json

# Sum values
jq '[.items[].price] | add' file.json

# Unique values
jq '[.items[].category] | unique' file.json
```

### Streaming large JSON
```bash
# Process line by line (JSONL)
cat large.jsonl | while read line; do
  echo "$line" | jq '.field'
done

# jq streaming mode
jq --stream 'select(.[0][0] == "users")' huge.json
```

## Log Analysis Patterns

### Extract error context
```bash
# Get lines before and after error
grep -B5 -A10 "FATAL" app.log

# Get entire stack trace (until empty line)
awk '/Exception/{p=1} p; /^$/{p=0}' app.log
```

### Time-based filtering
```bash
# Extract logs from time range
awk '$0 >= "2024-01-15 10:00" && $0 <= "2024-01-15 11:00"' app.log

# Last hour (requires GNU date)
HOUR_AGO=$(date -d '1 hour ago' '+%Y-%m-%d %H:%M')
awk -v start="$HOUR_AGO" '$0 >= start' app.log
```

### Request tracing
```bash
# Find all logs for a request ID
grep "req_abc123" *.log

# Extract request duration
grep "completed" app.log | awk -F'duration=' '{print $2}' | cut -d' ' -f1
```

### Performance analysis
```bash
# Slowest requests
grep "duration=" app.log | sed 's/.*duration=\([0-9.]*\).*/\1/' | sort -rn | head -20

# Requests per endpoint
grep "GET\|POST\|PUT\|DELETE" access.log | awk '{print $6, $7}' | sort | uniq -c | sort -rn
```

## Code Analysis Patterns

### Dependency analysis
```bash
# Python imports
grep -r "^import \|^from " --include="*.py" | sort -u

# JavaScript requires/imports
rg "^(import|const.*require)" --type js

# Go imports
rg "^\t\"" --type go | sort -u
```

### Find TODOs and FIXMEs
```bash
rg "TODO|FIXME|XXX|HACK" --type-add 'code:*.{py,js,ts,go,rs,java}' -t code
```

### Unused code detection
```bash
# Find defined but potentially unused functions
# First, list all definitions
grep -rn "^def \|^function " --include="*.py" --include="*.js" > /tmp/defs

# Then check for references (manual review needed)
```

### API endpoint mapping
```bash
# Express.js routes
rg "app\.(get|post|put|delete|patch)\(" --type js

# Flask routes  
rg "@app\.route\(" --type py

# FastAPI routes
rg "@(app|router)\.(get|post|put|delete)\(" --type py
```

## Binary Search in Sorted Files

For very large sorted files, use binary search:

```bash
# Using look command (for sorted files)
look "prefix" sorted_file.txt

# Using binary search with awk
binary_search() {
  local file=$1
  local target=$2
  local lines=$(wc -l < "$file")
  local low=1
  local high=$lines
  
  while [ $low -le $high ]; do
    local mid=$(( (low + high) / 2 ))
    local line=$(sed -n "${mid}p" "$file")
    if [[ "$line" < "$target" ]]; then
      low=$((mid + 1))
    elif [[ "$line" > "$target" ]]; then
      high=$((mid - 1))
    else
      echo "Found at line $mid: $line"
      return 0
    fi
  done
  echo "Not found"
  return 1
}
```

## Parallel Processing

### GNU Parallel
```bash
# Search in parallel
find . -name "*.log" | parallel grep "ERROR" {}

# Process files in batches
find . -name "*.json" | parallel -j4 'jq .status {} > {.}.status'
```

### xargs parallelization
```bash
# Parallel grep
find . -name "*.py" -print0 | xargs -0 -P4 grep -l "import pandas"
```

## Memory-Efficient Streaming

### Process without loading entire file
```bash
# Line-by-line processing
while IFS= read -r line; do
  # Process each line
  echo "$line" | grep -q "pattern" && echo "$line"
done < large_file.txt

# Using stdbuf to prevent buffering
stdbuf -oL tail -f growing.log | grep --line-buffered "ERROR"
```

### Chunked processing
```bash
# Split and process
split -l 10000 large.csv chunk_
for f in chunk_*; do
  process_chunk "$f"
  rm "$f"
done
```
