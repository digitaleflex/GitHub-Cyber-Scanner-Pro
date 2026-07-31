# TUI

Using the OpenCode terminal user interface.

OpenCode provides an interactive terminal interface or TUI for working on your projects with an LLM.

Running OpenCode starts the TUI for the current directory.

```bash
opencode
```

Or you can start it for a specific working directory.

```bash
opencode /path/to/project
```

Once you're in the TUI, you can prompt it with a message.

```
Give me a quick summary of the codebase.
```

---

## File references

You can reference files in your messages using `@`. This does a fuzzy file search in the current working directory.

> **Tip:** You can also use `@` to reference files in your messages.

```
How is auth handled in @packages/functions/src/api/index.ts?
```

The content of the file is added to the conversation automatically.

---

## Bash commands

Start a message with `!` to run a shell command.

```
!ls -la
```

The output of the command is added to the conversation as a tool result.

---

## Commands

When using the OpenCode TUI, you can type `/` followed by a command name to quickly execute actions. For example:

```
/help
```

Most commands also have keybind using `ctrl+x` as the leader key, where `ctrl+x` is the default leader key. [Learn more](keybinds.md).

Here are all available slash commands:

---

### connect

Add a provider to OpenCode. Allows you to select from available providers and add their API keys.

```
/connect
```

---

### compact

Compact the current session. *Alias*: `/summarize`

```
/compact
```

**Keybind:** `ctrl+x c`

---

### details

Toggle tool execution details.

```
/details
```

**Keybind:** `ctrl+x d`

---

### editor

Open external editor for composing messages. Uses the editor set in your `EDITOR` environment variable. [Learn more](#editor-setup).

```
/editor
```

**Keybind:** `ctrl+x e`

---

### exit

Exit OpenCode. *Aliases*: `/quit`, `/q`

```
/exit
```

**Keybind:** `ctrl+x q`

---

### export

Export current conversation to Markdown and open in your default editor. Uses the editor set in your `EDITOR` environment variable. [Learn more](#editor-setup).

```
/export
```

**Keybind:** `ctrl+x x`

---

### help

Show the help dialog.

```
/help
```

**Keybind:** `ctrl+x h`

---

### init

Create or update `AGENTS.md` file. [Learn more](rules.md).

```
/init
```

**Keybind:** `ctrl+x i`

---

### models

List available models.

```
/models
```

**Keybind:** `ctrl+x m`

---

### new

Start a new session. *Alias*: `/clear`

```
/new
```

**Keybind:** `ctrl+x n`

---

### redo

Redo a previously undone message. Only available after using `/undo`.

> **Tip:** Any file changes will also be restored.

Internally, this uses Git to manage the file changes. So your project **needs to be a Git repository**.

```
/redo
```

**Keybind:** `ctrl+x r`

---

### sessions

List and switch between sessions. *Aliases*: `/resume`, `/continue`

```
/sessions
```

**Keybind:** `ctrl+x l`

---

### share

Share current session. [Learn more](share.md).

```
/share
```

**Keybind:** `ctrl+x s`

---

### themes

List available themes.

```
/theme
```

**Keybind:** `ctrl+x t`

---

### thinking

Toggle the visibility of thinking/reasoning blocks in the conversation. When enabled, you can see the model's reasoning process for models that support extended thinking.

> **Note:** This command only controls whether thinking blocks are **displayed** - it does not enable or disable the model's reasoning capabilities. To toggle actual reasoning capabilities, use `ctrl+t` to cycle through model variants.

```
/thinking
```

---

### undo

Undo last message in the conversation. Removes the most recent user message, all subsequent responses, and any file changes.

> **Tip:** Any file changes made will also be reverted.

Internally, this uses Git to manage the file changes. So your project **needs to be a Git repository**.

```
/undo
```

**Keybind:** `ctrl+x u`

---

### unshare

Unshare current session. [Learn more](share.md#un-sharing).

```
/unshare
```

---

## Editor setup

Both the `/editor` and `/export` commands use the editor specified in your `EDITOR` environment variable.

### Linux/macOS

```bash
# Example for nano or vim
export EDITOR=nano
export EDITOR=vim

# For GUI editors, VS Code, Cursor, VSCodium, Windsurf, Zed, etc.
# include --wait
export EDITOR="code --wait"
```

To make it permanent, add this to your shell profile; `~/.bashrc`, `~/.zshrc`, etc.

### Windows (CMD)

```cmd
set EDITOR=notepad

# For GUI editors, VS Code, Cursor, VSCodium, Windsurf, Zed, etc.
# include --wait
set EDITOR=code --wait
```

To make it permanent, use **System Properties** > **Environment Variables**.

### Windows (PowerShell)

```powershell
$env:EDITOR = "notepad"

# For GUI editors
$env:EDITOR = "code --wait"
```

To make it permanent, add to your PowerShell profile.

---

## Configure

You can configure the TUI's behavior using the `tui` section in your `opencode.json`.

```json
{
  "$schema": "https://opencode.ai/config.json",
  "tui": {
    "disabled": false
  }
}
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `disabled` | boolean | `false` | Disable TUI interface |

---

## Customization

Check out the following pages to learn how to customize the TUI:

- [Themes](themes.md) - Customize the look and feel
- [Keybinds](keybinds.md) - Customize keyboard shortcuts
- [Commands](commands.md) - Add custom slash commands
