# Agent Profile Examples

Complete examples of different agent profile types for AiderDesk.

## 1. Power Tools Profile

Use case: Direct file system access and system operations.

```json
{
  "id": "power-tools-profile",
  "name": "Power Tools",
  "provider": "anthropic",
  "model": "claude-sonnet-4-5-20250929",
  "maxIterations": 250,
  "minTimeBetweenToolCalls": 0,
  "enabledServers": [],
  "toolApprovals": {
    "power---file_edit": "always",
    "power---file_write": "always",
    "power---file_read": "always",
    "power---glob": "always",
    "power---grep": "always",
    "power---bash": "ask",
    "power---semantic_search": "always",
    "power---fetch": "ask"
  },
  "toolSettings": {},
  "includeContextFiles": true,
  "includeRepoMap": true,
  "usePowerTools": true,
  "useAiderTools": false,
  "useTodoTools": true,
  "useSubagents": false,
  "useTaskTools": true,
  "useMemoryTools": true,
  "useSkillsTools": true,
  "customInstructions": "",
  "subagent": {
    "enabled": false,
    "contextMemory": "last-message",
    "systemPrompt": "",
    "invocationMode": "on-demand",
    "color": "#3b82f6",
    "description": ""
  }
}
```

**Key characteristics:**
- `usePowerTools: true` enables the full power tools group
- Most file operations set to "always" approve
- Shell commands set to "ask" for safety
- No Aider tools, uses direct file manipulation
- Includes memory and skills for enhanced capabilities

---

## 2. Aider Profile

Use case: AI-powered code generation using Aider's advanced capabilities.

```json
{
  "id": "aider-profile",
  "name": "Aider",
  "provider": "anthropic",
  "model": "claude-sonnet-4-5-20250929",
  "maxIterations": 250,
  "minTimeBetweenToolCalls": 0,
  "enabledServers": [],
  "toolApprovals": {
    "aider---add_context_files": "always",
    "aider---remove_context_files": "ask",
    "aider---run": "ask",
    "aider---get_diff": "always",
    "power---file_read": "always",
    "power---glob": "always",
    "power---grep": "always",
    "power---semantic_search": "always",
    "power---fetch": "ask"
  },
  "toolSettings": {},
  "includeContextFiles": true,
  "includeRepoMap": true,
  "usePowerTools": false,
  "useAiderTools": true,
  "useTodoTools": true,
  "useSubagents": false,
  "useTaskTools": true,
  "useMemoryTools": true,
  "useSkillsTools": true,
  "customInstructions": "",
  "subagent": {
    "enabled": false,
    "contextMemory": "last-message",
    "systemPrompt": "",
    "invocationMode": "on-demand",
    "color": "#10b981",
    "description": ""
  }
}
```

**Key characteristics:**
- `useAiderTools: true` enables Aider-specific tools
- `usePowerTools: false` - relies on Aider for file operations
- Limited power tools: only read-only operations
- Aider operations set to "ask" for review before execution
- Perfect for code refactoring and feature development

---

## 3. Code Reviewer Subagent

Use case: Specialized subagent for code review tasks.

```json
{
  "id": "code-reviewer",
  "name": "Code Reviewer",
  "provider": "anthropic",
  "model": "claude-sonnet-4-5-20250929",
  "maxIterations": 150,
  "minTimeBetweenToolCalls": 0,
  "maxTokens": 8192,
  "temperature": 0.3,
  "enabledServers": [],
  "toolApprovals": {
    "power---file_read": "always",
    "power---file_edit": "never",
    "power---bash": "never",
    "power---grep": "always",
    "power---semantic_search": "always",
    "power---fetch": "ask"
  },
  "toolSettings": {},
  "includeContextFiles": true,
  "includeRepoMap": true,
  "usePowerTools": true,
  "useAiderTools": false,
  "useTodoTools": false,
  "useSubagents": false,
  "useTaskTools": false,
  "useMemoryTools": true,
  "useSkillsTools": false,
  "customInstructions": "Focus on code quality, security, and best practices. Provide constructive feedback.",
  "subagent": {
    "enabled": true,
    "contextMemory": "full-context",
    "systemPrompt": "You are a code review expert. Analyze changes for correctness, security, and adherence to coding standards. Identify bugs, potential issues, and improvement opportunities. Be constructive and actionable.",
    "invocationMode": "automatic",
    "color": "#ef4444",
    "description": "Expert code review specialist focused on quality and security"
  }
}
```

**Key characteristics:**
- `subagent.enabled: true` for delegation
- `invocationMode: automatic` - triggers automatically for code reviews
- `contextMemory: full-context` - sees entire conversation
- Lower `maxIterations` (150) and `temperature` (0.3) for focused analysis
- Read-only tools (no editing or shell commands)
- Specialized system prompt for code review

---

## 4. Documentation Generator

Use case: Generating and updating documentation.

```json
{
  "id": "doc-generator",
  "name": "Documentation Generator",
  "provider": "anthropic",
  "model": "claude-sonnet-4-5-20250929",
  "maxIterations": 200,
  "minTimeBetweenToolCalls": 0,
  "maxTokens": 16384,
  "temperature": 0.5,
  "enabledServers": ["filesystem"],
  "toolApprovals": {
    "power---file_edit": "always",
    "power---file_write": "always",
    "power---file_read": "always",
    "power---glob": "always",
    "power---grep": "always",
    "power---semantic_search": "always",
    "power---bash": "never",
    "power---fetch": "always"
  },
  "toolSettings": {},
  "includeContextFiles": true,
  "includeRepoMap": false,
  "usePowerTools": true,
  "useAiderTools": false,
  "useTodoTools": true,
  "useSubagents": false,
  "useTaskTools": false,
  "useMemoryTools": true,
  "useSkillsTools": true,
  "customInstructions": "Generate clear, well-structured documentation in Markdown. Use proper formatting, code blocks, and examples. Maintain consistent style and include relevant diagrams when appropriate.",
  "subagent": {
    "enabled": true,
    "contextMemory": "last-message",
    "systemPrompt": "You are a technical documentation specialist. Create comprehensive, user-friendly documentation that explains concepts clearly and provides practical examples.",
    "invocationMode": "on-demand",
    "color": "#8b5cf6",
    "description": "Technical documentation expert specializing in clear, comprehensive docs"
  }
}
```

**Key characteristics:**
- High `maxTokens` (16384) for long-form content
- Moderate `temperature` (0.5) for creative yet structured output
- File editing enabled, shell commands disabled
- Custom instructions for Markdown formatting
- MCP servers enabled for additional context

---

## 5. Security Auditor

Use case: Security-focused code analysis and vulnerability detection.

```json
{
  "id": "security-auditor",
  "name": "Security Auditor",
  "provider": "anthropic",
  "model": "claude-sonnet-4-5-20250929",
  "maxIterations": 250,
  "minTimeBetweenToolCalls": 100,
  "maxTokens": 8192,
  "temperature": 0.2,
  "enabledServers": ["github"],
  "toolApprovals": {
    "power---file_read": "always",
    "power---file_edit": "never",
    "power---bash": "never",
    "power---grep": "always",
    "power---semantic_search": "always",
    "power---fetch": "always"
  },
  "toolSettings": {
    "power---bash": {
      "allowedPattern": "^$",
      "deniedPattern": ".*"
    }
  },
  "includeContextFiles": true,
  "includeRepoMap": true,
  "usePowerTools": true,
  "useAiderTools": false,
  "useTodoTools": false,
  "useSubagents": false,
  "useTaskTools": false,
  "useMemoryTools": true,
  "useSkillsTools": false,
  "customInstructions": "Focus exclusively on security vulnerabilities, including XSS, SQL injection, authentication issues, authorization flaws, and OWASP Top 10 risks. Provide severity ratings and remediation steps.",
  "subagent": {
    "enabled": true,
    "contextMemory": "full-context",
    "systemPrompt": "You are a security expert specializing in application security. Identify vulnerabilities following OWASP guidelines and industry best practices. Provide clear, actionable remediation steps with severity ratings (Critical, High, Medium, Low).",
    "invocationMode": "automatic",
    "color": "#dc2626",
    "description": "Security specialist focused on vulnerability detection and OWASP compliance"
  }
}
```

**Key characteristics:**
- Very low `temperature` (0.2) for precise analysis
- `minTimeBetweenToolCalls: 100` for rate limiting
- Strict `toolSettings` blocking all bash commands
- Read-only access (no editing capabilities)
- OWASP-focused custom instructions
- Automatic invocation for security context

---

## 6. Minimal Profile

Use case: Basic agent with minimal tool set.

```json
{
  "id": "minimal-profile",
  "name": "Minimal Agent",
  "provider": "anthropic",
  "model": "claude-sonnet-4-5-20250929",
  "maxIterations": 250,
  "minTimeBetweenToolCalls": 0,
  "enabledServers": [],
  "toolApprovals": {},
  "toolSettings": {},
  "includeContextFiles": false,
  "includeRepoMap": false,
  "usePowerTools": false,
  "useAiderTools": false,
  "useTodoTools": false,
  "useSubagents": false,
  "useTaskTools": false,
  "useMemoryTools": false,
  "useSkillsTools": false,
  "customInstructions": "",
  "subagent": {
    "enabled": false,
    "contextMemory": "last-message",
    "systemPrompt": "",
    "invocationMode": "on-demand",
    "color": "#3b82f6",
    "description": ""
  }
}
```

**Key characteristics:**
- All tool groups disabled
- No context files or repo map
- No approvals defined (uses defaults)
- Subagent enabled but not configured
- Base configuration that can be extended

---

## Profile Type Comparison

| Profile Type | Power Tools | Aider Tools | Read-Only | Subagent | Best For |
|--------------|-------------|-------------|-----------|----------|----------|
| Power Tools | ✅ | ❌ | No | ❌ | Direct file operations |
| Aider | ❌ | ✅ | Partial | ❌ | Code generation/refactoring |
| Code Reviewer | ✅ (limited) | ❌ | Yes | ✅ | Code analysis |
| Documentation | ✅ | ❌ | No | ✅ | Writing docs |
| Security Auditor | ✅ (limited) | ❌ | Yes | ✅ | Security analysis |
| Minimal | ❌ | ❌ | Yes | ❌ | Custom configurations |

---

## Common Patterns

### Read-Only Profiles
Set these to "never" in `toolApprovals`:
```json
{
  "power---file_edit": "never",
  "power---file_write": "never",
  "power---bash": "never"
}
```

### Automatic Subagent Invocation
Set in `subagent` config:
```json
{
  "invocationMode": "automatic",
  "description": "Clear description for auto-triggering"
}
```

### High Precision Analysis
Use these settings:
```json
{
  "temperature": 0.1 - 0.3,
  "maxTokens": 8192,
  "maxIterations": 150-200
}
```

### Creative Content Generation
Use these settings:
```json
{
  "temperature": 0.7 - 1.0,
  "maxTokens": 16384,
  "maxIterations": 250-300
}
```
