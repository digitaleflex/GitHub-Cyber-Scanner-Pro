---
description: Sign Windows executables (.exe, .dll, .msi) and macOS applications (.app) with code signing certificates. Use when signing binaries for distribution, setting up code signing workflows, or verifying signatures.
name: code-signing
---

# Code Signing Skill

Sign Windows executables (.exe, .dll, .msi) and macOS applications (.app) with Hyperspace Technologies certificate.

## Overview

This skill provides code signing capabilities for:
- **Windows**: EXE, DLL, MSI files using `osslsigncode`
- **macOS**: .app bundles using `codesign`

## Certificate Details

| Field | Value |
|-------|-------|
| Organization | Hyperspace Technologies |
| CN | Hyperspace Technologies Code Signing |
| Email | reactorpro@hyperspace.ng |
| Website | https://reactorpro.ng |
| Location | Lagos, Nigeria |
| Valid Until | January 21, 2036 (10 years) |

## Certificate Location

**Permanent Location** (survives reboots):
```
~/.config/opencode/certs/hyperspace/
├── hyperspace.crt      # X.509 Certificate
├── hyperspace.key      # Private Key (chmod 600)
├── hyperspace.pfx      # Windows PKCS#12 bundle (password: hyperspace2024)
└── hyperspace.cnf      # OpenSSL config
```

## Quick Start - Helper Scripts

Two helper scripts are installed for easy signing:

```bash
# Sign Windows executable
sign-windows /path/to/app.exe "Application Name" --replace

# Sign macOS app bundle  
sign-macos /path/to/App.app ng.hyperspace.appid "Application Name"
```

Scripts location: `~/.config/opencode/skills/code-signing/`
Symlinks: `~/.local/bin/sign-windows` and `~/.local/bin/sign-macos`

## Prerequisites

### Tools Required

```bash
# macOS (install via Homebrew)
brew install osslsigncode openssl

# Verify installation
which osslsigncode  # Should return path
which codesign      # Built into macOS
```

### Certificate Setup (First Time Only)

If certificates don't exist, create them:

```bash
mkdir -p /tmp/hyperspace-certs && cd /tmp/hyperspace-certs

# Create OpenSSL config
cat > hyperspace.cnf << 'EOF'
[req]
default_bits = 4096
prompt = no
default_md = sha256
distinguished_name = dn
x509_extensions = v3_code_sign

[dn]
C = NG
ST = Lagos
L = Lagos
O = Hyperspace Technologies
OU = Software Development
CN = Hyperspace Technologies Code Signing
emailAddress = reactorpro@hyperspace.ng

[v3_code_sign]
basicConstraints = critical, CA:FALSE
keyUsage = critical, digitalSignature
extendedKeyUsage = critical, codeSigning
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always
nsComment = "Hyperspace Technologies Code Signing Certificate"
subjectAltName = @alt_names

[alt_names]
URI.1 = https://reactorpro.ng
EOF

# Generate certificate (valid 10 years)
openssl req -x509 -newkey rsa:4096 -sha256 -days 3650 \
  -nodes -keyout hyperspace.key -out hyperspace.crt \
  -config hyperspace.cnf

# Create PKCS#12 for Windows signing
openssl pkcs12 -export -out hyperspace.pfx \
  -inkey hyperspace.key -in hyperspace.crt \
  -passout pass:hyperspace2024
```

---

## Signing Windows Executables

### Single File

```bash
osslsigncode sign \
  -pkcs12 /tmp/hyperspace-certs/hyperspace.pfx \
  -pass hyperspace2024 \
  -n "APPLICATION_NAME" \
  -i "https://reactorpro.ng" \
  -t http://timestamp.digicert.com \
  -h sha256 \
  -in "input.exe" \
  -out "output-signed.exe"
```

### Parameters

| Parameter | Description |
|-----------|-------------|
| `-pkcs12` | Path to PKCS#12 certificate bundle |
| `-pass` | Certificate password |
| `-n` | Application/Product name (displayed in Windows) |
| `-i` | Publisher URL |
| `-t` | Timestamp server URL |
| `-h` | Hash algorithm (sha256 recommended) |
| `-in` | Input file path |
| `-out` | Output signed file path |

### Timestamp Servers

Use one of these timestamp servers for long-term validity:

- `http://timestamp.digicert.com` (recommended)
- `http://timestamp.sectigo.com`
- `http://timestamp.globalsign.com/tsa/r6advanced1`
- `http://sha256timestamp.ws.symantec.com/sha256/timestamp`

### Batch Signing Script

```bash
#!/bin/bash
# Sign all EXE files in a directory

CERT="/tmp/hyperspace-certs/hyperspace.pfx"
PASS="hyperspace2024"
URL="https://reactorpro.ng"
TS="http://timestamp.digicert.com"

for exe in *.exe; do
  [ -f "$exe" ] || continue
  name="${exe%.exe}"
  
  echo "Signing: $exe"
  osslsigncode sign \
    -pkcs12 "$CERT" -pass "$PASS" \
    -n "$name" -i "$URL" \
    -t "$TS" -h sha256 \
    -in "$exe" -out "${name}-signed.exe"
  
  # Replace original with signed
  mv "$exe" "${name}-unsigned.exe"
  mv "${name}-signed.exe" "$exe"
done
```

### Verification

```bash
# Verify signature
osslsigncode verify "signed-file.exe"

# Quick verification (just show signer info)
osslsigncode verify "signed-file.exe" 2>&1 | grep -A5 "Signer's certificate:"

# Check timestamp
osslsigncode verify "signed-file.exe" 2>&1 | grep "Timestamp time:"
```

---

## Signing macOS Applications

### Update Info.plist (Optional but Recommended)

```bash
APP_PATH="/path/to/App.app"

# Add copyright
/usr/libexec/PlistBuddy -c "Delete :NSHumanReadableCopyright" "$APP_PATH/Contents/Info.plist" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Add :NSHumanReadableCopyright string 'Copyright © 2024-2026 Hyperspace Technologies. All rights reserved.'" "$APP_PATH/Contents/Info.plist"

# Add info string
/usr/libexec/PlistBuddy -c "Delete :CFBundleGetInfoString" "$APP_PATH/Contents/Info.plist" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Add :CFBundleGetInfoString string 'App Name - by Hyperspace Technologies'" "$APP_PATH/Contents/Info.plist"
```

### Ad-Hoc Signing (No Apple Developer Account)

```bash
# Remove existing signature
codesign --remove-signature "/path/to/App.app"

# Sign with ad-hoc signature
codesign --force --deep --sign - \
  --identifier "ng.hyperspace.appname" \
  --timestamp=none \
  "/path/to/App.app"
```

### With Apple Developer Certificate (If Available)

```bash
# List available identities
security find-identity -v -p codesigning

# Sign with Developer ID
codesign --force --deep --sign "Developer ID Application: Hyperspace Technologies" \
  --identifier "ng.hyperspace.appname" \
  --options runtime \
  --timestamp \
  "/path/to/App.app"
```

### Verification

```bash
# Detailed signature info
codesign -dvvv "/path/to/App.app"

# Verify signature is valid
codesign --verify --deep --strict "/path/to/App.app" && echo "✓ Valid" || echo "✗ Invalid"

# Check Gatekeeper assessment (requires Apple Developer cert)
spctl --assess --type execute "/path/to/App.app"
```

---

## Complete Signing Workflow

### Windows EXE

```bash
# 1. Ensure certificate exists
[ -f /tmp/hyperspace-certs/hyperspace.pfx ] || echo "Run certificate setup first!"

# 2. Sign the executable
EXE_PATH="/path/to/app.exe"
APP_NAME="MyApplication"

osslsigncode sign \
  -pkcs12 /tmp/hyperspace-certs/hyperspace.pfx \
  -pass hyperspace2024 \
  -n "$APP_NAME" \
  -i "https://reactorpro.ng" \
  -t http://timestamp.digicert.com \
  -h sha256 \
  -in "$EXE_PATH" \
  -out "${EXE_PATH%.exe}-signed.exe"

# 3. Replace original (optional)
mv "$EXE_PATH" "${EXE_PATH%.exe}-unsigned.exe"
mv "${EXE_PATH%.exe}-signed.exe" "$EXE_PATH"

# 4. Verify
osslsigncode verify "$EXE_PATH" 2>&1 | grep -A5 "Signer's certificate:"
```

### macOS App

```bash
# 1. Set app path
APP_PATH="/path/to/App.app"
APP_ID="ng.hyperspace.myapp"
APP_NAME="MyApp"

# 2. Update Info.plist
/usr/libexec/PlistBuddy -c "Delete :NSHumanReadableCopyright" "$APP_PATH/Contents/Info.plist" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Add :NSHumanReadableCopyright string 'Copyright © 2024-2026 Hyperspace Technologies. All rights reserved.'" "$APP_PATH/Contents/Info.plist"

/usr/libexec/PlistBuddy -c "Delete :CFBundleGetInfoString" "$APP_PATH/Contents/Info.plist" 2>/dev/null || true
/usr/libexec/PlistBuddy -c "Add :CFBundleGetInfoString string '$APP_NAME - by Hyperspace Technologies'" "$APP_PATH/Contents/Info.plist"

# 3. Sign
codesign --remove-signature "$APP_PATH" 2>/dev/null || true
codesign --force --deep --sign - \
  --identifier "$APP_ID" \
  --timestamp=none \
  "$APP_PATH"

# 4. Verify
codesign --verify --deep --strict "$APP_PATH" && echo "✓ Signature valid"
codesign -dvvv "$APP_PATH" 2>&1 | grep -E "Identifier|Signature|TeamIdentifier"
```

---

## Troubleshooting

### Windows Signing Issues

| Issue | Solution |
|-------|----------|
| `osslsigncode: command not found` | Install: `brew install osslsigncode` |
| Certificate password error | Use password: `hyperspace2024` |
| Timestamp server timeout | Try alternative timestamp server |
| File not found | Use absolute paths |

### macOS Signing Issues

| Issue | Solution |
|-------|----------|
| `resource fork, Finder information, or similar detritus not allowed` | Run: `xattr -cr /path/to/App.app` |
| `No identity found` | Use ad-hoc signing: `--sign -` |
| `code object is not signed at all` | Ensure `--deep` flag is used |
| Gatekeeper blocks app | Need Apple Developer ID for notarization |

### Removing Extended Attributes (macOS)

```bash
# Remove quarantine and resource forks before signing
xattr -cr "/path/to/App.app"
```

---

## Notes

1. **Self-Signed Certificate**: The Hyperspace Technologies certificate is self-signed. Windows will show "Unknown Publisher" warning. For trusted signatures, purchase a certificate from DigiCert, Sectigo, or GlobalSign.

2. **macOS Gatekeeper**: Ad-hoc signed apps will be blocked by Gatekeeper. Users must right-click → Open to bypass. For full Gatekeeper compatibility, use an Apple Developer ID ($99/year) and notarize.

3. **Timestamp Importance**: Always use a timestamp server. This ensures signatures remain valid even after the certificate expires.

4. **Certificate Backup**: The certificate files in `/tmp/` will be lost on reboot. For permanent storage, copy to a secure location.
