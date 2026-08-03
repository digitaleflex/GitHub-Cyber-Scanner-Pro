import json
import logging
import os
import re
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from src import database
import src.nlp_processor as nlp_processor

# Reconfigurer la sortie standard en UTF-8 sur Windows pour supporter l'affichage d'emojis
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Configurer le framework standard logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Charger les variables d'environnement
load_dotenv()

# --- CONFIGURATION ---
QUERIES = [
    # --- Fondamentaux ---
    '"cybersecurity" books',
    '"cybersecurity" awesome',
    '"hacking" books',
    '"hacking" awesome',
    '"infosec" resources',
    # --- Red Team / Offensif ---
    '"red team" tools',
    '"pentest" awesome',
    '"pentest" list',
    '"exploit-development"',
    '"c2-framework"',
    '"command-and-control" github',
    '"phishing-framework"',
    '"social-engineering" tools',
    # --- Blue Team / Défensif ---
    '"blue team" tools',
    '"dfir" tools',
    '"incident-response" playbook',
    '"soc" automation',
    '"siem" rules',
    '"edr" evasion',
    # --- Cloud & Container Security ---
    '"cloud-security" tools',
    '"kubernetes-security"',
    '"docker-security"',
    '"aws-security" tools',
    '"gcp-security"',
    '"azure-security"',
    '"serverless-security"',
    '"kubesec"',
    # --- CTF & Bug Bounty ---
    '"ctf-writeups"',
    '"bugbounty-methodology"',
    '"walkthrough" cybersecurity',
    '"poc-exploits" cybersecurity',
    '"bugbounty-tools"',
    # --- Hardening & Conformité ---
    '"hardening-guide" cybersecurity',
    '"security-checklist"',
    '"cis-benchmarks"',
    '"active-directory-hardening"',
    '"linux-hardening"',
    '"windows-hardening"',
    '"compliance" asvs',
    '"nist-framework"',
    # --- Rapports & Livrables ---
    '"pentest-report-template"',
    '"audit-template" cybersecurity',
    '"security-policy-samples"',
    '"risk-assessment" template',
    # --- Certifications & Formation ---
    '"cybersecurity-interview-questions"',
    '"oscp-notes"',
    '"cissp-study-guide"',
    '"cisa-study"',
    '"security-training" labs',
    '"capture-the-flag" platform',
    # --- Threat Intelligence ---
    '"yara-rules" malware',
    '"sigma-rules" threat',
    '"threat-intel" list',
    '"ioc-lists" ip',
    '"osint" framework',
    '"malware-analysis" sandbox',
    '"ransomware" decryptor',
    # --- DevSecOps & Supply Chain ---
    '"devsecops" tools',
    '"sbom" generator',
    '"dependency-check"',
    '"secret-scanning"',
    '"software-supply-chain" security',
    # --- Mobile & IoT Security ---
    '"mobile-security" framework',
    '"android-security"',
    '"ios-security"',
    '"iot-security" framework',
    '"firmware-analysis"',
    # --- Cryptographie & Auth ---
    '"cryptography" library',
    '"zero-trust" implementation',
    '"identity-management"',
    '"oauth2" security',
    '"jwt" security',
    # --- Malware Public (Source & Samples) ---
    '"malware-source" python',
    '"malware-source" go',
    '"malware-source" cpp',
    '"ransomware" source',
    '"ransomware-source"',
    '"stealer" source',
    '"remote-access-trojan"',
    '"rat" source',
    '"botnet" source',
    '"keylogger" source',
    '"loader" malware',
    '"crypter" source',
    '"process-injection"',
    '"rootkit" source',
    '"bootkit"',
    '"bypass-uac"',
    '"credential-dumper"',
    '"ddos" bot source',
    '"cryptominer" source',
    '"dropper" source',
    '"malware" sample collection',
    '"spreader" worm',
    '"reverse-shell" source',
    '"web-shell" source',
    '"webshell" source',
    '"form-grabber"',
    '"rdp-bruteforce"',
    '"bruteforce" rdp',
    '"adversary-in-the-middle"',
    '"evil-twin"',
    '"dns-tunnel" source',
    '"icmp-tunnel" source',
    '"lsass-dump"',
    '"mimikatz" source',
    '"sharphound" source',
    '"payload-generator"',
    '"macro-malware"',
    '"vba-macro" source',
    '"office-exploit" source',
    '"pdf-exploit" source',
    '"browser-exploit"',
    '"usb-rubber-ducky" payload',
    '"bad-usb" source',
    '"fodcha" source',
    '"mirai" source',
    '"botnet" malware source',
    '"infostealer" source',
    '"clipper" malware',
    '"banking-trojan" source',
    '"worm-source"',
    '"plugx" source',
    '"njrat" source',
    '"quasar" rat source',
    '"asyncrat" source',
    '"darkcomet" source',
    '"nanocore" rat source',
    '"cobalt-strike" source',
    '"metasploit" payload',
    '"sliver" c2 source',
    '"havoc" c2 source',
    '"payload" injection',
    '"dll-injection" source',
    '"reflective-dll" source',
    '"process-hollowing" source',
    '"shinject" source',
    '"srdi" source',
    '"nt-create-thread"',
    '"direct-syscall" source',
    '"syscall" inject',
    '"etw-bypass"',
    '"amsi-bypass"',
    '"wlmp-bypass"',
    '"callstack-spoof"',
    '"sleep-obfuscation"',
    '"stack-strings"',
    '"shellcode-loader"',
    '"loader-dropper" source',
    '"pe-injector"',
    '"memory-execution"',
    '"malware-devkit"',
    '"exploit-kit" source',
    '"c2-panel" source',
    '"discord" stealer',
    '"telegram" stealer',
    '"bypass-windows-defender"',
    '"windows-defender-bypass"',
    '"evasion-technique"',
    '"sandbox-evasion"',
    '"vm-detection"',
    '"anti-debug" source',
    '"anti-disassemble"',
    '"obfuscator" malware',
    '"packer" source',
    '"protector" malware',
]

DOMAIN = os.getenv("DOMAIN", "localhost")

# Variables de chemin
BASE_DIR = Path(__file__).parent.parent
FRONTEND_DIR = BASE_DIR / "frontend" / "dist"
REPORTS_DIR = BASE_DIR / "reports"

DATA_DIR = os.getenv("DATA_DIR", "data")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

EXCEL_FILE = os.path.join(DATA_DIR, "cyber_security_catalogues.xlsx")
JSON_FILE = os.path.join(DATA_DIR, "cyber_security_catalogues.json")
SCAN_INTERVAL_SECONDS = int(os.getenv("SCAN_INTERVAL_SECONDS", 1800))
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Variables d'état
scanner_status = "Prêt / En sommeil"
scanner_lock = threading.Lock()
scan_in_progress = False

bulk_lock = threading.Lock()
bulk_in_progress = False

harvest_in_progress = False

cve_in_progress = False

# Initialiser l'application FastAPI
app = FastAPI(title="GitHub Cyber Scanner Semantic API")

# Activer CORS pour faciliter le développement local ou les intégrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
