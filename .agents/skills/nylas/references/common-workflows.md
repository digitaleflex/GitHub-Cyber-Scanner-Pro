# Nylas CLI Common Workflows

## Email Workflows

### List and read recent emails

```bash
# Last 20 emails in inbox
nylas email list --limit 20

# Unread only
nylas email list --unread

# From specific sender
nylas email list --from boss@company.com

# All folders
nylas email list --all-folders

# Sent folder
nylas email list --folder SENT
```

### Read a specific email

```bash
# Read by message ID
nylas email read <message-id>

# Read with headers
nylas email read <message-id> --headers

# Read and mark as read
nylas email read <message-id> --mark-read

# Raw MIME source
nylas email read <message-id> --mime
```

### Search emails

```bash
# Full-text search
nylas email search "quarterly report"

# From specific person
nylas email search "meeting" --from alice@example.com

# Date range
nylas email search "invoice" --after 2026-01-01 --before 2026-03-31

# Unread with attachments
nylas email search "*" --unread --has-attachment

# In specific folder
nylas email search "urgent" --in INBOX

# Starred messages
nylas email search "*" --starred
```

### Send emails

```bash
# Simple plain text
nylas email send --to recipient@example.com --subject "Hello" --body "Hi there!" -y

# HTML body
nylas email send --to recipient@example.com --subject "Newsletter" \
  --body "<h1>Hello</h1><p>HTML content</p>" -y

# Multiple recipients with CC and BCC
nylas email send --to alice@example.com --to bob@example.com \
  --cc boss@example.com --bcc archive@example.com \
  --subject "Team update" --body "..." -y

# Reply to a message
nylas email send --to sender@example.com --subject "Re: Original subject" \
  --body "Thanks for the update." --reply-to <original-message-id> -y

# Schedule send (2 hours from now)
nylas email send --to recipient@example.com --subject "Reminder" \
  --body "Meeting in 2 hours" --schedule "2h" -y

# Schedule send (tomorrow at 9am)
nylas email send --to recipient@example.com --subject "Morning brief" \
  --body "..." --schedule "tomorrow 9am" -y

# With tracking
nylas email send --to prospect@example.com --subject "Proposal" \
  --body "..." --track-opens --track-links -y

# GPG sign
nylas email send --to partner@example.com --subject "Contract" \
  --body "..." --sign -y

# GPG encrypt (auto-fetches recipient's public key)
nylas email send --to partner@example.com --subject "Confidential" \
  --body "..." --encrypt -y

# Sign AND encrypt
nylas email send --to partner@example.com --subject "Top Secret" \
  --body "..." --sign --encrypt -y
```

### Manage email flags

```bash
# Mark as read
nylas email mark read <message-id>

# Mark as unread
nylas email mark unread <message-id>

# Star
nylas email mark starred <message-id>

# Unstar
nylas email mark unstarred <message-id>

# Delete (moves to trash)
nylas email delete <message-id>

# Force delete (no confirmation)
nylas email delete <message-id> -f
```

### Folder management

```bash
# List all folders
nylas email folders list

# List with folder IDs (for use with --folder flag)
nylas email folders list --id

# Create a new folder
nylas email folders create --name "Projects"

# Rename a folder
nylas email folders rename --folder <folder-id> --name "Archive"

# Delete a folder
nylas email folders delete --folder <folder-id>

# Show folder details
nylas email folders show <folder-id>
```

### Attachments

```bash
# Download all attachments from a message
nylas email attachments download <message-id>

# Download to specific directory
nylas email attachments download <message-id> --output-dir ./downloads

# List attachments
nylas email attachments list <message-id>
```

### Threads and conversations

```bash
# List email threads
nylas email threads list

# Show thread details
nylas email threads show <thread-id>
```

### Drafts

```bash
# List drafts
nylas email drafts list

# Create a draft
nylas email drafts create --to recipient@example.com --subject "Draft subject" --body "Draft content"

# Send a draft
nylas email drafts send <draft-id>

# Delete a draft
nylas email drafts delete <draft-id>
```

## OTP Extraction

```bash
# Get latest OTP code from email
nylas otp get

# Watch for new OTP codes (continuous mode)
nylas otp watch
```

## Calendar Workflows

> **Requires Google or Microsoft 365 provider**

### List and view events

```bash
# Upcoming events
nylas calendar events list

# Events for next 7 days
nylas calendar events list --days 7

# JSON output for scripting
nylas calendar events list --json
```

### Create events

```bash
# Simple event
nylas calendar events create --title "Team standup" --when "tomorrow 9am" --duration 30m

# Event with attendees
nylas calendar events create --title "1:1 with Alice" --when "friday 2pm" \
  --duration 45m --attendees alice@example.com

# All-day event
nylas calendar events create --title "Company offsite" --when "next monday" \
  --duration 1d --location "Conference Center"

# Event with location and description
nylas calendar events create --title "Sprint review" \
  --when "2026-05-20 14:00" --duration 1h \
  --location "Room 302" --description "Review sprint deliverables" \
  --busy
```

### Manage events

```bash
# Show event details
nylas calendar events show <event-id>

# Update event
nylas calendar events update <event-id> --title "Updated title"

# Delete event
nylas calendar events delete <event-id>

# Delete without confirmation
nylas calendar events delete <event-id> -f

# RSVP to event
nylas calendar events rsvp <event-id> --status accepted
nylas calendar events rsvp <event-id> --status tentative
nylas calendar events rsvp <event-id> --status declined
```

## Contact Workflows

```bash
# List contacts
nylas contacts list

# Search contacts
nylas contacts list --query "john"

# Show contact details
nylas contacts show <contact-id>

# List contact groups
nylas contacts groups

# JSON output
nylas contacts list --json | jq '.[].email[0].email'
```

## Scripting & Automation

### JSON output with jq

```bash
# Get message IDs for unread emails
nylas email list --unread --json | jq '.[].id'

# Extract subjects from search results
nylas email search "invoice" --json | jq '.[].subject'

# Get sender emails
nylas email list --json | jq '.[].from[0].email'

# Count messages per sender
nylas email list --limit 100 --json | jq -r '.[].from[0].email' | sort | uniq -c | sort -rn

# Get all calendar event titles
nylas calendar events list --json | jq '.[].title'
```

### Automated email processing

```bash
#!/bin/bash
# Check for urgent unread emails and notify
URGENT=$(nylas email search "urgent" --unread --json 2>/dev/null)
COUNT=$(echo "$URGENT" | jq 'length' 2>/dev/null)

if [ "$COUNT" -gt 0 ]; then
  echo "⚠️  $COUNT urgent unread emails found"
  echo "$URGENT" | jq -r '.[] | "  From: \(.from[0].email) - \(.subject)"'
fi
```

### Batch mark as read

```bash
# Get IDs of unread messages and mark them all as read
for id in $(nylas email list --unread --json | jq -r '.[].id'); do
  nylas email mark read "$id"
done
```

### Email archiving

```bash
# Move all read messages from a sender to Archive
for id in $(nylas email list --from newsletter@example.com --json | jq -r '.[].id'); do
  nylas email move "$id" --folder Archive
done
```

### Scheduled reports

```bash
# Send a daily report
nylas email send --to team@company.com \
  --subject "Daily Report - $(date +%Y-%m-%d)" \
  --body "$(generate-report.sh)" -y

# Schedule a reminder
nylas email send --to self@company.com \
  --subject "Weekly review" \
  --body "Time for your weekly review" \
  --schedule "friday 4pm" -y
```

### OTP automation

```bash
# Get OTP code for login automation
OTP=$(nylas otp get 2>/dev/null)
if [ -n "$OTP" ]; then
  echo "OTP code: $OTP"
  # Use in automated login flow
fi
```

## MCP Server for AI Agents

### Start MCP server

```bash
# Standard (stdio transport for Claude Desktop, Cursor, etc.)
nylas mcp

# SSE transport (for remote agents)
nylas mcp --transport sse --port 8080
```

### Configure for Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "nylas": {
      "command": "nylas",
      "args": ["mcp"]
    }
  }
}
```

### Configure for Cursor/Windsurf

Add to MCP settings:

```json
{
  "mcpServers": {
    "nylas": {
      "command": "nylas",
      "args": ["mcp"]
    }
  }
}
```

## Multi-Account Workflows

### Switch between accounts

```bash
# List all accounts
nylas auth list

# Use specific account for a command
nylas email list --grant-id <grant-id>
nylas email send --to user@example.com --subject "Hello" --body "..." \
  --grant-id <grant-id>

# Change default account
nylas config set default_grant "work@gmail.com"
```

### Detect provider for an email

```bash
nylas auth detect user@example.com
# Output: Email: user@example.com, Domain: example.com, Provider: google
```

## Demo Mode (No Account Required)

```bash
# Explore without credentials
nylas demo email list          # Sample emails
nylas demo calendar list       # Sample events
nylas demo contacts list       # Sample contacts
nylas demo tui                 # Interactive demo UI
```

## Interactive TUI

```bash
nylas tui    # Launch terminal UI
```

Key bindings:
- `j/k` — Move up/down
- `Enter` — Read message
- `s` — Toggle star
- `r` — Reply
- `q` — Quit
- `?` — Help