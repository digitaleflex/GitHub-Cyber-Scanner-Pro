# Nylas CLI Command Reference

## Global Flags

| Flag | Description |
|------|-------------|
| `--config <path>` | Custom config file path |
| `--format <fmt>` | Output format: `table`, `json`, `yaml` |
| `--json` | Shorthand for JSON output |
| `--no-color` | Disable color output |
| `-q, --quiet` | Only output essential data (IDs) |
| `-v, --verbose` | Enable verbose output |
| `-w, --wide` | Show full IDs without truncation |

## Email Commands

### `nylas email list`

List recent emails from inbox.

```bash
nylas email list [flags]
```

| Flag | Description |
|------|-------------|
| `-a, --all` | Fetch all messages (paginated) |
| `--all-folders` | Show messages from all folders |
| `--folder <name>` | Filter by folder (INBOX, SENT, TRASH, or folder ID) |
| `-f, --from <email>` | Filter by sender email |
| `--id` | Show message IDs |
| `-l, --limit <n>` | Number of messages (default 10) |
| `--max <n>` | Maximum messages with `--all` (0=unlimited) |
| `--metadata <kv>` | Filter by metadata (key:value, key1-key5) |
| `-s, --starred` | Only show starred messages |
| `-u, --unread` | Only show unread messages |

### `nylas email read`

Read and display the full content of a specific email.

```bash
nylas email read <message-id> [grant-id] [flags]
```

Aliases: `read`, `show`

| Flag | Description |
|------|-------------|
| `--decrypt` | Decrypt PGP/MIME encrypted message |
| `--headers` | Show email headers |
| `-r, --mark-read` | Mark as read after viewing |
| `--mime` | Show raw RFC822/MIME format |
| `--raw` | Show raw body without HTML processing |
| `--verify` | Verify GPG/PGP signature |

### `nylas email search`

Search for emails matching a query or filters.

```bash
nylas email search <query> [flags]
```

| Flag | Description |
|------|-------------|
| `--from <email>` | Filter by sender |
| `--to <email>` | Filter by recipient |
| `--unread` | Only unread messages |
| `--starred` | Only starred messages |
| `--in <folder>` | Search in specific folder |
| `--after <date>` | After date (YYYY-MM-DD) |
| `--before <date>` | Before date (YYYY-MM-DD) |
| `--has-attachment` | Only messages with attachments |
| `--limit <n>` | Max results |

Examples:
```bash
nylas email search "project update"
nylas email search "meeting" --from boss@company.com --unread
nylas email search "*" --from support@example.com
nylas email search "invoice" --in INBOX
nylas email search "invoice" --after 2024-01-01 --before 2024-12-31
nylas email search "*" --has-attachment --from hr@company.com
```

### `nylas email send`

Compose and send an email message.

```bash
nylas email send [grant-id] [flags]
```

| Flag | Description |
|------|-------------|
| `-t, --to <emails>` | Recipient email(s), repeatable |
| `--cc <emails>` | CC recipients |
| `--bcc <emails>` | BCC recipients |
| `-s, --subject <text>` | Email subject |
| `-b, --body <text>` | Email body (HTML or plain text) |
| `--reply-to <id>` | Message ID to reply to |
| `-i, --interactive` | Open in editor |
| `-y, --yes` | Skip confirmation prompt |
| `--schedule <when>` | Schedule send (e.g., `2h`, `tomorrow 9am`, `2024-01-15 14:30`) |
| `--track-opens` | Track email opens |
| `--track-links` | Track link clicks |
| `--track-label <label>` | Label for tracking |
| `--sign` | Sign with GPG |
| `--encrypt` | Encrypt with GPG |
| `--gpg-key <key-id>` | Specific GPG key |
| `--metadata <kv>` | Custom metadata (repeatable) |
| `--template-id <id>` | Hosted template ID |
| `--template-data <json>` | Template variables as JSON |
| `--template-data-file <path>` | Template variables from file |
| `--render-only` | Preview template without sending |
| `--signature-id <id>` | Stored signature to append |

### `nylas email delete`

Delete an email message (moves to trash).

```bash
nylas email delete <message-id> [grant-id] [flags]
```

| Flag | Description |
|------|-------------|
| `-f, --force` | Skip confirmation prompt |

### `nylas email mark`

Update message flags.

```bash
nylas email mark read <message-id>
nylas email mark unread <message-id>
nylas email mark starred <message-id>
nylas email mark unstarred <message-id>
```

### `nylas email folders`

Manage email folders/labels.

```bash
nylas email folders list [--id]              # List folders (with IDs)
nylas email folders create --name "Archive"  # Create folder
nylas email folders rename --folder <id> --name "New Name"  # Rename
nylas email folders delete --folder <id>      # Delete folder
nylas email folders show <folder-id>         # Show folder details
```

### `nylas email threads`

Manage email threads/conversations.

```bash
nylas email threads list              # List threads
nylas email threads show <thread-id>  # Show thread details
```

### `nylas email drafts`

Manage email drafts.

```bash
nylas email drafts list                     # List drafts
nylas email drafts create --to ... --subject ... --body ...  # Create draft
nylas email drafts send <draft-id>          # Send a draft
nylas email drafts delete <draft-id>         # Delete a draft
```

### `nylas email smart-compose`

Generate AI-powered email drafts.

```bash
nylas email smart-compose --prompt "Write a polite decline" --to user@example.com --subject "Re: Meeting"
```

### `nylas email signatures`

Manage stored email signatures.

```bash
nylas email signatures list              # List signatures
nylas email signatures create --name "Work" --body "<b>Best</b>"  # Create
nylas email signatures delete <sig-id>   # Delete
```

### `nylas email scheduled`

Manage scheduled messages.

```bash
nylas email scheduled list              # List scheduled messages
nylas email scheduled cancel <id>       # Cancel a scheduled send
```

### `nylas email metadata`

Manage message metadata.

```bash
nylas email metadata get <message-id>
nylas email metadata set <message-id> --metadata key1=value1 --metadata key2=value2
nylas email metadata delete <message-id> --key key1
```

### `nylas email tracking-info`

View email tracking data (opens, clicks).

```bash
nylas email tracking-info <message-id>
```

### `nylas email attachments`

Download email attachments.

```bash
nylas email attachments download <message-id> [--output-dir ./downloads]
nylas email attachments list <message-id>
```

### `nylas email ai`

AI-powered email intelligence.

```bash
nylas email ai summarize <message-id>      # Summarize an email
nylas email ai categorize <message-id>       # Categorize an email
nylas email ai extract-action <message-id>   # Extract action items
```

## Calendar Commands

> **Requires Google or Microsoft 365 provider. IMAP does not support calendar.**

### `nylas calendar events`

```bash
nylas calendar events list [--limit 10]           # List upcoming events
nylas calendar events show <event-id>              # Show event details
nylas calendar events create --title "Meeting" --when "tomorrow 3pm" --duration 30m
nylas calendar events update <event-id> --title "Updated"
nylas calendar events delete <event-id> [-f]
nylas calendar events rsvp <event-id> --status accepted
```

### `nylas calendar calendars`

```bash
nylas calendar calendars list    # List calendars
nylas calendar calendars show <id>  # Show calendar details
```

### Event creation flags

| Flag | Description |
|------|-------------|
| `--title <text>` | Event title |
| `--when <text>` | When (natural language: "tomorrow 3pm", "next monday") |
| `--duration <dur>` | Duration (e.g., `30m`, `1h`, `2h30m`) |
| `--attendees <emails>` | Comma-separated attendee emails |
| `--location <text>` | Event location |
| `--description <text>` | Event description |
| `--busy` | Mark as busy (default) |
| `--free` | Mark as free |

## Contact Commands

```bash
nylas contacts list [--limit 20]              # List contacts
nylas contacts list --query "john"            # Search contacts
nylas contacts show <contact-id>               # Show contact details
nylas contacts groups                          # List contact groups
```

## Auth Commands

```bash
nylas auth login --provider google     # Authenticate with Google
nylas auth login --provider microsoft  # Authenticate with Microsoft 365
nylas auth login --provider imap       # Authenticate with IMAP
nylas auth login --provider icloud     # Authenticate with iCloud
nylas auth login --provider yahoo      # Authenticate with Yahoo
nylas auth status                       # Show current auth status
nylas auth list                         # List all authenticated accounts
nylas auth add <grant-id>               # Add existing grant
nylas auth remove <grant-id>            # Remove grant
nylas auth revoke <grant-id>            # Revoke grant on server
nylas auth whoami                       # Show current user info
nylas auth detect <email>               # Detect provider from email
nylas auth config --api-key <key>       # Configure API credentials
```

## OTP Commands

```bash
nylas otp get                    # Get latest OTP code from email
nylas otp watch                  # Watch for new OTP codes
nylas otp list                   # List configured accounts
nylas otp messages                # Show recent messages (debug)
```

## Utility Commands

### `nylas doctor`

Check CLI health and configuration.

```bash
nylas doctor    # Run all diagnostic checks
```

Checks: configuration, secret store, API credentials, network connectivity, grant validity.

### `nylas config`

Manage CLI configuration.

```bash
nylas config show                  # Show current config
nylas config set <key> <value>     # Set a config value
nylas config get <key>              # Get a config value
```

### `nylas tui`

Launch interactive terminal UI (k9s-style).

```bash
nylas tui    # Interactive email browser
```

Navigation: `j/k` to move, `Enter` to read, `q` to quit, `s` to star.

### `nylas demo`

Explore CLI features with sample data (no credentials required).

```bash
nylas demo email list       # Sample emails
nylas demo calendar list    # Sample events
nylas demo contacts list    # Sample contacts
nylas demo tui               # Interactive demo
```

### `nylas mcp`

Start MCP server for AI agent integration.

```bash
nylas mcp                              # Start with stdio transport
nylas mcp --transport sse --port 8080  # Start with SSE transport
```

### `nylas update`

Check for and install the latest version.

```bash
nylas update    # Check and install updates
```

## Output Formats

All commands support three output formats:

```bash
nylas email list                       # Table (default, human-readable)
nylas email list --json                # JSON (for scripting)
nylas email list --format yaml         # YAML (for config files)
nylas email list -q                    # Quiet (IDs only)
nylas email list -w                    # Wide (full IDs)
```