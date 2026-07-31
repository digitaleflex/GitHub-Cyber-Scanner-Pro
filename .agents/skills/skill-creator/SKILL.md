---
name: skill-creator
# prettier-ignore
description: Design and create Agent Skills using progressive disclosure principles. Use when building new skills, planning skill architecture, or writing skill content.
---

# Skill Creator

Create effective Agent Skills using progressive disclosure.

## When to Create a Skill

Create a skill when you notice:

- **Repeating context** across conversations
- **Domain expertise** needed repeatedly
- **Project-specific knowledge** the agent should know automatically

## Progressive Disclosure

Skills load in 3 levels:

1. **Metadata** (~27 tokens) - YAML frontmatter for triggering
2. **Instructions** (<680 tokens) - SKILL.md body with core patterns
3. **Resources** (unlimited) - references/ scripts/ assets/ loaded on
   demand

**Key**: Keep Levels 1 & 2 lean. Move details to Level 3.

## Structure

```
my-skill/
├── SKILL.md       # Core instructions + metadata
├── references/    # Detailed docs (loaded as needed)
├── scripts/       # Executable operations
└── assets/        # Templates, images, files
```

## References

- [quick-start.md](references/quick-start.md) - Creating your first
  skill
- [writing-guide.md](references/writing-guide.md) - Writing effective
  skills
- [development-process.md](references/development-process.md) -
  Step-by-step workflow
- [skill-examples.md](references/skill-examples.md) - Patterns and
  examples
- [cli-reference.md](references/cli-reference.md) - CLI tool usage
- [agent-skills-resources.md](references/agent-skills-resources.md) -
  Architecture and best practices
