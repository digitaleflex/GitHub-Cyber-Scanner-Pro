# Tool Approval Configuration Guide

Complete guide to configuring tool approvals for agent profiles.

## Overview

Tool approvals control when and how an agent can use specific tools. Each tool can be set to one of three states:

1. **Always** - Auto-approve tool usage without prompting
2. **Ask** - Prompt user for approval each time the tool is used (DEFAULT)
3. **Never** - Disable the tool completely

**Important**: The default value is "ask". You only need to explicitly set tools to "always" or "never" based on the agent's needs.

## Tool Approval States

### Always (`"always"`)
- Tool executes immediately without user confirmation
- Best for safe, read-only operations
- Reduces friction for trusted actions

**Use cases:**
- Reading files (`file_read`)
- Searching code (`semantic_search`, `grep`)
- Finding files (`glob`)

### Ask (`"ask"`)
- Prompts user before each tool execution
- Provides transparency and control
- Ideal for potentially destructive operations

**Use cases:**
- Editing files (`file_edit`)
- Running commands (`bash`)
- Aider operations (`aider:run`)
- External requests (`fetch`)

### Never (`"never"`)
- Tool is completely disabled for the profile
- Cannot be used even with manual approval
- Useful for restricting dangerous capabilities

**Use cases:**
- Shell commands for read-only profiles
- Network access in air-gapped environments
- File editing in review-only agents

## Tool Groups and Their Tools

### Power Tools (`power---*`)

Direct file system and system operations.

| Tool | Recommended Default | When to Use "Always" | When to Use "Ask" | When to Use "Never" |
|------|-------------------|---------------------|-------------------|---------------------|
| `power---file_read` | **always** | Most profiles | Default | Air-gapped systems |
| `power---file_write` | ask | Trusted contexts | Default | Review-only agents |
| `power---file_edit` | ask | Trusted contexts | Default | Review-only agents |
| `power---glob` | **always** | Most profiles | Default | None |
| `power---grep` | **always** | Most profiles | Default | None |
| `power---semantic_search` | **always** | Most profiles | Default | None |
| `power---bash` | ask | Trusted scripts | Default | Read-only profiles |
| `power---fetch` | ask | Trusted domains | Default | Air-gapped systems |

**Recommended Patterns:**

```json
// Full access profile
{
  "toolApprovals": {
    "power---file_read": "always",
    "power---file_write": "ask",
    "power---file_edit": "ask",
    "power---glob": "always",
    "power---grep": "always",
    "power---semantic_search": "always",
    "power---bash": "ask",
    "power---fetch": "ask"
  }
}

// Read-only profile
{
  "toolApprovals": {
    "power---file_read": "always",
    "power---file_write": "never",
    "power---file_edit": "never",
    "power---glob": "always",
    "power---grep": "always",
    "power---semantic_search": "always",
    "power---bash": "never",
    "power---fetch": "always"
  }
}
```

### Aider Tools (`aider---*`)

AI-powered code generation via Aider.

| Tool | Recommended Default | When to Use "Always" | When to Use "Ask" | When to Use "Never" |
|------|-------------------|---------------------|-------------------|---------------------|
| `aider---add_context_files` | **always** | Auto-building context | Default | N/A |
| `aider---remove_context_files` | ask | Bulk operations | Default | N/A |
| `aider---run` | ask | Trusted contexts | Default | Non-Aider profiles |
| `aider---get_diff` | **always** | Always helpful | Default | N/A |

**Recommended Patterns:**

```json
// Full Aider profile
{
  "toolApprovals": {
    "aider---add_context_files": "always",
    "aider---remove_context_files": "ask",
    "aider---run": "ask",
    "aider---get_diff": "always"
  }
}

// Aider with auto-approve (advanced users)
{
  "toolApprovals": {
    "aider---add_context_files": "always",
    "aider---remove_context_files": "always",
    "aider---run": "always",
    "aider---get_diff": "always"
  }
}
```

### Subagents Tools (`subagents---*`)

Task delegation to specialized subagents.

| Tool | Recommended Default | When to Use "Always" | When to Use "Ask" | When to Use "Never" |
|------|-------------------|---------------------|-------------------|---------------------|
| `subagents---run_task` | **always** | Trusted subagents | Default | Subagent-free profiles |

**Recommended Patterns:**

```json
// With subagent delegation
{
  "toolApprovals": {
    "subagents---run_task": "always"
  }
}

// Manual subagent control
{
  "toolApprovals": {
    "subagents---run_task": "ask"
  }
}
```

### Memory Tools (`memory---*`)

Persistent information storage and retrieval.

| Tool | Recommended Default | When to Use "Always" | When to Use "Ask" | When to Use "Never" |
|------|-------------------|---------------------|-------------------|---------------------|
| `memory---store_memory` | **always** | Learning preferences | Default | Stateless profiles |
| `memory---retrieve_memory` | **always** | Always helpful | Default | Stateless profiles |
| `memory---delete_memory` | **always** | Always helpful | Default | Stateless profiles |
| `memory---list_memories` | **always** | Always helpful | Default | Stateless profiles |
| `memory---update_memory` | **always** | Always helpful | Default | Stateless profiles |

**Recommended Patterns:**

```json
// Full memory support
{
  "toolApprovals": {
    "memory---store_memory": "always",
    "memory---retrieve_memory": "always",
    "memory---delete_memory": "always",
    "memory---list_memories": "always",
    "memory---update_memory": "always"
  }
}

// Stateless profile (no memory)
{
  "useMemoryTools": false
  // toolApprovals not needed for memory tools when disabled
}
```

### Skills Tools (`skills---*`)

Access to project-specific skills.

| Tool | Recommended Default | When to Use "Always" | When to Use "Ask" | When to Use "Never" |
|------|-------------------|---------------------|-------------------|---------------------|
| `skills---activate_skill` | **always** | Auto-skills | Default | No custom skills |

**Recommended Patterns:**

```json
// With skills
{
  "toolApprovals": {
    "skills---activate_skill": "always"
  }
}
```

### Task Tools (`task---*`)

Task management and tracking.

| Tool | Recommended Default | When to Use "Always" | When to Use "Ask" | When to Use "Never" |
|------|-------------------|---------------------|-------------------|---------------------|
| `task---complete_task` | **always** | Always helpful | Default | N/A |
| `task---pause_task` | **always** | Always helpful | Default | N/A |

### Todo Tools (`todo---*`)

Todo list management.

| Tool | Recommended Default | When to Use "Always" | When to Use "Ask" | When to Use "Never" |
|------|-------------------|---------------------|-------------------|---------------------|
| `todo---add_todo` | **always** | Always helpful | Default | N/A |
| `todo---complete_todo` | **always** | Always helpful | Default | N/A |
| `todo---list_todos` | **always** | Always helpful | Default | N/A |

## Tool Settings

Some tools support additional configuration beyond approval states.

### Bash Tool Settings

Control which shell commands can be executed.

```json
{
  "toolSettings": {
    "power---bash": {
      "allowedPattern": "^(git|npm|ls|cat|echo)\\s",
      "deniedPattern": "(rm -rf|dd|mkfs|format)"
    }
  }
}
```

**Components:**
- `allowedPattern` - Regex pattern for allowed commands (empty = all allowed)
- `deniedPattern` - Regex pattern for denied commands (overrides allowed)

**Examples:**

```json
// Allow only git commands
{
  "power---bash": {
    "allowedPattern": "^git\\s",
    "deniedPattern": ""
  }
}

// Block dangerous commands
{
  "power---bash": {
    "allowedPattern": "",
    "deniedPattern": "(rm -rf|--force|dd|mkfs|format)"
  }
}
```

## Best Practices

### 1. Start Conservative
Begin with "ask" for most tools, then relax as trust builds.

### 2. Profile-Specific Defaults
Different profiles need different defaults:

- **Code Reviewer**: Read-only, always for search tools
- **Developer**: Ask for edits, always for read operations
- **Auditor**: Never for destructive tools, always for analysis

### 3. Group-Level Control
Use tool group toggles (`usePowerTools`, `useAiderTools`, etc.) before configuring individual tools.

### 4. Context Awareness
Consider:
- Environment (development vs production)
- User expertise level
- Project criticality
- Security requirements

### 5. Review Regularly
Periodically audit tool approvals:
- Remove unused "never" tools
- Relax "ask" to "always" for trusted operations
- Add restrictions for security concerns

## Common Configurations

### Safe Development Profile
```json
{
  "toolApprovals": {
    "power---file_read": "always",
    "power---file_write": "ask",
    "power---file_edit": "ask",
    "power---glob": "always",
    "power---grep": "always",
    "power---semantic_search": "always",
    "power---bash": "ask",
    "power---fetch": "ask",
    "memory---store_memory": "always",
    "memory---retrieve_memory": "always"
  }
}
```

### Read-Only Auditor Profile
```json
{
  "toolApprovals": {
    "power---file_read": "always",
    "power---file_write": "never",
    "power---file_edit": "never",
    "power---glob": "always",
    "power---grep": "always",
    "power---semantic_search": "always",
    "power---bash": "never",
    "power---fetch": "ask"
  }
}
```

### Automated Agent Profile
```json
{
  "toolApprovals": {
    "power---file_read": "always",
    "power---file_write": "always",
    "power---file_edit": "always",
    "power---glob": "always",
    "power---grep": "always",
    "power---semantic_search": "always",
    "power---bash": "never",
    "power---fetch": "always",
    "subagents---run_task": "always"
  },
  "toolSettings": {
    "power---bash": {
      "allowedPattern": "",
      "deniedPattern": ".*"
    }
  }
}
```

## Troubleshooting

### Tool Not Available
**Issue**: Agent tries to use a tool marked "never"

**Solution**:
1. Check `toolApprovals` in profile config
2. Verify tool group is enabled (e.g., `usePowerTools: true`)
3. Update tool approval to "ask" or "always"

### Excessive Prompts
**Issue**: Too many approval prompts during workflow

**Solution**:
1. Identify frequently-used tools
2. Change "ask" to "always" for trusted operations
3. Consider creating specialized profiles for different tasks

### Tool Executes Unexpectedly
**Issue**: Tool runs without confirmation

**Solution**:
1. Review `toolApprovals` for "always" settings
2. Change to "ask" for better control
3. Implement `toolSettings` restrictions if needed

### Bash Command Blocked
**Issue**: Shell command is denied

**Solution**:
1. Check `allowedPattern` regex
2. Review `deniedPattern` restrictions
3. Adjust patterns to permit necessary commands
