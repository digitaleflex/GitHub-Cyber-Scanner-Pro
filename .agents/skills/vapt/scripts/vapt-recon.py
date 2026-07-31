#!/usr/bin/env python3
"""VAPT Automated Reconnaissance Orchestrator

Orchestrates Secator and NetExec reconnaissance phases for comprehensive
target discovery across all OSSTMM channels.

Usage:
    python3 vapt-recon.py --target target.com --type blackbox --scope webapp+network --output /tmp/vapt/
    python3 vapt-recon.py --target 10.0.0.0/24 --type greybox --scope network --output /tmp/vapt/
"""

import argparse
import json
import os
import subprocess
import sys
import hashlib
import datetime
from pathlib import Path


def log(msg, level="INFO"):
    ts = datetime.datetime.utcnow().isoformat() + "Z"
    print(f"[{ts}] [{level}] {msg}", flush=True)


def run_cmd(cmd, timeout=300, capture=True):
    """Execute command, return (returncode, stdout, stderr)."""
    log(f"Running: {cmd}")
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=capture, text=True, timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        log(f"Command timed out after {timeout}s: {cmd}", "WARN")
        return -1, "", "TIMEOUT"
    except Exception as e:
        log(f"Command failed: {e}", "ERROR")
        return -1, "", str(e)


def hash_file(filepath):
    """SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def save_evidence(data, filepath, evidence_dir):
    """Save data to evidence directory with SHA-256 hash."""
    full_path = os.path.join(evidence_dir, filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(data)
    # Hash
    hash_val = hash_file(full_path)
    with open(full_path + ".sha256", "w") as f:
        f.write(f"{hash_val}  {os.path.basename(full_path)}\n")
    log(f"Saved evidence: {full_path} (sha256: {hash_val[:16]}...)")
    return full_path


def check_tool(tool_name):
    """Check if a tool is available on PATH."""
    rc, _, _ = run_cmd(f"which {tool_name}", timeout=5)
    return rc == 0


def phase_passive_recon(target, output_dir, evidence_dir):
    """Phase 1a: Passive reconnaissance — no direct target interaction."""
    log("=" * 60)
    log("PHASE 1a: PASSIVE RECONNAISSANCE")
    log("=" * 60)
    results = {"subdomains": [], "dns_records": [], "certs": []}

    # Subdomain discovery with subfinder (via secator)
    if check_tool("secator"):
        rc, stdout, stderr = run_cmd(
            f"secator x subfinder {target} -raw -json", timeout=120
        )
        if rc == 0 and stdout:
            save_evidence(stdout, "recon/subfinder-raw.json", evidence_dir)
            for line in stdout.strip().split("\n"):
                try:
                    obj = json.loads(line)
                    if obj.get("host"):
                        results["subdomains"].append(obj["host"])
                except json.JSONDecodeError:
                    if line.strip():
                        results["subdomains"].append(line.strip())

    # Certificate transparency
    rc, stdout, stderr = run_cmd(
        f'curl -s "https://crt.sh/?q=%25.{target}&output=json" | jq -r ".[].name_value" 2>/dev/null | sort -u',
        timeout=30,
    )
    if rc == 0 and stdout:
        crt_domains = [d.strip() for d in stdout.strip().split("\n") if d.strip()]
        results["certs"] = crt_domains
        results["subdomains"].extend(crt_domains)
        save_evidence("\n".join(crt_domains), "recon/crtsh-domains.txt", evidence_dir)

    results["subdomains"] = list(set(results["subdomains"]))
    log(f"Passive recon found {len(results['subdomains'])} unique subdomains")
    return results


def phase_active_recon(target, subdomains, output_dir, evidence_dir):
    """Phase 1b: Active reconnaissance — direct target interaction."""
    log("=" * 60)
    log("PHASE 1b: ACTIVE RECONNAISSANCE")
    log("=" * 60)
    results = {"alive_hosts": [], "technologies": [], "open_ports": []}

    # HTTP probing
    targets = [target] + subdomains[:50]  # Limit for safety
    target_list = os.path.join(output_dir, "recon_targets.txt")
    with open(target_list, "w") as f:
        f.write("\n".join(targets))

    if check_tool("secator"):
        # HTTP probe
        rc, stdout, stderr = run_cmd(
            f"secator x httpx -l {target_list} -td -asn -cdn -server -title -status-code -json",
            timeout=180,
        )
        if rc == 0 and stdout:
            save_evidence(stdout, "recon/httpx-probe.json", evidence_dir)
            for line in stdout.strip().split("\n"):
                try:
                    obj = json.loads(line)
                    results["alive_hosts"].append({
                        "url": obj.get("url", ""),
                        "status": obj.get("status_code", 0),
                        "title": obj.get("title", ""),
                        "tech": obj.get("technologies", []),
                        "server": obj.get("server", ""),
                    })
                except json.JSONDecodeError:
                    pass

    # Port scanning
    if check_tool("secator"):
        rc, stdout, stderr = run_cmd(
            f"secator x naabu {target} -top-ports 1000 -json",
            timeout=120,
        )
        if rc == 0 and stdout:
            save_evidence(stdout, "recon/naabu-ports.json", evidence_dir)

    log(f"Active recon found {len(results['alive_hosts'])} alive hosts")
    return results


def phase_network_recon(target, output_dir, evidence_dir, creds=None):
    """Phase 2: Network-level reconnaissance with NetExec."""
    log("=" * 60)
    log("PHASE 2: NETWORK RECONNAISSANCE (NetExec)")
    log("=" * 60)
    results = {"smb_hosts": [], "ssh_hosts": [], "ldap_info": {}, "shares": []}

    if not check_tool("nxc"):
        log("NetExec (nxc) not found, skipping network recon", "WARN")
        return results

    # SMB discovery
    rc, stdout, stderr = run_cmd(
        f"nxc smb {target} -u '' -p '' 2>&1", timeout=120
    )
    if rc == 0 and stdout:
        save_evidence(stdout, "network/nxc-smb-null.txt", evidence_dir)
        for line in stdout.strip().split("\n"):
            if "SMB" in line or "445" in line:
                results["smb_hosts"].append(line.strip())

    # SMB shares (if creds provided)
    if creds:
        user, password = creds
        rc, stdout, stderr = run_cmd(
            f"nxc smb {target} -u '{user}' -p '{password}' --shares 2>&1", timeout=60
        )
        if rc == 0 and stdout:
            save_evidence(stdout, "network/nxc-smb-shares.txt", evidence_dir)
            results["shares"] = stdout.strip().split("\n")

    # LDAP enumeration
    if creds:
        user, password = creds
        rc, stdout, stderr = run_cmd(
            f"nxc ldap {target} -u '{user}' -p '{password}' --users 2>&1", timeout=60
        )
        if rc == 0 and stdout:
            save_evidence(stdout, "network/nxc-ldap-users.txt", evidence_dir)

    # SSH check
    rc, stdout, stderr = run_cmd(
        f"nxc ssh {target} -u '' -p '' 2>&1", timeout=60
    )
    if rc == 0 and stdout:
        save_evidence(stdout, "network/nxc-ssh.txt", evidence_dir)

    log(f"Network recon: {len(results['smb_hosts'])} SMB hosts, "
        f"{len(results.get('shares', []))} shares")
    return results


def phase_vuln_scan(target, output_dir, evidence_dir):
    """Phase 3: Automated vulnerability scanning."""
    log("=" * 60)
    log("PHASE 3: VULNERABILITY SCANNING")
    log("=" * 60)
    results = {"vulnerabilities": []}

    if check_tool("secator"):
        # Nuclei scan
        rc, stdout, stderr = run_cmd(
            f"secator x nuclei {target} -tags cve,exposure,misconfig "
            f"-severity critical,high,medium -json",
            timeout=600,
        )
        if rc == 0 and stdout:
            save_evidence(stdout, "vulns/nuclei-scan.json", evidence_dir)
            for line in stdout.strip().split("\n"):
                try:
                    obj = json.loads(line)
                    results["vulnerabilities"].append({
                        "name": obj.get("info", {}).get("name", ""),
                        "severity": obj.get("info", {}).get("severity", ""),
                        "cve": obj.get("info", {}).get("classification", {}).get("cve-id", []),
                        "type": obj.get("type", ""),
                    })
                except json.JSONDecodeError:
                    pass

        # Nmap vuln scan
        rc, stdout, stderr = run_cmd(
            f"secator x nmap {target} -sV --script vuln -json",
            timeout=300,
        )
        if rc == 0 and stdout:
            save_evidence(stdout, "vulns/nmap-vuln.json", evidence_dir)

    log(f"Vulnerability scan found {len(results['vulnerabilities'])} findings")
    return results


def main():
    parser = argparse.ArgumentParser(description="VAPT Automated Reconnaissance")
    parser.add_argument("--target", required=True, help="Target (domain, IP, CIDR)")
    parser.add_argument("--type", choices=["blackbox", "greybox", "whitebox"],
                        default="blackbox", help="Assessment type")
    parser.add_argument("--scope", default="webapp+network",
                        help="Scope: webapp, network, webapp+network")
    parser.add_argument("--output", default="/tmp/vapt", help="Output directory")
    parser.add_argument("--user", help="Username for authenticated scans")
    parser.add_argument("--password", help="Password for authenticated scans")
    parser.add_argument("--skip-passive", action="store_true", help="Skip passive recon")
    parser.add_argument("--skip-network", action="store_true", help="Skip network recon")

    args = parser.parse_args()

    # Setup directories
    output_dir = os.path.abspath(args.output)
    evidence_dir = os.path.join(output_dir, "evidence")
    os.makedirs(evidence_dir, exist_ok=True)

    # Initialize results
    all_results = {
        "meta": {
            "target": args.target,
            "type": args.type,
            "scope": args.scope,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        },
        "passive_recon": {},
        "active_recon": {},
        "network_recon": {},
        "vuln_scan": {},
    }

    log(f"Starting VAPT Recon: target={args.target}, type={args.type}, scope={args.scope}")

    # Check available tools
    tools = {}
    for tool in ["secator", "nxc", "nmap", "nuclei", "httpx"]:
        tools[tool] = check_tool(tool)
        log(f"Tool {tool}: {'✓' if tools[tool] else '✗'}")

    # Phase 1a: Passive Recon
    if not args.skip_passive and "webapp" in args.scope:
        all_results["passive_recon"] = phase_passive_recon(
            args.target, output_dir, evidence_dir
        )

    # Phase 1b: Active Recon
    if "webapp" in args.scope:
        subdomains = all_results["passive_recon"].get("subdomains", [])
        all_results["active_recon"] = phase_active_recon(
            args.target, subdomains, output_dir, evidence_dir
        )

    # Phase 2: Network Recon
    if not args.skip_network and "network" in args.scope:
        creds = (args.user, args.password) if args.user and args.password else None
        all_results["network_recon"] = phase_network_recon(
            args.target, output_dir, evidence_dir, creds=creds
        )

    # Phase 3: Vulnerability Scanning
    all_results["vuln_scan"] = phase_vuln_scan(
        args.target, output_dir, evidence_dir
    )

    # Save consolidated results
    results_file = os.path.join(output_dir, "recon-results.json")
    with open(results_file, "w") as f:
        json.dump(all_results, f, indent=2, default=str)

    # Summary
    log("=" * 60)
    log("RECONNAISSANCE SUMMARY")
    log("=" * 60)
    log(f"Subdomains: {len(all_results['passive_recon'].get('subdomains', []))}")
    log(f"Alive hosts: {len(all_results['active_recon'].get('alive_hosts', []))}")
    log(f"SMB hosts: {len(all_results['network_recon'].get('smb_hosts', []))}")
    log(f"Vulnerabilities: {len(all_results['vuln_scan'].get('vulnerabilities', []))}")
    log(f"Results saved: {results_file}")
    log(f"Evidence dir: {evidence_dir}")

    return all_results


if __name__ == "__main__":
    main()
