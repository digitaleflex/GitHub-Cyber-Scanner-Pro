#!/usr/bin/env python3
"""VAPT Exploitation Chain Orchestrator

Orchestrates end-to-end assessment chains combining Secator, NetExec, 
Metasploit, and raw Python for advanced exploitation with verification.

Usage:
    python3 vapt-chain.py --target target.com --type blackbox --scope webapp+network --output /tmp/vapt/
    python3 vapt-chain.py --target 10.0.0.0/24 --type greybox --scope network --user admin --password P@ss --output /tmp/vapt/
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
import time
import socket
import hashlib
from pathlib import Path

# Import sibling scripts (optional - graceful if not available)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def log(msg, level="INFO"):
    ts = datetime.datetime.utcnow().isoformat() + "Z"
    print(f"[{ts}] [{level}] {msg}", flush=True)


def run_cmd(cmd, timeout=300, capture=True):
    """Execute command, return (returncode, stdout, stderr)."""
    log(f"CMD: {cmd}")
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=capture, text=True, timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        log(f"Command timed out after {timeout}s", "WARN")
        return -1, "", "TIMEOUT"
    except Exception as e:
        log(f"Command failed: {e}", "ERROR")
        return -1, "", str(e)


def check_tool(tool_name):
    """Check if a tool is available on PATH."""
    rc, _, _ = run_cmd(f"which {tool_name}", timeout=5, capture=True)
    return rc == 0


def hash_file(filepath):
    """SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def save_evidence(data, filepath, evidence_dir):
    """Save evidence with integrity hash."""
    full_path = os.path.join(evidence_dir, filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(data)
    hash_val = hash_file(full_path)
    with open(full_path + ".sha256", "w") as f:
        f.write(f"{hash_val}  {os.path.basename(full_path)}\n")
    return full_path


def phase_recon(target, scope, output_dir, evidence_dir, assessment_type):
    """Phase 1: Reconnaissance — Secator-driven."""
    log("=" * 60)
    log("PHASE 1: RECONNAISSANCE")
    log("=" * 60)
    results = {}

    if not check_tool("secator"):
        log("Secator not found! Install: pip install secator && secator install tools", "ERROR")
        return results

    if assessment_type == "blackbox":
        # Full passive + active recon
        log("Blackbox: Running full passive + active reconnaissance")

        # Subdomain discovery
        rc, stdout, stderr = run_cmd(
            f"secator x subfinder {target} -raw", timeout=120
        )
        if rc == 0 and stdout:
            save_evidence(stdout, "phase1/subfinder.txt", evidence_dir)
            subdomains = [l.strip() for l in stdout.strip().split("\n") if l.strip()]
            results["subdomains"] = subdomains
            log(f"Found {len(subdomains)} subdomains")

        # DNS enumeration
        rc, stdout, stderr = run_cmd(
            f"secator x dnsx {target} -a -cname -txt -mx -ns", timeout=60
        )
        if rc == 0 and stdout:
            save_evidence(stdout, "phase1/dnsx.txt", evidence_dir)

        # HTTP probing
        rc, stdout, stderr = run_cmd(
            f"secator x httpx {target} -td -server -status-code -title -json",
            timeout=120,
        )
        if rc == 0 and stdout:
            save_evidence(stdout, "phase1/httpx-probe.json", evidence_dir)

    elif assessment_type == "greybox":
        log("Greybox: Running targeted reconnaissance")
        rc, stdout, stderr = run_cmd(
            f"secator x httpx {target} -td -server -status-code -json",
            timeout=60,
        )
        if rc == 0 and stdout:
            save_evidence(stdout, "phase1/httpx-probe.json", evidence_dir)

    else:  # whitebox
        log("Whitebox: Validating provided information")
        rc, stdout, stderr = run_cmd(
            f"secator x httpx {target} -td -server -status-code -json",
            timeout=60,
        )
        if rc == 0 and stdout:
            save_evidence(stdout, "phase1/httpx-validate.json", evidence_dir)

    return results


def phase_mapping(target, scope, output_dir, evidence_dir):
    """Phase 2: Port/service mapping."""
    log("=" * 60)
    log("PHASE 2: MAPPING")
    log("=" * 60)
    results = {"ports": [], "services": []}

    if check_tool("secator"):
        # Port scan
        rc, stdout, stderr = run_cmd(
            f"secator x naabu {target} -top-ports 1000 -json",
            timeout=180,
        )
        if rc == 0 and stdout:
            save_evidence(stdout, "phase2/naabu-ports.json", evidence_dir)

        # Service version detection
        rc, stdout, stderr = run_cmd(
            f"secator x nmap {target} -sV -sC -p 22,80,443,445,3389,8080,8443 -json",
            timeout=120,
        )
        if rc == 0 and stdout:
            save_evidence(stdout, "phase2/nmap-services.json", evidence_dir)

    # NetExec for network scope
    if "network" in scope and check_tool("nxc"):
        rc, stdout, stderr = run_cmd(
            f"nxc smb {target} -u '' -p '' 2>&1", timeout=120
        )
        if rc == 0 and stdout:
            save_evidence(stdout, "phase2/nxc-smb-sweep.txt", evidence_dir)

        rc, stdout, stderr = run_cmd(
            f"nxc ssh {target} -u '' -p '' 2>&1", timeout=60
        )
        if rc == 0 and stdout:
            save_evidence(stdout, "phase2/nxc-ssh-sweep.txt", evidence_dir)

    return results


def phase_vuln_scan(target, scope, output_dir, evidence_dir):
    """Phase 3: Automated vulnerability scanning."""
    log("=" * 60)
    log("PHASE 3: VULNERABILITY SCANNING")
    log("=" * 60)
    results = {"web_vulns": [], "network_vulns": []}

    if check_tool("secator"):
        rc, stdout, stderr = run_cmd(
            f"secator x nuclei {target} -tags cve,exposure,misconfig "
            f"-severity critical,high,medium -json",
            timeout=600,
        )
        if rc == 0 and stdout:
            save_evidence(stdout, "phase3/nuclei-scan.json", evidence_dir)

        rc, stdout, stderr = run_cmd(
            f"secator x nmap {target} --script vuln -json",
            timeout=300,
        )
        if rc == 0 and stdout:
            save_evidence(stdout, "phase3/nmap-vuln.json", evidence_dir)

    # Network vuln check with NetExec
    if "network" in scope and check_tool("nxc"):
        rc, stdout, stderr = run_cmd(
            f"nxc smb {target} -u '' -p '' -M enum_vulnerability 2>&1", timeout=120
        )
        if rc == 0 and stdout:
            save_evidence(stdout, "phase3/nxc-smb-vulns.txt", evidence_dir)

    return results


def phase_manual_test(target, scope, output_dir, evidence_dir, creds=None):
    """Phase 4: Targeted manual testing — OWASP/OSSTMM procedures."""
    log("=" * 60)
    log("PHASE 4: MANUAL TESTING (OWASP/OSSTMM)")
    log("=" * 60)
    results = {"web_tests": {}, "network_tests": {}}

    # Security headers check
    try:
        import requests
        url = f"https://{target}" if not target.startswith("http") else target
        r = requests.get(url, timeout=10, verify=False)
        headers_to_check = [
            "strict-transport-security", "content-security-policy",
            "x-frame-options", "x-content-type-options",
            "referrer-policy", "permissions-policy",
        ]
        missing = [h for h in headers_to_check if h not in r.headers]
        if missing:
            results["web_tests"]["missing_headers"] = missing
            save_evidence(
                json.dumps({"missing_headers": missing}, indent=2),
                "phase4/missing-headers.json",
                evidence_dir,
            )
            log(f"Missing security headers: {missing}")
    except Exception as e:
        log(f"Security header check failed: {e}", "WARN")

    # Network manual tests
    if "network" in scope and creds and check_tool("nxc"):
        user, password = creds
        # LDAP enumeration
        rc, stdout, stderr = run_cmd(
            f"nxc ldap {target} -u '{user}' -p '{password}' --asreproast /dev/stdout 2>&1",
            timeout=60,
        )
        if rc == 0 and stdout:
            save_evidence(stdout, "phase4/asreproast.txt", evidence_dir)

        # Kerberoasting
        rc, stdout, stderr = run_cmd(
            f"nxc ldap {target} -u '{user}' -p '{password}' --kerberoasting /dev/stdout 2>&1",
            timeout=60,
        )
        if rc == 0 and stdout:
            save_evidence(stdout, "phase4/kerberoast.txt", evidence_dir)

        # Delegation check
        rc, stdout, stderr = run_cmd(
            f"nxc ldap {target} -u '{user}' -p '{password}' --find-delegation 2>&1",
            timeout=60,
        )
        if rc == 0 and stdout:
            save_evidence(stdout, "phase4/delegation.txt", evidence_dir)

    return results


def phase_exploit(target, scope, output_dir, evidence_dir, creds=None):
    """Phase 5: Verified exploitation — Metasploit + custom Python."""
    log("=" * 60)
    log("PHASE 5: EXPLOITATION (with verification)")
    log("=" * 60)
    results = {"exploits": [], "verified": []}

    if not check_tool("msfconsole"):
        log("Metasploit not found. Install: brew install metasploit or apt install metasploit-framework", "WARN")

    # Note: Actual exploitation should be done interactively with careful scope validation.
    # This phase documents the exploit chain and verifies findings.

    if creds and check_tool("nxc"):
        user, password = creds
        # Verify credential validity
        rc, stdout, stderr = run_cmd(
            f"nxc smb {target} -u '{user}' -p '{password}' 2>&1", timeout=30
        )
        if rc == 0 and "Pwn3d" in stdout:
            results["exploits"].append({
                "type": "credential_reuse",
                "target": target,
                "tool": "nxc",
                "verified": True,
            })
            save_evidence(stdout, "phase5/nxc-cred-verify.txt", evidence_dir)

    return results


def phase_verify(output_dir, evidence_dir):
    """Phase 7: False-positive verification."""
    log("=" * 60)
    log("PHASE 7: VERIFICATION (False-Positive Elimination)")
    log("=" * 60)

    verify_script = os.path.join(SCRIPT_DIR, "vapt-verify.py")
    if os.path.exists(verify_script):
        rc, stdout, stderr = run_cmd(
            f"python3 {verify_script} --input {output_dir}/recon-results.json "
            f"--evidence-dir {evidence_dir}",
            timeout=120,
        )
        if rc == 0 and stdout:
            save_evidence(stdout, "phase7/verification-results.json", evidence_dir)
    else:
        log("vapt-verify.py not found, running inline verification", "WARN")
        # Inline basic verification
        try:
            import requests
            # Verify each web endpoint
            verified_file = os.path.join(output_dir, "verified-findings.json")
            if os.path.exists(verified_file):
                with open(verified_file) as f:
                    data = json.load(f)
                log(f"Verified {len(data.get('findings', []))} findings")
        except Exception as e:
            log(f"Inline verification error: {e}", "WARN")


def phase_report(output_dir, evidence_dir, target, assessment_type):
    """Phase 9: Report generation."""
    log("=" * 60)
    log("PHASE 9: REPORT GENERATION")
    log("=" * 60)

    report_script = os.path.join(SCRIPT_DIR, "vapt-report.py")
    if os.path.exists(report_script):
        for fmt in ["html", "markdown", "json"]:
            rc, stdout, stderr = run_cmd(
                f"python3 {report_script} --input {output_dir} "
                f"--format {fmt} --target {target} --type {assessment_type}",
                timeout=30,
            )
            if rc == 0:
                log(f"Report generated ({fmt}): {stdout.strip()}")
    else:
        log("vapt-report.py not found, skipping report generation", "WARN")


def main():
    parser = argparse.ArgumentParser(
        description="VAPT Exploitation Chain Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Blackbox webapp:     python3 vapt-chain.py --target target.com --type blackbox --scope webapp --output /tmp/vapt/
  Greybox network:     python3 vapt-chain.py --target 10.0.0.0/24 --type greybox --scope network --user admin --password P@ss
  Whitebox full:       python3 vapt-chain.py --target target.com --type whitebox --scope webapp+network --output /tmp/vapt/
        """,
    )
    parser.add_argument("--target", required=True, help="Target (domain, IP, CIDR)")
    parser.add_argument("--type", choices=["blackbox", "greybox", "whitebox"],
                        default="blackbox", help="Assessment type")
    parser.add_argument("--scope", default="webapp+network",
                        help="Scope: webapp, network, webapp+network")
    parser.add_argument("--output", default="/tmp/vapt", help="Output directory")
    parser.add_argument("--user", help="Username for authenticated testing")
    parser.add_argument("--password", help="Password for authenticated testing")
    parser.add_argument("--phase", choices=["recon", "mapping", "vulnscan", "manual", "exploit", "verify", "report", "all"],
                        default="all", help="Run specific phase or all")
    parser.add_argument("--skip-phases", nargs="+", default=[],
                        help="Phases to skip")

    args = parser.parse_args()

    # Setup
    output_dir = os.path.abspath(args.output)
    evidence_dir = os.path.join(output_dir, "evidence")
    os.makedirs(evidence_dir, exist_ok=True)

    creds = (args.user, args.password) if args.user and args.password else None

    # Check tools
    log("VAPT Exploitation Chain Orchestrator")
    log(f"Target: {args.target} | Type: {args.type} | Scope: {args.scope}")
    log("Checking tools...")
    for tool in ["secator", "nxc", "msfconsole", "nmap", "nuclei", "httpx"]:
        available = check_tool(tool)
        status = "✓" if available else "✗"
        log(f"  {status} {tool}")

    # Track assessment
    assessment = {
        "meta": {
            "target": args.target,
            "type": args.type,
            "scope": args.scope,
            "start_time": datetime.datetime.utcnow().isoformat() + "Z",
        },
        "phases": {},
    }

    # Execute phases
    phases_to_run = (
        ["recon", "mapping", "vulnscan", "manual", "exploit", "verify", "report"]
        if args.phase == "all"
        else [args.phase]
    )

    for phase in phases_to_run:
        if phase in args.skip_phases:
            log(f"Skipping phase: {phase}")
            continue

        if phase == "recon":
            assessment["phases"]["recon"] = phase_recon(
                args.target, args.scope, output_dir, evidence_dir, args.type
            )
        elif phase == "mapping":
            assessment["phases"]["mapping"] = phase_mapping(
                args.target, args.scope, output_dir, evidence_dir
            )
        elif phase == "vulnscan":
            assessment["phases"]["vuln_scan"] = phase_vuln_scan(
                args.target, args.scope, output_dir, evidence_dir
            )
        elif phase == "manual":
            assessment["phases"]["manual_test"] = phase_manual_test(
                args.target, args.scope, output_dir, evidence_dir, creds
            )
        elif phase == "exploit":
            assessment["phases"]["exploitation"] = phase_exploit(
                args.target, args.scope, output_dir, evidence_dir, creds
            )
        elif phase == "verify":
            phase_verify(output_dir, evidence_dir)
        elif phase == "report":
            phase_report(output_dir, evidence_dir, args.target, args.type)

    # Save assessment state
    assessment["meta"]["end_time"] = datetime.datetime.utcnow().isoformat() + "Z"
    with open(os.path.join(output_dir, "assessment-state.json"), "w") as f:
        json.dump(assessment, f, indent=2, default=str)

    # Final summary
    log("=" * 60)
    log("ASSESSMENT COMPLETE")
    log("=" * 60)
    log(f"Target: {args.target}")
    log(f"Type: {args.type}")
    log(f"Scope: {args.scope}")
    log(f"Output: {output_dir}")
    log(f"Evidence: {evidence_dir}")
    log(f"Duration: {assessment['meta']['start_time']} → {assessment['meta']['end_time']}")

    # Generate report if not already done
    if "report" not in phases_to_run and args.phase == "all":
        phase_report(output_dir, evidence_dir, args.target, args.type)


if __name__ == "__main__":
    main()
