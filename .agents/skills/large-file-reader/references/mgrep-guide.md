# mgrep Complete Guide

## Overview

mgrep is a CLI-native semantic search tool by Mixedbread AI that uses embeddings instead of regex patterns. It's designed specifically for AI agents to efficiently search large codebases.

## Installation

```bash
npm install -g @mixedbread/mgrep
# or
pnpm add -g @mixedbread/mgrep
# or
bun add -g @mixedbread/mgrep
```

## Authentication

### Interactive Login
```bash
mgrep login
```

### Headless/CI (API Key)
```bash
export MXBAI_API_KEY=your_api_key_here
```

## Core Commands

### mgrep watch
Index and keep files synced:

```bash
cd /path/to/project
mgrep watch                           # Index current directory
mgrep watch --max-file-size 1048576   # Limit to 1MB files
mgrep watch --max-file-count 5000     # Limit to 5000 files
mgrep watch --dry-run                 # Preview without syncing
```

### mgrep search (default)
Search semantically:

```bash
mgrep "query"                         # Search current directory
mgrep "query" src/lib                 # Search specific path
mgrep -m 25 "query"                   # Limit results
mgrep -c "query"                      # Show content in results
mgrep -a "query"                      # Get AI-generated answer
mgrep --web "query"                   # Include web results
mgrep --agentic "complex query"       # Multi-query refinement
mgrep -s "query"                      # Sync before searching
mgrep --no-rerank "query"             # Disable reranking
```

## Flags Reference

| Flag | Short | Description |
|------|-------|-------------|
| `--max-count` | `-m` | Maximum results to return |
| `--content` | `-c` | Show content in results |
| `--answer` | `-a` | Generate AI answer |
| `--web` | `-w` | Include web search |
| `--agentic` | | Multi-search refinement |
| `--sync` | `-s` | Sync files before search |
| `--dry-run` | `-d` | Preview without syncing |
| `--no-rerank` | | Disable result reranking |
| `--max-file-size` | | Max file size in bytes |
| `--max-file-count` | | Max files to sync |

## Environment Variables

```bash
# Authentication
export MXBAI_API_KEY=your_key

# Store configuration
export MXBAI_STORE=custom-store-name

# Search defaults
export MGREP_MAX_COUNT=20
export MGREP_CONTENT=1
export MGREP_ANSWER=1
export MGREP_WEB=1
export MGREP_AGENTIC=1
export MGREP_RERANK=0

# Sync limits
export MGREP_MAX_FILE_SIZE=1048576
export MGREP_MAX_FILE_COUNT=1000
```

## Configuration Files

### Local config: `.mgreprc.yaml`
```yaml
maxFileSize: 5242880    # 5MB
maxFileCount: 5000
```

### Global config: `~/.config/mgrep/config.yaml`
```yaml
maxFileSize: 1048576    # 1MB
maxFileCount: 1000
```

### Ignore patterns: `.mgrepignore`
Same syntax as `.gitignore`:
```
node_modules/
*.log
dist/
.env*
```

## Agent Integrations

```bash
mgrep install-claude-code  # Claude Code
mgrep install-opencode     # OpenCode  
mgrep install-codex        # Codex
mgrep install-droid        # Factory Droid
```

## File Type Support

| Type | Support | Notes |
|------|---------|-------|
| Code | ✅ Full | All major languages |
| Text | ✅ Full | .txt, .md, .rst, etc. |
| PDF | ✅ Full | Text extraction |
| Images | ✅ Full | OCR/embedding |
| Audio | 🔜 Coming | Planned |
| Video | 🔜 Coming | Planned |

## Best Practices for Agents

### 1. Start watcher early
```bash
mgrep watch &  # Background indexing
```

### 2. Use semantic queries
```bash
# Good - describes intent
mgrep "user authentication flow"
mgrep "database connection error handling"

# Less effective - too literal
mgrep "def authenticate"
```

### 3. Limit results for context efficiency
```bash
mgrep -m 5 "query"  # Only top 5 results
```

### 4. Use --answer for summaries
```bash
mgrep -a "how does caching work in this project?"
```

### 5. Combine with --agentic for complex questions
```bash
mgrep --agentic "What are all the API endpoints and their authentication requirements?"
```

## Comparison: mgrep vs grep vs ripgrep

| Feature | grep | ripgrep | mgrep |
|---------|------|---------|-------|
| Speed | Slow | Fast | Moderate |
| Pattern | Exact/Regex | Exact/Regex | Semantic |
| Intent | ❌ | ❌ | ✅ |
| PDF/Images | ❌ | ❌ | ✅ |
| Web search | ❌ | ❌ | ✅ |
| Token efficiency | Low | Low | High |

## Troubleshooting

### "No results found"
- Ensure `mgrep watch` is running
- Check `.mgrepignore` for exclusions
- Rephrase query semantically

### "Store not found"
- Run `mgrep watch` to create store
- Check `MXBAI_STORE` environment variable

### Slow indexing
- Reduce `--max-file-count`
- Add large files to `.mgrepignore`
- Exclude `node_modules`, `vendor`, etc.

### Authentication issues
- Run `mgrep logout` then `mgrep login`
- For CI: ensure `MXBAI_API_KEY` is set
