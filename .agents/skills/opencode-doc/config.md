# Config

Using the OpenCode JSON config.

You can configure OpenCode using a JSON config file.

---

## Format

OpenCode supports both **JSON** and **JSONC** (JSON with Comments) formats.

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  // Theme configuration
  "theme": "opencode",
  "model": "anthropic/claude-sonnet-4-5",
  "autoupdate": true,
}
```

---

## Locations

You can place your config in a couple of different locations and they have a different order of precedence.

> **Note:** Configuration files are **merged together**, not replaced.

### Precedence order

Config sources are loaded in this order (later sources override earlier ones):

1. **Remote config** (from `.well-known/opencode`) - organizational defaults
2. **Global config** (`~/.config/opencode/opencode.json`) - user preferences
3. **Custom config** (`OPENCODE_CONFIG` env var) - custom overrides
4. **Project config** (`opencode.json` in project) - project-specific settings
5. **`.opencode` directories** - agents, commands, plugins
6. **Inline config** (`OPENCODE_CONFIG_CONTENT` env var) - runtime overrides

### Remote

Organizations can provide default configuration via the `.well-known/opencode` endpoint.

### Global

Place your global OpenCode config in `~/.config/opencode/opencode.json`. Use global config for user-wide preferences like themes, providers, or keybinds.

### Per project

Add `opencode.json` in your project root. Project config has the highest precedence among standard config files.

> **Tip:** Place project specific config in the root of your project.

### Custom path

Specify a custom config file path using the `OPENCODE_CONFIG` environment variable.

```bash
export OPENCODE_CONFIG=/path/to/my/custom-config.json
opencode run "Hello world"
```

### Custom directory

Specify a custom config directory using the `OPENCODE_CONFIG_DIR` environment variable.

```bash
export OPENCODE_CONFIG_DIR=/path/to/my/config-directory
opencode run "Hello world"
```

---

## Schema

The config file has a schema that's defined in [**`opencode.ai/config.json`**](https://opencode.ai/config.json).

Your editor should be able to validate and autocomplete based on the schema.

### TUI

Configure TUI-specific settings through the `tui` option.

```json
{
  "$schema": "https://opencode.ai/config.json",
  "tui": {
    "scroll_speed": 3,
    "scroll_acceleration": {
      "enabled": true
    },
    "diff_style": "auto"
  }
}
```

### Server

Configure server settings for the `opencode serve` and `opencode web` commands.

```json
{
  "$schema": "https://opencode.ai/config.json",
  "server": {
    "port": 4096,
    "hostname": "0.0.0.0",
    "mdns": true,
    "cors": ["http://localhost:5173"]
  }
}
```

### Tools

Manage the tools an LLM can use through the `tools` option.

```json
{
  "$schema": "https://opencode.ai/config.json",
  "tools": {
    "write": false,
    "bash": false
  }
}
```

### Models

Configure providers and models through the `provider`, `model` and `small_model` options.

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {},
  "model": "anthropic/claude-sonnet-4-5",
  "small_model": "anthropic/claude-haiku-4-5"
}
```

### Themes

Configure the theme through the `theme` option.

```json
{
  "$schema": "https://opencode.ai/config.json",
  "theme": "tokyonight"
}
```

### Agents

Configure specialized agents through the `agent` option.

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "agent": {
    "code-reviewer": {
      "description": "Reviews code for best practices and potential issues",
      "model": "anthropic/claude-sonnet-4-5",
      "prompt": "You are a code reviewer. Focus on security, performance, and maintainability.",
      "tools": {
        "write": false,
        "edit": false,
      },
    },
  },
}
```

### Default agent

Set the default agent using the `default_agent` option.

```json
{
  "$schema": "https://opencode.ai/config.json",
  "default_agent": "plan"
}
```

### Sharing

Configure the share feature through the `share` option.

```json
{
  "$schema": "https://opencode.ai/config.json",
  "share": "manual"
}
```

Options: `"manual"` (default), `"auto"`, `"disabled"`

### Commands

Configure custom commands through the `command` option.

### Keybinds

Customize your keybinds through the `keybinds` option.

### Autoupdate

Control automatic updates with the `autoupdate` option.

```json
{
  "$schema": "https://opencode.ai/config.json",
  "autoupdate": false
}
```

### Formatters

Configure code formatters through the `formatter` option.

### Permissions

Configure permissions through the `permission` option.

```json
{
  "$schema": "https://opencode.ai/config.json",
  "permission": {
    "edit": "ask",
    "bash": "ask"
  }
}
```

### Compaction

Control context compaction behavior through the `compaction` option.

```json
{
  "$schema": "https://opencode.ai/config.json",
  "compaction": {
    "auto": true,
    "prune": true
  }
}
```

### Watcher

Configure file watcher ignore patterns through the `watcher` option.

```json
{
  "$schema": "https://opencode.ai/config.json",
  "watcher": {
    "ignore": ["node_modules/**", "dist/**", ".git/**"]
  }
}
```

### MCP servers

Configure MCP servers through the `mcp` option.

### Plugins

Load plugins from npm through the `plugin` option.

```json
{
  "$schema": "https://opencode.ai/config.json",
  "plugin": ["opencode-helicone-session", "@my-org/custom-plugin"]
}
```

### Instructions

Configure instruction files through the `instructions` option.

```json
{
  "$schema": "https://opencode.ai/config.json",
  "instructions": ["CONTRIBUTING.md", "docs/guidelines.md", ".cursor/rules/*.md"]
}
```

### Disabled providers

Disable providers through the `disabled_providers` option.

```json
{
  "$schema": "https://opencode.ai/config.json",
  "disabled_providers": ["openai", "gemini"]
}
```

### Enabled providers

Specify an allowlist of providers through the `enabled_providers` option.

```json
{
  "$schema": "https://opencode.ai/config.json",
  "enabled_providers": ["anthropic", "openai"]
}
```

### Experimental

The `experimental` key contains options that are under active development.

> **Caution:** Experimental options are not stable. They may change or be removed without notice.

---

## Variables

You can use variable substitution in your config files.

### Env vars

Use `{env:VARIABLE_NAME}` to substitute environment variables:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "{env:OPENCODE_MODEL}"
}
```

### Files

Use `{file:path/to/file}` to substitute the contents of a file:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "openai": {
      "options": {
        "apiKey": "{file:~/.secrets/openai-key}"
      }
    }
  }
}
```
