import logging
import os
import time

import psycopg2
from psycopg2.extras import RealDictCursor

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "scanner_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "cyberpass")


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
                f"PostgreSQL non disponible. Tentative {attempt + 1}/{retries}... Erreur: {e}"
            )
            time.sleep(delay)
    logging.critical("Impossible de se connecter a PostgreSQL.")
    raise ConnectionError("Echec de connexion a PostgreSQL.")


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

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
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id SERIAL PRIMARY KEY,
            repo_id VARCHAR(50) REFERENCES repositories(id) ON DELETE CASCADE,
            title VARCHAR(500) NOT NULL,
            url VARCHAR(1000) UNIQUE NOT NULL,
            category VARCHAR(150),
            is_dead INTEGER DEFAULT 0,
            last_checked TIMESTAMP,
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS etag_cache (
            query VARCHAR(500) PRIMARY KEY,
            etag VARCHAR(500),
            last_modified VARCHAR(500),
            last_checked TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()
    logging.info("Tables PostgreSQL initialisees.")


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
        logging.error(f"Erreur ETag cache: {e}")


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
        logging.error(f"Erreur ETag read cache: {e}")
    return None, None


def save_repositories(items):
    if not items:
        return 0

    conn = get_db_connection()
    cursor = conn.cursor()
    new_discoveries = 0

    for item in items:
        repo_id = str(item.get("id"))
        cursor.execute("SELECT 1 FROM repositories WHERE id = %s", (repo_id,))
        if not cursor.fetchone():
            new_discoveries += 1

        cursor.execute(
            """
            INSERT INTO repositories (id, full_name, stars, description, html_url, language, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE 
            SET full_name = EXCLUDED.full_name,
                stars = EXCLUDED.stars,
                description = EXCLUDED.description,
                html_url = EXCLUDED.html_url,
                language = EXCLUDED.language,
                updated_at = EXCLUDED.updated_at
            """,
            (
                repo_id,
                item.get("full_name"),
                item.get("stargazers_count"),
                item.get("description") or "Aucune description.",
                item.get("html_url"),
                item.get("language") or "Non specifiee",
                item.get("updated_at"),
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


def save_book(repo_id, title, url, category):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO books (repo_id, title, url, category)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (url) DO UPDATE 
            SET title = EXCLUDED.title,
                category = EXCLUDED.category
            """,
            (repo_id, title, url, category)
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


def get_repositories():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT id, full_name, stars, description, html_url, language, updated_at
            FROM repositories 
            ORDER BY stars DESC
            """
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        logging.error(f"Erreur get_repositories: {e}")
        return []


def get_books(search_query=None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        if search_query:
            cursor.execute(
                """
                SELECT b.id, b.title, b.url, b.category, r.full_name AS repo_name, r.html_url AS repo_url, b.is_dead, b.last_checked
                FROM books b 
                LEFT JOIN repositories r ON b.repo_id = r.id 
                WHERE b.title ILIKE %s OR b.category ILIKE %s
                ORDER BY b.discovered_at DESC
                """,
                (f"%{search_query}%", f"%{search_query}%")
            )
        else:
            cursor.execute(
                """
                SELECT b.id, b.title, b.url, b.category, r.full_name AS repo_name, r.html_url AS repo_url, b.is_dead, b.last_checked
                FROM books b 
                LEFT JOIN repositories r ON b.repo_id = r.id 
                ORDER BY b.discovered_at DESC
                """
            )

        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        logging.error(f"Erreur get_books: {e}")
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
        logging.error(f"Erreur get_books_to_verify: {e}")
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
        logging.error(f"Erreur update_book_status: {e}")
