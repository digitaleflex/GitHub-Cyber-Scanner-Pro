#!/bin/bash
# av-submit-prep.sh - Prepare AV false positive submission for ReactorPro
# Usage: ./av-submit-prep.sh /path/to/ReactorPro.exe

set -euo pipefail

FILE="${1:-}"
if [ -z "$FILE" ] || [ ! -f "$FILE" ]; then
    echo "Usage: $0 /path/to/executable"
    echo "Example: $0 ~/Downloads/ReactorPro.exe"
    exit 1
fi

FILENAME=$(basename "$FILE")
FILESIZE=$(stat -f%z "$FILE" 2>/dev/null || stat -c%s "$FILE" 2>/dev/null)
SHA256=$(shasum -a 256 "$FILE" 2>/dev/null | awk '{print $1}' || sha256sum "$FILE" | awk '{print $1}')
MD5=$(md5 -q "$FILE" 2>/dev/null || md5sum "$FILE" 2>/dev/null | awk '{print $1}')
SHA1=$(shasum -a 1 "$FILE" 2>/dev/null | awk '{print $1}' || sha1sum "$FILE" | awk '{print $1}')

# Get latest release info
RELEASE_URL="https://github.com/DrOlu/ReactorPro/releases/latest"

cat << EOF
================================================================================
ANTIVIRUS FALSE POSITIVE SUBMISSION - ReactorPro
================================================================================

FILE INFORMATION:
-----------------
Filename:      $FILENAME
File Size:     $FILESIZE bytes
SHA256:        $SHA256
SHA1:          $SHA1
MD5:           $MD5
Download URL:  $RELEASE_URL

VENDOR INFORMATION:
-------------------
Product Name:   ReactorPro
Vendor:         Hyperspace Technologies
Website:        https://reactorpro.ng
Contact Email:  reactorpro@hyperspace.ng
GitHub Repo:    https://github.com/DrOlu/ReactorPro
License:        MIT (Open Source)

DESCRIPTION (copy for submissions):
------------------------------------
ReactorPro is an AI-powered coding assistant desktop application for software
developers. Built with Electron, it provides AI-assisted code completion,
chat functionality, and integrates with various language model APIs.

Key facts:
- Open source software (MIT License)
- Digitally signed by Hyperspace Technologies
- Built via automated GitHub Actions CI/CD pipeline
- No malicious functionality - source code publicly auditable
- Legitimate developer productivity tool

This file is incorrectly flagged as malicious. Please review and whitelist.

================================================================================
SUBMISSION CHECKLIST
================================================================================

Priority 1 - Critical (submit first):
[ ] Microsoft Defender:  https://www.microsoft.com/en-us/wdsi/filesubmission
    - Select "I believe this file should not be detected"
    - Upload file or provide SHA256 hash above
    
[ ] Google Safe Browsing: https://safebrowsing.google.com/safebrowsing/report_error/
    - Report false warning for download URL

Priority 2 - Major AV (submit within 24 hours):
[ ] Norton/Symantec:    https://submit.norton.com/
[ ] McAfee:             https://www.mcafee.com/enterprise/en-us/threat-center/threat-feedback.html
[ ] Kaspersky:          https://opentip.kaspersky.com/
[ ] Avast/AVG:          https://www.avast.com/false-positive-file-form.php
[ ] Bitdefender:        https://www.bitdefender.com/submit/

Priority 3 - Secondary (submit within 48 hours):
[ ] ESET:               https://support.eset.com/en/kb141
[ ] Trend Micro:        https://www.trendmicro.com/en_us/about/legal/detection-reevaluation.html
[ ] Malwarebytes:       https://www.malwarebytes.com/support/fp
[ ] Sophos:             https://support.sophos.com/support/s/filesubmission
[ ] F-Secure:           https://www.f-secure.com/en/business/support-and-downloads/submit-a-sample

================================================================================
QUICK COPY - SUBMISSION TEXT
================================================================================

Subject: False Positive Report - ReactorPro Desktop Application

Body:
The file "$FILENAME" (SHA256: $SHA256) is being incorrectly 
detected as malicious. This is a false positive.

ReactorPro is a legitimate, open-source AI coding assistant for developers.
- GitHub: https://github.com/DrOlu/ReactorPro
- Website: https://reactorpro.ng
- Vendor: Hyperspace Technologies

The application is digitally signed and built via automated CI/CD.
Please review and whitelist this software.

Thank you.

================================================================================
EOF

# Copy SHA256 to clipboard if available
if command -v pbcopy &> /dev/null; then
    echo "$SHA256" | pbcopy
    echo "SHA256 copied to clipboard!"
elif command -v xclip &> /dev/null; then
    echo "$SHA256" | xclip -selection clipboard
    echo "SHA256 copied to clipboard!"
fi
