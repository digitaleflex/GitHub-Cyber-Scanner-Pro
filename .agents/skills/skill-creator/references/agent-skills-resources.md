# Agent Skills Resources - Architecture & Best Practices

Key insights into Agent Skills architecture and implementation patterns.

---

## The Progressive Disclosure System

**Core Design Principle**: Skills load information in stages as
needed, rather than consuming context upfront.

### The 3-Level Loading System

| Level  | File                                           | Context Window             | Token Budget | When Loaded   |
| ------ | ---------------------------------------------- | -------------------------- | ------------ | ------------- |
| **1**  | SKILL.md Metadata (YAML)                       | Always loaded              | ~100 tokens  | At startup    |
| **2**  | SKILL.md Body (Markdown)                       | Loaded when skill triggers | <5k tokens   | When relevant |
| **3+** | Bundled files (references/, scripts/, assets/) | Loaded as needed by the agent | Unlimited\*  | On-demand     |

\*No practical limit - files only load when accessed

### Why This Matters

> "Like a well-organized manual that starts with a table of contents,
> then specific chapters, and finally a detailed appendix, skills let
> agents load information only as needed."

**Benefits**:

- You can install many skills without context penalty
- The agent only knows each skill exists and when to use it (Level 1)
- Detailed content doesn't consume tokens until needed
- Effectively unbounded context per skill (via Level 3)

---

## How Skills Work

### Skill Discovery and Loading

1. **Startup**: The agent pre-loads `name` and `description` of every
   installed skill into system prompt
2. **User request**: User makes a request that might need a skill
3. **Skill matching**: The agent scans available skills to find relevant
   matches
4. **Skill loading**: If relevant, the agent reads SKILL.md from
   filesystem via bash
5. **On-demand access**: The agent reads additional files (references/,
   scripts/) as needed

### The Filesystem Architecture

Skills run in a code execution environment where the agent has:

- **Filesystem access**: Skills exist as directories on the file system
- **Bash commands**: The agent uses bash to read files and execute
  scripts
- **Code execution**: Scripts run without loading code into context

**How the agent accesses content**:

```bash
# Agent triggers skill by reading SKILL.md
bash: cat pdf-skill/SKILL.md

# Agent reads additional references if needed
bash: cat pdf-skill/references/forms.md

# Agent executes scripts (only output enters context)
bash: node pdf-skill/scripts/validate_form.js
```

**Key insight**: Script code never enters the context window. Only the
output does. This makes scripts far more token-efficient than
generating equivalent code on the fly.

---

## Best Practices

Based on agent skills architecture and implementation experience:

### 1. Start with Evaluation

Identify specific gaps in agent capabilities by running them
on representative tasks and observing where they struggle or require
additional context. Then build skills incrementally to address these
shortcomings.

**Process**:

- Use the agent on real tasks
- Notice where it struggles
- Create skills to fill gaps
- Test and iterate

### 2. Structure for Scale

> "When the SKILL.md file becomes unwieldy, split its content into
> separate files and reference them."

**Guidelines**:

- Keep SKILL.md under ~5k words
- Split mutually exclusive contexts into separate files
- Use code for both execution and documentation
- Make it clear whether the agent should run or read scripts

### 3. Think from the agent's Perspective

> "Monitor how the agent uses your skill in real scenarios and iterate
> based on observations: watch for unexpected trajectories or
> overreliance on certain contexts."

**Key areas**:

- `name` and `description` drive skill triggering
- the agent decides whether to use the skill based on metadata
- Observe actual usage patterns, not assumed ones

### 4. Iterate with the agent

> "As you work on a task with the agent, ask the agent to capture its
> successful approaches and common mistakes into reusable context and
> code within a skill."

**Workflow**:

1. Work on task with the agent
2. Notice successful patterns
3. Ask the agent to capture them in skill
4. Test and refine

---

## Writing for the agent

### Skills as "Onboarding Guides"

> "Building a skill for an agent is like putting together an
> onboarding guide for a new hire."
>
> — Anthropic Engineering Blog

**What this means**:

- Focus on procedural knowledge ("how to do X")
- Include workflows, not just facts
- Provide examples of actual usage
- Capture organizational context

### Skills Transform General → Specialized Agents

> "Skills extend the agent's capabilities by packaging your expertise
> into composable resources for the agent, transforming general-purpose
> agents into specialized agents that fit your needs."

**Examples**:

- General the agent + Database skill = Database specialist
- General the agent + Auth skill = Security specialist
- General the agent + UI skill = Frontend specialist

---

## The Skill Anatomy

### Required Structure

Every skill must have:

```
skill-name/
└── SKILL.md          # Required
```

SKILL.md must have:

```markdown
---
name: skill-name
description: What it does and when to use it
---

# Skill content...
```

### Frontmatter Limits

| Field         | Limit           | Required |
| ------------- | --------------- | -------- |
| `name`        | 64 characters   | Yes      |
| `description` | 1024 characters | Yes      |

Only `name` and `description` are supported. No other YAML fields.

### Optional Bundled Content

```
skill-name/
├── SKILL.md                    # Level 2: Instructions
├── references/                 # Level 3: Documentation
│   ├── detailed-guide.md
│   └── api-reference.md
├── scripts/                    # Level 3: Executable code
│   ├── validate.js
│   └── generate.sh
└── assets/                     # Level 3: Resources
    ├── template.json
    └── diagram.png
```

---

## Context Window Behavior

### How the Context Window Changes

From Anthropic's documentation:

**Initial state**:

```
[System Prompt]
[Skill 1 Metadata]
[Skill 2 Metadata]
[Skill N Metadata]
[User Message]
```

**After skill triggers**:

```
[System Prompt]
[Skill Metadata (all skills)]
[User Message]
[SKILL.md Body]              ← Loaded via bash
[references/forms.md]        ← Loaded as needed
```

**Key point**: Metadata for ALL skills is always loaded. Only
triggered skills load their SKILL.md body.

---

## Progressive Disclosure in Practice

### Example: PDF Skill

**Level 1 (Always):**

```yaml
name: pdf
description:
  Extract text and tables from PDF files, fill forms, merge documents.
  Use when working with PDF files.
```

~100 tokens

**Level 2 (When triggered):**

```markdown
# PDF Processing

## Quick Start

Use pdfplumber to extract text...

For form filling, see [forms.md](forms.md)
```

~3k tokens

**Level 3 (As needed):**

- `references/forms.md` - Form-filling guide (only if filling forms)
- `scripts/extract_fields.js` - Executable script (runs, doesn't load)

**Total token cost if NOT filling forms**: ~3,100 tokens (Level 1 +
Level 2) **Total token cost if filling forms**: ~6,000 tokens (Level
1 + Level 2 + forms.md)

---

## Code Execution in Skills

### Why Include Scripts

> "Large language models excel at many tasks, but certain operations
> are better suited for traditional code execution. For example,
> sorting a list via token generation is far more expensive than
> simply running a sorting algorithm."
>
> — Anthropic Engineering Blog

**When to use scripts**:

- **Efficiency**: Operations that are cheaper to execute than generate
- **Determinism**: Tasks requiring consistent, repeatable results
- **Complexity**: Algorithms better suited to code than token
  generation

### Script Execution Model

```bash
# the agent runs script
bash: node scripts/validate_form.js form.pdf

# Output (only this enters context)
✅ All form fields valid
Found 12 fillable fields
```

**Context consumed**: ~20 tokens (just the output) **Alternative
(the agent generates validation code)**: ~500 tokens

**50x more efficient**

---

## Security Considerations

From Anthropic's security guidelines:

### Trusted Sources Only

> "We strongly recommend using Skills only from trusted sources: those
> you created yourself or obtained from Anthropic."

**Risk**: Malicious skills can:

- Direct the agent to invoke tools in harmful ways
- Execute code with unintended effects
- Exfiltrate data to external systems
- Compromise system security

### Auditing Third-Party Skills

If you must use untrusted skills:

1. **Review all files**: SKILL.md, scripts, images, bundled resources
2. **Check for unusual patterns**:
   - Unexpected network calls
   - File access beyond skill scope
   - Operations not matching stated purpose
3. **Examine external sources**: Skills fetching from URLs are risky
4. **Verify dependencies**: Check code dependencies and imports

### Runtime Constraints

Skills run in the code execution container with:

- ❌ **No network access**: Cannot make external API calls
- ❌ **No runtime package installation**: Only pre-installed packages
  available
- ✅ **Sandboxed execution**: Isolated from host system

---

## Skills are Composable

> "Skills stack together. the agent automatically identifies which skills
> are needed and coordinates their use."

### Example: Multi-Skill Task

**User request**: "Create a GitHub contact card with database-backed
favorites"

**Skills activated**:

1. `github-integration` - Fetch profile data
2. `database-patterns` - Query favorites table
3. `ui-components` - Build card component
4. `styling-patterns` - Apply CSS/styles

**Result**: Skills work together naturally, each handling its domain.

---

## Where Skills Work

### AiderDesk

- **Custom Skills**: Filesystem-based (`.aider-desk/skills/` or
  `~/.aider-desk/skills/`)
- **Sharing**: Via git/version control
- **Integration**: Skills are activated through the agent's skill activation system

**Note**: Skills are specific to AiderDesk's implementation and work through the built-in skill management system.

---

## Future of Skills

From Anthropic:

> "Looking further ahead, we hope to enable agents to create, edit,
> and evaluate Skills on their own, letting them codify their own
> patterns of behavior into reusable capabilities."

**Coming soon**:

- Simplified skill creation workflows
- Enterprise-wide deployment
- Skills complement MCP for complex workflows
- Agents creating their own skills

---

## Key Quotes

### On Progressive Disclosure

Progressive disclosure is the core design principle that makes
Agent Skills flexible and scalable.

### On Simplicity

Skills are a simple concept with a correspondingly simple format.
This simplicity makes it easier for organizations, developers, and
end users to build customized agents and give them new
capabilities.

### On Filesystem Architecture

Agents with a filesystem and code execution tools don't need to
read the entirety of a skill into their context window when working
on a particular task. This means that the amount of context that can
be bundled into a skill is effectively unbounded.

### On Purpose

Think of Skills as custom onboarding materials that let you package
expertise, making the agent a specialist on what matters most to you.

---

## Summary: Agent Skills Philosophy

**Skills are**:

- Composable (stack together)
- Portable (same format everywhere)
- Efficient (only load what's needed)
- Powerful (include executable code)

**Build like**:

- Onboarding guides (procedural knowledge)
- Specialized tools (domain expertise)
- Reference manuals (progressive detail)

**Optimize for**:

- Token efficiency (3-level loading)
- the agent's perspective (discovery via metadata)
- Real usage (iterate based on observation)
- Scalability (split when too large)
