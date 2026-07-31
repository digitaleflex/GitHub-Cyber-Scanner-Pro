---
name: himalaya
description: CLI email client for IMAP and SMTP. Use when reading, searching, composing, sending, or managing email via terminal. Covers account setup, envelope listing, message reading, sending raw RFC 5322 messages, folder management, attachments, flags, and multi-account configuration.
---

# Himalaya — CLI Email Client

## Quick Start

```bash
# List recent envelopes (INBOX)
himalaya envelope list -a hyperspace

# Read a message
himalaya message read -a hyperspace 4658

# Send a message (raw RFC 5322)
cat <<'EOF' | himalaya message send -a hyperspace
From: seyi@hyperspace.ng
To: recipient@example.com
Subject: Test Subject

Message body here.
EOF

# Check account health
himalaya account doctor hyperspace
```

## Core Patterns

### 1. Account Configuration

Config file: `~/.config/himalaya/config.toml`

Each account requires IMAP backend + SMTP send backend. See [references/config-reference.md](references/config-reference.md) for full schema.

```toml
[accounts.hyperspace]
default = true
display-name = "Seyi"
email = "seyi@hyperspace.ng"
message.send.save-copy = false          # Disable if server's IMAP APPEND is quirky

[accounts.hyperspace.backend]
type = "imap"
host = "mail.hyperspace.ng"
port = 993
login = "seyi@hyperspace.ng"

[accounts.hyperspace.backend.auth]
type = "password"
raw = "YOUR_PASSWORD"

[accounts.hyperspace.backend.encryption]
type = "tls"
starttls = false

[accounts.hyperspace.message.send.backend]
type = "smtp"
host = "mail.hyperspace.ng"
port = 465
login = "seyi@hyperspace.ng"

[accounts.hyperspace.message.send.backend.auth]
type = "password"
raw = "YOUR_PASSWORD"

[accounts.hyperspace.message.send.backend.encryption]
type = "tls"
starttls = false

[accounts.hyperspace.folder.alias]
drafts = "Drafts"
trash = "Trash"
junk = "Junk"
```

### 2. Listing Envelopes

```bash
# Default folder (INBOX), page size 10
himalaya envelope list -a hyperspace

# Specific folder
himalaya envelope list -a hyperspace --folder Sent

# Page through results
himalaya envelope list -a hyperspace --page-size 20

# JSON output for scripting
himalaya envelope list -a hyperspace -o json
```

### 3. Reading Messages

```bash
# Read full message (headers + body)
himalaya message read -a hyperspace 4658

# Read only body text
himalaya message read -a hyperspace 4658 --no-headers

# JSON output
himalaya message read -a hyperspace 4658 -o json
```

### 4. Sending Messages

Himalaya accepts **raw RFC 5322** format. It does NOT have `--to`, `--subject` flags.

```bash
# Simple plain text
cat <<'EOF' | himalaya message send -a hyperspace
From: seyi@hyperspace.ng
To: recipient@example.com
Subject: Hello

Body text here.
EOF

# HTML email
cat <<'EOF' | himalaya message send -a hyperspace
From: seyi@hyperspace.ng
To: recipient@example.com
Subject: HTML Email
Content-Type: text/html; charset=utf-8

<h1>Hello</h1><p>This is <b>HTML</b>.</p>
EOF

# CC and Reply-To
cat <<'EOF' | himalaya message send -a hyperspace
From: seyi@hyperspace.ng
To: recipient@example.com
Cc: other@example.com
Reply-To: noreply@hyperspace.ng
Subject: With CC and Reply-To

Body text.
EOF
```

### 5. Managing Flags

```bash
# Mark as read (add Seen flag)
himalaya flag add -a hyperspace 4658 seen

# Mark as unread (remove Seen flag)
himalaya flag remove -a hyperspace 4658 seen

# Star a message
himalaya flag add -a hyperspace 4658 flagged

# Delete a message (add Deleted flag + expunge)
himalaya flag add -a hyperspace 4658 deleted
```

### 6. Folder Operations

```bash
# List all folders
himalaya folder list -a hyperspace

# Create a new folder
himalaya folder add -a hyperspace "Archive"

# Delete a folder
himalaya folder delete -a hyperspace "Archive"
```

## Important Notes

- **`message send` takes raw RFC 5322 on stdin** — no `--to`, `--subject`, or `--body` flags.
- **`save-copy = false`** — set this if the server's IMAP APPEND to Sent folder causes "unexpected tag" errors (common with cPanel/Dovecot).
- **Password auth type is `password`**, not `passwd` or `plain`.
- **Encryption types**: `tls` (IMAPS/SMTPS on dedicated port) or `starttls` (STARTTLS on plain port).
- **Auth mechanisms**: `password` (auto-selects PLAIN/LOGIN) or `oauth2` (for Gmail/Outlook).
- Use `-o json` for scripting; `-o plain` (default) for human output.
- Use `--debug` or `--trace` for troubleshooting connection issues.

## References

- [references/cli-reference.md](references/cli-reference.md) — Complete command reference for all himalaya subcommands
- [references/config-reference.md](references/config-reference.md) — Full TOML configuration schema, multi-account setup, OAuth2, and keyring
- [references/common-workflows.md](references/common-workflows.md) — Search/filter, attachments, threading, batch operations, and scripting patterns