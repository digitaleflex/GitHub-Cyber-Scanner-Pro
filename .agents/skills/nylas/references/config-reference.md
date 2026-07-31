# Nylas CLI Configuration Reference

## Config File Location

```
~/.config/nylas/config.yaml
```

Override with `--config <path>` flag or `NYLAS_CONFIG` environment variable.

## Config Structure

```yaml
# ~/.config/nylas/config.yaml

# API Configuration
api:
  key: nyl_v0_xxxxx                          # API key (stored in keyring if available)
  client_id: 613733f4-5aaf-4aeb-bbd7-xxx    # Application client ID
  region: us                                  # API region: us or eu

# Default grant (account) to use
default_grant: seyi@hyperspace.ng

# Output preferences
output: table                                 # table, json, or yaml
no_color: false                              # Disable color output
wide: false                                  # Show full IDs

# MCP server settings
mcp:
  transport: stdio                            # stdio or sse
  port: 8080                                  # Port for SSE transport
```

## Secret Storage

Nylas CLI stores sensitive data (API keys, OAuth tokens) in the **system keyring** by default:

- **macOS**: Keychain
- **Linux**: Secret Service API (GNOME Keyring / KDE Wallet)
- **Windows**: Windows Credential Manager

### Migrate to keyring

```bash
nylas auth migrate    # Migrate credentials from config file to system keyring
```

### View current auth

```bash
nylas auth status     # Show current account and grant status
nylas auth list       # List all authenticated accounts
nylas auth whoami     # Show current user details
```

## Multi-Account Setup

Nylas CLI supports multiple accounts (grants). Use `--grant-id` or `--email` to select:

```bash
# Authenticate multiple providers
nylas auth login --provider google      # Work Gmail
nylas auth login --provider imap        # Custom IMAP
nylas auth login --provider microsoft   # Outlook

# Switch default account
nylas config set default_grant "work@gmail.com"

# Use specific account for a command
nylas email list --grant-id 195fcdc7-04c1-48a1-b224-e5db334ee656
nylas email send --to user@example.com --subject "Hello" --body "..." -y \
  --grant-id 195fcdc7-04c1-48a1-b224-e5db334ee656
```

## Provider Templates

### Google (Gmail) — OAuth

```bash
# Authenticate (opens browser)
nylas auth login --provider google

# Requires Google OAuth consent
# Supports: email, calendar, contacts
# Free tier: 1 grant, limited API calls
```

### Microsoft 365 (Outlook) — OAuth

```bash
# Authenticate (opens browser)
nylas auth login --provider microsoft

# Requires Microsoft OAuth consent
# Supports: email, calendar, contacts
```

### Exchange on-premises (EWS)

```bash
# Authenticate with EWS
nylas auth login --provider ews

# Supports: email, calendar, contacts via Exchange Web Services
```

### iCloud — App-specific password

```bash
# Requires app-specific password from appleid.apple.com
nylas auth login --provider icloud

# Supports: email, calendar, contacts
# Generate app password at: https://appleid.apple.com > Sign-In and Security > App-Specific Passwords
```

### Yahoo — App password

```bash
# Requires Yahoo app password
nylas auth login --provider yahoo

# Supports: email, calendar, contacts
# Generate app password at: https://login.yahoo.com/myaccount/security/app-passwords
```

### Generic IMAP/SMTP

```bash
# Interactive setup (prompts for credentials)
nylas auth login --provider imap

# IMAP settings needed:
#   IMAP username (email)
#   IMAP password
#   IMAP host (e.g., mail.example.com)
#   IMAP port (993 for TLS, 143 for STARTTLS)
#   Add SMTP? Y
#   SMTP host
#   SMTP port (465 for TLS, 587 for STARTTLS)
#   SMTP username
#   SMTP password
```

## Provider Capabilities

| Provider | Email | Calendar | Contacts | Auth Method |
|----------|-------|----------|----------|-------------|
| Google | ✅ | ✅ | ✅ | OAuth |
| Microsoft 365 | ✅ | ✅ | ✅ | OAuth |
| Exchange (EWS) | ✅ | ✅ | ✅ | OAuth |
| iCloud | ✅ | ✅ | ✅ | App password |
| Yahoo | ✅ | ✅ | ✅ | App password |
| IMAP/SMTP | ✅ | ❌ | ❌ | Credentials |

## IMAP Provider Details

IMAP providers (like cPanel, Dovecot, Postfix) support **email only**:

- ✅ List, read, send, search, delete, mark, move
- ✅ Folders and labels
- ✅ Attachments
- ✅ Threads
- ✅ Scheduled send
- ✅ Drafts
- ❌ Calendar events
- ❌ Contacts
- ❌ Availability/free-busy

### Common IMAP configurations

| Provider | IMAP Host | IMAP Port | SMTP Host | SMTP Port |
|----------|-----------|------------|-----------|------------|
| cPanel | mail.domain.com | 993 | mail.domain.com | 465 |
| Gmail (IMAP mode) | imap.gmail.com | 993 | smtp.gmail.com | 587 |
| Outlook (IMAP mode) | outlook.office365.com | 993 | smtp.office365.com | 587 |
| Fastmail | imap.fastmail.com | 993 | smtp.fastmail.com | 465 |
| Zoho | imap.zoho.com | 993 | smtp.zoho.com | 465 |
| ProtonMail Bridge | 127.0.0.1 | 1143 | 127.0.0.1 | 1025 |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `NYLAS_API_KEY` | Override API key |
| `NYLAS_CLIENT_ID` | Override client ID |
| `NYLAS_REGION` | Override region (`us` or `eu`) |
| `NYLAS_CONFIG` | Override config file path |
| `NYLAS_GRANT_ID` | Override default grant ID |

## Troubleshooting

### "nylas not configured"

```bash
nylas auth config --api-key nyl_xxx
# or
nylas init
```

### "grant not found" or "expired"

```bash
nylas auth list              # Check grants
nylas auth login --provider imap   # Re-authenticate
```

### "provider not responding"

For IMAP: verify host, port, and encryption settings match your mail server.

```bash
# Test IMAP connectivity
openssl s_client -connect mail.example.com:993 -quiet

# Test SMTP connectivity
openssl s_client -connect mail.example.com:465 -quiet
```

### "IMAP contact persistence feature is not enabled"

IMAP provider does not support contacts. This is a Nylas platform limitation for IMAP grants.

### Reset configuration

```bash
nylas auth config --reset    # Reset all configuration
```

### Debug mode

```bash
nylas email list -v          # Verbose output
nylas email list --verbose    # Debug-level output
nylas doctor                  # Full diagnostic check
```