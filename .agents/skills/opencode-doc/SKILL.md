---
description: Comprehensive OpenCode documentation covering installation, configuration, providers, tools, agents, MCP servers, skills, plugins, SDK, and all features. Use this skill when you need to understand how to use, configure, or extend OpenCode.
name: opencode-doc
---

# OpenCode Documentation Skill

This skill provides comprehensive documentation for OpenCode, an open-source AI coding agent available as a terminal interface, desktop app, or IDE extension.

## Quick Reference

### Installation

```bash
# Install script (recommended)
curl -fsSL https://opencode.ai/install | bash

# Node.js
npm install -g opencode-ai

# Homebrew (macOS/Linux)
brew install anomalyco/tap/opencode

# Windows (Chocolatey)
choco install opencode

# Windows (Scoop)
scoop install opencode

# Docker
docker run -it --rm ghcr.io/anomalyco/opencode
```

### First Run

```bash
cd /path/to/project
opencode
/init  # Initialize project with AGENTS.md
```

### Key Commands

| Command | Description |
|---------|-------------|
| `/init` | Initialize project with AGENTS.md |
| `/connect` | Configure LLM provider credentials |
| `/models` | Select/switch models |
| `/share` | Share conversation |
| `/undo` | Undo last changes |
| `/redo` | Redo undone changes |
| `Tab` | Toggle Plan/Build mode |
| `@` | Fuzzy search files |

---

## Configuration

### Config Locations (Precedence Order)

1. Remote config (`.well-known/opencode`) - organizational defaults
2. Global config (`~/.config/opencode/opencode.json`) - user preferences  
3. Custom config (`OPENCODE_CONFIG` env var)
4. Project config (`opencode.json` in project root)
5. `.opencode` directories - agents, commands, plugins
6. Inline config (`OPENCODE_CONFIG_CONTENT` env var)

### Config File Format

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "theme": "opencode",
  "model": "anthropic/claude-sonnet-4-5",
  "small_model": "anthropic/claude-haiku-4-5",
  "autoupdate": true,
  "share": "manual",
  "default_agent": "code"
}
```

### Variable Substitution

```jsonc
{
  "model": "{env:OPENCODE_MODEL}",
  "provider": {
    "openai": {
      "options": {
        "apiKey": "{file:~/.secrets/openai-key}"
      }
    }
  }
}
```

---

## Providers

OpenCode supports 75+ LLM providers via AI SDK and Models.dev.

### Supported Providers

- **OpenCode Zen** - Curated models tested by OpenCode team
- **Anthropic** - Claude Pro/Max
- **OpenAI** - ChatGPT Plus/Pro
- **Amazon Bedrock**
- **Azure OpenAI**
- **GitHub Copilot**
- **Google Vertex AI**
- **Groq**
- **OpenRouter**
- **DeepSeek**
- **Local Models** - Ollama, LM Studio, llama.cpp

### Configure Provider

```bash
/connect  # In TUI, select provider
```

Credentials stored in: `~/.local/share/opencode/auth.json`

### Custom OpenAI-Compatible Provider

```jsonc
{
  "provider": {
    "myprovider": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "My Provider",
      "options": {
        "baseURL": "https://api.myprovider.com/v1"
      },
      "models": {
        "my-model": {
          "name": "My Model"
        }
      }
    }
  }
}
```

### Local Models (Ollama)

```jsonc
{
  "provider": {
    "ollama": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "Ollama (local)",
      "options": {
        "baseURL": "http://localhost:11434/v1"
      },
      "models": {
        "llama2": { "name": "Llama 2" }
      }
    }
  }
}
```

---

## Tools

### Built-in Tools

| Tool | Description | Permission Key |
|------|-------------|----------------|
| `bash` | Execute shell commands | `bash` |
| `edit` | Modify files with string replacements | `edit` |
| `write` | Create/overwrite files | `edit` |
| `read` | Read file contents | `read` |
| `grep` | Search contents with regex | `grep` |
| `glob` | Find files by pattern | `glob` |
| `list` | List directory contents | `list` |
| `lsp` | LSP code intelligence (experimental) | `lsp` |
| `patch` | Apply patches | `edit` |
| `skill` | Load SKILL.md files | `skill` |
| `todowrite` | Manage task lists | `todowrite` |
| `todoread` | Read task lists | `todoread` |
| `webfetch` | Fetch web content | `webfetch` |
| `question` | Ask user questions | `question` |

### Tool Permissions

```jsonc
{
  "permission": {
    "edit": "ask",      // Require approval
    "bash": "allow",    // Auto-approve
    "webfetch": "deny", // Block tool
    "mymcp_*": "ask"    // Wildcard pattern
  }
}
```

Permission values: `"allow"`, `"deny"`, `"ask"`

---

## MCP Servers

Add external tools via Model Context Protocol.

### Local MCP Server

```jsonc
{
  "mcp": {
    "my-mcp": {
      "type": "local",
      "command": ["npx", "-y", "my-mcp-package"],
      "enabled": true,
      "environment": {
        "MY_VAR": "value"
      }
    }
  }
}
```

### Remote MCP Server

```jsonc
{
  "mcp": {
    "my-remote": {
      "type": "remote",
      "url": "https://mcp.example.com",
      "headers": {
        "Authorization": "Bearer {env:API_KEY}"
      }
    }
  }
}
```

### OAuth Authentication

```bash
opencode mcp auth my-server     # Authenticate
opencode mcp list               # List servers
opencode mcp logout my-server   # Remove credentials
```

### Popular MCP Servers

**Sentry:**
```jsonc
{
  "mcp": {
    "sentry": {
      "type": "remote",
      "url": "https://mcp.sentry.dev/mcp",
      "oauth": {}
    }
  }
}
```

**Context7:**
```jsonc
{
  "mcp": {
    "context7": {
      "type": "remote",
      "url": "https://mcp.context7.com/mcp"
    }
  }
}
```

**Grep by Vercel:**
```jsonc
{
  "mcp": {
    "gh_grep": {
      "type": "remote",
      "url": "https://mcp.grep.app"
    }
  }
}
```

### Per-Agent MCP

```jsonc
{
  "mcp": { "my-mcp": { ... } },
  "tools": { "my-mcp*": false },
  "agent": {
    "my-agent": {
      "tools": { "my-mcp*": true }
    }
  }
}
```

---

## Agents

### Configure Custom Agent

```jsonc
{
  "agent": {
    "code-reviewer": {
      "description": "Reviews code for best practices",
      "model": "anthropic/claude-sonnet-4-5",
      "prompt": "You are a code reviewer...",
      "tools": {
        "write": false,
        "edit": false
      }
    }
  }
}
```

### Agent Files

Create `.opencode/agents/<name>/AGENT.md`:

```markdown
---
name: my-agent
description: My custom agent
model: anthropic/claude-sonnet-4-5
tools:
  bash: true
  edit: true
---

## Instructions

Your custom agent instructions here.
```

### Built-in Agents

- `code` - Default coding agent
- `plan` - Planning mode (no modifications)
- Task agents (subagents)

---

## Skills

Reusable instruction sets loaded on-demand.

### Skill Locations

- Project: `.opencode/skills/<name>/SKILL.md`
- Global: `~/.config/opencode/skills/<name>/SKILL.md`
- Claude-compatible: `.claude/skills/<name>/SKILL.md`

### Create a Skill

```markdown
---
name: my-skill
description: Brief description (1-1024 chars)
license: MIT
compatibility: opencode
metadata:
  key: value
---

## Instructions

Your skill content here.
```

### Skill Name Rules

- 1-64 characters
- Lowercase alphanumeric with single hyphens
- Must match directory name
- Regex: `^[a-z0-9]+(-[a-z0-9]+)*$`

### Skill Permissions

```jsonc
{
  "permission": {
    "skill": {
      "*": "allow",
      "internal-*": "deny"
    }
  }
}
```

---

## Commands

Custom slash commands in `.opencode/commands/`.

### Create Command

`.opencode/commands/my-command.md`:

```markdown
---
name: my-command
description: My custom command
---

Execute this task: $ARGUMENTS
```

### Command Variables

- `$ARGUMENTS` - User-provided arguments
- `$SELECTION` - Selected text/code
- `$FILE` - Current file path

---

## Keybinds

```jsonc
{
  "keybinds": {
    "input:submit": ["enter", "ctrl+enter"],
    "input:newline": ["shift+enter"],
    "session:new": ["ctrl+n"],
    "session:list": ["ctrl+l"],
    "mode:toggle": ["tab"],
    "quit": ["ctrl+c", "ctrl+d"]
  }
}
```

---

## Themes

```jsonc
{
  "theme": "tokyonight"
}
```

Built-in themes: `opencode`, `tokyonight`, `catppuccin`, `gruvbox`, `nord`, `dracula`

Custom themes in `~/.config/opencode/themes/`.

---

## Formatters

Auto-format code after edits:

```jsonc
{
  "formatter": {
    "*.ts": "prettier --write",
    "*.go": "gofmt -w",
    "*.py": "black"
  }
}
```

---

## CLI Commands

```bash
opencode                    # Start TUI
opencode run "prompt"       # Non-interactive
opencode run -p prompt.md   # From file
opencode serve              # Start server
opencode web                # Web interface
opencode auth list          # List credentials
opencode mcp list           # List MCP servers
opencode mcp auth <name>    # Authenticate MCP
```

---

## SDK

```typescript
import { createSession } from "opencode-ai/sdk"

const session = await createSession({
  model: "anthropic/claude-sonnet-4-5"
})

for await (const event of session.chat("Hello")) {
  console.log(event)
}
```

---

## Plugins

```jsonc
{
  "plugin": ["opencode-helicone-session", "@my-org/plugin"]
}
```

Create plugins with hooks for `session.create`, `session.chat`, `tool.call`.

---

## File Reference

All documentation files available in this skill directory:

| File | Topic |
|------|-------|
| `intro.md` | Getting started |
| `config.md` | Configuration |
| `providers.md` | LLM providers |
| `tools.md` | Built-in tools |
| `mcp-servers.md` | MCP integration |
| `agents.md` | Custom agents |
| `skills.md` | Agent skills |
| `commands.md` | Custom commands |
| `keybinds.md` | Keyboard shortcuts |
| `themes.md` | Theme configuration |
| `formatters.md` | Code formatters |
| `permissions.md` | Permission system |
| `lsp.md` | LSP servers |
| `custom-tools.md` | Custom tools |
| `cli.md` | CLI reference |
| `tui.md` | TUI reference |
| `web.md` | Web interface |
| `zen.md` | OpenCode Zen |
| `sdk.md` | SDK reference |
| `server.md` | Server mode |
| `plugins.md` | Plugin development |
| `ecosystem.md` | Ecosystem |
| `github.md` | GitHub integration |
| `gitlab.md` | GitLab integration |
| `share.md` | Sharing |
| `ide.md` | IDE extensions |
| `network.md` | Network config |
| `enterprise.md` | Enterprise |
| `troubleshooting.md` | Troubleshooting |

For detailed information on any topic, read the corresponding markdown file in this skill directory.
