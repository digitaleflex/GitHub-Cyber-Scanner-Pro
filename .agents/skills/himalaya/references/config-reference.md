# Himalaya Configuration Reference

## Config File Location

```
~/.config/himalaya/config.toml
```

Override with `-c` flag or `HIMALAYA_CONFIG` env var.

Multiple config files can be merged using `:` as delimiter:
```bash
himalaya -c ~/public-config.toml:~/private-config.toml envelope list
```

## Minimal Single-Account Config

```toml
[accounts.myaccount]

default = true
display-name = "Your Name"
email = "you@example.com"

[accounts.myaccount.backend]
type = "imap"
host = "imap.example.com"
port = 993
login = "you@example.com"

[accounts.myaccount.backend.auth]
type = "password"
raw = "your-password"

[accounts.myaccount.backend.encryption]
type = "tls"
starttls = false

[accounts.myaccount.message.send.backend]
type = "smtp"
host = "smtp.example.com"
port = 465
login = "you@example.com"

[accounts.myaccount.message.send.backend.auth]
type = "password"
raw = "your-password"

[accounts.myaccount.message.send.backend.encryption]
type = "tls"
starttls = false
```

## Multi-Account Config

```toml
[accounts.work]
default = true
display-name = "Work User"
email = "work@company.com"

[accounts.work.backend]
type = "imap"
host = "imap.company.com"
port = 993
login = "work@company.com"

[accounts.work.backend.auth]
type = "password"
raw = "work-password"

[accounts.work.backend.encryption]
type = "tls"
starttls = false

[accounts.work.message.send.backend]
type = "smtp"
host = "smtp.company.com"
port = 465
login = "work@company.com"

[accounts.work.message.send.backend.auth]
type = "password"
raw = "work-password"

[accounts.work.message.send.backend.encryption]
type = "tls"
starttls = false

[accounts.personal]
default = false
display-name = "Personal User"
email = "personal@gmail.com"

[accounts.personal.backend]
type = "imap"
host = "imap.gmail.com"
port = 993
login = "personal@gmail.com"

[accounts.personal.backend.auth]
type = "oauth2"

[accounts.personal.backend.auth.oauth2]
method = "xoauth2"
client-id = "your-client-id"
client-secret = "your-client-secret"
auth-url = "https://accounts.google.com/o/oauth2/auth"
token-url = "https://oauth2.googleapis.com/token"
redirect-host = "localhost"
redirect-port = 9999
scopes = ["https://mail.google.com/"]

[accounts.personal.backend.encryption]
type = "tls"
starttls = false

[accounts.personal.message.send.backend]
type = "smtp"
host = "smtp.gmail.com"
port = 465
login = "personal@gmail.com"

[accounts.personal.message.send.backend.auth]
type = "oauth2"

[accounts.personal.message.send.backend.auth.oauth2]
method = "xoauth2"
client-id = "your-client-id"
client-secret = "your-client-secret"
auth-url = "https://accounts.google.com/o/oauth2/auth"
token-url = "https://oauth2.googleapis.com/token"
redirect-host = "localhost"
redirect-port = 9999
scopes = ["https://mail.google.com/"]

[accounts.personal.message.send.backend.encryption]
type = "tls"
starttls = false
```

Use `-a work` or `-a personal` to select the account.

## Auth Types

### Password Auth

```toml
[accounts.myaccount.backend.auth]
type = "password"
raw = "your-password"      # Plaintext password

# Or use keyring (system password manager):
# type = "password"
# command = "secret-tool lookup email you@example.com"
```

### OAuth2 Auth (Gmail, Outlook, etc.)

```toml
[accounts.myaccount.backend.auth]
type = "oauth2"

[accounts.myaccount.backend.auth.oauth2]
method = "xoauth2"             # Required: "xoauth2"
client-id = "..."              # OAuth2 client ID
client-secret = "..."          # OAuth2 client secret
auth-url = "https://accounts.google.com/o/oauth2/auth"
token-url = "https://oauth2.googleapis.com/token"
redirect-host = "localhost"
redirect-port = 9999
scopes = ["https://mail.google.com/"]
```

### Command-Based Auth (Keyring, 1Password, etc.)

```toml
[accounts.myaccount.backend.auth]
type = "password"
command = "op read 'op://Vault/Item/field'"   # 1Password CLI

# Or:
# command = "secret-tool lookup email you@example.com"  # libsecret
# command = "security find-generic-password -s my-email -w"  # macOS Keychain
```

## Encryption Types

### TLS (IMAPS / SMTPS)
Default for ports 993 (IMAP) and 465 (SMTP). Wraps the entire connection in TLS from the start.

```toml
[accounts.myaccount.backend.encryption]
type = "tls"
starttls = false
```

### STARTTLS
Default for ports 143 (IMAP) and 587 (SMTP). Starts plain, then upgrades to TLS.

```toml
[accounts.myaccount.backend.encryption]
type = "tls"
starttls = true
```

### None (not recommended)
```toml
[accounts.myaccount.backend.encryption]
type = "none"
```

## Message Send Options

### Save Copy to Sent Folder

```toml
[accounts.myaccount.message.send]
save-copy = true   # Default: true — saves a copy to the sent folder after sending

[accounts.myaccount.message.send]
save-copy = false  # Disable if server's IMAP APPEND causes errors
```

### Folder Aliases

```toml
[accounts.myaccount.folder.alias]
sent = "Sent Items"     # Maps internal "sent" to actual folder name
drafts = "Drafts"
trash = "Deleted Items"
junk = "Spam"
archive = "Archive"
```

## Common Provider Configs

### Gmail (OAuth2 required since Sept 2024)

```toml
[accounts.gmail]
default = true
display-name = "Your Name"
email = "you@gmail.com"

[accounts.gmail.backend]
type = "imap"
host = "imap.gmail.com"
port = 993
login = "you@gmail.com"

[accounts.gmail.backend.auth]
type = "oauth2"

[accounts.gmail.backend.auth.oauth2]
method = "xoauth2"
client-id = "YOUR_GOOGLE_CLIENT_ID"
client-secret = "YOUR_GOOGLE_CLIENT_SECRET"
auth-url = "https://accounts.google.com/o/oauth2/auth"
token-url = "https://oauth2.googleapis.com/token"
redirect-host = "localhost"
redirect-port = 9999
scopes = ["https://mail.google.com/"]

[accounts.gmail.backend.encryption]
type = "tls"
starttls = false

[accounts.gmail.message.send.backend]
type = "smtp"
host = "smtp.gmail.com"
port = 465
login = "you@gmail.com"

[accounts.gmail.message.send.backend.auth]
type = "oauth2"

[accounts.gmail.message.send.backend.auth.oauth2]
method = "xoauth2"
client-id = "YOUR_GOOGLE_CLIENT_ID"
client-secret = "YOUR_GOOGLE_CLIENT_SECRET"
auth-url = "https://accounts.google.com/o/oauth2/auth"
token-url = "https://oauth2.googleapis.com/token"
redirect-host = "localhost"
redirect-port = 9999
scopes = ["https://mail.google.com/"]

[accounts.gmail.message.send.backend.encryption]
type = "tls"
starttls = false
```

### Outlook / Office 365

```toml
[accounts.outlook]
default = false
display-name = "Your Name"
email = "you@outlook.com"

[accounts.outlook.backend]
type = "imap"
host = "outlook.office365.com"
port = 993
login = "you@outlook.com"

[accounts.outlook.backend.auth]
type = "password"
raw = "your-password"

[accounts.outlook.backend.encryption]
type = "tls"
starttls = false

[accounts.outlook.message.send.backend]
type = "smtp"
host = "smtp.office365.com"
port = 587
login = "you@outlook.com"

[accounts.outlook.message.send.backend.auth]
type = "password"
raw = "your-password"

[accounts.outlook.message.send.backend.encryption]
type = "tls"
starttls = true
```

### cPanel / Custom Hosting (like hyperspace.ng)

```toml
[accounts.hyperspace]
default = true
display-name = "Seyi"
email = "seyi@hyperspace.ng"
message.send.save-copy = false

[accounts.hyperspace.backend]
type = "imap"
host = "mail.hyperspace.ng"
port = 993
login = "seyi@hyperspace.ng"

[accounts.hyperspace.backend.auth]
type = "password"
raw = "your-password"

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
raw = "your-password"

[accounts.hyperspace.message.send.backend.encryption]
type = "tls"
starttls = false

[accounts.hyperspace.folder.alias]
drafts = "Drafts"
trash = "Trash"
junk = "Junk"
```

## Troubleshooting

### "cannot add IMAP message" / "unexpected tag"

This error occurs when himalaya tries to APPEND a sent message copy to the IMAP Sent folder and the server has a quirk with the APPEND response. Fix:

```toml
message.send.save-copy = false
```

### Authentication failures

1. Verify credentials: `himalaya account doctor <account>`
2. Check encryption type (TLS vs STARTTLS)
3. For Gmail: OAuth2 is required since Sept 2024
4. Use `--debug` to see auth mechanism negotiation

### Connection timeouts

1. Verify host and port are correct
2. Check firewall allows outbound on IMAP (993/143) and SMTP (465/587)
3. Try `--trace` for full protocol dump