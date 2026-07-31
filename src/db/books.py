import logging
import src.db.connection as _conn
from psycopg2.extras import RealDictCursor
from typing import Dict


def save_book(repo_id, title, url, category, lemmas_str=None, type_ressource=None):
    conn = _conn.get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO books (repo_id, title, url, category, lemmas_str, type_ressource, tsv_content)
            VALUES (%s, %s, %s, %s, %s, %s, to_tsvector('simple', COALESCE(%s, '')))
            ON CONFLICT (url) DO UPDATE 
            SET title = EXCLUDED.title,
                category = EXCLUDED.category,
                lemmas_str = COALESCE(EXCLUDED.lemmas_str, books.lemmas_str),
                type_ressource = COALESCE(EXCLUDED.type_ressource, books.type_ressource),
                tsv_content = COALESCE(to_tsvector('simple', COALESCE(EXCLUDED.lemmas_str, '')), books.tsv_content)
            """,
            (repo_id, title, url, category, lemmas_str, type_ressource, lemmas_str)
        )
        conn.commit()
        return True
    except psycopg2.IntegrityError:
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def get_books(search_query=None):
    try:
        conn = _conn.get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        if search_query:
            cursor.execute(
                """
                SELECT b.id, b.title, b.url, b.category, b.type_ressource,
                       r.full_name AS repo_name, r.html_url AS repo_url,
                       b.is_dead, b.last_checked
                FROM books b
                LEFT JOIN repositories r ON b.repo_id = r.id
                WHERE b.tsv_content @@ plainto_tsquery('simple', %s)
                   OR b.title ILIKE %s
                   OR b.category ILIKE %s
                ORDER BY ts_rank(b.tsv_content, plainto_tsquery('simple', %s)) DESC,
                         b.discovered_at DESC
                """,
                (search_query, f"%{search_query}%", f"%{search_query}%", search_query)
            )
        else:
            cursor.execute(
                """
                SELECT b.id, b.title, b.url, b.category, b.type_ressource,
                       r.full_name AS repo_name, r.html_url AS repo_url,
                       b.is_dead, b.last_checked
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
        conn = _conn.get_db_connection()
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
        conn = _conn.get_db_connection()
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
