import logging
import src.db.connection as _conn
from psycopg2.extras import RealDictCursor
from typing import Dict


def save_discovered_keywords(keywords: list[dict]) -> int:
    """Sauvegarde les mots-clés découverts par le miner."""
    if not keywords:
        return 0
    try:
        conn = _conn.get_db_connection()
        cursor = conn.cursor()
        saved = 0
        for kw in keywords:
            term = kw.get("term", "")[:150].lower()
            if not term or len(term) < 3:
                continue
            try:
                cursor.execute(
                    """
                    INSERT INTO discovered_keywords (term, category_guess, score, sources, source_samples, status)
                    VALUES (%s, %s, %s, %s, %s, 'pending')
                    ON CONFLICT (term) DO UPDATE
                    SET score = GREATEST(discovered_keywords.score, EXCLUDED.score),
                        sources = EXCLUDED.sources,
                        source_samples = EXCLUDED.source_samples,
                        category_guess = COALESCE(EXCLUDED.category_guess, discovered_keywords.category_guess)
                    WHERE discovered_keywords.status = 'pending'
                    """,
                    (
                        term,
                        kw.get("category_guess"),
                        kw.get("score", 0),
                        kw.get("sources", 1),
                        kw.get("source_samples", ""),
                    )
                )
                if cursor.rowcount > 0:
                    saved += 1
            except Exception:
                pass
        conn.commit()
        cursor.close()
        conn.close()
        logging.info("Keyword miner: %d/%d candidats sauvegardes", saved, len(keywords))
        return saved
    except Exception as e:
        logging.error(f"Erreur save_discovered_keywords: {e}")
        return 0

def get_keywords(status: str = "pending", limit: int = 100, min_score: float = 0.0) -> list[dict]:
    try:
        conn = _conn.get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        if status == "all":
            cursor.execute(
                """
                SELECT term, category_guess, score, sources, source_samples, status, discovered_at, reviewed_at
                FROM discovered_keywords
                ORDER BY score DESC, sources DESC
                LIMIT %s
                """,
                (limit,)
            )
        else:
            cursor.execute(
                """
                SELECT term, category_guess, score, sources, source_samples, status, discovered_at, reviewed_at
                FROM discovered_keywords
                WHERE status = %s AND score >= %s
                ORDER BY score DESC, sources DESC
                LIMIT %s
                """,
                (status, min_score, limit)
            )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        logging.error(f"Erreur get_keywords: {e}")
        return []

def get_pending_keywords(limit: int = 100, min_score: float = 0.0) -> list[dict]:
    try:
        conn = _conn.get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT term, category_guess, score, sources, source_samples, discovered_at
            FROM discovered_keywords
            WHERE status = 'pending' AND score >= %s
            ORDER BY score DESC, sources DESC
            LIMIT %s
            """,
            (min_score, limit)
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        logging.error(f"Erreur get_pending_keywords: {e}")
        return []

def get_approved_keywords() -> list[dict]:
    try:
        conn = _conn.get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT term, category_guess, score
            FROM discovered_keywords
            WHERE status = 'approved'
            ORDER BY score DESC
            """
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        logging.error(f"Erreur get_approved_keywords: {e}")
        return []

def approve_keyword(term: str, status: str = "approved", category: str | None = None) -> bool:
    try:
        conn = _conn.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE discovered_keywords
            SET status = %s, reviewed_at = CURRENT_TIMESTAMP, category_guess = COALESCE(%s, category_guess)
            WHERE term = %s
            """,
            (status, category, term.lower())
        )
        conn.commit()
        updated = cursor.rowcount
        cursor.close()
        conn.close()
        return updated > 0
    except Exception as e:
        logging.error(f"Erreur approve_keyword: {e}")
        return False

def auto_approve_keywords(min_score: float = 0.75, min_sources: int = 3) -> int:
    """Approuve automatiquement les mots-clés très sûrs."""
    try:
        conn = _conn.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE discovered_keywords
            SET status = 'approved', reviewed_at = CURRENT_TIMESTAMP
            WHERE status = 'pending' AND score >= %s AND sources >= %s
            """,
            (min_score, min_sources)
        )
        conn.commit()
        updated = cursor.rowcount
        cursor.close()
        conn.close()
        logging.info("Keyword auto-approve: %d termes approuves", updated)
        return updated
    except Exception as e:
        logging.error(f"Erreur auto_approve_keywords: {e}")
        return 0

def backfill_semantic_categories(batch_size: int = 200) -> int:
    """Calcule la categorie semantique pour les repos qui n'en ont pas."""
    try:
        from semantic_classifier import classify_semantic
        conn = _conn.get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, full_name, description
            FROM repositories
            WHERE semantic_category IS NULL
            LIMIT %s
            """,
            (batch_size,)
        )
        rows = cursor.fetchall()
        updated = 0
        for repo_id, full_name, description in rows:
            sem_cat, _ = classify_semantic(description or "", full_name or "")
            cursor.execute(
                "UPDATE repositories SET semantic_category = %s WHERE id = %s",
                (sem_cat, repo_id)
            )
            updated += 1
        conn.commit()
        cursor.close()
        conn.close()
        logging.info("Backfill semantic_category: %d repos mis a jour", updated)
        return updated
    except Exception as e:
        logging.error(f"Erreur backfill_semantic_categories: {e}")
        return 0
