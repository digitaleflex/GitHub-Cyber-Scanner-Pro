# Himalaya CLI Reference

## Global Options

| Option | Description |
|--------|-------------|
| `-c, --config <PATH>` | Override config file path |
| `-o, --output <FORMAT>` | Output format: `plain` (default) or `json` |
| `--quiet` | Disable all logs (`RUST_LOG=off`) |
| `--debug` | Enable debug logs (`RUST_LOG=debug`) |
| `--trace` | Enable trace logs with backtrace (`RUST_LOG=trace`) |
| `-a, --account <NAME>` | Override default account |
| `-f, --folder <NAME>` | Folder name (default: INBOX) |

## Account Management

### List accounts
```bash
himalaya account list [-o json]
```

### Diagnose account
```bash
himalaya account doctor [ACCOUNT] [-f]  # -f attempts to fix issues
```

### Configure account (interactive wizard)
```bash
himalaya account configure <ACCOUNT>
```

## Envelope Commands

### List envelopes
```bash
himalaya envelope list [QUERY]... [-f FOLDER] [-p PAGE] [-s PAGE_SIZE] [-a ACCOUNT] [-o json]
```

**Query syntax:**

**Filter operators:**
- `not <condition>` — exclude matching
- `<cond1> and <cond2>` — both must match
- `<cond1> or <cond2>` — either must match

**Filter conditions:**
- `date <yyyy-mm-dd>` — exact date match
- `before <yyyy-mm-dd>` — before date
- `after <yyyy-mm-dd>` — after date
- `from <pattern>` — sender matches pattern
- `to <pattern>` — recipient matches pattern
- `subject <pattern>` — subject matches pattern
- `body <pattern>` — body text matches pattern
- `flag <flag>` — matches flag (seen, answered, flagged, deleted, draft)

**Sort syntax:**
- `order by date [asc|desc]` — sort by date
- `order by from [asc|desc]` — sort by sender
- `order by to [asc|desc]` — sort by recipient
- `order by subject [asc|desc]` — sort by subject

**Examples:**
```bash
# Unread from specific sender
himalaya envelope list 'not flag seen and from boss@company.com'

# Sort by newest first
himalaya envelope list 'order by date desc'

# Combined filter + sort
himalaya envelope list 'subject urgent and after 2026-01-01 order by date desc'
```

### Thread view
```bash
himalaya envelope thread [QUERY]... [-f FOLDER] [-a ACCOUNT]
```

## Message Commands

### Read message
```bash
himalaya message read <ID>... [-f FOLDER] [-p] [--no-headers] [-H HEADER] [-a ACCOUNT] [-o json]
```

| Flag | Description |
|------|-------------|
| `-p, --preview` | Read without marking as seen |
| `--no-headers` | Body only, no headers |
| `-H, --header <NAME>` | Show specific header(s) only |

### Export message (raw RFC 5322)
```bash
himalaya message export <ID> [-f FOLDER] [-a ACCOUNT] [-o json]
```

### Send message (raw RFC 5322 on stdin)
```bash
cat <<'EOF' | himalaya message send [-a ACCOUNT]
From: sender@example.com
To: recipient@example.com
Subject: Subject Line

Body text here.
EOF
```

### Compose new message (opens editor)
```bash
himalaya message write [-a ACCOUNT]
```

### Reply to message (opens editor)
```bash
himalaya message reply <ID> [-f FOLDER] [-a ACCOUNT]
```

### Forward message (opens editor)
```bash
himalaya message forward <ID> [-f FOLDER] [-a ACCOUNT]
```

### Edit draft message (opens editor)
```bash
himalaya message edit <ID> [-f FOLDER] [-a ACCOUNT]
```

### Parse mailto URL (opens editor)
```bash
himalaya message mailto <MAILTO_URL> [-a ACCOUNT]
```

### Save raw message to folder
```bash
cat <<'EOF' | himalaya message save [-f FOLDER] [-a ACCOUNT]
From: sender@example.com
To: recipient@example.com
Subject: Draft

Draft content.
EOF
```

### Copy message to folder
```bash
himalaya message copy <ID>... [-f FOLDER] --target <TARGET_FOLDER> [-a ACCOUNT]
```

### Move message to folder
```bash
himalaya message move <ID>... [-f FOLDER] --target <TARGET_FOLDER> [-a ACCOUNT]
```

### Delete message
```bash
himalaya message delete <ID>... [-f FOLDER] [-a ACCOUNT]
```

## Flag Commands

### Add flags
```bash
himalaya flag add <ID_OR_FLAG>... [-f FOLDER] [-a ACCOUNT]
# Examples:
himalaya flag add 4658 seen          # Mark as read
himalaya flag add 4658 flagged        # Star
himalaya flag add 4658 seen flagged   # Multiple flags
```

### Set flags (replace all)
```bash
himalaya flag set <ID_OR_FLAG>... [-f FOLDER] [-a ACCOUNT]
```

### Remove flags
```bash
himalaya flag remove <ID_OR_FLAG>... [-f FOLDER] [-a ACCOUNT]
# Examples:
himalaya flag remove 4658 seen        # Mark as unread
himalaya flag remove 4658 flagged     # Unstar
```

**Standard flags:** `seen`, `answered`, `flagged`, `deleted`, `draft`

## Folder Commands

### List folders
```bash
himalaya folder list [-a ACCOUNT] [-o json]
```

### Create folder
```bash
himalaya folder add <NAME> [-a ACCOUNT]
# Alias: himalaya folder create <NAME>
```

### Delete folder
```bash
himalaya folder delete <NAME> [-a ACCOUNT]
```

### Expunge folder (remove deleted messages)
```bash
himalaya folder expunge <NAME> [-a ACCOUNT]
```

### Purge folder (delete all messages)
```bash
himalaya folder purge <NAME> [-a ACCOUNT]
```

## Attachment Commands

### Download attachments
```bash
himalaya attachment download <ID> [-f FOLDER] [-a ACCOUNT] [-o json]
```

Downloads all attachments from the specified message to the current directory.

## Template Commands

Templates use MML (Mime Markup Language). See <https://crates.io/crates/mml-lib>.

### Write template (new message)
```bash
himalaya template write [-a ACCOUNT]
```

### Reply template
```bash
himalaya template reply <ID> [-f FOLDER] [-a ACCOUNT]
```

### Forward template
```bash
himalaya template forward <ID> [-f FOLDER] [-a ACCOUNT]
```

### Save template to folder
```bash
himalaya template save [-f FOLDER] [-a ACCOUNT]
```

### Send template
```bash
himalaya template send [-a ACCOUNT]
```

## Output Formats

### Plain (default, human-readable)
```bash
himalaya envelope list -a hyperspace
```

### JSON (machine-readable, for scripting)
```bash
himalaya envelope list -a hyperspace -o json | jq '.[] | .id'
```

## Debugging

```bash
# Debug mode — shows IMAP/SMTP protocol details
himalaya envelope list --debug -a hyperspace

# Trace mode — verbose with backtraces
himalaya message send --trace -a hyperspace < email.txt

# Diagnose account connectivity
himalaya account doctor hyperspace

# Diagnose and attempt fixes
himalaya account doctor hyperspace -f
```