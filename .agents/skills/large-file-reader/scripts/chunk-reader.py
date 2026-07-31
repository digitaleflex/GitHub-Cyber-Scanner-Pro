#!/usr/bin/env python3
"""
chunk-reader.py - Read large files in manageable chunks with overlap

Usage:
    chunk-reader.py <file> [--chunk-size 100] [--overlap 10] [--chunk N]
    
Examples:
    chunk-reader.py large.log                    # Show chunk info
    chunk-reader.py large.log --chunk 1          # Read first chunk
    chunk-reader.py large.log --chunk 5          # Read 5th chunk
    chunk-reader.py large.log --chunk-size 200   # Use 200-line chunks
"""

import argparse
import sys
from pathlib import Path


def count_lines(filepath: Path) -> int:
    """Count lines in file efficiently."""
    with open(filepath, 'rb') as f:
        return sum(1 for _ in f)


def read_chunk(filepath: Path, chunk_num: int, chunk_size: int, overlap: int) -> tuple[list[str], int, int]:
    """Read a specific chunk from file with overlap."""
    start_line = max(0, (chunk_num - 1) * chunk_size - overlap)
    end_line = chunk_num * chunk_size + overlap
    
    lines = []
    with open(filepath, 'r', errors='replace') as f:
        for i, line in enumerate(f, 1):
            if i > end_line:
                break
            if i >= start_line + 1:
                lines.append(f"{i:6}| {line.rstrip()}")
    
    return lines, start_line + 1, min(end_line, start_line + len(lines))


def main():
    parser = argparse.ArgumentParser(description='Read large files in chunks')
    parser.add_argument('file', help='File to read')
    parser.add_argument('--chunk-size', type=int, default=100, help='Lines per chunk (default: 100)')
    parser.add_argument('--overlap', type=int, default=10, help='Overlap lines between chunks (default: 10)')
    parser.add_argument('--chunk', type=int, help='Chunk number to read (1-indexed)')
    
    args = parser.parse_args()
    
    filepath = Path(args.file)
    if not filepath.exists():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)
    
    total_lines = count_lines(filepath)
    total_chunks = (total_lines + args.chunk_size - 1) // args.chunk_size
    
    print(f"=== File: {filepath.name} ===")
    print(f"Total lines: {total_lines:,}")
    print(f"Chunk size: {args.chunk_size} lines")
    print(f"Overlap: {args.overlap} lines")
    print(f"Total chunks: {total_chunks}")
    print()
    
    if args.chunk:
        if args.chunk < 1 or args.chunk > total_chunks:
            print(f"Error: Chunk {args.chunk} out of range (1-{total_chunks})", file=sys.stderr)
            sys.exit(1)
        
        lines, start, end = read_chunk(filepath, args.chunk, args.chunk_size, args.overlap)
        print(f"=== Chunk {args.chunk}/{total_chunks} (lines {start}-{end}) ===")
        print()
        for line in lines:
            print(line)
    else:
        print("Chunk map:")
        for i in range(1, min(total_chunks + 1, 11)):
            start = (i - 1) * args.chunk_size + 1
            end = min(i * args.chunk_size, total_lines)
            print(f"  Chunk {i}: lines {start}-{end}")
        
        if total_chunks > 10:
            print(f"  ... ({total_chunks - 10} more chunks)")
        
        print()
        print(f"To read a chunk: {sys.argv[0]} {args.file} --chunk N")


if __name__ == '__main__':
    main()
