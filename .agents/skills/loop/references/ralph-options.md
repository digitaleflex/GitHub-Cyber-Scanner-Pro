# Ralph CLI Complete Reference

## Installation

```bash
# npm (recommended)
npm install -g @th0rgal/ralph-wiggum

# Bun
bun add -g @th0rgal/ralph-wiggum

# From source
git clone https://github.com/Th0rgal/opencode-ralph-wiggum
cd opencode-ralph-wiggum
./install.sh  # or install.ps1 on Windows
```

## Prerequisites

- [Bun](https://bun.sh/) runtime
- [OpenCode](https://opencode.ai/) CLI

## Command Syntax

```
ralph "<prompt>" [options]
ralph --prompt-file <path> [options]
ralph --status
ralph --add-context "<hint>"
ralph --clear-context
```

## Options Reference

### Core Options

| Option | Short | Description |
|--------|-------|-------------|
| `--max-iterations N` | | Stop after N iterations (default: unlimited) |
| `--completion-promise TEXT` | | Phrase that signals completion (default: COMPLETE) |
| `--prompt-file PATH` | `-f` | Read prompt content from a file |
| `--model MODEL` | | Model to use (e.g., anthropic/claude-sonnet) |

### Execution Options

| Option | Description |
|--------|-------------|
| `--allow-all` | Auto-approve all tool permissions (for non-interactive use) |
| `--no-stream` | Buffer OpenCode output and print at the end |
| `--verbose-tools` | Print every tool line (disable compact tool summary) |
| `--no-plugins` | Disable non-auth OpenCode plugins for this run |
| `--no-commit` | Don't auto-commit after each iteration |

### Control Commands

| Command | Description |
|---------|-------------|
| `--status` | Show current Ralph loop status and history |
| `--add-context TEXT` | Add context for the next iteration |
| `--clear-context` | Clear any pending context |
| `--version`, `-v` | Show version |
| `--help`, `-h` | Show help |

## Status Dashboard

When running `ralph --status`, you see:

```
╔══════════════════════════════════════════════════════════════════╗
║                    Ralph Wiggum Status                           ║
╚══════════════════════════════════════════════════════════════════╝

🔄 ACTIVE LOOP
   Iteration:    3 / 10
   Elapsed:      5m 23s
   Promise:      COMPLETE
   Prompt:       Build a REST API...

📊 HISTORY (3 iterations)
   Total time:   5m 23s

   Recent iterations:
   🔄 #1: 2m 10s | Bash:5 Write:3 Read:2
   🔄 #2: 1m 45s | Edit:4 Bash:3 Read:2
   🔄 #3: 1m 28s | Bash:2 Edit:1

⚠️  STRUGGLE INDICATORS:
   - No file changes in 3 iterations
   💡 Consider using: ralph --add-context "your hint here"
```

## State Files

During operation, Ralph stores state in `.opencode/`:

| File | Purpose |
|------|---------|
| `ralph-loop.state.json` | Active loop state |
| `ralph-history.json` | Iteration history and metrics |
| `ralph-context.md` | Pending context for next iteration |

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Completion promise detected |
| 1 | Max iterations reached without completion |
| 2 | Error during execution |

## Examples

### Basic Task

```bash
ralph "Create a hello.txt file with 'Hello World'. \
Output <promise>DONE</promise> when complete." \
--max-iterations 5
```

### Complex Feature

```bash
ralph "Build a REST API for todos with CRUD operations and tests. \
Run tests after each change. \
Output <promise>COMPLETE</promise> when all tests pass." \
--max-iterations 20
```

### From Prompt File

```bash
ralph --prompt-file feature-spec.md \
--max-iterations 15 \
--completion-promise FEATURE_DONE
```

### Non-Interactive (CI/CD)

```bash
ralph "Run linter and fix all errors. \
Output <promise>LINTED</promise> when clean." \
--max-iterations 5 \
--allow-all \
--no-commit
```

### With Specific Model

```bash
ralph "Implement authentication system. \
Output <promise>AUTH_COMPLETE</promise> when done." \
--model anthropic/claude-sonnet \
--max-iterations 10
```

## Prompt File Format

Prompt files are markdown with the task description:

```markdown
# Feature: User Authentication

## Requirements
- JWT-based authentication
- Login/logout endpoints
- Password hashing with bcrypt
- Refresh token rotation

## Verification
Run `npm test` after each change.

## Completion
Output <promise>AUTH_COMPLETE</promise> when:
1. All requirements implemented
2. All tests pass
3. No security vulnerabilities in code
```

## Best Practices

1. **Always set max-iterations** - Prevents runaway loops
2. **Use specific completion promises** - Avoid false positives
3. **Include verification steps** - "Run `npm test` after changes"
4. **Break complex tasks** - Multiple focused loops > one large loop
5. **Monitor with --status** - Check progress from another terminal
6. **Use --add-context** - Guide struggling agents without stopping

## Troubleshooting

### "bun: command not found"

Install Bun: https://bun.sh/

### "ralph-wiggum" plugin errors

This package is CLI-only. Remove from OpenCode plugins or use:

```bash
ralph "Your task" --no-plugins
```

### Agent keeps looping

- Check if completion promise matches exactly
- Make success criteria more verifiable
- Add automated checks to the prompt
