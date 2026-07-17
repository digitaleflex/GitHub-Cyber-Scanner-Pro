import json
import logging
import os
import time

from src import database
from src import github_client

STATUS_FILE = os.getenv("DATA_DIR", "data") + "/bulk_status.json"


def _write_status(status):
    try:
        os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)
        with open(STATUS_FILE, "w") as f:
            json.dump(status, f)
    except Exception:
        pass


def get_bulk_status():
    try:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {"running": False, "new": 0, "seen": 0, "last_topic": None, "error": None}

BULK_TOPICS = [
    "security", "cybersecurity", "pentest", "penetration-testing", "red-team",
    "blue-team", "malware", "exploit", "vulnerability", "cve", "infosec",
    "reverse-engineering", "forensics", "encryption", "cryptography", "firewall",
    "ids", "ips", "siem", "soar", "threat-intelligence", "osint", "recon",
    "fuzzing", "payload", "ransomware", "botnet", "phishing", "scanner",
    "vulnerability-scanner", "owasp", "devsecops", "hardening", "incident-response",
    "cloud-security", "container-security", "kubernetes-security", "api-security",
    "web-security", "network-security", "endpoint-security", "mobile-security",
    "iot-security", "zero-trust", "sast", "dast", "secrets-detection", "sbom",
    "c2", "rat", "keylogger", "rootkit", "trojan", "worm", "backdoor", "implant",
    "lateral-movement", "privilege-escalation", "active-directory", "kerberos",
    "windows-exploit", "linux-exploit", "buffer-overflow", "rce", "sqli", "xss",
    "auth-bypass", "token", "credential", "brute-force", "ddos", "proxy",
    "vpn", "tor", "anonymity", "steganography", "honeypot", "sandbox",
    "yara", "sigma", "snort", "suricata", "wireshark", "pcap", "packet",
    "powershell", "bash", "python", "go", "rust", "c", "cpp", "assembly",
    "exploit-development", "shellcode", "injection", "hooking", "debugger",
    "disassembler", "decompiler", "obfuscation", "packer", "cracker", "cracking",
    "waf", "bypass", "evasion", "persistence", "exfiltration", "c2-framework",
    "phishing-kit", "carding", "skimmer", "clipper", "stealer", "spyware",
    "adware", "cryptominer", "loader", "dropper", "crypter", "binder",
]

STAR_BUCKETS = [
    (0, 5), (5, 10), (10, 25), (25, 50), (50, 100), (100, 250),
    (250, 500), (500, 1000), (1000, 2500), (2500, 5000), (5000, 10000),
    (10000, 50000), (50000, 1000000),
]


def _search_repos(query, per_page=100, page=1, sort_by="stars"):
    url = "https://api.github.com/search/repositories"
    params = {"q": query, "sort": sort_by, "order": "desc", "per_page": per_page, "page": page}
    data, rate_hit = github_client.get_json(url, params=params)
    if rate_hit:
        return [], True
    return data.get("items", []), False


def bulk_seed(topics=None, buckets=None, max_pages_per_bucket=10):
    """Scan massif multi-topics avec buckets de popularité pour dépasser la limite 1000 résultats."""
    topics = topics or BULK_TOPICS
    buckets = buckets or STAR_BUCKETS
    total_new = 0
    total_seen = 0
    interrupted = False
    error = None

    _write_status({"running": True, "new": 0, "seen": 0, "last_topic": None, "error": None})

    try:
        for topic in topics:
            for lo, hi in buckets:
                if interrupted:
                    break
                star_filter = f"stars:{lo}..{hi}" if hi < 1000000 else f"stars:>{lo}"
                query = f"topic:{topic} {star_filter}"
                for page in range(1, max_pages_per_bucket + 1):
                    items, rate_hit = _search_repos(query, page=page)
                    if rate_hit:
                        interrupted = True
                        break
                    if not items:
                        break
                    total_seen += len(items)
                    new = database.save_repositories(items)
                    total_new += new
                    _write_status({"running": True, "new": total_new, "seen": total_seen,
                                   "last_topic": query, "error": None})
                    logging.info(f"🌱 [{topic} {star_filter}] p{page}: +{new} nouveaux ({total_new} cumul)")
                    time.sleep(2)
                if interrupted:
                    break
            if interrupted:
                break
    except Exception as e:
        error = str(e)
        logging.error(f"❌ Erreur bulk-seed: {e}")

    _write_status({"running": False, "new": total_new, "seen": total_seen,
                   "last_topic": None, "error": error})
    logging.info(f"✅ Bulk-seed terminé: {total_new} nouveaux repos sur {total_seen} vus")
    return {"new": total_new, "seen": total_seen, "error": error}
