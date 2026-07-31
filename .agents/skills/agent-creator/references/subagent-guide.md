# Subagent Configuration Guide

Complete guide to configuring subagents for agent profiles in AiderDesk.

## SubagentConfig Properties

| Property | Type | Description | Default |
|-----------|------|-------------|----------|
| `enabled` | boolean | Can this profile be used as a subagent? | `true` (always) |
| `contextMemory` | ContextMemoryMode | How much previous conversation context to remember | `"off"` |
| `systemPrompt` | string | Specialized system prompt for this subagent | Empty or specialized |
| `invocationMode` | InvocationMode | When to invoke this subagent | `"on-demand"` |
| `color` | string | Visual identifier (hex or CSS color) | `"#3b82f6"` (blue) |
| `description` | string | Description for automatic invocation | Empty string |

## Context Memory Modes

**Controls how much of previous conversation context is remembered by subagent. 'Full Context' maintains all previous subagents history, 'Last Message' only uses the final messages from previous subagent runs, and 'Off' starts fresh each time.**

### Off (`"off"`)

**Behavior:**
- Subagent starts fresh with no previous conversation history
- No context from previous subagent runs is passed
- Each invocation is completely independent

**When to Use:**
- Tasks are independent and self-contained
- Token cost is a priority
- Previous context isn't relevant to new tasks
- Default for most profiles

**Pros:**
- Lower token cost
- Cleaner context
- No confusion from previous conversations
- Predictable behavior

**Cons:**
- No continuity across multiple invocations
- Cannot reference previous decisions or work

**Examples:**
- Power Tools profile
- Aider profile
- General purpose agents
- Single-task agents

### Last Message (`"last-message"`)

**Behavior:**
- Subagent receives only the final message from previous runs
- Intermediate steps and reasoning are filtered out
- Provides continuity via latest result only

**When to Use:**
- You need the result of previous work but not the full journey
- Want cost savings but still need continuity
- Building upon latest state is sufficient

**Pros:**
- Token-efficient
- Provides continuity via latest result
- Avoids context bloat
- Maintains current state awareness

**Cons:**
- Loses intermediate steps and reasoning
- Cannot reference earlier decisions
- Limited context for complex dependencies

**Examples:**
- Documentation Generator: Builds on latest documentation state
- Status update agents: Only need current state
- Progressive builders: Latest result is sufficient

### Full Context (`"full-context"`)

**Behavior:**
- Subagent receives entire conversation history from previous runs
- All messages, tool calls, and results are preserved
- Maintains complete context awareness

**When to Use:**
- Complex, iterative tasks requiring deep continuity
- Building upon previous decisions and reasoning
- Analysis that needs complete history
- Specialized, expert agents

**Pros:**
- Complete context awareness
- Maintains reasoning and decisions
- Can reference any point in conversation history
- Best for complex, multi-step tasks

**Cons:**
- Higher token cost
- Potential for context bloat
- May include irrelevant information
- Slower processing with large contexts

**Examples:**
- Code Reviewer: Needs full context of what was reviewed before
- Security Auditor: Needs complete context for security analysis
- Debugging agents: Benefits from seeing full conversation history
- Long-running analysis tasks

## Invocation Modes

### On-Demand (`"on-demand"`)
- Only invoked when explicitly requested by user
- Manual control over when to use
- Default for most profiles

**When to Use:**
- General purpose profiles
- Profiles with broad capabilities
- User wants manual control
- Default behavior

### Automatic (`"automatic"`)
- Automatically invoked when relevant to current task
- Based on `description` matching task context
- Requires clear, specific description

**When to Use:**
- Specialized profiles with clear purpose
- Experts for specific domains
- Code Reviewer, Security Auditor, Documentation Generator
- Profiles with narrow, well-defined scope

**Tips for Automatic Invocation:**
- Write clear, specific descriptions
- Include domain keywords (e.g., "security", "code review", "documentation")
- Avoid overly broad descriptions that trigger too frequently
- Focus on the agent's unique value proposition

## System Prompts

A specialized system prompt defines the subagent's role and approach.

**Good System Prompt Characteristics:**
- Clear role definition
- Specific instructions for behavior
- Guidelines for output format
- Constraints and limitations

**Examples:**

```javascript
// Code Reviewer
"You are a code review expert. Analyze changes for correctness, security, and adherence to coding standards. Provide constructive feedback with severity ratings."

// Documentation Generator
"You are a technical documentation specialist. Create comprehensive, user-friendly documentation in Markdown format with proper structure, code blocks, and examples."

// Security Auditor
"You are a security expert. Identify vulnerabilities following OWASP guidelines. Provide severity ratings (Critical, High, Medium, Low) and actionable remediation steps."
```

**Best Practices:**
- Keep prompts focused and specific
- Include output format requirements
- Define the scope clearly
- Mention any constraints or limitations

## Color Selection

Colors help visually distinguish subagents in the UI.

**Common Color Patterns:**
- **Blue** (`#3b82f6`): General purpose, power tools
- **Red** (`#ef4444`): Security, critical tasks
- **Green** (`#10b981`): Success, Aider, positive actions
- **Purple** (`#8b5cf6`): Documentation, creative tasks
- **Yellow/Orange** (`#f59e0b`): Warnings, analysis
- **Gray** (`#6b7280`): Neutral, default

**Color Guidelines:**
- Use colors that match the agent's purpose
- Ensure contrast with UI background
- Avoid overly bright or dark colors
- Keep consistent across similar agent types

## Default Configuration

**Every agent should be a subagent by default:**

```json
{
  "subagent": {
    "enabled": true,
    "contextMemory": "off",
    "systemPrompt": "",
    "invocationMode": "on-demand",
    "color": "#3b82f6",
    "description": ""
  }
}
```

**Adjust Based on Agent Type:**
- **Analysis experts**: `contextMemory: "full-context"`, `invocationMode: "automatic"`
- **Progressive builders**: `contextMemory: "last-message"`, `invocationMode: "automatic"`
- **General purpose**: `contextMemory: "off"`, `invocationMode: "on-demand"`
- **Single-task agents**: `contextMemory: "off"`, `invocationMode: "on-demand"`

## Configuration Checklist

Before finalizing subagent configuration:

- [ ] `enabled` is `true` (every agent is a subagent)
- [ ] `contextMemory` is appropriate for agent type
- [ ] `systemPrompt` is clear and specific
- [ ] `invocationMode` matches agent's intended use
- [ ] `color` is visually distinct and appropriate
- [ ] `description` is clear for automatic invocation (if applicable)

## Common Subagent Patterns

### Analysis Agent
```json
{
  "subagent": {
    "enabled": true,
    "contextMemory": "full-context",
    "systemPrompt": "You are an expert analyst specializing in...",
    "invocationMode": "automatic",
    "color": "#ef4444",
    "description": "Expert analyst for detailed code and security analysis"
  }
}
```

### Documentation Agent
```json
{
  "subagent": {
    "enabled": true,
    "contextMemory": "last-message",
    "systemPrompt": "You are a technical documentation specialist...",
    "invocationMode": "automatic",
    "color": "#8b5cf6",
    "description": "Documentation expert for creating clear, comprehensive docs"
  }
}
```

### General Purpose Agent
```json
{
  "subagent": {
    "enabled": true,
    "contextMemory": "off",
    "systemPrompt": "",
    "invocationMode": "on-demand",
    "color": "#3b82f6",
    "description": ""
  }
}
```

## Integration Notes

- Context messages are collected from both `contextMessages` and `currentMessages`
- Filtered by role='assistant' to find tool-call entries
- Matched by subagent ID to ensure only relevant messages are collected
- Enhanced prompt is added when context is passed: "Make sure to reuse previous conversation if possible."
- Nested subagents are disabled by default to prevent infinite loops
