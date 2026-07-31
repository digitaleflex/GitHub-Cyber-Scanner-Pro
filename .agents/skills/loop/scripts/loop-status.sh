#!/bin/bash
# loop-status.sh - Check status of running Ralph loop
# Usage: loop-status.sh

if ! command -v ralph &> /dev/null; then
    echo "Error: ralph CLI not found. Install with: npm install -g @th0rgal/ralph-wiggum"
    exit 1
fi

ralph --status
