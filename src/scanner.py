import json
import logging
import os
import re
import sys
import threading
import time

import pandas as pd
import requests
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse

from src import database

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
    '"cybersecurity" books',
    '"cybersecurity" awesome',
    '"hacking" books',
    '"hacking" awesome',
    '"pentest" awesome',
    '"pentest" list',
    '"infosec" resources',
    '"red team" tools',
    '"blue team" tools',
    # 1. Write-ups CTF et Bug Bounty
    '"ctf-writeups"',
    '"bugbounty-methodology"',
    '"walkthrough" cybersecurity',
    '"poc-exploits" cybersecurity',
    # 2. Checklists de Durcissement (Hardening) et Conformité
    '"hardening-guide" cybersecurity',
    '"security-checklist"',
    '"cis-benchmarks"',
    '"active-directory-hardening"',
    # 3. Modèles de Rapports d'Audit & Livrables Pro
    '"pentest-report-template"',
    '"audit-template" cybersecurity',
    '"security-policy-samples"',
    # 4. Questions d'Entretiens & Certifs
    '"cybersecurity-interview-questions"',
    '"oscp-notes"',
    '"cissp-study-guide"',
    # 5. Flux de Threat Intelligence
    '"yara-rules" malware',
    '"sigma-rules" threat',
    '"threat-intel" list',
    '"ioc-lists" ip'
]

DATA_DIR = os.getenv("DATA_DIR", "data")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

EXCEL_FILE = os.path.join(DATA_DIR, "cyber_security_catalogues.xlsx")
JSON_FILE = os.path.join(DATA_DIR, "cyber_security_catalogues.json")
SCAN_INTERVAL_SECONDS = int(os.getenv("SCAN_INTERVAL_SECONDS", 3600))
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Variables d'état
scanner_status = "Prêt / En sommeil"
scanner_lock = threading.Lock()
scan_in_progress = False

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
            rate_remaining = response.headers.get("X-RateLimit-Remaining")
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

            pg_cursor.execute(
                """
                INSERT INTO repositories (id, full_name, stars, description, html_url, language, updated_at, readme_parsed, score_qualite, vecteur_semantique)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE
                SET full_name = EXCLUDED.full_name,
                    stars = EXCLUDED.stars,
                    description = EXCLUDED.description,
                    html_url = EXCLUDED.html_url,
                    language = EXCLUDED.language,
                    updated_at = EXCLUDED.updated_at,
                    readme_parsed = EXCLUDED.readme_parsed,
                    score_qualite = EXCLUDED.score_qualite,
                    vecteur_semantique = EXCLUDED.vecteur_semantique
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
                    vector
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


def scan_cycle():
    """Effectue un cycle de scan GitHub hybride (popularité et activité récente)."""
    logging.info("🔄 Début du cycle de scan sur GitHub...")
    new_discoveries_total = 0
    any_success = False

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

    if any_success:
        if new_discoveries_total > 0:
            logging.info(f"✨ {new_discoveries_total} nouvelle(s) pépite(s) découverte(s) lors de ce cycle !")
        else:
            logging.info("ℹ️ Données existantes synchronisées. Aucun nouveau dépôt.")

        parse_unprocessed_readmes()
        export_to_excel()
        export_to_json()


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
    """Sert l'interface HTML principale."""
    index_path = "templates/index.html"
    if os.path.exists(index_path):
        with open(index_path, encoding="utf-8") as f:
            return f.read()
    return "<h1>Erreur : Fichier templates/index.html introuvable.</h1>"


@app.get("/api/stats")
def get_stats():
    """Retourne les statistiques de la base de données et le statut du scanner."""
    global scanner_status
    repos, books = database.get_stats()
    return {
        "total_repos": repos,
        "total_books": books,
        "status": scanner_status
    }


@app.get("/api/repositories")
def get_repositories_api():
    """Renvoie la liste des dépôts."""
    return database.get_repositories()


@app.get("/api/books")
def get_books_api(q: str = None):
    """
    Renvoie la liste des livres extraits.
    Si le paramètre q est fourni, effectue une recherche sémantique intelligente.
    """
    return database.get_books(q)


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


if __name__ == "__main__":
    database.init_db()

    daemon_thread = threading.Thread(target=run_scanner_daemon, daemon=True)
    daemon_thread.start()

    import uvicorn
    logging.info("Lancement du serveur Web FastAPI sur le port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
