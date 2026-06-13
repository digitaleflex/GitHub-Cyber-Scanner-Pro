import sys
import os
import time
import json
import sqlite3
import logging
import re
import threading
import pandas as pd
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse

# Reconfigurer la sortie standard en UTF-8 sur Windows pour supporter l'affichage d'emojis
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Configurer le framework standard logging vers stdout
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Charger les variables d'environnement depuis le fichier .env
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
]

DATA_DIR = os.getenv("DATA_DIR", "data")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

DB_FILE = os.path.join(DATA_DIR, "scanner.db")
EXCEL_FILE = os.path.join(DATA_DIR, "cyber_security_catalogues.xlsx")
JSON_FILE = os.path.join(DATA_DIR, "cyber_security_catalogues.json")
SCAN_INTERVAL_SECONDS = int(os.getenv("SCAN_INTERVAL_SECONDS", 3600))

# Récupération sécurisée du token depuis l'environnement système
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Variables d'état du scanner d'arrière-plan
scanner_status = "Prêt / En sommeil"
scanner_lock = threading.Lock()
scan_in_progress = False

# Initialiser l'application FastAPI
app = FastAPI(title="GitHub Cyber Scanner API")


def init_db():
    """Initialise les tables de la base de données SQLite si elles n'existent pas et gère les mises à niveau de schéma."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS repositories (
            id TEXT PRIMARY KEY,
            full_name TEXT NOT NULL,
            stars INTEGER,
            description TEXT,
            html_url TEXT,
            language TEXT,
            updated_at TEXT,
            readme_parsed INTEGER DEFAULT 0,
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_id TEXT,
            title TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            category TEXT,
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (repo_id) REFERENCES repositories(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS etag_cache (
            query TEXT PRIMARY KEY,
            etag TEXT,
            last_modified TEXT,
            last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Gérer une éventuelle mise à niveau si la colonne 'readme_parsed' n'existe pas encore dans repositories
    try:
        cursor.execute("ALTER TABLE repositories ADD COLUMN readme_parsed INTEGER DEFAULT 0")
        conn.commit()
    except sqlite3.OperationalError:
        pass # La colonne existe déjà

    # Inspecter les colonnes de la table books pour des mises à jour incrémentales sécurisées
    cursor.execute("PRAGMA table_info(books)")
    books_cols = [row[1] for row in cursor.fetchall()]

    if "is_dead" not in books_cols:
        cursor.execute("ALTER TABLE books ADD COLUMN is_dead INTEGER DEFAULT 0")
        conn.commit()

    if "last_checked" not in books_cols:
        cursor.execute("ALTER TABLE books ADD COLUMN last_checked TIMESTAMP")
        conn.commit()
        
    conn.close()


def get_etag_from_cache(query):
    """Récupère l'ETag et Last-Modified associés à une requête de recherche depuis le cache SQLite."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT etag, last_modified FROM etag_cache WHERE query = ?", (query,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0], row[1]
    return None, None


def save_etag_to_cache(query, etag, last_modified):
    """Sauvegarde ou met à jour l'ETag et Last-Modified associés à une requête dans SQLite."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO etag_cache (query, etag, last_modified, last_checked)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (query, etag, last_modified)
    )
    conn.commit()
    conn.close()


def categorize_book(title, url):
    """Catégorise un livre/ressource en fonction de mots-clés dans son titre et son URL."""
    title_lower = title.lower()
    url_lower = url.lower()
    
    # 1. Certifications
    cert_keywords = ["oscp", "ceh", "cissp", "cism", "comptia", "security+", "security plus", "ccna", "ccnp", "sans", "gsec", "giac"]
    if any(k in title_lower or k in url_lower for k in cert_keywords):
        return "Certifications"
        
    # 2. Cheat Sheets / Références
    cheat_keywords = ["cheat sheet", "cheatsheet", "checklist", "reference", "commands", "cmd", "guide rapide", "aide-mémoire"]
    if any(k in title_lower or k in url_lower for k in cheat_keywords):
        return "Cheat Sheets / Références"
        
    # 3. Offensive / Red Team
    off_keywords = ["red team", "offensive", "hack", "exploit", "pentest", "penetration", "malware", "reverse engineering", "reversing", "buffer overflow", "pwn", "bypass", "privilege escalation", "privesc", "metasploit", "nmap", "burp", "injection", "sqli", "xss", "lfi"]
    if any(k in title_lower or k in url_lower for k in off_keywords):
        return "Offensive / Red Team"
        
    # 4. Defensive / Blue Team
    def_keywords = ["blue team", "defensive", "defense", "soc", "siem", "incident response", "forensics", "dfir", "threat hunting", "hardening", "wireshark", "snort", "yara", "detection", "firewall", "log", "audit", "compliance"]
    if any(k in title_lower or k in url_lower for k in def_keywords):
        return "Defensive / Blue Team"
        
    # 5. Général / InfoSec par défaut
    return "Général / InfoSec"


def fetch_github_data(query):
    """Interroge l'API GitHub de manière authentifiée ou anonyme pour une requête spécifique, avec gestion d'ETag, de Rate Limit et de retry."""
    url = "https://api.github.com/search/repositories"
    params = {"q": query, "sort": "stars", "order": "desc", "per_page": 50}
    headers = {"Accept": "application/vnd.github.v3+json"}

    # Authentification si token présent
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    # Récupérer l'ETag et Last-Modified du cache pour cette requête
    etag, last_modified = get_etag_from_cache(query)
    if etag:
        headers["If-None-Match"] = etag
    if last_modified:
        headers["If-Modified-Since"] = last_modified

    # Logique de retry avec Exponential Backoff pour les erreurs serveur (5xx) et réseau
    max_retries = 5
    backoff_delay = 2

    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=15)
            
            # Gérer la lecture des Rate Limits
            rate_remaining = response.headers.get("X-RateLimit-Remaining")
            rate_reset = response.headers.get("X-RateLimit-Reset")
            
            if response.status_code == 200:
                new_etag = response.headers.get("ETag")
                new_last_modified = response.headers.get("Last-Modified")
                if new_etag or new_last_modified:
                    save_etag_to_cache(query, new_etag, new_last_modified)
                
                return response.json().get("items", []), False
                
            elif response.status_code == 304:
                logging.info(f"🔄 [Cache 304] Aucun changement détecté pour la requête : {query}")
                return [], False
                
            elif response.status_code == 403:
                # Gérer le dépassement de quota (Rate Limit) ou limite secondaire (Abuse)
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
                            f"⚠️ Limite d'appels API atteinte pour la requête '{query}'. "
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
            
    logging.error(f"❌ Échec de la récupération après {max_retries} tentatives pour : {query}")
    return [], False


def fetch_and_parse_readme(repo_id, full_name):
    """Télécharge le README d'un dépôt GitHub, extrait les liens de livres ou de ressources et les insère dans SQLite."""
    logging.info(f"📖 Analyse du README pour {full_name}...")
    readme_api_url = f"https://api.github.com/repos/{full_name}/readme"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    try:
        res = requests.get(readme_api_url, headers=headers, timeout=15)
        
        # Gérer spécifiquement le cas où l'API limite le quota durant l'extraction des README
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
            # Si le README n'existe pas, on marque tout de même comme traité pour éviter de boucler indéfiniment
            if res.status_code == 404:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("UPDATE repositories SET readme_parsed = 1 WHERE id = ?", (repo_id,))
                conn.commit()
                conn.close()
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
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        book_keywords = [
            "book", "guide", "manual", "handbook", "tutorial", "course", "pdf", "epub", "mobi",
            "livre", "manuel", "cours", "reference", "cheat", "lectures", "bibliotheque", "library"
        ]
        book_extensions = [".pdf", ".epub", ".mobi", ".docx"]
        book_domains = ["drive.google.com", "dropbox.com", "mega.nz", "mediafire.com", "books.google.com", "leanpub.com", "gitbook.io"]

        for title, url in links:
            title = title.strip()
            url = url.strip()
            
            title_lower = title.lower()
            url_lower = url.lower()
            
            # Valider si c'est un livre/ressource d'apprentissage
            is_book = False
            
            # 1. Vérifier l'extension dans l'URL
            if any(url_lower.endswith(ext) or f"{ext}?" in url_lower or f"{ext}#" in url_lower for ext in book_extensions):
                is_book = True
            # 2. Vérifier si le domaine est une source de livres typique
            elif any(domain in url_lower for domain in book_domains):
                is_book = True
            # 3. Vérifier si le titre ou l'URL contient des mots-clés de livre
            elif any(k in title_lower or k in url_lower for k in book_keywords):
                ignore_keywords = ["twitter.com", "linkedin.com", "facebook.com", "github.com/sponsors", "patreon.com", "paypal.me", "github.com/users/"]
                if not any(ignore in url_lower for ignore in ignore_keywords):
                    is_book = True
            
            # Si c'est validé, enregistrer dans SQLite
            if is_book and len(title) > 2 and len(url) < 1000:
                category = categorize_book(title, url)
                try:
                    cursor.execute(
                        """
                        INSERT INTO books (repo_id, title, url, category)
                        VALUES (?, ?, ?, ?)
                        """,
                        (repo_id, title, url, category)
                    )
                    extracted_count += 1
                except sqlite3.IntegrityError:
                    pass # Déjà présent (l'URL est UNIQUE)
                    
        # Marquer le dépôt comme README traité
        cursor.execute("UPDATE repositories SET readme_parsed = 1 WHERE id = ?", (repo_id,))
        conn.commit()
        conn.close()
        
        if extracted_count > 0:
            logging.info(f"✨ Extrait {extracted_count} livre(s)/ressource(s) depuis {full_name}")
        return True
    except Exception as e:
        logging.error(f"❌ Erreur lors du parsing du README pour {full_name} : {e}")
        return False


def save_repositories_to_db(raw_items):
    """Enregistre les dépôts découverts dans SQLite et retourne le nombre de nouvelles découvertes."""
    if not raw_items:
        return 0
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    new_discoveries = 0
    
    for item in raw_items:
        repo_id = str(item.get("id"))
        
        cursor.execute("SELECT 1 FROM repositories WHERE id = ?", (repo_id,))
        exists = cursor.fetchone()
        if not exists:
            new_discoveries += 1
            
        cursor.execute(
            """
            INSERT OR REPLACE INTO repositories (id, full_name, stars, description, html_url, language, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                repo_id,
                item.get("full_name"),
                item.get("stargazers_count"),
                item.get("description") if item.get("description") else "Aucune description.",
                item.get("html_url"),
                item.get("language") if item.get("language") else "Non spécifiée",
                item.get("updated_at")
            )
        )
    conn.commit()
    conn.close()
    return new_discoveries


def parse_unprocessed_readmes():
    """Sélectionne tous les dépôts dont le README n'a pas été traité et extrait les livres."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name FROM repositories WHERE readme_parsed = 0")
    unprocessed = cursor.fetchall()
    conn.close()
    
    if not unprocessed:
        return
        
    logging.info(f"📚 Extraction des README en cours pour {len(unprocessed)} dépôt(s)...")
    if not GITHUB_TOKEN and len(unprocessed) > 10:
        logging.warning("⚠️ Attention : Grand nombre de README à parser sans GITHUB_TOKEN configuré. Le traitement sera ralenti par les quotas.")
        
    for repo_id, full_name in unprocessed:
        # Appeler la fonction de parsing du README
        fetch_and_parse_readme(repo_id, full_name)
        # Petite pause entre les appels API pour éviter le rate limiting secondaire
        time.sleep(1.5)


def verify_book_link(book_id, url):
    """Vérifie si un lien de livre est toujours valide (HEAD ou GET partiel retournant HTTP < 400)."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, line Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    try:
        # Tenter une requête HEAD d'abord (très rapide)
        response = requests.head(url, headers=headers, timeout=10, allow_redirects=True)
        
        if response.status_code in [404, 410]:
            return False
        elif response.status_code >= 400:
            # Si le HEAD échoue ou n'est pas autorisé (405), tenter un GET léger en streaming
            response = requests.get(url, headers=headers, timeout=10, stream=True, allow_redirects=True)
            if response.status_code in [404, 410]:
                return False
                
        return response.status_code < 400
    except Exception:
        # En cas d'erreur de connexion/timeout, on ne le marque pas comme mort tout de suite (on retourne None pour réessai)
        return None


def run_link_validator_daemon():
    """Démon d'arrière-plan qui valide régulièrement la disponibilité des liens de livres extraits."""
    logging.info("🚀 Démarrage du démon de validation des liens (Link Checker)...")
    time.sleep(30) # Laisser l'application démarrer tranquillement
    
    while True:
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            # Sélectionner les livres n'ayant pas été vérifiés depuis 24h ou jamais vérifiés (max 50 par cycle)
            cursor.execute(
                """
                SELECT id, url FROM books 
                WHERE last_checked IS NULL 
                   OR datetime(last_checked) < datetime('now', '-24 hours')
                LIMIT 50
                """
            )
            books_to_check = cursor.fetchall()
            conn.close()
            
            if not books_to_check:
                # Tout est à jour, on dort 1 heure
                time.sleep(3600)
                continue
                
            logging.info(f"🔍 [Link Checker] Vérification de la disponibilité de {len(books_to_check)} liens...")
            
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            for book_id, url in books_to_check:
                status = verify_book_link(book_id, url)
                
                if status is False:
                    logging.warning(f"❌ Lien mort détecté et désactivé : {url}")
                    cursor.execute(
                        "UPDATE books SET is_dead = 1, last_checked = CURRENT_TIMESTAMP WHERE id = ?", 
                        (book_id,)
                    )
                else:
                    # Le lien est vivant (True) ou a échoué temporairement (None)
                    # On met à jour la date sans le marquer comme mort
                    cursor.execute(
                        "UPDATE books SET is_dead = 0, last_checked = CURRENT_TIMESTAMP WHERE id = ?", 
                        (book_id,)
                    )
                conn.commit()
                # Pause de 3 secondes pour préserver les serveurs distants et éviter d'être bloqué
                time.sleep(3)
                
            conn.close()
            # Mettre à jour l'export Excel et JSON après avoir filtré les liens morts
            export_to_excel()
            export_to_json()
            
        except Exception as e:
            logging.error(f"❌ Erreur dans le démon de validation des liens : {e}")
            time.sleep(60)


def export_to_excel():
    """Exporte les dépôts et les livres de SQLite vers un fichier Excel multi-onglets."""
    logging.info("📊 Exportation de la base de données SQLite vers Excel...")
    try:
        conn = sqlite3.connect(DB_FILE)
        
        # 1. Lire les dépôts
        df_repos = pd.read_sql_query(
            "SELECT full_name, stars, description, html_url, language, updated_at FROM repositories", 
            conn
        )
        
        # 2. Lire les livres
        df_books = pd.read_sql_query(
            """
            SELECT b.title, b.category, r.full_name AS repo_name, 
                   CASE WHEN b.is_dead = 1 THEN 'Hors ligne' 
                        WHEN b.last_checked IS NULL THEN 'Non vérifié'
                        ELSE 'Disponible' END AS status,
                   b.url 
            FROM books b 
            LEFT JOIN repositories r ON b.repo_id = r.id
            """, 
            conn
        )
        conn.close()
        
        # Formater les dépôts
        if not df_repos.empty:
            df_repos.columns = [
                "Nom du Dépôt",
                "Étoiles (Stars)",
                "Description",
                "Lien GitHub",
                "Langue Principale",
                "Dernière Mise à Jour",
            ]
            df_repos = df_repos.sort_values(by="Étoiles (Stars)", ascending=False)
            for col in df_repos.select_dtypes(include=['object']).columns:
                df_repos[col] = df_repos[col].astype(str).str.slice(0, 32000)
                
        # Formater les livres
        if not df_books.empty:
            df_books.columns = [
                "Titre de la Ressource / Livre",
                "Catégorie",
                "Dépôt Source",
                "Disponibilité",
                "Lien de Téléchargement"
            ]
            df_books = df_books.sort_values(by=["Catégorie", "Titre de la Ressource / Livre"])
            for col in df_books.select_dtypes(include=['object']).columns:
                df_books[col] = df_books[col].astype(str).str.slice(0, 32000)
                
        # Sauvegarder dans un fichier Excel multi-onglets
        with pd.ExcelWriter(EXCEL_FILE, engine='openpyxl') as writer:
            if not df_repos.empty:
                df_repos.to_excel(writer, sheet_name="Dépôts GitHub", index=False)
            if not df_books.empty:
                df_books.to_excel(writer, sheet_name="Livres & Ressources", index=False)
                
        logging.info(f"💾 Fichier Excel multi-onglets mis à jour avec succès : [{EXCEL_FILE}]")
    except Exception as e:
        logging.error(f"❌ Erreur lors de la génération du fichier Excel : {e}")


def export_to_json():
    """Exporte les dépôts et leurs livres associés de SQLite vers un fichier JSON structuré."""
    logging.info("📂 Exportation de la base de données SQLite vers JSON...")
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Récupérer tous les dépôts
        cursor.execute("SELECT id, full_name, stars, description, html_url, language, updated_at FROM repositories")
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
                "Ressources": []
            }
            
        # Récupérer tous les livres
        cursor.execute(
            """
            SELECT repo_id, title, category, 
                   CASE WHEN is_dead = 1 THEN 'Hors ligne'
                        WHEN last_checked IS NULL THEN 'Non vérifié'
                        ELSE 'Disponible' END AS status,
                   url 
            FROM books
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
                    "Disponibilité": b[3],
                    "Lien de Téléchargement": b[4]
                })
                
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(data_dict, f, indent=4, ensure_ascii=False)
            
        logging.info(f"💾 Fichier JSON mis à jour avec succès : [{JSON_FILE}]")
    except Exception as e:
        logging.error(f"❌ Erreur lors de la génération du fichier JSON : {e}")


def migrate_json_to_sqlite():
    """Migre les données historiques d'un fichier JSON existant vers la base SQLite au premier démarrage."""
    json_path = "cyber_security_catalogues.json"
    
    paths_to_check = [
        json_path,
        os.path.join(DATA_DIR, json_path)
    ]
    
    found_path = None
    for path in paths_to_check:
        if os.path.exists(path):
            found_path = path
            break
            
    if not found_path:
        return
        
    logging.info(f"📂 Fichier JSON existant détecté : {found_path}. Lancement de la migration vers SQLite...")
    try:
        with open(found_path, "r", encoding="utf-8") as f:
            data_dict = json.load(f)
            
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        migrated_count = 0
        for repo_id, repo in data_dict.items():
            cursor.execute(
                """
                INSERT OR IGNORE INTO repositories (id, full_name, stars, description, html_url, language, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(repo_id),
                    repo.get("Nom du Dépôt") or repo.get("full_name") or "",
                    repo.get("Étoiles (Stars)") or repo.get("stars") or 0,
                    repo.get("Description") or "",
                    repo.get("Lien GitHub") or repo.get("html_url") or "",
                    repo.get("Langue Principale") or repo.get("language") or "Non spécifiée",
                    repo.get("Dernière Mise à Jour") or repo.get("updated_at") or ""
                )
            )
            if cursor.rowcount > 0:
                migrated_count += 1
                
        conn.commit()
        conn.close()
        logging.info(f"✨ Migration réussie : {migrated_count} dépôts importés dans SQLite.")
        
        new_path = found_path + ".bak"
        os.rename(found_path, new_path)
        logging.info(f"📦 Fichier JSON d'origine renommé en {new_path}.")
    except Exception as e:
        logging.error(f"❌ Erreur lors de la migration du JSON : {e}")


def scan_cycle():
    """Exécute un cycle complet de requêtes GitHub, parsing des README, insertion en base et génération Excel."""
    logging.info("🔄 Début du cycle de scan sur GitHub...")
    new_discoveries_total = 0
    any_success = False
    
    for query in QUERIES:
        logging.info(f"🔍 Recherche pour : {query}...")
        raw_items, rate_limit_hit = fetch_github_data(query)
        
        if rate_limit_hit:
            logging.warning("⚠️ Cycle de scan interrompu en raison d'une limite de quota API non résolue.")
            break
            
        if raw_items:
            any_success = True
            new_discoveries = save_repositories_to_db(raw_items)
            new_discoveries_total += new_discoveries
            
        time.sleep(2)
        
    if any_success:
        if new_discoveries_total > 0:
            logging.info(f"✨ {new_discoveries_total} nouvelle(s) pépite(s) découverte(s) lors de ce cycle !")
        else:
            logging.info("ℹ️ Données existantes synchronisées. Aucun nouveau dépôt.")
            
        # Analyser les README des dépôts non traités pour en extraire des livres
        parse_unprocessed_readmes()
        
        # Générer l'export Excel et JSON
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
    """Démon d'arrière-plan exécutant les scans automatiques périodiques."""
    global scanner_status, scan_in_progress
    logging.info("🚀 Démarrage du démon de scan automatique...")
    
    # Attente initiale pour laisser le temps au serveur web de démarrer
    time.sleep(5)
    
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
    """Sert le tableau de bord HTML principal."""
    index_path = "templates/index.html"
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Erreur : Fichier templates/index.html introuvable.</h1>"


@app.get("/api/stats")
def get_stats():
    """Retourne les statistiques de la base de données et le statut du scanner."""
    global scanner_status
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM repositories")
        total_repos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM books WHERE is_dead = 0")
        total_books = cursor.fetchone()[0]
        conn.close()
    except Exception:
        total_repos = 0
        total_books = 0
        
    return {
        "total_repos": total_repos,
        "total_books": total_books,
        "status": scanner_status
    }


@app.get("/api/repositories")
def get_repositories():
    """Renvoie la liste de tous les dépôts ordonnés par étoiles."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id, full_name, stars, description, html_url, language, updated_at FROM repositories ORDER BY stars DESC")
        rows = cursor.fetchall()
        conn.close()
        
        repos = []
        for r in rows:
            repos.append({
                "id": r[0],
                "full_name": r[1],
                "stars": r[2],
                "description": r[3],
                "html_url": r[4],
                "language": r[5],
                "updated_at": r[6]
            })
        return repos
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/books")
def get_books():
    """Renvoie tous les livres extraits classés par date de découverte."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT b.id, b.title, b.url, b.category, r.full_name, r.html_url, b.is_dead, b.last_checked 
            FROM books b 
            LEFT JOIN repositories r ON b.repo_id = r.id 
            ORDER BY b.discovered_at DESC
            """
        )
        rows = cursor.fetchall()
        conn.close()
        
        books = []
        for r in rows:
            books.append({
                "id": r[0],
                "title": r[1],
                "url": r[2],
                "category": r[3],
                "repo_name": r[4] if r[4] else "Dépôt inconnu",
                "repo_url": r[5] if r[5] else "#",
                "is_dead": r[6],
                "last_checked": r[7]
            })
        return books
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/download")
def download_excel():
    """Génère le fichier Excel le plus frais possible et le propose en téléchargement."""
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
    """Génère le fichier JSON le plus frais possible et le propose en téléchargement."""
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
    # Initialiser la base de données SQLite
    init_db()
    
    # Migrer le JSON d'origine vers la base SQLite au premier démarrage
    migrate_json_to_sqlite()
    
    # Lancer le démon de scan automatique dans un thread séparé
    daemon_thread = threading.Thread(target=run_scanner_daemon, daemon=True)
    daemon_thread.start()
    
    # Lancer le démon de validation des liens dans un thread séparé
    validator_thread = threading.Thread(target=run_link_validator_daemon, daemon=True)
    validator_thread.start()
    
    # Démarrer le serveur FastAPI avec Uvicorn
    import uvicorn
    logging.info("🔌 Lancement du serveur Web FastAPI sur le port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
