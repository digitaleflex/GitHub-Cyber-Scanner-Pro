"""GitHub API collectors and readme/link tools."""
import logging
import os
import re
import time
import json
import hashlib
import requests
import pandas as pd
from src import database
import src.nlp_processor as nlp_processor
import src.sast_scanner as sast_scanner
import src.threat_intel as threat_intel

def fetch_github_data(query, sort_by="stars"):
    """Interroge l'API GitHub avec gestion d'ETag, de Rate Limit et de retry."""
    url = "https://api.github.com/search/repositories"
    params = {"q": query, "sort": sort_by, "order": "desc", "per_page": 50}
    headers = {"Accept": "application/vnd.github.v3+json"}

    if os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = f"token {os.getenv('GITHUB_TOKEN', '')}"

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
    if os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = f"token {os.getenv('GITHUB_TOKEN', '')}"

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
            from src.exports import export_to_excel, export_to_json
            export_to_excel()
            export_to_json()

        except Exception as e:
            logging.error(f"❌ Erreur dans le démon de validation des liens : {e}")
            time.sleep(60)


