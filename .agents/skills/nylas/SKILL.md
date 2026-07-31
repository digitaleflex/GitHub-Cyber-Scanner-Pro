---
name: nylas
description: Nylas CLI for unified email, calendar, and contacts via IMAP/SMTP, Google, and Microsoft 365. Use when reading, searching, composing, sending, or managing email from terminal, scheduling calendar events, managing contacts, extracting OTP codes, running MCP server for AI agents, or using the interactive TUI.
---

# Nylas CLI — Unified Email, Calendar & Contacts

## Quick Start

```bash
# List recent emails
nylas email list

# Send an email
nylas email send --to recipient@example.com --subject "Hello" --body "Hi there!" -y

# Search emails
nylas email search "invoice"

# Read a specific email
nylas email read <message-id>

# Check account health
nylas doctor

# Interactive TUI
nylas tui
```

## Setup & Authentication

### Install

```bash
brew install nylas/nylas-cli/nylas
```

### First-time setup

```bash
# Interactive guided setup (opens browser for OAuth)
nylas init

# Or configure with existing API key
nylas auth config --api-key nyl_xxx

# Then authenticate with an email provider
nylas auth login --provider google     # Gmail
nylas auth login --provider microsoft  # Outlook/M365
nylas auth login --provider imap       # Generic IMAP (prompts for credentials)
```

### IMAP setup (non-interactive)

```bash
expect -c '
set timeout 60
spawn nylas auth login --provider imap
expect "IMAP username"    ; send "user@example.com\r"
expect "IMAP password"    ; send "YOUR_PASSWORD\r"
expect "IMAP host"        ; send "mail.example.com\r"
expect "IMAP port"         ; send "993\r"
expect "Add SMTP"          ; send "Y\r"
expect "SMTP host"         ; send "mail.example.com\r"
expect "SMTP port"         ; send "465\r"
expect eof
'
```

### Verify setup

```bash
nylas auth status    # Show current auth
nylas auth list      # List all accounts
nylas doctor         # Full health check
```

## Core Email Commands

### List emails

```bash
# Recent 10 from INBOX
nylas email list

# More emails
nylas email list --limit 50

# Unread only
nylas email list --unread

# From specific sender
nylas email list --from boss@company.com

# Specific folder
nylas email list --folder SENT
nylas email list --folder TRASH

# All folders
nylas email list --all-folders

# Paginate through all
nylas email list --all --max 500

# JSON output for scripting
nylas email list --json
nylas email list --json --limit 50 | jq '.[].subject'
```

### Read email

```bash
# Read a specific message
nylas email read <message-id>

# Show full headers
nylas email read <message-id> --headers

# Raw MIME source
nylas email read <message-id> --raw

# Mark as read after viewing
nylas email read <message-id> --mark-read
```

### Search emails

```bash
# Full-text search
nylas email search "quarterly report"

# From specific person
nylas email search "from:alice@example.com"

# Subject filter
nylas email search "subject:urgent"

# Date range
nylas email search "after:2026-01-01 before:2026-03-01"

# Unread
nylas email search "is:unread"

# Starred
nylas email search "is:starred"

# Has attachments
nylas email search "has:attachment"
```

### Send email

```bash
# Simple send
nylas email send --to user@example.com --subject "Hello" --body "Hi there!" -y

# Multiple recipients
nylas email send --to a@example.com --to b@example.com --subject "Team update" --body "..." -y

# CC and BCC
nylas email send --to user@example.com --cc boss@example.com --bcc archive@example.com \
  --subject "FYI" --body "See attached" -y

# HTML body
nylas email send --to user@example.com --subject "Newsletter" \
  --body "<h1>Hello</h1><p>HTML content</p>" -y

# Scheduled send
nylas email send --to user@example.com --subject "Reminder" --body "..." --schedule "2h" -y
nylas email send --to user@example.com --subject "Morning" --body "..." --schedule "tomorrow 9am" -y

# With tracking
nylas email send --to user@example.com --subject "Proposal" --body "..." \
  --track-opens --track-links -y

# GPG sign
nylas email send --to user@example.com --subject "Secure" --body "..." --sign -y

# GPG encrypt
nylas email send --to bob@example.com --subject "Confidential" --body "..." --encrypt -y

# Interactive mode (opens editor)
nylas email send --to user@example.com --subject "Draft" -i
```

### Mark, move, delete

```bash
# Mark as read/unread
nylas email mark read <message-id>
nylas email mark unread <message-id>

# Star/unstar
nylas email mark starred <message-id>
nylas email mark unstarred <message-id>

# Delete
nylas email delete <message-id>

# Move to folder
nylas email move <message-id> --folder Archive
```

## Calendar Commands

> **Note:** Calendar requires Google or Microsoft 365 provider. IMAP does not support calendar.

```bash
# List calendars
nylas calendar calendars list

# List upcoming events
nylas calendar events list

# Create event
nylas calendar events create --title "Team standup" --when "tomorrow 9am" --duration 30m

# Create with attendees
nylas calendar events create --title "1:1" --when "friday 2pm" --duration 45m \
  --attendees alice@example.com,bob@example.com

# Show event details
nylas calendar events show <event-id>

# Delete event
nylas calendar events delete <event-id>
```

## Contact Commands

```bash
# List contacts
nylas contacts list

# Search contacts
nylas contacts list --query "john"

# JSON output
nylas contacts list --json
```

## Folder Management

```bash
# List all folders
nylas email folders list

# Show folder with IDs
nylas email folders list --id

# Create a new folder
nylas email folders create --name "Projects"

# Rename a folder
nylas email folders rename --folder <folder-id> --name "Renamed"

# Delete a folder
nylas email folders delete --folder <folder-id>
```

## OTP Extraction

```bash
# Get latest OTP code from email
nylas otp get

# Watch for new OTP codes
nylas otp watch
```

## MCP Server (AI Integration)

```bash
# Start MCP server for Claude/Cursor/Windsurf
nylas mcp

# With specific transport
nylas mcp --transport stdio
nylas mcp --transport sse --port 8080
```

## TUI (Interactive Mode)

```bash
# Launch interactive terminal UI
nylas tui

# Vim-style navigation: j/k to move, Enter to read, q to quit
```

## Global Flags

| Flag | Description |
|------|-------------|
| `--config <path>` | Custom config file path |
| `--format <fmt>` | Output format: `table`, `json`, `yaml` |
| `--json` | Shorthand for `--format json` |
| `--no-color` | Disable color output |
| `-q, --quiet` | Only output essential data (IDs) |
| `-v, --verbose` | Enable verbose output |
| `-w, --wide` | Show full IDs without truncation |

## Provider Support

| Provider | Email | Calendar | Contacts | Auth |
|----------|-------|----------|----------|------|
| **Google (Gmail)** | ✅ | ✅ | ✅ | OAuth |
| **Microsoft 365 (Outlook)** | ✅ | ✅ | ✅ | OAuth |
| **Exchange (EWS)** | ✅ | ✅ | ✅ | OAuth |
| **iCloud** | ✅ | ✅ | ✅ | App password |
| **Yahoo** | ✅ | ✅ | ✅ | App password |
| **IMAP/SMTP** | ✅ | ❌ | ❌ | Credentials |

## Important Notes

- **IMAP provider supports email only** — no calendar or contacts
- **Send uses `--to`, `--subject`, `--body` flags** (unlike himalaya which takes raw RFC 5322)
- **Use `-y` flag to skip confirmation prompts** in scripts
- **Use `--json` for scripting** — all commands support JSON output
- **API key stored in system keyring** — config at `~/.config/nylas/config.yaml`
- **Free tier (Sandbox)** has rate limits — 1 grant, limited API calls
- **Nylas routes email through its servers** — not a direct IMAP client like himalaya
- **Demo mode available** — `nylas demo email list` works without any account

## References

- [references/cli-reference.md](references/cli-reference.md) — Complete command reference for all nylas subcommands
- [references/config-reference.md](references/config-reference.md) — Config file format, multi-account setup, keyring, and provider templates
- [references/common-workflows.md](references/common-workflows.md) — Search patterns, scheduled send, templates, MCP setup, and scripting patterns