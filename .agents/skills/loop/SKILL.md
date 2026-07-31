---
name: loop
description: Run any task iteratively until completion using Ralph Wiggum methodology. Executes tasks in a persistent loop where the AI receives the same prompt repeatedly, seeing its previous work in files and git history, enabling self-correction and incremental progress until a completion signal is detected. Use when tasks require multiple iterations, complex multi-step work that benefits from self-correction, tasks with verifiable success criteria (tests, builds, linters), long-running autonomous work, or iterative refinement tasks like getting tests to pass.
---

# Loop Skill

Execute any task iteratively until completion using the Ralph Wiggum methodology.

## Core Concept

The loop methodology repeatedly sends the **same prompt** to OpenCode until a completion promise is detected or max iterations reached. Each iteration, the AI sees its previous work in modified files and git history, creating a feedback loop for self-correction.

```
while not complete and iterations < max:
    run opencode with prompt
    check for completion promise in output
    iterations++
```

## Quick Start

### Basic Loop Execution

```bash
# Run task with default settings (max 10 iterations)
ralph "Build feature X. Output <promise>DONE</promise> when complete." --max-iterations 10

# With prompt file for complex tasks
ralph --prompt-file task.md --max-iterations 10 --completion-promise COMPLETE
```

### Essential Options

| Option | Description | Default |
|--------|-------------|---------|
| `--max-iterations N` | Stop after N iterations | 10 |
| `--completion-promise TEXT` | Signal phrase for completion | COMPLETE |
| `--prompt-file, -f` | Read prompt from file | - |
| `--allow-all` | Auto-approve tool permissions | false |
| `--no-commit` | Skip auto-commits after iterations | false |
| `--no-stream` | Buffer output, print at end | false |

## Writing Effective Loop Prompts

### Include Clear Success Criteria

```markdown
# Good prompt structure
Build a REST API for todos with:
- CRUD endpoints (GET, POST, PUT, DELETE)
- Input validation
- Tests for each endpoint

Run tests after each change. Output <promise>COMPLETE</promise> when all tests pass.
```

### Use Verifiable Conditions

```markdown
Refactor auth.ts to:
1. Extract validation into separate functions
2. Add error handling for network failures
3. Ensure all existing tests still pass

Output <promise>DONE</promise> when refactored and tests pass.
```

### Always Set Max Iterations

```bash
ralph "Your task" --max-iterations 10
```

## Monitoring Active Loops

### Check Status (from another terminal)

```bash
ralph --status
```

Shows:
- Current iteration number
- Elapsed time
- Prompt summary
- Iteration history with tools used
- Struggle indicators (if agent appears stuck)

### Inject Context Mid-Loop

Guide a struggling agent without stopping:

```bash
ralph --add-context "Focus on fixing the auth module first"
ralph --add-context "The bug is in utils/parser.ts line 42"
```

Context is consumed after one iteration.

### Clear Pending Context

```bash
ralph --clear-context
```

## Common Loop Patterns

### 1. Build Until Tests Pass

```bash
ralph "Implement user authentication with JWT tokens. \
Run 'npm test' after each change. \
Output <promise>COMPLETE</promise> when all tests pass." \
--max-iterations 10
```

### 2. Fix Linting Errors

```bash
ralph "Fix all ESLint errors in the project. \
Run 'npm run lint' to check. \
Output <promise>DONE</promise> when no errors remain." \
--max-iterations 5
```

### 3. Complex Feature Development

```bash
# Create a prompt file for complex tasks
cat > feature.md << 'EOF'
# Task: Implement Shopping Cart

## Requirements
- Add/remove items
- Update quantities  
- Calculate totals with tax
- Persist to localStorage

## Verification
Run `npm test` after changes.

## Completion
Output <promise>FEATURE_COMPLETE</promise> when:
1. All requirements implemented
2. All tests pass
3. No console errors
EOF

ralph -f feature.md --max-iterations 15 --completion-promise FEATURE_COMPLETE
```

### 4. Database Migration

```bash
ralph "Create and run database migrations for the new user schema. \
Verify with 'npm run db:check'. \
Output <promise>MIGRATED</promise> when complete." \
--max-iterations 5 --no-commit
```

### 5. Bug Fixing Loop

```bash
ralph "Fix the login redirect issue reported in #123. \
Test manually and run 'npm test auth'. \
Output <promise>FIXED</promise> when the bug is resolved." \
--max-iterations 8
```

## Best Practices

### When to Use Loops

- Tasks with automatic verification (tests, linters, type checking)
- Well-defined tasks with clear completion criteria
- Greenfield projects where iterative progress works
- Iterative refinement (getting tests to pass)

### When NOT to Use Loops

- Tasks requiring human judgment at each step
- One-shot operations (simple file edits)
- Unclear success criteria
- Production debugging (needs human oversight)

### Prompt Writing Tips

1. **Be specific about success criteria** - What exactly signals completion?
2. **Include verification commands** - "Run `npm test` after each change"
3. **Use clear completion promises** - `<promise>DONE</promise>` or custom text
4. **Break complex tasks into phases** - Run multiple sequential loops if needed

## Troubleshooting

### Agent Stuck in Loop

```bash
# Check status for struggle indicators
ralph --status

# Inject helpful context
ralph --add-context "Try a different approach: use async/await instead"

# Or stop and restart with clearer prompt
# Ctrl+C to stop, then revise prompt
```

### Premature Completion

If agent outputs completion promise too early:
- Make success criteria more specific
- Add verification commands to prompt
- Use automated checks (tests, linters)

### Too Many Iterations

- Break task into smaller sub-tasks
- Add intermediate milestones
- Clarify the prompt with more detail

## Integration with OpenCode

### Use in Prompt Files

```markdown
# Task: Full Stack Feature

Use the loop skill to iterate until completion.

Execute with:
ralph -f this-file.md --max-iterations 10

## Requirements
...

## Completion
Output <promise>COMPLETE</promise> when done.
```

### Combining with Other Skills

```bash
# Use casper skill for pentest, loop until report complete
ralph "Perform security assessment on https://example.com \
using casper methodology. Create full report. \
Output <promise>COMPLETE</promise> when report.md exists with all findings." \
--max-iterations 15
```

## Reference

See `references/ralph-options.md` for complete CLI reference.
