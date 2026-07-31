---
description: Submit software to antivirus vendors to prevent false positive detections. Use when releasing new software that triggers AV warnings, submitting binaries for whitelisting, or checking VirusTotal detection status.
name: av-whitelisting
---

# Antivirus Whitelisting Skill

Submit software to antivirus vendors to prevent false positive detections.

## Overview

When releasing new software, antivirus engines often flag unknown executables as suspicious. This skill provides the process and links to submit binaries for whitelisting.

## Major AV Vendor Submission Links

### Tier 1 - Critical (Highest Impact)

| Vendor | Submission URL | Notes |
|--------|----------------|-------|
| **Microsoft Defender** | https://www.microsoft.com/en-us/wdsi/filesubmission | Also affects SmartScreen reputation |
| **Google Safe Browsing** | https://safebrowsing.google.com/safebrowsing/report_error/?hl=en | For Chrome/Google download warnings |
| **Windows SmartScreen** | https://www.microsoft.com/en-us/wdsi/filesubmission | Same as Defender, select "Should not be detected" |

### Tier 2 - Major Consumer AV

| Vendor | Submission URL | Notes |
|--------|----------------|-------|
| **Norton/Symantec** | https://submit.norton.com/ | |
| **McAfee** | https://www.mcafee.com/enterprise/en-us/threat-center/threat-feedback.html | |
| **Kaspersky** | https://opentip.kaspersky.com/ | Upload file or submit hash |
| **Avast/AVG** | https://www.avast.com/false-positive-file-form.php | Avast owns AVG |
| **Bitdefender** | https://www.bitdefender.com/submit/ | |
| **ESET** | https://support.eset.com/en/kb141-submit-a-virus-detection-or-a-false-positive-sample-to-esets-laboratory | |
| **Trend Micro** | https://www.trendmicro.com/en_us/about/legal/detection-reevaluation.html | |
| **Malwarebytes** | https://www.malwarebytes.com/support/fp | |

### Tier 3 - Enterprise/Regional

| Vendor | Submission URL | Notes |
|--------|----------------|-------|
| **Sophos** | https://support.sophos.com/support/s/filesubmission | |
| **F-Secure** | https://www.f-secure.com/en/business/support-and-downloads/submit-a-sample | |
| **Panda** | https://www.pandasecurity.com/en/homeusers/false-positive/ | |
| **Comodo** | https://www.comodo.com/home/internet-security/submit-file.php | |
| **ClamAV** | https://www.clamav.net/reports/fp | Open source, used by many mail servers |
| **VirusTotal** | https://www.virustotal.com/gui/contact-us | Contact for persistent false positives |

## Submission Process

### Step 1: Check Current Detection Status

```bash
# Upload to VirusTotal first to see which engines detect it
# https://www.virustotal.com/gui/home/upload

# Or use the API
VT_API_KEY="your_key"
curl -s --request POST \
  --url 'https://www.virustotal.com/api/v3/files' \
  --header "x-apikey: $VT_API_KEY" \
  --form file=@/path/to/executable.exe
```

### Step 2: Prepare Submission Information

For each submission, you'll need:

1. **File Details**
   - Filename: `ReactorPro.exe` or `ReactorPro.app`
   - SHA256 hash: `sha256sum /path/to/file`
   - File size
   - Download URL (GitHub release link)

2. **Software Description**
   ```
   Product Name: ReactorPro
   Vendor: Hyperspace Technologies
   Website: https://reactorpro.ng
   Description: AI-powered coding assistant desktop application
   
   ReactorPro is an Electron-based desktop application that provides
   AI-assisted code completion and chat functionality. It connects to
   language model APIs and provides a local interface for developers.
   
   The application is open source: https://github.com/DrOlu/ReactorPro
   ```

3. **Why it's a False Positive**
   ```
   This is a legitimate desktop application for software developers.
   It is digitally signed by Hyperspace Technologies.
   The source code is publicly available on GitHub.
   The application does not contain any malicious functionality.
   ```

### Step 3: Submit to Each Vendor

Use the submission script below to automate hash generation and create submission text.

## Submission Script

```bash
#!/bin/bash
# av-submit-prep.sh - Prepare AV false positive submission

FILE="$1"
if [ -z "$FILE" ] || [ ! -f "$FILE" ]; then
    echo "Usage: $0 /path/to/executable"
    exit 1
fi

FILENAME=$(basename "$FILE")
FILESIZE=$(stat -f%z "$FILE" 2>/dev/null || stat -c%s "$FILE")
SHA256=$(shasum -a 256 "$FILE" | awk '{print $1}')
MD5=$(md5 -q "$FILE" 2>/dev/null || md5sum "$FILE" | awk '{print $1}')
SHA1=$(shasum -a 1 "$FILE" | awk '{print $1}')

cat << EOF
================================================================================
ANTIVIRUS FALSE POSITIVE SUBMISSION
================================================================================

FILE INFORMATION:
-----------------
Filename:   $FILENAME
File Size:  $FILESIZE bytes
SHA256:     $SHA256
SHA1:       $SHA1
MD5:        $MD5

VENDOR INFORMATION:
-------------------
Product Name:   ReactorPro
Vendor:         Hyperspace Technologies
Website:        https://reactorpro.ng
Contact:        reactorpro@hyperspace.ng
GitHub:         https://github.com/DrOlu/ReactorPro

DESCRIPTION:
------------
ReactorPro is an AI-powered coding assistant desktop application built with
Electron. It provides developers with AI-assisted code completion, chat
functionality, and integrates with various language model APIs.

The application is:
- Open source (MIT License)
- Digitally signed by Hyperspace Technologies
- Built automatically via GitHub Actions CI/CD
- Distributed through GitHub Releases

This is NOT malware. Please whitelist this application.

SUBMISSION LINKS:
-----------------
1. Microsoft Defender:  https://www.microsoft.com/en-us/wdsi/filesubmission
2. Norton/Symantec:     https://submit.norton.com/
3. McAfee:              https://www.mcafee.com/enterprise/en-us/threat-center/threat-feedback.html
4. Kaspersky:           https://opentip.kaspersky.com/
5. Avast/AVG:           https://www.avast.com/false-positive-file-form.php
6. Bitdefender:         https://www.bitdefender.com/submit/
7. ESET:                https://support.eset.com/en/kb141
8. Trend Micro:         https://www.trendmicro.com/en_us/about/legal/detection-reevaluation.html
9. Malwarebytes:        https://www.malwarebytes.com/support/fp
10. Google Safe Browse: https://safebrowsing.google.com/safebrowsing/report_error/

================================================================================
EOF
```

## Best Practices

1. **Submit after each major release** - New versions may trigger new detections
2. **Keep records** - Track submission tickets/case numbers
3. **Be patient** - Whitelisting can take 1-7 days per vendor
4. **Monitor VirusTotal** - Check periodically for new detections
5. **Code sign properly** - Signed binaries are more likely to be whitelisted quickly
6. **Provide source code links** - Open source projects are easier to verify

## Automated Monitoring

Set up a GitHub Action to check VirusTotal after each release:

```yaml
name: Check VirusTotal

on:
  release:
    types: [published]

jobs:
  check-vt:
    runs-on: ubuntu-latest
    steps:
      - name: Download release asset
        run: |
          gh release download ${{ github.event.release.tag_name }} \
            --pattern "*.exe" --dir ./assets
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          
      - name: Submit to VirusTotal
        run: |
          for file in ./assets/*.exe; do
            echo "Submitting $file to VirusTotal..."
            curl -s --request POST \
              --url 'https://www.virustotal.com/api/v3/files' \
              --header "x-apikey: ${{ secrets.VT_API_KEY }}" \
              --form file=@"$file"
          done
```

## Priority Vendors for ReactorPro

For a developer tool targeting Windows users, prioritize:

1. **Microsoft Defender/SmartScreen** - Most critical, affects all Windows users
2. **Google Safe Browsing** - Affects Chrome downloads
3. **Norton** - High consumer market share
4. **Windows Defender ATP** - Enterprise users
5. **Malwarebytes** - Popular among tech-savvy users

## Timeframes

| Vendor | Typical Response Time |
|--------|----------------------|
| Microsoft | 1-3 business days |
| Norton | 2-5 business days |
| Kaspersky | 1-2 business days |
| Avast/AVG | 1-3 business days |
| Bitdefender | 2-4 business days |
| ESET | 1-2 business days |

## Contact for Escalation

If false positives persist after submission:
- Microsoft: msrc@microsoft.com
- Norton: security-response@symantec.com
- Most vendors have business/developer programs for persistent issues
