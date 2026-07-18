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
import src.sast_scanner as sast_scanner
import src.threat_intel as threat_intel
import src.rss_feed as rss_feed

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


def fetch_github_data(query, sort_by="stars"):
    """Interroge l'API GitHub avec gestion d'ETag, de Rate Limit et de retry."""
    url = "https://api.github.com/search/repositories"
    params = {"q": query, "sort": sort_by, "order": "desc", "per_page": 50}
    headers = {"Accept": "application/vnd.github.v3+json"}

    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    # Récupérer l'ETag du cache PostgreSQL (clé de cache enrichie avec le critère de tri)
    cache_key = f"{query}_{sort_by}"
    etag, last_modified = database.get_etag_from_cache(cache_key)
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified

    max_retries = 5
    backoff_delay = 2

    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=15)
            rate_reset = response.headers.get("X-RateLimit-Reset")

            if response.status_code == 200:
                new_etag = response.headers.get("ETag")
                new_last_modified = response.headers.get("Last-Modified")
                if new_etag or new_last_modified:
                    database.save_etag_to_cache(cache_key, new_etag, new_last_modified)

                return response.json().get("items", []), False

            elif response.status_code == 304:
                logging.info(f"🔄 [Cache 304] Aucun changement détecté pour la recherche : {query} ({sort_by})")
                return [], False

            elif response.status_code == 403:
                retry_after = response.headers.get("Retry-After")
                if retry_after:
                    wait_time = float(retry_after)
                    logging.warning(f"⚠️ Limite secondaire (Abuse) détectée. Pause de {wait_time}s...")
                    time.sleep(wait_time + 2)
                    continue

                if rate_reset:
                    try:
                        reset_time = float(rate_reset)
                        wait_time = max(1.0, reset_time - time.time()) + 5.0
                        logging.warning(
                            f"⚠️ Limite d'appels API atteinte pour la requête '{query}' ({sort_by}). "
                            f"Mise en pause obligatoire pendant {int(wait_time)} secondes..."
                        )
                        time.sleep(wait_time)
                        continue
                    except ValueError:
                        pass

                logging.warning("⚠️ Limite d'appels API atteinte. Prochain cycle.")
                return [], True

            elif response.status_code >= 500:
                logging.error(
                    f"❌ Erreur serveur GitHub ({response.status_code}). "
                    f"Tentative dans {backoff_delay}s (essai {attempt + 1}/{max_retries})..."
                )
                time.sleep(backoff_delay)
                backoff_delay *= 2
                continue
            else:
                logging.error(f"❌ Erreur API GitHub : {response.status_code} - {response.text}")
                return [], False

        except requests.exceptions.RequestException as e:
            logging.error(
                f"🔌 Erreur réseau ou de connexion ({e}). "
                f"Tentative dans {backoff_delay}s (essai {attempt + 1}/{max_retries})..."
            )
            time.sleep(backoff_delay)
            backoff_delay *= 2

    logging.error(f"❌ Échec de la récupération après {max_retries} tentatives pour : {query} ({sort_by})")
    return [], False


def fetch_and_parse_readme(repo_id, full_name, repo_description=""):
    """Télécharge le README, extrait et nettoie les lemmes par NLP Spacy, et insère les livres dans Postgres."""
    logging.info(f"📖 Analyse du README pour {full_name}...")
    readme_api_url = f"https://api.github.com/repos/{full_name}/readme"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    try:
        res = requests.get(readme_api_url, headers=headers, timeout=15)

        if res.status_code == 403:
            rate_reset = res.headers.get("X-RateLimit-Reset")
            retry_after = res.headers.get("Retry-After")
            if retry_after:
                wait_time = float(retry_after)
                logging.warning(f"⚠️ Limite secondaire Abuse détectée pour le README. Pause de {wait_time}s...")
                time.sleep(wait_time + 2)
                return False
            elif rate_reset:
                try:
                    reset_time = float(rate_reset)
                    wait_time = max(1.0, reset_time - time.time()) + 5.0
                    logging.warning(f"⚠️ Limite d'appels API atteinte pour le README. Pause de {int(wait_time)}s...")
                    time.sleep(wait_time)
                    return False
                except ValueError:
                    pass

        if res.status_code != 200:
            if res.status_code == 404:
                database.mark_repo_as_parsed(repo_id)
                logging.info(f"ℹ️ Aucun README trouvé pour {full_name} (marqué traité).")
            return False

        download_url = res.json().get("download_url")
        if not download_url:
            return False

        readme_res = requests.get(download_url, timeout=15)
        if readme_res.status_code != 200:
            return False

        readme_content = readme_res.text

        # Extraire tous les liens Markdown [Titre](URL)
        links = re.findall(r'\[([^\]\n]+)\]\((https?://[^\)\s]+)\)', readme_content)

        extracted_count = 0
        resource_keywords = [
            "book", "guide", "manual", "handbook", "tutorial", "course", "pdf", "epub", "mobi",
            "livre", "manuel", "cours", "reference", "cheat", "lectures", "bibliotheque", "library",
            "writeup", "write-up", "walkthrough", "hardening", "checklist", "benchmark", "template",
            "report", "interview", "questions", "yara", "sigma", "threat-intel", "threat intel", "ioc"
        ]
        book_extensions = [".pdf", ".epub", ".mobi", ".docx"]
        book_domains = ["drive.google.com", "dropbox.com", "mega.nz", "mediafire.com", "books.google.com", "leanpub.com", "gitbook.io"]

        for title, url in links:
            title = title.strip()
            url = url.strip()

            title_lower = title.lower()
            url_lower = url.lower()

            is_resource = False

            if any(url_lower.endswith(ext) or f"{ext}?" in url_lower or f"{ext}#" in url_lower for ext in book_extensions):
                is_resource = True
            elif any(domain in url_lower for domain in book_domains):
                is_resource = True
            elif any(k in title_lower or k in url_lower for k in resource_keywords):
                ignore_keywords = ["twitter.com", "linkedin.com", "facebook.com", "github.com/sponsors", "patreon.com", "paypal.me", "github.com/users/"]
                if not any(ignore in url_lower for ignore in ignore_keywords):
                    is_resource = True

            if is_resource and len(title) > 2 and len(url) < 1000:
                # 1. Traitement NLP : Nettoyage et lemmatisation avec Spacy
                # Concaténer le titre et la description du dépôt pour donner du contexte NLP
                context_text = f"{title} {repo_description}"
                lemmas = nlp_processor.clean_and_lemmatize(context_text)

                # 2. Catégorisation sémantique
                category = nlp_processor.categorize_by_semantic_ontology(title, repo_description, lemmas)

                # 3. Détection du type de ressource (IA)
                type_ressource = nlp_processor.detect_resource_type(title, repo_description, url, category)

                # 4. Sauvegarde dans Postgres avec génération du TSVector
                saved = database.save_book(repo_id, title, url, category, lemmas, type_ressource)
                if saved:
                    extracted_count += 1

        # Marquer le dépôt comme traité
        database.mark_repo_as_parsed(repo_id)

        if extracted_count > 0:
            logging.info(f"✨ Extrait sémantiquement {extracted_count} livre(s)/ressource(s) depuis {full_name}")
        return True
    except Exception as e:
        logging.error(f"❌ Erreur lors du parsing du README pour {full_name} : {e}")
        return False


def parse_unprocessed_readmes():
    """Sélectionne tous les dépôts non traités et traite leurs README."""
    unprocessed = database.get_unprocessed_repositories()
    if not unprocessed:
        return

    logging.info(f"📚 Extraction des README en cours pour {len(unprocessed)} dépôt(s)...")
    for repo_id, full_name in unprocessed:
        # Récupérer la description du dépôt pour le contexte sémantique
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT description FROM repositories WHERE id = %s", (repo_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        description = row[0] if row else ""

        fetch_and_parse_readme(repo_id, full_name, description)
        time.sleep(1.5)


def verify_book_link(url):
    """Vérifie si un lien de livre est toujours valide (HEAD ou GET partiel retournant HTTP < 400)."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    try:
        response = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
        if response.status_code in [404, 410]:
            return False
        elif response.status_code >= 400:
            response = requests.get(url, headers=headers, timeout=10, stream=True, allow_redirects=True)
            if response.status_code in [404, 410]:
                return False
        return response.status_code < 400
    except Exception:
        return None


def run_link_validator_daemon():
    """Démon de validation périodique de la validité des liens dans Postgres."""
    logging.info("🚀 Démarrage du démon de validation des liens (Link Checker)...")
    time.sleep(30)

    while True:
        try:
            books_to_check = database.get_books_to_verify(50)

            if not books_to_check:
                time.sleep(3600)
                continue

            logging.info(f"🔍 [Link Checker] Vérification de la disponibilité de {len(books_to_check)} liens...")

            for book_id, url in books_to_check:
                status = verify_book_link(url)

                if status is False:
                    logging.warning(f"❌ Lien mort détecté et désactivé : {url}")
                    database.update_book_status(book_id, is_dead=1)
                else:
                    database.update_book_status(book_id, is_dead=0)
                time.sleep(3)

            # Mettre à jour les exports Excel et JSON
            export_to_excel()
            export_to_json()

        except Exception as e:
            logging.error(f"❌ Erreur dans le démon de validation des liens : {e}")
            time.sleep(60)


def export_to_excel():
    """Exporte les dépôts et les livres de Postgres vers un fichier Excel multi-onglets."""
    logging.info("📊 Exportation de la base de données PostgreSQL vers Excel...")
    try:
        conn = database.get_db_connection()

        # 1. Lire les dépôts avec score_qualite et verdict de sécurité
        df_repos = pd.read_sql_query(
            "SELECT full_name, stars, description, html_url, language, updated_at, score_qualite, security_verdict FROM repositories",
            conn
        )

        # 2. Lire les livres avec score_qualite et type_ressource
        df_books = pd.read_sql_query(
            """
            SELECT b.title, b.category, b.type_ressource, r.full_name AS repo_name, 
                   CASE WHEN b.is_dead = 1 THEN 'Hors ligne' 
                        WHEN b.last_checked IS NULL THEN 'Non vérifié'
                        ELSE 'Disponible' END AS status,
                   b.url, b.score_qualite, r.security_verdict 
            FROM books b 
            LEFT JOIN repositories r ON b.repo_id = r.id
            """,
            conn
        )
        conn.close()

        # Formater les dépôts
        if not df_repos.empty:
            df_repos.columns = [
                "Nom du Dépôt", "Étoiles (Stars)", "Description", "Lien GitHub", "Langue Principale", "Dernière Mise à Jour", "Score Qualité (IA)", "Verdict Sécurité"
            ]
            # Trier d'abord par Score Qualité (IA) puis par Étoiles
            df_repos = df_repos.sort_values(by=["Score Qualité (IA)", "Étoiles (Stars)"], ascending=[False, False])
            for col in df_repos.select_dtypes(include=['object']).columns:
                df_repos[col] = df_repos[col].astype(str).str.slice(0, 32000)

        # Formater les livres
        if not df_books.empty:
            df_books.columns = [
                "Titre de la Ressource / Livre", "Catégorie", "Type de Ressource", "Dépôt Source", "Disponibilité", "Lien de Téléchargement", "Score Qualité (IA)", "Sécurité Source"
            ]
            # Trier d'abord par Score Qualité (IA) puis par Type, Catégorie et Titre
            df_books = df_books.sort_values(by=["Score Qualité (IA)", "Type de Ressource", "Catégorie", "Titre de la Ressource / Livre"], ascending=[False, True, True, True])
            for col in df_books.select_dtypes(include=['object']).columns:
                df_books[col] = df_books[col].astype(str).str.slice(0, 32000)

        # Sauvegarder Excel
        with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
            if not df_repos.empty:
                df_repos.to_excel(writer, sheet_name="Dépôts GitHub", index=False)
            if not df_books.empty:
                df_books.to_excel(writer, sheet_name="Livres & Ressources", index=False)

        logging.info(f"💾 Fichier Excel mis à jour avec succès : [{EXCEL_FILE}]")
    except Exception as e:
        logging.error(f"❌ Erreur lors de la génération du fichier Excel : {e}")


def export_to_json():
    """Exporte les dépôts et leurs livres associés de Postgres vers un fichier JSON structuré."""
    logging.info("📂 Exportation de la base de données PostgreSQL vers JSON...")
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()

        # Récupérer tous les dépôts avec score_qualite et verdict de sécurité
        cursor.execute("SELECT id, full_name, stars, description, html_url, language, updated_at, score_qualite, security_verdict FROM repositories ORDER BY score_qualite DESC, stars DESC")
        repos_rows = cursor.fetchall()

        data_dict = {}
        for r in repos_rows:
            repo_id = r[0]
            data_dict[repo_id] = {
                "Nom du Dépôt": r[1],
                "Étoiles (Stars)": r[2],
                "Description": r[3],
                "Lien GitHub": r[4],
                "Langue Principale": r[5],
                "Dernière Mise à Jour": r[6],
                "Score Qualité (IA)": r[7],
                "Verdict Sécurité": r[8],
                "Ressources": []
            }

        # Récupérer tous les livres avec score_qualite et type_ressource
        cursor.execute(
            """
            SELECT repo_id, title, category, type_ressource, 
                   CASE WHEN is_dead = 1 THEN 'Hors ligne'
                        WHEN last_checked IS NULL THEN 'Non vérifié'
                        ELSE 'Disponible' END AS status,
                   url, score_qualite 
            FROM books
            ORDER BY score_qualite DESC, title ASC
            """
        )
        books_rows = cursor.fetchall()
        conn.close()

        for b in books_rows:
            repo_id = b[0]
            if repo_id in data_dict:
                data_dict[repo_id]["Ressources"].append({
                    "Titre de la Ressource / Livre": b[1],
                    "Catégorie": b[2],
                    "Type de Ressource": b[3],
                    "Disponibilité": b[4],
                    "Lien de Téléchargement": b[5],
                    "Score Qualité (IA)": b[6]
                })

        # Pour trier le dictionnaire par score_qualite des dépôts
        sorted_data = dict(sorted(data_dict.items(), key=lambda item: item[1]["Score Qualité (IA)"], reverse=True))

        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(sorted_data, f, indent=4, ensure_ascii=False)

        logging.info(f"💾 Fichier JSON mis à jour avec succès : [{JSON_FILE}]")
    except Exception as e:
        logging.error(f"❌ Erreur lors de la génération du fichier JSON : {e}")


def export_reports():
    """Génère le rapport Markdown et le dashboard HTML du scan depuis la base."""
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM repositories")
        total_repos = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(stars), 0) FROM repositories")
        total_stars = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT language) FROM repositories WHERE language IS NOT NULL AND language != 'Non specifiee'")
        total_langs = cursor.fetchone()[0]

        cursor.execute("""
            SELECT full_name, stars, description, html_url, language, updated_at, security_verdict
            FROM repositories ORDER BY stars DESC LIMIT 10
        """)
        top_repos = cursor.fetchall()

        cursor.execute("""
            SELECT language, COUNT(*) FROM repositories
            WHERE language IS NOT NULL AND language != 'Non specifiee'
            GROUP BY language ORDER BY COUNT(*) DESC LIMIT 10
        """)
        lang_dist = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) FROM repositories WHERE security_verdict = 'Critique'")
        critique_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM repositories WHERE security_verdict = 'Suspect'")
        suspect_count = cursor.fetchone()[0]

        cursor.execute("SELECT full_name, security_verdict FROM repositories WHERE security_verdict IN ('Critique', 'Suspect') ORDER BY security_scan_date DESC NULLS LAST LIMIT 10")
        flagged_repos = cursor.fetchall()

        cursor.execute("SELECT full_name, stars FROM repositories ORDER BY stars DESC LIMIT 5")
        top5 = cursor.fetchall()

        cursor.close()
        conn.close()

        now = datetime.now()
        date_str = now.strftime("%d/%m/%Y %H:%M")
        file_date = now.strftime("%Y%m%d_%H%M%S")
        reports_dir = REPORTS_DIR
        reports_dir.mkdir(parents=True, exist_ok=True)

        verdict_badge = {"Critique": "🔴", "Suspect": "🟡", "Sain": "🟢"}

        md_lines = [
            "# CyberScan — Rapport de Scan",
            f"**{date_str}**\n",
            "## Résumé",
            f"- Total dépôts : **{total_repos:,}**",
            f"- Total étoiles : **{total_stars:,}**",
            f"- Langages distincts : **{total_langs}**",
            f"- Dépôts critique : **{critique_count}**",
            f"- Dépôts suspect : **{suspect_count}**",
            "",
            "## Top 5 par étoiles",
        ]
        for i, (name, stars) in enumerate(top5, 1):
            md_lines.append(f"{i}. ★ **{stars:,}** — {name}")

        md_lines.extend(["", "## Top 10", ""])
        for i, (name, stars, desc, url, lang, updated, verdict) in enumerate(top_repos, 1):
            badge = verdict_badge.get(verdict, "⚪")
            md_lines.append(f"### {i}. [{name}]({url})")
            md_lines.append(f"★ {stars:,} | {lang or '?'} | {updated[:10] if updated else 'N/A'} | {badge} {verdict or 'Non analysé'}")
            md_lines.append("")
            if desc:
                md_lines.append(f"> {desc[:200]}")
                md_lines.append("")

        if flagged_repos:
            md_lines.extend(["## Alertes Sécurité", ""])
            for name, verdict in flagged_repos:
                badge = verdict_badge.get(verdict, "⚪")
                md_lines.append(f"- {badge} **{verdict}** — {name}")
            md_lines.append("")

        md_lines.extend(["## Distribution par Langage", ""])
        for lang, count in lang_dist:
            md_lines.append(f"- **{lang}** : {count}")
        md_lines.append("")

        md_lines.append("---")
        md_lines.append(f"*Généré automatiquement par CyberScan Pro — {date_str}*")

        md_report = "\n".join(md_lines)
        md_filename = reports_dir / f"rapport_{file_date}.md"
        md_filename.write_text(md_report, encoding="utf-8")
        logging.info(f"📄 Rapport Markdown généré : [{md_filename}]")

        lang_rows = ""
        if lang_dist:
            max_lang = lang_dist[0][1]
            colors = ["#6366f1","#10b981","#f59e0b","#ef4444","#06b6d4","#8b5cf6","#ec4899","#14b8a6","#f97316","#84cc16"]
            for i, (lang, count) in enumerate(lang_dist):
                pct = max(5, count / max_lang * 100)
                lang_rows += f'<div class="lang-bar"><span style="width:80px;font-size:0.85rem;color:#94a3b8;">{lang}</span><div class="bar-wrap"><div class="bar-fill" style="width:{pct}%;background:{colors[i % 10]};"></div></div><span class="count">{count}</span></div>'

        flag_rows = ""
        if flagged_repos:
            for name, verdict in flagged_repos:
                color = "#ef4444" if verdict == "Critique" else "#eab308"
                flag_rows += f'<tr><td style="color:{color};font-weight:600;">{verdict}</td><td>{name}</td></tr>'

        top_rows = ""
        for i, (name, stars, _desc, url, lang, updated, verdict) in enumerate(top_repos, 1):
            color = {"Critique": "#ef4444", "Suspect": "#eab308", "Sain": "#22c55e"}.get(verdict, "#64748b")
            badge = verdict or "N/A"
            top_rows += f"""<tr>
                <td>{i}</td>
                <td><a href="{url}" target="_blank" style="color:#818cf8;text-decoration:none;">{name}</a></td>
                <td style="color:#f59e0b;">★{stars:,}</td>
                <td><span style="display:inline-block;padding:2px 8px;border-radius:4px;font-size:0.75rem;background:rgba(99,102,241,0.15);color:#a5b4fc;">{lang or '?'}</span></td>
                <td style="color:{color};font-weight:600;">{badge}</td>
                <td style="color:#94a3b8;font-size:0.8rem;">{(updated or '')[:10]}</td>
            </tr>"""

        html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CyberScan — Rapport {file_date}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'Inter',sans-serif; background:#0a0e17; color:#e2e8f0; min-height:100vh; }}
.wrapper {{ max-width:1200px; margin:0 auto; padding:2rem; }}
h1 {{ font-size:1.75rem; font-weight:800; background:linear-gradient(135deg,#a5b4fc,#6366f1,#8b5cf6); -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin-bottom:0.5rem; }}
.subtitle {{ color:#64748b; font-size:0.9rem; margin-bottom:2rem; }}
.stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:1rem; margin-bottom:2rem; }}
.stat-card {{ background:rgba(17,25,45,0.75); border:1px solid rgba(255,255,255,0.06); border-radius:12px; padding:1.25rem; backdrop-filter:blur(12px); }}
.stat-card .num {{ font-size:1.5rem; font-weight:700; color:#e2e8f0; }}
.stat-card .label {{ font-size:0.8rem; color:#64748b; margin-top:4px; }}
.card {{ background:rgba(17,25,45,0.75); border:1px solid rgba(255,255,255,0.06); border-radius:12px; padding:1.5rem; margin-bottom:1.5rem; }}
.card h2 {{ font-size:1.1rem; font-weight:600; margin-bottom:1rem; color:#94a3b8; }}
table {{ width:100%; border-collapse:collapse; font-size:0.85rem; }}
th {{ text-align:left; padding:0.75rem 0.5rem; color:#64748b; font-weight:500; border-bottom:1px solid rgba(255,255,255,0.06); }}
td {{ padding:0.6rem 0.5rem; border-bottom:1px solid rgba(255,255,255,0.03); }}
tr:hover td {{ background:rgba(99,102,241,0.04); }}
a:hover {{ text-decoration:underline !important; }}
.lang-bar {{ display:flex; align-items:center; gap:0.5rem; padding:0.3rem 0; }}
.lang-bar .bar-wrap {{ flex:1; height:6px; background:rgba(255,255,255,0.06); border-radius:3px; overflow:hidden; }}
.lang-bar .bar-fill {{ height:100%; border-radius:3px; }}
.lang-bar .count {{ font-size:0.8rem; color:#64748b; min-width:2rem; text-align:right; }}
.footer {{ text-align:center; padding:2rem 0; color:#475569; font-size:0.8rem; }}
</style>
</head>
<body>
<div class="wrapper">
<h1>CyberScan — Rapport de Scan</h1>
<p class="subtitle">{date_str}</p>
<div class="stats">
<div class="stat-card"><div class="num">{total_repos:,}</div><div class="label">Dépôts</div></div>
<div class="stat-card"><div class="num">{total_stars:,}</div><div class="label">Étoiles</div></div>
<div class="stat-card"><div class="num">{total_langs}</div><div class="label">Langages</div></div>
<div class="stat-card"><div class="num" style="color:#ef4444;">{critique_count}</div><div class="label">Critique</div></div>
<div class="stat-card"><div class="num" style="color:#eab308;">{suspect_count}</div><div class="label">Suspect</div></div>
</div>

<div class="card">
<h2>Top 10</h2>
<table><thead><tr><th>#</th><th>Nom</th><th>Stars</th><th>Langage</th><th>Sécurité</th><th>Mis à jour</th></tr></thead>
<tbody>{top_rows}</tbody></table>
</div>

<div class="card">
<h2>Distribution par Langage</h2>
{lang_rows}
</div>

{'<div class="card"><h2 style="color:#ef4444;">Alertes Sécurité</h2><table><thead><tr><th>Verdict</th><th>Dépôt</th></tr></thead><tbody>' + flag_rows + '</tbody></table></div>' if flag_rows else ''}

<footer class="footer">Généré par CyberScan Pro — {date_str}</footer>
</div>
</body>
</html>"""

        html_filename = reports_dir / f"dashboard_{file_date}.html"
        html_filename.write_text(html, encoding="utf-8")
        logging.info(f"📊 Dashboard HTML généré : [{html_filename}]")

    except Exception as e:
        logging.error(f"❌ Erreur lors de la génération des rapports : {e}")


def migrate_sqlite_to_postgres():
    """Migre de manière unique les données existantes de la base SQLite vers PostgreSQL au premier démarrage."""
    sqlite_db = "data/scanner.db"
    if not os.path.exists(sqlite_db):
        return

    logging.info("📂 Base de données SQLite existante détectée. Lancement de la migration vers PostgreSQL...")
    import sqlite3
    try:
        sqlite_conn = sqlite3.connect(sqlite_db)
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_cursor = sqlite_conn.cursor()

        # 1. Lire tous les dépôts de SQLite
        sqlite_cursor.execute("SELECT id, full_name, stars, description, html_url, language, updated_at, readme_parsed FROM repositories")
        repos = [dict(row) for row in sqlite_cursor.fetchall()]

        # Construire le corpus pour le TF-IDF
        corpus = [r.get("description", "") for r in repos if r.get("description")]
        analyzer = nlp_processor.CyberTextAnalyzer(corpus)

        pg_conn = database.get_db_connection()
        pg_cursor = pg_conn.cursor()

        migrated_repos = 0
        for r in repos:
            # Lancer l'analyse d'IA (Embedding, mots-clés et score de pertinence)
            repo_data = {
                "id": r["id"],
                "full_name": r["full_name"],
                "description": r["description"],
                "stargazers_count": r["stars"],
                "stars": r["stars"],
                "html_url": r["html_url"],
                "language": r["language"],
                "updated_at": r["updated_at"]
            }
            analysis = analyzer.process_repository(repo_data)
            score_qualite = 0
            vector = None
            if analysis:
                score_qualite = analysis["score_qualite"]
                vector = analysis["vecteur_semantique"]

            if not vector:
                vector = None

            sem_cat, _ = nlp_processor.classify_semantic(r["description"], r["full_name"])

            pg_cursor.execute(
                """
                INSERT INTO repositories (id, full_name, stars, description, html_url, language, updated_at, readme_parsed, score_qualite, vecteur_semantique, semantic_category)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE
                SET full_name = EXCLUDED.full_name,
                    stars = EXCLUDED.stars,
                    description = EXCLUDED.description,
                    html_url = EXCLUDED.html_url,
                    language = EXCLUDED.language,
                    updated_at = EXCLUDED.updated_at,
                    readme_parsed = EXCLUDED.readme_parsed,
                    score_qualite = EXCLUDED.score_qualite,
                    vecteur_semantique = EXCLUDED.vecteur_semantique,
                    semantic_category = EXCLUDED.semantic_category
                """,
                (
                    str(r["id"]),
                    r["full_name"],
                    r["stars"],
                    r["description"] if r["description"] else "Aucune description.",
                    r["html_url"],
                    r["language"] if r["language"] else "Non spécifiée",
                    r["updated_at"],
                    r["readme_parsed"],
                    score_qualite,
                    vector,
                    sem_cat
                )
            )
            if pg_cursor.rowcount > 0:
                migrated_repos += 1

        # 2. Migrer les livres de SQLite
        sqlite_cursor.execute("SELECT repo_id, title, url, category, is_dead, last_checked FROM books")
        books = [dict(row) for row in sqlite_cursor.fetchall()]

        migrated_books = 0
        for b in books:
            repo_id = str(b["repo_id"])
            title = b["title"]
            url = b["url"]
            category = b["category"]
            is_dead = b["is_dead"]
            last_checked = b["last_checked"]

            # Rechercher la description du dépôt et ses données de qualité déjà insérées dans Postgres
            pg_cursor.execute("SELECT description, score_qualite, vecteur_semantique FROM repositories WHERE id = %s", (repo_id,))
            desc_row = pg_cursor.fetchone()
            if desc_row:
                description = desc_row[0] if desc_row[0] else ""
                score_qualite = desc_row[1]
                vecteur_semantique = desc_row[2]
            else:
                description = ""
                score_qualite = 0
                vecteur_semantique = None

            # Détecter le type de ressource (IA) pour la migration
            type_ressource = nlp_processor.detect_resource_type(title, description, url, category)

            lemmas = nlp_processor.clean_and_lemmatize(f"{title} {description}")
            lemmas_str = " ".join(lemmas)
            semantic_text = f"{title} {category if category else ''} {type_ressource} {lemmas_str}"

            pg_cursor.execute(
                """
                INSERT INTO books (repo_id, title, url, category, is_dead, last_checked, lemmas_str, score_qualite, vecteur_semantique, type_ressource, tsv_content)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, to_tsvector('simple', %s))
                ON CONFLICT (url) DO UPDATE
                SET title = EXCLUDED.title,
                    category = EXCLUDED.category,
                    is_dead = EXCLUDED.is_dead,
                    last_checked = EXCLUDED.last_checked,
                    lemmas_str = EXCLUDED.lemmas_str,
                    score_qualite = EXCLUDED.score_qualite,
                    vecteur_semantique = EXCLUDED.vecteur_semantique,
                    type_ressource = EXCLUDED.type_ressource,
                    tsv_content = to_tsvector('simple', EXCLUDED.lemmas_str)
                """,
                (repo_id, title, url, category, is_dead, last_checked, lemmas_str, score_qualite, vecteur_semantique, type_ressource, semantic_text)
            )
            if pg_cursor.rowcount > 0:
                migrated_books += 1

        pg_conn.commit()
        pg_cursor.close()
        pg_conn.close()
        sqlite_conn.close()

        # Renommer la base SQLite pour éviter de la réimporter au prochain reboot
        os.rename(sqlite_db, sqlite_db + ".bak")
        logging.info(f"✨ Migration réussie : {migrated_repos} dépôts et {migrated_books} livres importés dans PostgreSQL avec calcul de score et embeddings sémantiques.")
    except Exception as e:
        logging.error(f"❌ Erreur lors de la migration SQLite -> PostgreSQL : {e}")


def _run_keyword_miner():
    """Extrait, score et sauvegarde de nouveaux mots-clés depuis le corpus de repos."""
    import keyword_miner
    from database import get_db_connection
    from psycopg2.extras import RealDictCursor

    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("""
        SELECT description, full_name
        FROM repositories
        WHERE description IS NOT NULL AND description != 'Aucune description.'
        ORDER BY stars DESC
        LIMIT 3000
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    descriptions = [r["description"] for r in rows]
    news = []
    try:
        from database import get_cyber_news
        for n in get_cyber_news(limit=100):
            news.append(f"{n.get('title', '')} {n.get('summary', '')}")
    except Exception:
        pass

    candidates = keyword_miner.mine_keywords(descriptions, news, top_n=200)
    if candidates:
        from database import save_discovered_keywords, auto_approve_keywords, refresh_cyber_terms
        saved = save_discovered_keywords(candidates)
        approved = auto_approve_keywords(min_score=0.75, min_sources=3)
        if saved or approved:
            refresh_cyber_terms()
            logging.info(f"⛏️ Keyword miner: {saved} candidats, {approved} auto-approuvés")


def scan_cycle():
    """Effectue un cycle de scan GitHub hybride (popularité et activité récente)."""
    logging.info("🔄 Début du cycle de scan sur GitHub...")
    new_discoveries_total = 0
    any_success = False

    # Phase 1: scan avec les queries statiques
    for query in QUERIES:
        # 1. Recherche par popularité (stars)
        logging.info(f"🔍 Recherche (Popularité) pour : {query}...")
        raw_items_stars, rate_limit_hit = fetch_github_data(query, sort_by="stars")

        if rate_limit_hit:
            logging.warning("⚠️ Cycle de scan interrompu en raison d'une limite de quota API non résolue.")
            break

        if raw_items_stars:
            any_success = True
            new_discoveries = database.save_repositories(raw_items_stars)
            new_discoveries_total += new_discoveries

        time.sleep(2.5)

        # 2. Recherche par activité récente (updated) pour découvrir les nouveaux dépôts / pépites
        logging.info(f"🔍 Recherche (Nouveautés récentes) pour : {query}...")
        raw_items_updated, rate_limit_hit = fetch_github_data(query, sort_by="updated")

        if rate_limit_hit:
            logging.warning("⚠️ Cycle de scan interrompu en raison d'une limite de quota API non résolue.")
            break

        if raw_items_updated:
            any_success = True
            new_discoveries = database.save_repositories(raw_items_updated)
            new_discoveries_total += new_discoveries

        time.sleep(2.5)

    # Phase 2: générer des queries dynamiques via NLP et scanner les nouveaux mots-clés
    try:
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT description FROM repositories WHERE description IS NOT NULL AND description != ''")
        descriptions = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()

        if descriptions:
            dynamic_queries = nlp_processor.extract_keywords(descriptions, top_n=30)
            if dynamic_queries:
                logging.info(f"🧠 Phase NLP: {len(dynamic_queries)} nouvelles queries dynamiques")
                for query in dynamic_queries:
                    logging.info(f"🔍 (NLP) Recherche (Popularité) pour : {query}...")
                    raw_items, rate_hit = fetch_github_data(query, sort_by="stars")
                    if rate_hit:
                        break
                    if raw_items:
                        any_success = True
                        new = database.save_repositories(raw_items)
                        new_discoveries_total += new
                    time.sleep(2.5)

                    logging.info(f"🔍 (NLP) Recherche (Nouveautés) pour : {query}...")
                    raw_items, rate_hit = fetch_github_data(query, sort_by="updated")
                    if rate_hit:
                        break
                    if raw_items:
                        any_success = True
                        new = database.save_repositories(raw_items)
                        new_discoveries_total += new
                    time.sleep(2.5)
    except Exception as e:
        logging.error(f"❌ Erreur lors de la phase NLP dynamique: {e}")

    # Phase 3: Threat Intelligence — nouveaux mots-clés depuis CISA, CERT-FR, MITRE
    try:
        threat_kw = threat_intel.aggregate_threat_keywords()
        if threat_kw:
            threat_queries = []
            for kw in threat_kw[:20]:
                for template in threat_intel.THREAT_TEMPLATES:
                    threat_queries.append(template.format(kw))
            logging.info(f"🛡️ Phase ThreatIntel: {len(threat_queries)} nouvelles queries")
            for query in threat_queries[:30]:
                raw_items, rate_hit = fetch_github_data(query, sort_by="stars")
                if rate_hit:
                    break
                if raw_items:
                    any_success = True
                    new = database.save_repositories(raw_items)
                    new_discoveries_total += new
                time.sleep(2.5)
    except Exception as e:
        logging.error(f"❌ Erreur lors de la phase ThreatIntel: {e}")

    if any_success:
        if new_discoveries_total > 0:
            logging.info(f"✨ {new_discoveries_total} nouvelle(s) pépite(s) découverte(s) lors de ce cycle !")
        else:
            logging.info("ℹ️ Données existantes synchronisées. Aucun nouveau dépôt.")

        parse_unprocessed_readmes()
        try:
            scanned = sast_scanner.process_unscanned_repos(limit=10)
            if scanned:
                logging.info(f"🔬 Analyse SAST terminee pour {scanned} depot(s)")
        except Exception as e:
            logging.error(f"❌ Erreur lors de l'analyse SAST: {e}")
        try:
            vitality_updated = database.recalculate_vitality_scores()
            if vitality_updated:
                logging.info(f"📊 Scores de vitalite recalculés pour {vitality_updated} depot(s)")
        except Exception as e:
            logging.error(f"❌ Erreur lors du recalcul des scores de vitalite: {e}")
        try:
            sem_backfilled = database.backfill_semantic_categories(batch_size=500)
            if sem_backfilled:
                logging.info(f"🧠 Catégories sémantiques backfillées pour {sem_backfilled} dépôt(s)")
        except Exception as e:
            logging.error(f"❌ Erreur lors du backfill des catégories sémantiques: {e}")
        try:
            _run_keyword_miner()
        except Exception as e:
            logging.error(f"❌ Erreur lors du minage de mots-clés: {e}")
        try:
            import src.miniflux_bridge as miniflux_bridge
            if miniflux_bridge.MINIFLUX_ENABLED and miniflux_bridge.MINIFLUX_TOKEN:
                bridge_res = miniflux_bridge.run_bridge()
                logging.info(f"📰 Pont Miniflux: {bridge_res}")
            else:
                # Fallback : collecteur maison (anti-bot/dead auto-desactive)
                feeds = rss_feed.fetch_all_feeds()
                if feeds:
                    saved = database.save_cyber_news(feeds)
                    logging.info(f"📰 {saved} article(s) RSS enregistré(s) (collecteur maison)")
                health = rss_feed.count_usable_feeds()
                logging.info(f"📊 Flux RSS utilisables: {health['usable']}/{health['total']} (morts/bloqués: {len(health['dead']) + len(health['blocked_antibot'])})")
            # Enrichissement CVE/IOC/ATT&CK (idempotent)
            enriched = database.enrich_unenriched_news(limit=300)
            if enriched:
                logging.info(f"🔍 {enriched} article(s) enrichi(s) en entités cyber")
        except Exception as e:
            logging.error(f"❌ Erreur lors de la récupération des flux RSS: {e}")
        try:
            corr = database.correlate_news_with_repos()
            if corr:
                logging.info(f"🔗 {corr} corrélation(s) news → repos établie(s)")
        except Exception as e:
            logging.error(f"❌ Erreur lors de la corrélation news/repos: {e}")
        try:
            import src.harvest_artifacts as harvest_artifacts
            hres = harvest_artifacts.harvest_batch(limit=80)
            if hres["issues"] or hres["commits"]:
                logging.info(f"🌾 Harvest: {hres['issues']} issues, {hres['commits']} commits")
        except Exception as e:
            logging.error(f"❌ Erreur lors de la récolte d'artifacts: {e}")
        export_to_excel()
        export_to_json()
        export_reports()


def run_scan_once_manual():
    """Déclenche manuellement un scan unique."""
    global scan_in_progress, scanner_status
    with scanner_lock:
        if scan_in_progress:
            return
        scan_in_progress = True

    try:
        scanner_status = "Scan manuel en cours..."
        logging.info("⚡ Lancement d'un scan manuel...")
        scan_cycle()
        logging.info("⚡ Scan manuel terminé avec succès.")
    except Exception as e:
        logging.error(f"❌ Erreur lors du scan manuel : {e}")
    finally:
        scanner_status = "Prêt / En sommeil"
        scan_in_progress = False


def run_scanner_daemon():
    """Démon de scan périodique."""
    global scanner_status, scan_in_progress
    logging.info("🚀 Démarrage du démon de scan automatique...")

    # Attendre que Postgres soit prêt et migré
    time.sleep(15)

    while True:
        with scanner_lock:
            if not scan_in_progress:
                scan_in_progress = True
            else:
                time.sleep(60)
                continue

        try:
            scanner_status = "Scan automatique en cours..."
            scan_cycle()
        except Exception as e:
            logging.error(f"❌ Erreur lors du cycle de scan automatique : {e}")
        finally:
            scanner_status = "Prêt / En sommeil"
            scan_in_progress = False

        logging.info(f"💤 En sommeil pour {SCAN_INTERVAL_SECONDS // 60} minutes...")
        time.sleep(SCAN_INTERVAL_SECONDS)


# --- ROUTAGE FASTAPI ---

@app.get("/", response_class=HTMLResponse)
def read_index():
    """Sert le frontend React ou l'interface HTML de secours."""
    react_index = FRONTEND_DIR / "index.html"
    if react_index.exists():
        return HTMLResponse(react_index.read_text())
    fallback = "templates/index.html"
    if os.path.exists(fallback):
        with open(fallback, encoding="utf-8") as f:
            return f.read()
    return "<h1>Erreur : Frontend non disponible.</h1>"


@app.get("/api/stats")
def get_stats():
    """Retourne les statistiques (format compatible frontend React)."""
    global scanner_status
    (total_repos, total_stars, languages, lang_dist, last_scan, critique,
     suspect, unscanned, avg_vitality, top_vitality, low_vitality, dead_vitality) = database.get_frontend_stats()
    last_scan_str = last_scan.isoformat() if last_scan else None
    return {
        "total_repos": total_repos,
        "total_stars": int(total_stars),
        "languages": languages,
        "lang_distribution": lang_dist,
        "last_scan": last_scan_str,
        "status": scanner_status,
        "security_critique": critique,
        "security_suspect": suspect,
        "security_unscanned": unscanned,
        "avg_vitality": round(float(avg_vitality), 1),
        "top_vitality": top_vitality,
        "low_vitality": low_vitality,
        "dead_vitality": dead_vitality,
    }


@app.get("/api/repos")
def get_repos_api(q: str = "", page: int = 1, per_page: int = 50, sort_by: str = "stars", vitality_min: int = 0):
    """Renvoie les dépôts paginés au format attendu par le frontend React."""
    repos, total = database.search_repos_frontend(q, page, per_page, sort_by, vitality_min)
    pages = max(1, (total + per_page - 1) // per_page)
    return {"total": total, "page": page, "per_page": per_page, "pages": pages, "repos": repos}


@app.get("/api/repositories")
def get_repositories_api():
    """Renvoie la liste des dépôts (format brut)."""
    return database.get_repositories()


@app.get("/api/books")
def get_books_api(q: str = None):
    """
    Renvoie la liste des livres extraits.
    Si le paramètre q est fourni, effectue une recherche sémantique intelligente.
    """
    return database.get_books(q)


@app.get("/api/news")
def get_news_api(limit: int = 15, country: str = None):
    """Renvoie les actualités cyber avec leurs repos corrélés. Filtre optionnel par pays (code ISO)."""
    return database.get_news_with_correlations(limit, country)


@app.get("/api/news/health")
def get_news_health_api():
    import src.miniflux_bridge as miniflux_bridge
    health = rss_feed.count_usable_feeds()
    miniflux_status = {"enabled": miniflux_bridge.MINIFLUX_ENABLED}
    if miniflux_bridge.MINIFLUX_ENABLED and miniflux_bridge.MINIFLUX_TOKEN:
        try:
            import requests
            resp = requests.get(
                f"{miniflux_bridge.MINIFLUX_URL}/healthcheck",
                timeout=5,
            )
            miniflux_status["reachable"] = resp.status_code == 200
            miniflux_status["feeds"] = miniflux_bridge.sync_feeds()
        except Exception as e:
            miniflux_status["reachable"] = False
            miniflux_status["error"] = str(e)[:120]
    return {
        "collector": "miniflux" if (miniflux_bridge.MINIFLUX_ENABLED and miniflux_bridge.MINIFLUX_TOKEN) else "builtin",
        "feeds_total": health["total"],
        "feeds_usable": health["usable"],
        "feeds_dead": health["dead"],
        "feeds_blocked_antibot": health["blocked_antibot"],
        "miniflux": miniflux_status,
    }


@app.get("/api/news/countries")
def get_news_countries_api():
    """Liste les pays (codes ISO) disponibles dans les actualités, avec leur nombre."""
    return database.get_news_countries()


@app.get("/api/news/incidents")
def get_news_incidents_api(limit: int = 50, country: str = None):
    """Retourne les incidents unifies (plusieurs flux corrélés par CVE/IOC/produit)."""
    return {"incidents": database.get_incidents(limit=limit, country=country)}


@app.get("/api/keywords")
def get_keywords_api(status: str = "pending", limit: int = 100, min_score: float = 0.0):
    """Liste les mots-clés découverts par le miner."""
    if status == "approved":
        return {"keywords": database.get_approved_keywords()[:limit]}
    return {"keywords": database.get_pending_keywords(limit, min_score)}


@app.post("/api/keywords/{term}/approve")
def approve_keyword_api(term: str, category: str = None):
    ok = database.approve_keyword(term, "approved", category)
    if ok:
        from nlp_processor import refresh_cyber_terms
        refresh_cyber_terms()
    return {"success": ok, "term": term}


@app.post("/api/keywords/{term}/reject")
def reject_keyword_api(term: str):
    ok = database.approve_keyword(term, "rejected")
    return {"success": ok, "term": term}


@app.post("/api/enrich-ontology")
def enrich_ontology_api(background_tasks: BackgroundTasks):
    """Télécharge MITRE ATT&CK / CAPEC / CWE et enrichit l'ontologie."""
    background_tasks.add_task(_run_ontology_enrichment)
    return {"message": "Enrichissement de l'ontologie lancé en arrière-plan"}


def _run_ontology_enrichment():
    import ontology_enricher
    count = ontology_enricher.import_ontology_to_db()
    logging.info(f"🧬 Enrichissement ontologique terminé : {count} termes")


@app.get("/api/download")
def download_excel():
    """Téléchargement de l'export Excel."""
    export_to_excel()
    if os.path.exists(EXCEL_FILE):
        return FileResponse(
            EXCEL_FILE,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="cyber_security_catalogues.xlsx"
        )
    return {"error": "Fichier Excel non disponible."}


@app.get("/api/download/json")
def download_json():
    """Téléchargement de l'export JSON."""
    export_to_json()
    if os.path.exists(JSON_FILE):
        return FileResponse(
            JSON_FILE,
            media_type="application/json",
            filename="cyber_security_catalogues.json"
        )
    return {"error": "Fichier JSON non disponible."}


@app.post("/api/scan")
def start_scan(background_tasks: BackgroundTasks):
    """Déclenche un scan manuel en arrière-plan."""
    global scan_in_progress
    if scan_in_progress:
        return {"message": "Un scan est déjà en cours."}

    background_tasks.add_task(run_scan_once_manual)
    return {"message": "Le scan en arrière-plan a été démarré !"}


@app.post("/api/bulk-seed")
def start_bulk_seed(background_tasks: BackgroundTasks, max_pages_per_bucket: int = 10):
    """Scan massif multi-topics pour monter en charge vers 1M de dépôts."""
    global bulk_in_progress
    if bulk_in_progress:
        return {"message": "Un bulk-seed est déjà en cours."}

    def _run():
        global bulk_in_progress, scanner_status
        bulk_in_progress = True
        scanner_status = "Bulk-seed en cours..."
        try:
            import src.bulk_seed as bulk_seed
            result = bulk_seed.bulk_seed(max_pages_per_bucket=max_pages_per_bucket)
            logging.info(f"🌱 Bulk-seed terminé: {result}")
        except Exception as e:
            logging.error(f"❌ Erreur bulk-seed: {e}")
        finally:
            bulk_in_progress = False
            scanner_status = "Prêt / En sommeil"

    background_tasks.add_task(_run)
    return {"message": "Bulk-seed lancé en arrière-plan.", "max_pages_per_bucket": max_pages_per_bucket}


@app.get("/api/bulk-status")
def bulk_status_api():
    """Retourne l'état d'avancement du dernier bulk-seed."""
    import src.bulk_seed as bulk_seed
    return bulk_seed.get_bulk_status()


@app.post("/api/harvest")
def start_harvest(background_tasks: BackgroundTasks, limit: int = 50, max_issues_pages: int = 3, max_commits_pages: int = 3):
    """Récolte les issues/commits des repos pour exploser le volume de données."""
    global harvest_in_progress
    if harvest_in_progress:
        return {"message": "Une récolte d'artifacts est déjà en cours."}

    def _run():
        global harvest_in_progress, scanner_status
        harvest_in_progress = True
        scanner_status = "Récolte issues/commits en cours..."
        try:
            import src.harvest_artifacts as harvest_artifacts
            result = harvest_artifacts.harvest_batch(limit, max_issues_pages, max_commits_pages)
            logging.info(f"🌾 Harvest terminé: {result}")
        except Exception as e:
            logging.error(f"❌ Erreur harvest: {e}")
        finally:
            harvest_in_progress = False
            scanner_status = "Prêt / En sommeil"

    background_tasks.add_task(_run)
    return {"message": "Récolte d'artifacts lancée en arrière-plan.", "limit": limit}


@app.get("/api/data-points")
def data_points_api():
    """Retourne le nombre total de points de données (repos + issues + commits + ...)."""
    return database.count_total_data_points()


@app.get("/api/harvest-status")
def harvest_status_api():
    """Retourne l'état d'avancement de la récolte d'artifacts."""
    import src.harvest_artifacts as harvest_artifacts
    return harvest_artifacts.get_harvest_status()


@app.post("/api/import-cve")
def start_cve_import(background_tasks: BackgroundTasks, max_entries_per_year: int = 0):
    """Importe les feeds NVD/CVE (2002-2025) pour ~300k+ vulnérabilités."""
    global cve_in_progress
    if cve_in_progress:
        return {"message": "Un import CVE est déjà en cours."}

    def _run():
        global cve_in_progress, scanner_status
        cve_in_progress = True
        scanner_status = "Import CVE NVD en cours..."
        try:
            import src.cve_importer as cve_importer
            lim = max_entries_per_year if max_entries_per_year > 0 else None
            result = cve_importer.import_cve_all(max_entries_per_year=lim)
            logging.info(f"🛡️ Import CVE terminé: {result}")
        except Exception as e:
            logging.error(f"❌ Erreur import CVE: {e}")
        finally:
            cve_in_progress = False
            scanner_status = "Prêt / En sommeil"

    background_tasks.add_task(_run)
    return {"message": "Import CVE NVD lancé en arrière-plan."}


@app.get("/api/cve-status")
def cve_status_api():
    """Retourne l'état d'avancement de l'import CVE."""
    import src.cve_importer as cve_importer
    return cve_importer.get_cve_status()


@app.get("/api/token-status")
def token_status_api():
    """Retourne le nombre de tokens configurés (sans exposer les valeurs)."""
    from src import github_client
    return {"token_count": github_client.token_count(), "has_tokens": github_client.token_count() > 0}


# --- FRONTEND SERVING (React SPA + Reports) ---

FRONTEND_DIR = Path("frontend/dist")
if FRONTEND_DIR.exists() and (FRONTEND_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="frontend_assets")

REPORTS_DIR = Path("reports")


@app.get("/api/reports")
def api_reports():
    if not REPORTS_DIR.exists():
        return {"reports": [], "dashboards": []}
    reports = sorted([f.name for f in REPORTS_DIR.glob("rapport_*.md")], reverse=True)
    dashboards = sorted([f.name for f in REPORTS_DIR.glob("dashboard_*.html")], reverse=True)
    return {"reports": reports, "dashboards": dashboards}


@app.get("/reports/{filename}")
def serve_report(filename: str):
    filepath = REPORTS_DIR / filename
    if filepath.exists() and filepath.suffix in (".md", ".html"):
        return FileResponse(filepath)
    return HTMLResponse("<h1>404</h1>", status_code=404)


@app.get("/dashboards/{filename}")
def serve_dashboard(filename: str):
    filepath = REPORTS_DIR / filename
    if filepath.exists() and filepath.suffix == ".html":
        return FileResponse(filepath)
    return HTMLResponse("<h1>404</h1>", status_code=404)


@app.get("/{path:path}")
def serve_frontend(path: str):
    if path.startswith("api/") or path.startswith("reports/") or path.startswith("dashboards/"):
        return HTMLResponse("<h1>404</h1>", status_code=404)
    index = FRONTEND_DIR / "index.html" if FRONTEND_DIR.exists() else None
    if index and index.exists():
        return HTMLResponse(index.read_text())
    return HTMLResponse("<h1>CyberScan API</h1><p>Frontend non disponible</p>")


def _bootstrap_ontology():
    """Importe l'ontologie MITRE au premier démarrage si la base est vide."""
    try:
        approved = database.get_approved_keywords()
        if len(approved) >= 1000:
            logging.info("🧬 Ontologie déjà chargée (%d termes)", len(approved))
            from nlp_processor import refresh_cyber_terms
            refresh_cyber_terms()
            return
        import ontology_enricher
        count = ontology_enricher.import_ontology_to_db()
        logging.info("🧬 Ontologie bootstrap: %d termes importes", count)
    except Exception as e:
        logging.error(f"❌ Erreur bootstrap ontologie: {e}")


if __name__ == "__main__":
    database.init_db()

    bootstrap_thread = threading.Thread(target=_bootstrap_ontology, daemon=True)
    bootstrap_thread.start()

    daemon_thread = threading.Thread(target=run_scanner_daemon, daemon=True)
    daemon_thread.start()

    import uvicorn
    logging.info("Lancement du serveur Web FastAPI sur le port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
