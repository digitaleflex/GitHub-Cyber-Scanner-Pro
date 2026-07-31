# Himalaya Common Workflows

## Reading & Searching Email

### List recent inbox messages
```bash
himalaya envelope list -a hyperspace
```

### Search by subject
```bash
himalaya envelope list 'subject invoice' -a hyperspace
```

### Search by sender
```bash
himalaya envelope list 'from boss@company.com' -a hyperspace
```

### Search unread messages
```bash
himalaya envelope list 'not flag seen' -a hyperspace
```

### Search by date range
```bash
himalaya envelope list 'after 2026-05-01 and before 2026-05-15' -a hyperspace
```

### Combined filter + sort
```bash
himalaya envelope list 'from amazon and not flag seen order by date desc' -a hyperspace
```

### View a specific folder
```bash
himalaya envelope list -a hyperspace -f Sent
himalaya envelope list -a hyperspace -f Junk
himalaya envelope list -a hyperspace -f Archive
```

### Read full message
```bash
himalaya message read -a hyperspace 4658
```

### Read body only (no headers)
```bash
himalaya message read -a hyperspace 4658 --no-headers
```

### Preview without marking as read
```bash
himalaya message read -a hyperspace 4658 --preview
```

### Export raw RFC 5322 source
```bash
himalaya message export -a hyperspace 4658 > email.eml
```

### View thread
```bash
himalaya envelope thread 'subject "Re: Project"' -a hyperspace
```

## Sending Email

### Send plain text email
```bash
cat <<'EOF' | himalaya message send -a hyperspace
From: seyi@hyperspace.ng
To: recipient@example.com
Subject: Meeting Tomorrow

Hi team,

Just a reminder about tomorrow's meeting at 10 AM.

Best,
Seyi
EOF
```

### Send HTML email
```bash
cat <<'EOF' | himalaya message send -a hyperspace
From: seyi@hyperspace.ng
To: recipient@example.com
Subject: HTML Email
Content-Type: text/html; charset=utf-8

<h1>Hello</h1>
<p>This is an <b>HTML</b> email.</p>
EOF
```

### Send with CC and Reply-To
```bash
cat <<'EOF' | himalaya message send -a hyperspace
From: seyi@hyperspace.ng
To: recipient@example.com
Cc: other@example.com, team@example.com
Reply-To: noreply@hyperspace.ng
Subject: Announcement

Please review the attached proposal.
EOF
```

### Send to multiple recipients
```bash
cat <<'EOF' | himalaya message send -a hyperspace
From: seyi@hyperspace.ng
To: alice@example.com, bob@example.com
Subject: Team Update

Hello everyone...
EOF
```

### Send from a file
```bash
himalaya message send -a hyperspace < email.txt
```

### Pipe command output as email body
```bash
echo "Subject: Daily Report\n\n$(date)\n\n$(some-command)" | himalaya message send -a hyperspace
```

## Email Management

### Mark as read / unread
```bash
# Mark as read
himalaya flag add -a hyperspace 4658 seen

# Mark as unread
himalaya flag remove -a hyperspace 4658 seen
```

### Star / unstar
```bash
# Star
himalaya flag add -a hyperspace 4658 flagged

# Unstar
himalaya flag remove -a hyperspace 4658 flagged
```

### Mark as answered
```bash
himalaya flag add -a hyperspace 4658 answered
```

### Delete messages
```bash
himalaya message delete -a hyperspace 4658
# Delete multiple
himalaya message delete -a hyperspace 4658 4659 4660
```

### Move message to another folder
```bash
himalaya message move -a hyperspace 4658 --target Archive
```

### Copy message to another folder
```bash
himalaya message copy -a hyperspace 4658 --target Archive
```

## Folder Management

### List all folders
```bash
himalaya folder list -a hyperspace
```

### Create a new folder
```bash
himalaya folder add -a hyperspace "Projects"
```

### Delete a folder
```bash
himalaya folder delete -a hyperspace "Projects"
```

### Expunge (permanently remove deleted messages)
```bash
himalaya folder expunge -a hyperspace INBOX
```

### Purge (delete all messages in folder)
```bash
himalaya folder purge -a hyperspace Junk
```

## Attachments

### Download all attachments from a message
```bash
himalaya attachment download -a hyperspace 4658
```

Files are saved to the current working directory.

## Scripting & Automation

### Parse JSON output with jq
```bash
# Get all message IDs from inbox
himalaya envelope list -a hyperspace -o json | jq '.[].id'

# Get subjects from unread messages
himalaya envelope list 'not flag seen' -a hyperspace -o json | jq '.[] | "\(.id): \(.subject)"'

# Count messages per sender
himalaya envelope list -a hyperspace -o json | jq -r '.[].from' | sort | uniq -c | sort -rn
```

### Automated email notification
```bash
#!/bin/bash
# Check for new emails from a specific sender
UNREAD=$(himalaya envelope list -a hyperspace -o json 'from alerts@monitoring.com and not flag seen')
COUNT=$(echo "$UNREAD" | jq 'length')

if [ "$COUNT" -gt 0 ]; then
  echo "$COUNT new alert emails found"
  echo "$UNREAD" | jq -r '.[] | "\(.id): \(.subject)"'
fi
```

### Bulk archive read messages
```bash
# Get IDs of all read messages
IDS=$(himalaya envelope list -a hyperspace -o json 'flag seen' | jq -r '.[].id' | tr '\n' ' ')

# Move each to Archive
for id in $IDS; do
  himalaya message move -a hyperspace "$id" --target Archive
done
```

### Backup emails to files
```bash
# Export all messages from a specific sender
IDS=$(himalaya envelope list -a hyperspace -o json 'from important@client.com' | jq -r '.[].id')

for id in $IDS; do
  himalaya message export -a hyperspace "$id" > "email_${id}.eml"
done
```

### Send automated report
```bash
cat <<EOF | himalaya message send -a hyperspace --quiet
From: seyi@hyperspace.ng
To: team@hyperspace.ng
Subject: Daily Status Report - $(date +%Y-%m-%d)

$(generate-daily-report.sh)
EOF
```

## Multi-Account Workflows

### Switch between accounts
```bash
# Work account (default)
himalaya envelope list

# Personal account
himalaya envelope list -a personal

# Specific account
himalaya envelope list -a gmail
```

### Send from different accounts
```bash
cat <<'EOF' | himalaya message send -a personal
From: personal@gmail.com
To: friend@example.com
Subject: Weekend Plans

Hey, are you free this Saturday?
EOF
```

## Troubleshooting Workflows

### Diagnose account connectivity
```bash
himalaya account doctor hyperspace
```

### Diagnose and attempt fixes
```bash
himalaya account doctor hyperspace -f
```

### Debug IMAP/SMTP protocol
```bash
himalaya envelope list --debug -a hyperspace 2>&1 | head -50
```

### Full trace with backtraces
```bash
himalaya message send --trace -a hyperspace < email.txt 2>&1 | tail -30
```

### Verify config syntax
```bash
himalaya account list -a hyperspace -o json
```

### Check folder listing (tests IMAP connection)
```bash
himalaya folder list -a hyperspace
```