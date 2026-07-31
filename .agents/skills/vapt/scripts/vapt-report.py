#!/usr/bin/env python3
"""VAPT Report Generator

Generates professional VAPT assessment reports in HTML, Markdown, and JSON formats.

Usage:
    python3 vapt-report.py --input /tmp/vapt/ --format html --template executive
    python3 vapt-report.py --input /tmp/vapt/ --format markdown --template technical
    python3 vapt-report.py --input /tmp/vapt/ --format json --template full
"""

import argparse
import datetime
import json
import os
import sys
from pathlib import Path


SEVERITY_COLORS = {
    "CRITICAL": "#CC1100",
    "HIGH": "#FF6600",
    "MEDIUM": "#FFAA00",
    "LOW": "#3399FF",
    "INFORMATIONAL": "#999999",
}

SEVERITY_ORDER = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL"]


def load_findings(input_dir):
    """Load findings from verified-findings.json and recon-results.json."""
    findings = []

    verified_file = os.path.join(input_dir, "verified-findings.json")
    if os.path.exists(verified_file):
        with open(verified_file) as f:
            data = json.load(f)
            findings.extend(data.get("findings", []))

    # Also check for individual scan outputs
    evidence_dir = os.path.join(input_dir, "evidence")
    if os.path.exists(evidence_dir):
        for root, dirs, files in os.walk(evidence_dir):
            for fname in files:
                if fname.endswith(".json") and not fname.endswith(".sha256"):
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath) as f:
                            data = json.load(f)
                            if isinstance(data, list):
                                findings.extend(data)
                            elif isinstance(data, dict) and "findings" in data:
                                findings.extend(data["findings"])
                    except (json.JSONDecodeError, KeyError):
                        pass

    return findings


def classify_severity(finding):
    """Classify finding severity."""
    sev = finding.get("severity", "INFORMATIONAL").upper()
    if sev in SEVERITY_ORDER:
        return sev
    # Try to map common variants
    mapping = {
        "CRIT": "CRITICAL", "CRITICAL": "CRITICAL",
        "HIGH": "HIGH", "IMPORTANT": "HIGH",
        "MEDIUM": "MEDIUM", "MODERATE": "MEDIUM", "MED": "MEDIUM",
        "LOW": "LOW", "MINOR": "LOW",
        "INFO": "INFORMATIONAL", "INFORMATIONAL": "INFORMATIONAL",
    }
    return mapping.get(sev, "INFORMATIONAL")


def generate_html_report(findings, meta, template="executive"):
    """Generate HTML report."""
    severity_counts = {}
    for sev in SEVERITY_ORDER:
        severity_counts[sev] = sum(1 for f in findings if classify_severity(f) == sev)

    total = len(findings)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VAPT Assessment Report - {meta.get('target', 'Unknown')}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               margin: 0; padding: 20px; background: #f5f5f5; color: #333; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #1a1a2e, #16213e); color: white; 
                   padding: 30px; border-radius: 10px; margin-bottom: 20px; }}
        .header h1 {{ margin: 0 0 10px 0; font-size: 28px; }}
        .header .meta {{ font-size: 14px; opacity: 0.8; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 15px; margin-bottom: 30px; }}
        .summary-card {{ padding: 20px; border-radius: 8px; text-align: center; color: white; font-weight: bold; }}
        .summary-card .count {{ font-size: 36px; display: block; margin-bottom: 5px; }}
        .summary-card .label {{ font-size: 12px; text-transform: uppercase; }}
        .finding {{ background: white; padding: 25px; border-radius: 8px; margin-bottom: 15px; 
                    border-left: 4px solid #ccc; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .finding.critical {{ border-left-color: {SEVERITY_COLORS['CRITICAL']}; }}
        .finding.high {{ border-left-color: {SEVERITY_COLORS['HIGH']}; }}
        .finding.medium {{ border-left-color: {SEVERITY_COLORS['MEDIUM']}; }}
        .finding.low {{ border-left-color: {SEVERITY_COLORS['LOW']}; }}
        .finding.info {{ border-left-color: {SEVERITY_COLORS['INFORMATIONAL']}; }}
        .severity-badge {{ display: inline-block; padding: 3px 10px; border-radius: 4px; 
                           color: white; font-size: 12px; font-weight: bold; text-transform: uppercase; }}
        .finding h3 {{ margin: 0 0 10px 0; }}
        .finding-detail {{ margin: 10px 0; font-size: 14px; }}
        .finding-detail strong {{ color: #555; }}
        .remediation {{ background: #f0f7ff; padding: 15px; border-radius: 6px; margin-top: 10px; 
                        border: 1px solid #cce0ff; }}
        .remediation h4 {{ margin: 0 0 10px 0; color: #0066cc; }}
        .remediation ol {{ margin: 5px 0; padding-left: 20px; }}
        .remediation li {{ margin: 5px 0; font-size: 13px; }}
        code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-size: 13px; }}
        .attack-path {{ background: #fff3f0; padding: 15px; border-radius: 6px; 
                        border: 1px solid #ffccbb; margin-bottom: 15px; }}
        .attack-path h4 {{ margin: 0 0 10px 0; color: #cc3300; }}
        table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
        th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f8f8; font-weight: bold; }}
        .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; padding: 20px; }}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>VAPT Assessment Report</h1>
        <div class="meta">
            <p>Target: <strong>{meta.get('target', 'N/A')}</strong> | 
               Type: <strong>{meta.get('type', 'N/A')}</strong> | 
               Date: <strong>{meta.get('timestamp', datetime.datetime.utcnow().strftime('%Y-%m-%d'))}</strong></p>
            <p>Methodology: OSSTMM 3.0 | OWASP WSTG v4.2 | OWASP API Top 10 | MITRE ATT&CK</p>
            <p>Tools: Secator | NetExec | Metasploit | Python</p>
        </div>
    </div>

    <div class="summary-grid">
"""

    for sev in SEVERITY_ORDER:
        count = severity_counts.get(sev, 0)
        html += f"""        <div class="summary-card" style="background:{SEVERITY_COLORS[sev]}">
            <span class="count">{count}</span>
            <span class="label">{sev}</span>
        </div>\n"""

    html += f"""    </div>

    <h2>Findings Overview ({total} total)</h2>
    <table>
        <tr><th>#</th><th>Finding</th><th>Severity</th><th>Category</th><th>Target</th><th>Status</th></tr>
"""

    # Sort findings by severity
    sorted_findings = sorted(findings, key=lambda f: SEVERITY_ORDER.index(classify_severity(f)))

    for i, finding in enumerate(sorted_findings, 1):
        sev = classify_severity(finding)
        html += f"""        <tr>
            <td>{i}</td>
            <td>{finding.get('name', finding.get('type', 'Unknown'))}</td>
            <td><span class="severity-badge" style="background:{SEVERITY_COLORS[sev]}">{sev}</span></td>
            <td>{finding.get('category', finding.get('type', 'N/A'))}</td>
            <td><code>{finding.get('target', 'N/A')}</code></td>
            <td>{finding.get('verification_status', finding.get('status', 'Confirmed'))}</td>
        </tr>\n"""

    html += """    </table>

    <h2>Detailed Findings</h2>
"""

    for i, finding in enumerate(sorted_findings, 1):
        sev = classify_severity(finding)
        sev_class = sev.lower().replace("informational", "info")
        name = finding.get("name", finding.get("type", "Unknown Finding"))
        target = finding.get("target", "N/A")
        impact = finding.get("impact", finding.get("details", "See details below"))
        remediation = finding.get("remediation", "See remediation-guide.md for detailed fix instructions")
        steps = finding.get("steps_to_reproduce", [])
        remediation_steps = finding.get("remediation_steps", [])

        html += f"""    <div class="finding {sev_class}">
        <h3>[VAPT-{i:03d}] {name}</h3>
        <p><span class="severity-badge" style="background:{SEVERITY_COLORS[sev]}">{sev}</span> 
           Target: <code>{target}</code></p>
        <div class="finding-detail">
            <strong>Impact:</strong> {impact}
        </div>
"""

        if steps:
            html += """        <div class="finding-detail"><strong>Steps to Reproduce:</strong><ol>\n"""
            for step in steps:
                html += f"            <li><code>{step}</code></li>\n"
            html += "        </ol></div>\n"

        if remediation_steps:
            html += f"""        <div class="remediation">
            <h4>Step-by-Step Remediation</h4>
            <ol>\n"""
            for step in remediation_steps:
                html += f"            <li>{step}</li>\n"
            html += "        </ol>\n"
        else:
            html += f"""        <div class="remediation">
            <h4>Remediation</h4>
            <p>{remediation}</p>\n"""

        html += """        </div>
    </div>\n"""

    html += f"""
    <div class="footer">
        <p>Generated by VAPT Report Generator | {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        <p>Methodology: OSSTMM 3.0 | OWASP WSTG v4.2 | OWASP API Security Top 10 (2023)</p>
    </div>
</div>
</body>
</html>"""

    return html


def generate_markdown_report(findings, meta, template="technical"):
    """Generate Markdown report."""
    severity_counts = {}
    for sev in SEVERITY_ORDER:
        severity_counts[sev] = sum(1 for f in findings if classify_severity(f) == sev)

    md = f"""# VAPT Assessment Report

## Metadata

| Field | Value |
|-------|-------|
| **Target** | {meta.get('target', 'N/A')} |
| **Assessment Type** | {meta.get('type', 'N/A')} |
| **Date** | {meta.get('timestamp', datetime.datetime.utcnow().strftime('%Y-%m-%d'))} |
| **Methodology** | OSSTMM 3.0, OWASP WSTG v4.2, OWASP API Top 10, MITRE ATT&CK |
| **Tools** | Secator, NetExec, Metasploit, Python |

## Executive Summary

This report presents the findings of a **{meta.get('type', 'N/A')}** vulnerability assessment and penetration test 
conducted against **{meta.get('target', 'N/A')}**.

### Finding Distribution

| Severity | Count |
|----------|-------|
"""

    for sev in SEVERITY_ORDER:
        md += f"| {sev} | {severity_counts.get(sev, 0)} |\n"

    md += f"\n**Total Findings: {len(findings)}**\n\n"

    # Top recommendations
    critical = [f for f in findings if classify_severity(f) == "CRITICAL"]
    high = [f for f in findings if classify_severity(f) == "HIGH"]
    if critical or high:
        md += "### Immediate Actions Required\n\n"
        for f in critical + high:
            name = f.get("name", f.get("type", "Unknown"))
            md += f"- **[{classify_severity(f)}]** {name}\n"
        md += "\n"

    md += """## Detailed Findings

"""

    sorted_findings = sorted(findings, key=lambda f: SEVERITY_ORDER.index(classify_severity(f)))

    for i, finding in enumerate(sorted_findings, 1):
        sev = classify_severity(finding)
        name = finding.get("name", finding.get("type", "Unknown Finding"))
        target = finding.get("target", "N/A")
        impact = finding.get("impact", finding.get("details", "See details"))
        remediation = finding.get("remediation", "See remediation-guide.md")

        md += f"""### [VAPT-{i:03d}] {name}

| Field | Value |
|-------|-------|
| **Severity** | {sev} |
| **Target** | `{target}` |
| **Status** | {finding.get('verification_status', finding.get('status', 'Confirmed'))} |

**Impact**: {impact}

**Remediation**: {remediation}

---

"""

    md += f"""---
*Generated by VAPT Report Generator on {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*
"""

    return md


def generate_json_report(findings, meta):
    """Generate JSON machine-readable report."""
    sorted_findings = sorted(findings, key=lambda f: SEVERITY_ORDER.index(classify_severity(f)))

    report = {
        "meta": {
            **meta,
            "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
            "methodology": ["OSSTMM 3.0", "OWASP WSTG v4.2", "OWASP API Top 10 2023", "MITRE ATT&CK"],
            "tools": ["Secator", "NetExec", "Metasploit", "Python"],
        },
        "summary": {
            "total": len(findings),
            "by_severity": {
                sev: sum(1 for f in findings if classify_severity(f) == sev)
                for sev in SEVERITY_ORDER
            },
        },
        "findings": [
            {
                "id": f"VAPT-{i:03d}",
                "name": f.get("name", f.get("type", "Unknown")),
                "severity": classify_severity(f),
                "category": f.get("category", f.get("type", "")),
                "target": f.get("target", ""),
                "impact": f.get("impact", f.get("details", "")),
                "remediation": f.get("remediation", ""),
                "status": f.get("verification_status", f.get("status", "Confirmed")),
            }
            for i, f in enumerate(sorted_findings, 1)
        ],
    }
    return json.dumps(report, indent=2, default=str)


def main():
    parser = argparse.ArgumentParser(description="VAPT Report Generator")
    parser.add_argument("--input", required=True, help="Input directory with findings")
    parser.add_argument("--format", choices=["html", "markdown", "json"], default="html")
    parser.add_argument("--template", choices=["executive", "technical", "full"], default="executive")
    parser.add_argument("--output", help="Output file path (auto-generated if not specified)")
    parser.add_argument("--target", default="Unknown", help="Target name for report header")
    parser.add_argument("--type", default="Blackbox", help="Assessment type")

    args = parser.parse_args()

    findings = load_findings(args.input)
    meta = {
        "target": args.target,
        "type": args.type,
        "timestamp": datetime.datetime.utcnow().strftime("%Y-%m-%d"),
    }

    if not findings:
        print("No findings found. Check input directory.")
        sys.exit(1)

    if args.format == "html":
        content = generate_html_report(findings, meta, args.template)
        ext = "html"
    elif args.format == "markdown":
        content = generate_markdown_report(findings, meta, args.template)
        ext = "md"
    else:
        content = generate_json_report(findings, meta)
        ext = "json"

    # Output
    if args.output:
        output_path = args.output
    else:
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        output_path = os.path.join(args.input, f"vapt-report-{timestamp}.{ext}")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        f.write(content)

    print(f"Report generated: {output_path}")
    print(f"Findings: {len(findings)}")
    for sev in SEVERITY_ORDER:
        count = sum(1 for f in findings if classify_severity(f) == sev)
        if count:
            print(f"  {sev}: {count}")


if __name__ == "__main__":
    main()
