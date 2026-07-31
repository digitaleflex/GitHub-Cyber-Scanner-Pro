#!/usr/bin/env python3
"""
log-analyzer.py - Analyze and extract from large log files

Usage:
    log-analyzer.py <logfile> stats           # Show log statistics
    log-analyzer.py <logfile> errors [N]      # Show last N errors (default: 10)
    log-analyzer.py <logfile> search <pattern> [context]  # Search with context
    log-analyzer.py <logfile> timeline        # Show activity timeline
    log-analyzer.py <logfile> unique-errors   # List unique error messages
"""

import argparse
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


# Common log level patterns
LOG_LEVEL_PATTERNS = [
    r'\b(DEBUG|INFO|WARN(?:ING)?|ERROR|FATAL|CRITICAL)\b',
    r'\[(DEBUG|INFO|WARN(?:ING)?|ERROR|FATAL|CRITICAL)\]',
]

# Common timestamp patterns
TIMESTAMP_PATTERNS = [
    r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}',
    r'\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2}',
    r'\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}',
]


def detect_log_level(line: str) -> str | None:
    """Detect log level from a line."""
    for pattern in LOG_LEVEL_PATTERNS:
        match = re.search(pattern, line, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    return None


def detect_timestamp(line: str) -> str | None:
    """Extract timestamp from a line."""
    for pattern in TIMESTAMP_PATTERNS:
        match = re.search(pattern, line)
        if match:
            return match.group(0)
    return None


def cmd_stats(filepath: Path):
    """Show log file statistics."""
    level_counts = Counter()
    total_lines = 0
    first_ts = None
    last_ts = None
    
    with open(filepath, 'r', errors='replace') as f:
        for line in f:
            total_lines += 1
            level = detect_log_level(line)
            if level:
                level_counts[level] += 1
            
            ts = detect_timestamp(line)
            if ts:
                if first_ts is None:
                    first_ts = ts
                last_ts = ts
    
    print(f"=== Log Statistics: {filepath.name} ===")
    print(f"Total lines: {total_lines:,}")
    print(f"Time range: {first_ts or 'unknown'} → {last_ts or 'unknown'}")
    print()
    print("Log levels:")
    for level in ['DEBUG', 'INFO', 'WARN', 'WARNING', 'ERROR', 'FATAL', 'CRITICAL']:
        if level in level_counts:
            pct = (level_counts[level] / total_lines) * 100
            print(f"  {level:10} {level_counts[level]:>8,}  ({pct:.1f}%)")
    
    unknown = total_lines - sum(level_counts.values())
    if unknown > 0:
        pct = (unknown / total_lines) * 100
        print(f"  {'UNKNOWN':10} {unknown:>8,}  ({pct:.1f}%)")


def cmd_errors(filepath: Path, count: int = 10):
    """Show last N errors with context."""
    errors = []
    
    with open(filepath, 'r', errors='replace') as f:
        lines = list(enumerate(f, 1))
    
    for i, (line_num, line) in enumerate(lines):
        level = detect_log_level(line)
        if level in ('ERROR', 'FATAL', 'CRITICAL'):
            # Get context
            start = max(0, i - 2)
            end = min(len(lines), i + 3)
            context = [(ln, l.rstrip()) for ln, l in lines[start:end]]
            errors.append((line_num, line.rstrip(), context))
    
    print(f"=== Last {count} Errors ===")
    print(f"Total errors found: {len(errors)}")
    print()
    
    for line_num, error_line, context in errors[-count:]:
        print(f"--- Line {line_num} ---")
        for ctx_num, ctx_line in context:
            marker = ">>>" if ctx_num == line_num else "   "
            print(f"{marker} {ctx_num:6}| {ctx_line}")
        print()


def cmd_search(filepath: Path, pattern: str, context: int = 3):
    """Search for pattern with context."""
    regex = re.compile(pattern, re.IGNORECASE)
    matches = []
    
    with open(filepath, 'r', errors='replace') as f:
        lines = [(i, line.rstrip()) for i, line in enumerate(f, 1)]
    
    for i, (line_num, line) in enumerate(lines):
        if regex.search(line):
            start = max(0, i - context)
            end = min(len(lines), i + context + 1)
            ctx = [(ln, l) for ln, l in lines[start:end]]
            matches.append((line_num, ctx))
    
    print(f"=== Search: {pattern} ===")
    print(f"Found: {len(matches)} matches")
    print()
    
    for line_num, ctx in matches[:20]:  # Limit output
        print(f"--- Match at line {line_num} ---")
        for ctx_num, ctx_line in ctx:
            marker = ">>>" if ctx_num == line_num else "   "
            print(f"{marker} {ctx_num:6}| {ctx_line}")
        print()
    
    if len(matches) > 20:
        print(f"... and {len(matches) - 20} more matches")


def cmd_timeline(filepath: Path):
    """Show activity timeline by hour."""
    hourly = defaultdict(lambda: Counter())
    
    with open(filepath, 'r', errors='replace') as f:
        for line in f:
            ts = detect_timestamp(line)
            level = detect_log_level(line)
            if ts and level:
                # Extract hour (simplified)
                hour_match = re.search(r'(\d{2}):\d{2}:\d{2}', ts)
                if hour_match:
                    hour = hour_match.group(1)
                    hourly[hour][level] += 1
    
    print("=== Activity Timeline (by hour) ===")
    print(f"{'Hour':>6} {'Total':>8} {'ERROR':>8} {'WARN':>8} {'INFO':>8}")
    print("-" * 40)
    
    for hour in sorted(hourly.keys()):
        counts = hourly[hour]
        total = sum(counts.values())
        print(f"{hour}:00  {total:>8} {counts.get('ERROR', 0):>8} {counts.get('WARN', 0) + counts.get('WARNING', 0):>8} {counts.get('INFO', 0):>8}")


def cmd_unique_errors(filepath: Path):
    """List unique error messages."""
    error_patterns = Counter()
    
    with open(filepath, 'r', errors='replace') as f:
        for line in f:
            level = detect_log_level(line)
            if level in ('ERROR', 'FATAL', 'CRITICAL'):
                # Normalize: remove timestamps, numbers, UUIDs
                normalized = re.sub(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}[.\d]*', '<TS>', line)
                normalized = re.sub(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', '<UUID>', normalized)
                normalized = re.sub(r'\b\d+\b', '<N>', normalized)
                normalized = normalized.strip()[:200]  # Truncate long messages
                error_patterns[normalized] += 1
    
    print("=== Unique Error Patterns ===")
    print(f"Found {len(error_patterns)} unique patterns")
    print()
    
    for pattern, count in error_patterns.most_common(20):
        print(f"  [{count:>5}x] {pattern[:100]}")


def main():
    parser = argparse.ArgumentParser(description='Analyze large log files')
    parser.add_argument('file', help='Log file to analyze')
    parser.add_argument('command', choices=['stats', 'errors', 'search', 'timeline', 'unique-errors'],
                        help='Command to run')
    parser.add_argument('args', nargs='*', help='Command arguments')
    
    args = parser.parse_args()
    
    filepath = Path(args.file)
    if not filepath.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)
    
    if args.command == 'stats':
        cmd_stats(filepath)
    elif args.command == 'errors':
        count = int(args.args[0]) if args.args else 10
        cmd_errors(filepath, count)
    elif args.command == 'search':
        if not args.args:
            print("Error: search requires a pattern", file=sys.stderr)
            sys.exit(1)
        pattern = args.args[0]
        context = int(args.args[1]) if len(args.args) > 1 else 3
        cmd_search(filepath, pattern, context)
    elif args.command == 'timeline':
        cmd_timeline(filepath)
    elif args.command == 'unique-errors':
        cmd_unique_errors(filepath)


if __name__ == '__main__':
    main()
