# Reporting Templates & Documentation Standards

Standard templates for VAPT assessment reports with evidence packaging requirements.

## Report Structure

### Executive Summary
- Assessment scope and objectives
- Key findings summary (no technical details)
- Risk rating distribution (Critical/High/Medium/Low/Info)
- Business impact summary
- Top 5 prioritized recommendations

### Technical Findings

Each finding follows this structure:

```markdown
## [VAPT-XXX] Finding Title

| Field | Value |
|-------|-------|
| **ID** | VAPT-001 |
| **Severity** | Critical / High / Medium / Low / Informational |
| **CVSS v3.1** | X.X (vector string) |
| **Category** | OWASP / OSSTMM category |
| **Affected Asset** | hostname:port or URL |
| **Status** | Confirmed / Remediated |
| **Assessment Type** | Blackbox / Greybox / Whitebox |

### Description
Clear description of the vulnerability and how it was discovered.

### Impact
What an attacker can achieve by exploiting this vulnerability. Include:
- Confidentiality impact
- Integrity impact
- Availability impact
- Business impact (data loss, financial, reputation)

### Steps to Reproduce
1. Step 1: Exact command or action
2. Step 2: Exact command or action
3. Step 3: Expected result demonstrating vulnerability

### Evidence
- Screenshot: `evidence/VAPT-001-screenshot-1.png` (timestamp: 2024-XX-XX HH:MM:SS UTC)
- Raw output: `evidence/VAPT-001-raw-output.txt`
- Network capture: `evidence/VAPT-001-capture.pcap` (if applicable)

### Verification Method
How this finding was verified (2+ methods):
1. Method 1: [Tool] [command] → [result]
2. Method 2: [Tool] [command] → [result]

### Remediation (Step-by-Step)
1. Step 1: Exact fix command or configuration change
2. Step 2: Exact fix command or configuration change
3. Step 3: ...

### Verification of Remediation
1. Run: [verification command]
2. Expected: [what to see if fixed]
3. Confirm: [final confirmation step]

### References
- CVE-XXXX-XXXX
- OWASP WSTG-XXXX-XX
- CIS Control X.X
- Vendor advisory: URL
```

---

## Finding ID Convention

```
VAPT-[SEQUENCE]
```

Example: VAPT-001, VAPT-002, VAPT-003...

## Severity & CVSS Mapping

| Severity | CVSS Range | Urgency |
|----------|-----------|----------|
| Critical | 9.0 - 10.0 | Immediate remediation (24-48h) |
| High | 7.0 - 8.9 | Urgent remediation (1 week) |
| Medium | 4.0 - 6.9 | Planned remediation (2 weeks) |
| Low | 0.1 - 3.9 | Scheduled remediation (1 month) |
| Informational | 0.0 | Best practice (next release) |

## CVSS v3.1 Vector Calculation

```
CVSS:3.1/AV:[N/A/L/P]/AC:[L/H]/PR:[N/L/H]/UI:[N/R]/S:[U/C]/C:[H/L/N]/I:[H/L/N]/A:[H/L/N]
```

### Attack Vector (AV)
- N = Network (remote, no physical access)
- A = Adjacent (same network segment)
- L = Local (local access required)
- P = Physical (physical access required)

### Attack Complexity (AC)
- L = Low (no special conditions)
- H = High (specific conditions required)

### Privileges Required (PR)
- N = None (no authentication)
- L = Low (standard user)
- H = High (admin/privileged user)

### User Interaction (UI)
- N = None (no user interaction)
- R = Required (victim must interact)

### Scope (S)
- U = Unchanged (same security authority)
- C = Changed (different security authority)

### Impact (C/I/A)
- H = High (total compromise)
- L = Low (limited compromise)
- N = None (no impact)

---

## Attack Path Documentation

For chained exploits, document the complete attack path:

```markdown
## Attack Path: [Name]

### Path Overview
Start → Step 1 → Step 2 → ... → Goal

### Step 1: Initial Access
- **Finding**: VAPT-XXX
- **Technique**: MITRE ATT&CK TXXXX
- **Tool**: [tool name and command]
- **Result**: [what was gained]

### Step 2: Execution
- **Finding**: VAPT-XXX
- **Technique**: MITRE ATT&CK TXXXX
- **Tool**: [tool name and command]
- **Result**: [what was gained]

### Step 3: Privilege Escalation
...

### Step 4: Lateral Movement
...

### Step 5: Data Exfiltration / Impact
...

### Overall Risk Rating
Based on the complete attack path (not individual findings): [Critical/High/Medium]

### Key Remediation (Breaking the Chain)
1. [Fix that breaks Step 1 — highest priority]
2. [Fix that breaks Step 3]
3. [Fix that breaks Step 5]
```

---

## Evidence Package Structure

```
evidence/
├── VAPT-001/
│   ├── screenshot-1.png
│   ├── screenshot-1.png.sha256
│   ├── raw-output.txt
│   ├── raw-output.txt.sha256
│   └── capture.pcap (if applicable)
├── VAPT-002/
│   ├── screenshot-1.png
│   ├── screenshot-1.png.sha256
│   └── tool-output.json
├── hashes.txt          # All SHA-256 hashes
├── timestamps.txt      # Evidence collection timestamps
└── chain-of-custody.log
```

### Hash Generation Command
```bash
find evidence/ -type f ! -name "*.sha256" -exec sh -c 'sha256sum "$1" > "$1.sha256"' _ {} \;
cat evidence/*/raw-output.txt.sha256 > evidence/hashes.txt
```

---

## Report Formats

### HTML Executive Report (vapt-report.py)
```bash
python3 scripts/vapt-report.py --input output/ --format html --template executive
```

### Technical Markdown Report
```bash
python3 scripts/vapt-report.py --input output/ --format markdown --template technical
```

### JSON Machine-Readable Report
```bash
python3 scripts/vapt-report.py --input output/ --format json --template full
```

---

## Assessment Metadata Template

Include at the beginning of every report:

```yaml
assessment:
  id: VAPT-2024-001
  client: "[Client Name]"
  scope: "[Scope Description]"
  type: "Blackbox | Greybox | Whitebox"
  start_date: "2024-01-15"
  end_date: "2024-01-19"
  assessor: "[Assessor Name]"
  methodology:
    - OSSTMM 3.0
    - OWASP WSTG v4.2
    - OWASP API Security Top 10 (2023)
    - MITRE ATT&CK
  tools:
    - Secator v0.31.0
    - NetExec v1.5.1
    - Metasploit Framework v6.x
    - Custom Python scripts
  findings:
    total: X
    critical: X
    high: X
    medium: X
    low: X
    informational: X
  status: "Draft | Final"
```