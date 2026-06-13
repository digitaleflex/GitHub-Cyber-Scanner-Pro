import logging
import os
import time

import psycopg2
from psycopg2.extras import RealDictCursor
from qdrant_client import QdrantClient
from qdrant_client.http import models

import nlp_processor

# Configuration du logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Configuration de la base de données PostgreSQL
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "scanner_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "cyberpass")

# Configuration Qdrant
QDRANT_HOST = os.getenv("QDRANT_HOST", "cyber-vector-engine")
QDRANT_PORT = os.getenv("QDRANT_PORT", "6333")
QDRANT_COLLECTION = "cyber_resources"

qdrant_client = None

def get_qdrant_client():
    """Initialise et retourne le client Qdrant."""
    global qdrant_client
    if qdrant_client is None:
        try:
            qdrant_client = QdrantClient(host=QDRANT_HOST, port=int(QDRANT_PORT))
            logging.info(f"🛰️ Connecté à Qdrant sur {QDRANT_HOST}:{QDRANT_PORT}")
        except Exception as e:
            logging.error(f"❌ Erreur connexion Qdrant : {e}")
    return qdrant_client

def init_qdrant():
    """Crée la collection Qdrant si elle n'existe pas."""
    client = get_qdrant_client()
    if not client:
        return

    try:
        collections = client.get_collections().collections
        exists = any(c.name == QDRANT_COLLECTION for c in collections)
        
        if not exists:
            client.create_collection(
                collection_name=QDRANT_COLLECTION,
                vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
            )
            logging.info(f"✨ Collection Qdrant '{QDRANT_COLLECTION}' créée avec succès.")
        else:
            logging.info(f"✅ Collection Qdrant '{QDRANT_COLLECTION}' déjà existante.")
    except Exception as e:
        logging.error(f"❌ Erreur initialisation Qdrant : {e}")

def save_to_qdrant(repo_id, vector, payload):
    """Enregistre un vecteur et ses métadonnées dans Qdrant."""
    client = get_qdrant_client()
    if not client or not vector:
        return

    try:
        # Convertir l'ID en entier si possible pour Qdrant, sinon garder en string
        try:
            point_id = int(repo_id)
        except ValueError:
            # Générer un hash entier stable à partir de la string si besoin, 
            # ou utiliser l'UUID si Qdrant le supporte mieux
            import hashlib
            point_id = int(hashlib.md5(repo_id.encode()).hexdigest(), 16) % (10 ** 15)

        client.upsert(
            collection_name=QDRANT_COLLECTION,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload
                )
            ]
        )
        logging.info(f"🧠 Vecteur sauvegardé dans Qdrant pour le dépôt {repo_id}")
    except Exception as e:
        logging.error(f"❌ Erreur sauvegarde Qdrant : {e}")

def get_db_connection():
    conn = None
    retries = 10
    delay = 3
    for attempt in range(retries):
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                connect_timeout=5
            )
            return conn
        except psycopg2.OperationalError as e:
            logging.warning(
                f"⚠️ [Base de données] PostgreSQL non disponible. "
                f"Nouvelle tentative dans {delay}s (essai {attempt + 1}/{retries})... Erreur: {e}"
            )
            time.sleep(delay)
    logging.critical("❌ Impossible de se connecter à PostgreSQL après plusieurs tentatives.")
    raise ConnectionError("Échec de connexion à PostgreSQL.")


def update_repo_quality_and_vector(repo_id, score, vector):
    """Met à jour le score de qualité et le vecteur sémantique d'un dépôt."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE repositories SET score_qualite = %s, vecteur_semantique = %s WHERE id = %s",
            (score, vector, repo_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logging.error(f"❌ Erreur update_repo_quality_and_vector: {e}")
        return False

def init_db():
    """Initialise les tables PostgreSQL avec pgvector et TSVector pour la recherche sémantique de pointe."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 0. Initialiser Qdrant en parallèle
    init_qdrant()

    # 1. Activer l'extension pgvector si disponible
    try:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        conn.commit()
        logging.info("🧠 Extension pgvector installée/activée avec succès dans PostgreSQL.")
    except Exception as e:
        logging.warning(f"⚠️ Impossible d'activer l'extension pgvector (recherche vectorielle désactivée) : {e}")
        conn.rollback()

    # 2. Table des dépôts (avec score_qualite et vecteur_semantique)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS repositories (
            id VARCHAR(50) PRIMARY KEY,
            full_name VARCHAR(255) NOT NULL,
            stars INTEGER,
            description TEXT,
            html_url VARCHAR(500),
            language VARCHAR(100),
            updated_at VARCHAR(100),
            readme_parsed INTEGER DEFAULT 0,
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            score_qualite INTEGER DEFAULT 0,
            security_verdict VARCHAR(20) DEFAULT 'NON_AUDITE',
            security_details JSONB,
            llm_summary JSONB,
            vecteur_semantique vector(384)
        )
    """)

    # S'assurer de rajouter les colonnes si elles n'existent pas (migration fluide)
    try:
        cursor.execute("ALTER TABLE repositories ADD COLUMN IF NOT EXISTS security_verdict VARCHAR(20) DEFAULT 'NON_AUDITE';")
        cursor.execute("ALTER TABLE repositories ADD COLUMN IF NOT EXISTS security_details JSONB;")
        cursor.execute("ALTER TABLE repositories ADD COLUMN IF NOT EXISTS llm_summary JSONB;")
        conn.commit()
    except Exception as e:
        conn.rollback()
        logging.warning(f"⚠️ Erreur migration colonnes repositories : {e}")

    # 3. Table des livres (avec score_qualite, vecteur_semantique et tsvector)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id SERIAL PRIMARY KEY,
            repo_id VARCHAR(50) REFERENCES repositories(id) ON DELETE CASCADE,
            title VARCHAR(500) NOT NULL,
            url VARCHAR(1000) UNIQUE NOT NULL,
            category VARCHAR(150),
            is_dead INTEGER DEFAULT 0,
            last_checked TIMESTAMP,
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            lemmas_str TEXT,
            score_qualite INTEGER DEFAULT 0,
            vecteur_semantique vector(384),
            type_ressource VARCHAR(100) DEFAULT 'Book',
            tsv_content tsvector
        )
    """)

    # S'assurer de rajouter la colonne si elle n'existe pas (migration fluide)
    try:
        cursor.execute("ALTER TABLE books ADD COLUMN IF NOT EXISTS type_ressource VARCHAR(100) DEFAULT 'Book';")
        conn.commit()
    except Exception as e:
        conn.rollback()
        logging.warning(f"⚠️ Impossible d'ajouter la colonne type_ressource : {e}")

    # 4. Table de cache ETag
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS etag_cache (
            query VARCHAR(255) PRIMARY KEY,
            etag VARCHAR(255),
            last_modified VARCHAR(255),
            last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 5. Créer l'index GIN sur tsv_content
    cursor.execute("CREATE INDEX IF NOT EXISTS books_tsv_idx ON books USING GIN (tsv_content)")

    conn.commit()
    cursor.close()
    conn.close()
    logging.info("⚙️ [Base de données] Tables PostgreSQL initialisées.")


def save_etag_to_cache(query, etag, last_modified):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO etag_cache (query, etag, last_modified, last_checked)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (query) DO UPDATE 
            SET etag = EXCLUDED.etag, 
                last_modified = EXCLUDED.last_modified, 
                last_checked = CURRENT_TIMESTAMP
            """,
            (query, etag, last_modified)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        logging.error(f"❌ Erreur ETag cache: {e}")


def get_etag_from_cache(query):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT etag, last_modified FROM etag_cache WHERE query = %s", (query,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row:
            return row[0], row[1]
    except Exception as e:
        logging.error(f"❌ Erreur ETag read cache: {e}")
    return None, None


def save_repositories(items):
    """Enregistre les dépôts découverts, calcule leur score de qualité et leur embedding vectoriel sémantique."""
    if not items:
        return 0

    # Récupérer toutes les descriptions existantes pour initialiser le corpus TF-IDF
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT description FROM repositories WHERE description IS NOT NULL")
    existing_desc = [r[0] for r in cursor.fetchall()]

    # Ajouter les descriptions des nouveaux items au corpus pour calibrage TF-IDF
    new_desc = [item.get("description", "") for item in items if item.get("description")]
    corpus = existing_desc + new_desc

    # Instancier l'analyseur sémantique cyber de pointe
    analyzer = nlp_processor.CyberTextAnalyzer(corpus)

    new_discoveries = 0
    for item in items:
        repo_id = str(item.get("id"))

        # 1. Vérifier si le dépôt est nouveau
        cursor.execute("SELECT 1 FROM repositories WHERE id = %s", (repo_id,))
        exists = cursor.fetchone()
        if not exists:
            new_discoveries += 1

        # 2. Lancer l'analyse d'IA (Embedding, mots-clés et score de pertinence)
        analysis = analyzer.process_repository(item)
        score_qualite = 0
        vector = None

        if analysis:
            score_qualite = analysis["score_qualite"]
            vector = analysis["vecteur_semantique"]

        # S'assurer que le vecteur est None si vide (pour pgvector)
        if not vector:
            vector = None

        cursor.execute(
            """
            INSERT INTO repositories (id, full_name, stars, description, html_url, language, updated_at, score_qualite, vecteur_semantique)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE 
            SET full_name = EXCLUDED.full_name,
                stars = EXCLUDED.stars,
                description = EXCLUDED.description,
                html_url = EXCLUDED.html_url,
                language = EXCLUDED.language,
                updated_at = EXCLUDED.updated_at,
                score_qualite = EXCLUDED.score_qualite,
                vecteur_semantique = EXCLUDED.vecteur_semantique
            """,
            (
                repo_id,
                item.get("full_name"),
                item.get("stargazers_count"),
                item.get("description") if item.get("description") else "Aucune description.",
                item.get("html_url"),
                item.get("language") if item.get("language") else "Non spécifiée",
                item.get("updated_at"),
                score_qualite,
                vector
            )
        )
    conn.commit()
    cursor.close()
    conn.close()
    return new_discoveries


def get_unprocessed_repositories():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name FROM repositories WHERE readme_parsed = 0")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


def mark_repo_as_parsed(repo_id, readme_parsed=1):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE repositories SET readme_parsed = %s WHERE id = %s", (readme_parsed, repo_id))
    conn.commit()
    cursor.close()
    conn.close()


def save_book(repo_id, title, url, category, lemmas_list, type_ressource='Book'):
    """
    Enregistre un livre, hérite ou calcule son score de qualité, son embedding
    et génère le TSVector pour la recherche sémantique PostgreSQL.
    """
    lemmas_str = " ".join(lemmas_list) if lemmas_list else ""
    semantic_text = f"{title} {category if category else ''} {type_ressource} {lemmas_str}"

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Récupérer les informations de qualité du dépôt parent
        cursor.execute("SELECT score_qualite, vecteur_semantique FROM repositories WHERE id = %s", (repo_id,))
        row = cursor.fetchone()
        score_qualite = row[0] if row else 0
        vecteur_semantique = row[1] if row else None

        cursor.execute(
            """
            INSERT INTO books (repo_id, title, url, category, lemmas_str, score_qualite, vecteur_semantique, type_ressource, tsv_content)
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s,
                to_tsvector('simple', %s)
            )
            ON CONFLICT (url) DO UPDATE 
            SET title = EXCLUDED.title,
                category = EXCLUDED.category,
                lemmas_str = EXCLUDED.lemmas_str,
                score_qualite = EXCLUDED.score_qualite,
                vecteur_semantique = EXCLUDED.vecteur_semantique,
                type_ressource = EXCLUDED.type_ressource,
                tsv_content = to_tsvector('simple', %s)
            """,
            (repo_id, title, url, category, lemmas_str, score_qualite, vecteur_semantique, type_ressource, semantic_text, semantic_text)
        )
        conn.commit()
        return True
    except psycopg2.IntegrityError:
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def get_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM repositories")
        total_repos = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM books WHERE is_dead = 0")
        total_books = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return total_repos, total_books
    except Exception:
        return 0, 0


def update_repo_security(repo_id, verdict, details):
    """Met à jour le verdict de sécurité et les détails pour un dépôt."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE repositories SET security_verdict = %s, security_details = %s WHERE id = %s",
            (verdict, psycopg2.extras.Json(details), repo_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logging.error(f"❌ Erreur update_repo_security: {e}")
        return False

def get_repos_to_analyze(limit=10):
    """Récupère les dépôts qui n'ont pas encore été audités."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "SELECT id, full_name, html_url FROM repositories WHERE security_verdict = 'NON_AUDITE' LIMIT %s",
            (limit,)
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        logging.error(f"❌ Erreur get_repos_to_analyze: {e}")
        return []

def update_repo_llm_summary(repo_id, summary_json):
    """Enregistre la fiche de synthèse générée par le LLM."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE repositories SET llm_summary = %s WHERE id = %s",
            (psycopg2.extras.Json(summary_json), repo_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logging.error(f"❌ Erreur update_repo_llm_summary: {e}")
        return False

def get_repos_needing_summary(limit=10):
    """Récupère les dépôts qui n'ont pas encore de fiche de synthèse."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "SELECT id, full_name, description FROM repositories WHERE llm_summary IS NULL LIMIT %s",
            (limit,)
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        logging.error(f"❌ Erreur get_repos_needing_summary: {e}")
        return []

def get_repositories():
    """Renvoie les dépôts triés par score de qualité (IA) puis par étoiles."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT id, full_name, stars, description, html_url, language, updated_at, score_qualite, security_verdict, security_details, llm_summary
            FROM repositories 
            ORDER BY score_qualite DESC, stars DESC
            """
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        logging.error(f"❌ Erreur get_repositories: {e}")
        return []


def get_books(search_query=None):
    """
    Renvoie la liste des ressources/livres triée par score de qualité (IA).
    Si search_query est spécifié, effectue une recherche sémantique TSVector.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        if search_query:
            # Recherche sémantique TSVector ordonnée par pertinence textuelle
            cursor.execute(
                """
                SELECT b.id, b.title, b.url, b.category, r.full_name AS repo_name, r.html_url AS repo_url, b.is_dead, b.last_checked, b.score_qualite, b.type_ressource,
                       ts_rank(b.tsv_content, plainto_tsquery('simple', %s)) as rank
                FROM books b 
                LEFT JOIN repositories r ON b.repo_id = r.id 
                WHERE b.tsv_content @@ plainto_tsquery('simple', %s)
                ORDER BY rank DESC, b.score_qualite DESC, b.discovered_at DESC
                """,
                (search_query, search_query)
            )
        else:
            # Tri par score de qualité IA par défaut (propulse les pépites) puis date de découverte
            cursor.execute(
                """
                SELECT b.id, b.title, b.url, b.category, r.full_name AS repo_name, r.html_url AS repo_url, b.is_dead, b.last_checked, b.score_qualite, b.type_ressource
                FROM books b 
                LEFT JOIN repositories r ON b.repo_id = r.id 
                ORDER BY b.score_qualite DESC, b.discovered_at DESC
                """
            )

        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        logging.error(f"❌ Erreur get_books: {e}")
        return []


def get_books_to_verify(limit=50):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, url FROM books 
            WHERE last_checked IS NULL 
               OR last_checked < NOW() - INTERVAL '24 hours'
            LIMIT %s
            """,
            (limit,)
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    except Exception as e:
        logging.error(f"❌ Erreur get_books_to_verify: {e}")
        return []


def update_book_status(book_id, is_dead, last_checked=True):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        if last_checked:
            cursor.execute(
                "UPDATE books SET is_dead = %s, last_checked = CURRENT_TIMESTAMP WHERE id = %s",
                (is_dead, book_id)
            )
        else:
            cursor.execute(
                "UPDATE books SET is_dead = %s WHERE id = %s",
                (is_dead, book_id)
            )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        logging.error(f"❌ Erreur update_book_status: {e}")
