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
DB_PASSWORD = os.getenv("DB_PASSWORD") or "cyberpass"
if DB_PASSWORD == "cyberpass":
    logging.warning("DB_PASSWORD not set — using default 'cyberpass' (insecure for production)")


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
            security_verdict VARCHAR(20),
            security_details TEXT,
            security_scan_date TIMESTAMP,
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'repositories' AND column_name = 'security_verdict'
            ) THEN
                ALTER TABLE repositories ADD COLUMN security_verdict VARCHAR(20);
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'repositories' AND column_name = 'security_details'
            ) THEN
                ALTER TABLE repositories ADD COLUMN security_details TEXT;
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'repositories' AND column_name = 'security_scan_date'
            ) THEN
                ALTER TABLE repositories ADD COLUMN security_scan_date TIMESTAMP;
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'repositories' AND column_name = 'vitality_score'
            ) THEN
                ALTER TABLE repositories ADD COLUMN vitality_score INTEGER DEFAULT 0;
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'repositories' AND column_name = 'semantic_category'
            ) THEN
                ALTER TABLE repositories ADD COLUMN semantic_category VARCHAR(30);
            END IF;
        END $$;
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cyber_news (
            id SERIAL PRIMARY KEY,
            title VARCHAR(500) NOT NULL,
            link VARCHAR(1000) UNIQUE NOT NULL,
            summary TEXT,
            source_name VARCHAR(100),
            category VARCHAR(50),
            published TIMESTAMP,
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news_repo_correlation (
            id SERIAL PRIMARY KEY,
            news_id INTEGER REFERENCES cyber_news(id) ON DELETE CASCADE,
            repo_id VARCHAR(50) REFERENCES repositories(id) ON DELETE CASCADE,
            relevance_score INTEGER DEFAULT 0,
            match_type VARCHAR(50),
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(news_id, repo_id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS discovered_keywords (
            id SERIAL PRIMARY KEY,
            term VARCHAR(150) UNIQUE NOT NULL,
            category_guess VARCHAR(30),
            score FLOAT DEFAULT 0,
            sources INTEGER DEFAULT 0,
            source_samples TEXT,
            status VARCHAR(20) DEFAULT 'pending',
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reviewed_at TIMESTAMP
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

    from semantic_classifier import classify_semantic

    conn = get_db_connection()
    cursor = conn.cursor()
    new_discoveries = 0

    for item in items:
        repo_id = str(item.get("id"))
        cursor.execute("SELECT 1 FROM repositories WHERE id = %s", (repo_id,))
        if not cursor.fetchone():
            new_discoveries += 1

        description = item.get("description") or ""
        sem_cat, _ = classify_semantic(description, item.get("full_name") or "")

        cursor.execute(
            """
            INSERT INTO repositories (id, full_name, stars, description, html_url, language, updated_at, semantic_category)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE 
            SET full_name = EXCLUDED.full_name,
                stars = EXCLUDED.stars,
                description = EXCLUDED.description,
                html_url = EXCLUDED.html_url,
                language = EXCLUDED.language,
                updated_at = EXCLUDED.updated_at,
                semantic_category = EXCLUDED.semantic_category
            """,
            (
                repo_id,
                item.get("full_name"),
                item.get("stargazers_count"),
                item.get("description") or "Aucune description.",
                item.get("html_url"),
                item.get("language") or "Non specifiee",
                item.get("updated_at"),
                sem_cat,
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


def _parse_rss_date(date_str: str) -> str | None:
    """Parse RSS date formats to PostgreSQL timestamp."""
    if not date_str:
        return None
    try:
        clean = date_str.strip()
        for fmt in [
            '%a, %d %b %Y %H:%M:%S %z',
            '%a, %d %b %Y %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%d',
        ]:
            try:
                import datetime
                dt = datetime.datetime.strptime(clean[:25], fmt)
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            except (ValueError, IndexError):
                continue
        return clean[:19].replace('T', ' ')
    except Exception:
        return None


def save_cyber_news(items: list[dict]) -> int:
    if not items:
        return 0
    saved = 0
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        for item in items:
            published = _parse_rss_date(item.get("published", ""))
            try:
                cursor.execute("""
                    INSERT INTO cyber_news (title, link, summary, source_name, category, published)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (link) DO NOTHING
                """, (
                    item["title"][:500],
                    item["link"][:1000],
                    item.get("summary", "")[:2000],
                    item.get("source_name", "unknown"),
                    item.get("category", "general"),
                    published,
                ))
                if cursor.rowcount > 0:
                    saved += 1
            except Exception:
                pass
        conn.commit()
        cursor.close()
        conn.close()
        return saved
    except Exception as e:
        logging.error(f"Erreur save_cyber_news: {e}")
        return 0


def backfill_semantic_categories(batch_size: int = 200) -> int:
    """Calcule la categorie semantique pour les repos qui n'en ont pas."""
    try:
        from semantic_classifier import classify_semantic
        conn = get_db_connection()
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


def save_discovered_keywords(keywords: list[dict]) -> int:
    """Sauvegarde les mots-clés découverts par le miner."""
    if not keywords:
        return 0
    try:
        conn = get_db_connection()
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


def get_pending_keywords(limit: int = 100, min_score: float = 0.0) -> list[dict]:
    try:
        conn = get_db_connection()
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
        conn = get_db_connection()
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
        conn = get_db_connection()
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
        conn = get_db_connection()
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


def get_cyber_news(limit: int = 20) -> list[dict]:
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT title, link, summary, source_name, category, published, discovered_at
            FROM cyber_news
            ORDER BY COALESCE(published, discovered_at) DESC
            LIMIT %s
        """, (limit,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        logging.error(f"Erreur get_cyber_news: {e}")
        return []


def correlate_news_with_repos():
    """Corrèle les actualités cyber avec les dépôts existants."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT cn.id, cn.title, cn.summary, cn.category
            FROM cyber_news cn
            WHERE NOT EXISTS (
                SELECT 1 FROM news_repo_correlation nrc WHERE nrc.news_id = cn.id
            )
            ORDER BY cn.published DESC
            LIMIT 50
        """)
        news_items = cursor.fetchall()
        if not news_items:
            cursor.close()
            conn.close()
            return 0

        # Extract CVE IDs and keywords from news
        import re
        cve_pattern = re.compile(r'CVE-\d{4}-\d{4,7}', re.IGNORECASE)

        cursor.execute("SELECT id, full_name, description, language FROM repositories")
        all_repos = cursor.fetchall()
        repo_data = []
        for r in all_repos:
            text = ((r[1] or '') + ' ' + (r[2] or '') + ' ' + (r[3] or '')).lower()
            repo_data.append((r[0], text, r[1] or ''))

        total_correlations = 0
        for news_id, title, summary, category in news_items:
            news_text = ((title or '') + ' ' + (summary or '')).lower()
            cves = set(cve_pattern.findall(news_text))
            news_words = {w for w in re.sub(r'[^a-z0-9\-]', ' ', news_text).split() if len(w) > 3}

            for repo_id, repo_text, repo_name in repo_data:
                score = 0
                match_type = None

                # CVE match (strong signal)
                if cves:
                    repo_cves = cve_pattern.findall(repo_text)
                    matching_cves = cves & set(repo_cves)
                    if matching_cves:
                        score += 50
                        match_type = 'cve'

                # Category match
                if category and category != 'general':
                    if category in repo_text:
                        score += 20
                        match_type = match_type or 'category'

                # Keyword overlap
                repo_words = {w for w in repo_text.split() if len(w) > 3}
                overlap = news_words & repo_words
                if len(overlap) >= 3:
                    score += min(30, len(overlap) * 3)
                    match_type = match_type or 'keyword'

                # Repo name contains news keyword
                for w in news_words:
                    if w in repo_name.lower() and len(w) > 4:
                        score += 15
                        match_type = match_type or 'name_match'
                        break

                if score >= 20:
                    try:
                        cursor.execute("""
                            INSERT INTO news_repo_correlation (news_id, repo_id, relevance_score, match_type)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (news_id, repo_id) DO NOTHING
                        """, (news_id, repo_id, min(100, score), match_type))
                        if cursor.rowcount > 0:
                            total_correlations += 1
                    except Exception:
                        pass

        conn.commit()
        cursor.close()
        conn.close()
        if total_correlations:
            logging.info(f"🔗 {total_correlations} corrélation(s) news→repos créée(s)")
        return total_correlations
    except Exception as e:
        logging.error(f"Erreur correlate_news_with_repos: {e}")
        return 0


def get_news_with_correlations(limit: int = 15) -> list[dict]:
    """Retourne les news avec leurs repos corrélés."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT cn.id, cn.title, cn.link, cn.summary, cn.source_name,
                   cn.category, cn.published, cn.discovered_at
            FROM cyber_news cn
            ORDER BY COALESCE(cn.published, cn.discovered_at) DESC
            LIMIT %s
        """, (limit,))
        news_rows = cursor.fetchall()
        news_list = [dict(r) for r in news_rows]

        if news_list:
            ids = tuple(n['id'] for n in news_list)
            cursor.execute("""
                SELECT nrc.news_id, r.full_name, r.html_url, r.stars,
                       r.description, r.language, r.security_verdict,
                       r.vitality_score, nrc.relevance_score, nrc.match_type
                FROM news_repo_correlation nrc
                JOIN repositories r ON r.id = nrc.repo_id
                WHERE nrc.news_id IN %s
                ORDER BY nrc.relevance_score DESC
            """, (ids,))
            corr_rows = cursor.fetchall()
            corr_map: dict[int, list[dict]] = {}
            for c in corr_rows:
                corr_map.setdefault(c['news_id'], []).append({
                    'name': c['full_name'],
                    'url': c['html_url'],
                    'stars': c['stars'],
                    'desc': c['description'],
                    'lang': c['language'] or '?',
                    'security_verdict': c['security_verdict'],
                    'vitality_score': c['vitality_score'] or 0,
                    'relevance': c['relevance_score'],
                    'match_type': c['match_type'],
                })

            for n in news_list:
                n['correlated_repos'] = corr_map.get(n['id'], [])

        cursor.close()
        conn.close()
        return news_list
    except Exception as e:
        logging.error(f"Erreur get_news_with_correlations: {e}")
        return []


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


def recalculate_vitality_scores():
    """Recalcule le score de vitalité pour tous les dépôts."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, stars, updated_at, description, security_verdict, readme_parsed
            FROM repositories
        """)
        rows = cursor.fetchall()
        now = __import__('datetime').datetime.now()
        updated = 0
        for row in rows:
            repo_id, stars, updated_at, desc, verdict, readme_parsed = row
            stars = stars or 0
            score = 0
            # Stars (0-35 points) — log scale
            if stars > 0:
                score += min(35, int(10 * __import__('math').log10(stars + 1)))
            # Recency (0-30 points)
            if updated_at:
                try:
                    updated_dt = __import__('datetime').datetime.strptime(updated_at[:19], '%Y-%m-%dT%H:%M:%S')
                    days_since = (now - updated_dt).days
                    if days_since <= 30:
                        score += 30
                    elif days_since <= 90:
                        score += 25
                    elif days_since <= 180:
                        score += 20
                    elif days_since <= 365:
                        score += 15
                    elif days_since <= 730:
                        score += 8
                    else:
                        score += 3
                except (ValueError, IndexError):
                    score += 10
            # Security verdict (0-20 points)
            if verdict == 'Sain':
                score += 20
            elif verdict == 'Suspect':
                score += 10
            elif verdict == 'Critique':
                score += 0
            else:
                score += 5
            # Description quality (0-10 points)
            if desc and len(desc) > 20:
                score += 5 if len(desc) > 100 else 3
            else:
                score += 0
            # Readme parsed (0-5 points)
            if readme_parsed:
                score += 5
            score = min(100, max(0, score))
            cursor.execute("UPDATE repositories SET vitality_score = %s WHERE id = %s", (score, repo_id))
            updated += 1
        conn.commit()
        cursor.close()
        conn.close()
        logging.info(f"✅ Scores de vitalité recalculés pour {updated} dépôt(s)")
        return updated
    except Exception as e:
        logging.error(f"Erreur recalculate_vitality_scores: {e}")
        return 0


def get_frontend_stats():
    """Retourne les stats au format attendu par le frontend React."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM repositories")
        total_repos = cursor.fetchone()[0]
        cursor.execute("SELECT COALESCE(SUM(stars), 0) FROM repositories")
        total_stars = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT language) FROM repositories WHERE language IS NOT NULL AND language != 'Non specifiee'")
        languages = cursor.fetchone()[0]
        cursor.execute("SELECT language, COUNT(*) FROM repositories WHERE language IS NOT NULL AND language != 'Non specifiee' GROUP BY language ORDER BY COUNT(*) DESC")
        lang_dist = dict(cursor.fetchall())
        cursor.execute("SELECT MAX(discovered_at) FROM repositories")
        last_scan = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM repositories WHERE security_verdict = 'Critique'")
        critique = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM repositories WHERE security_verdict = 'Suspect'")
        suspect = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM repositories WHERE security_verdict IS NULL")
        unscanned = cursor.fetchone()[0]
        cursor.execute("SELECT COALESCE(AVG(vitality_score), 0) FROM repositories")
        avg_vitality = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM repositories WHERE vitality_score >= 70")
        top_vitality = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM repositories WHERE vitality_score < 30 AND vitality_score > 0")
        low_vitality = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM repositories WHERE vitality_score = 0")
        dead_vitality = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return (total_repos, int(total_stars), languages, lang_dist, last_scan,
                critique, suspect, unscanned, avg_vitality, top_vitality, low_vitality, dead_vitality)
    except Exception as e:
        logging.error(f"Erreur get_frontend_stats: {e}")
        return 0, 0, 0, {}, None, 0, 0, 0, 0, 0, 0, 0


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


def get_repos_frontend(sort_by: str = "stars"):
    """Retourne les repos au format attendu par le frontend React."""
    from nlp_processor import generate_synopsis
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        order_map = {
            "stars": "stars DESC",
            "vitality": "vitality_score DESC, stars DESC",
            "updated": "updated_at DESC NULLS LAST",
            "name": "full_name ASC",
        }
        order_clause = order_map.get(sort_by, "stars DESC")
        cursor.execute(
            f"""
            SELECT full_name AS name, description AS desc, stars,
                   language AS lang, html_url AS url, updated_at AS updated,
                   security_verdict, vitality_score, semantic_category
            FROM repositories
            ORDER BY {order_clause}
            """
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        repos = []
        for r in rows:
            d = dict(r)
            d["created"] = d.get("updated", "")
            d["size_kb"] = 0
            d["vitality_score"] = d.get("vitality_score") or 0
            d["synopsis"] = generate_synopsis(
                description=d.get("desc") or "",
                lang=d.get("lang") or "",
                stars=d.get("stars") or 0,
                verdict=d.get("security_verdict"),
                vitality=d.get("vitality_score"),
                semantic_category=d.get("semantic_category"),
            )
            repos.append(d)
        return repos
    except Exception as e:
        logging.error(f"Erreur get_repos_frontend: {e}")
        return []


def search_repos_frontend(q: str = "", page: int = 1, per_page: int = 50, sort_by: str = "stars", vitality_min: int = 0):
    """Recherche et pagination des repos pour le frontend React."""
    try:
        repos = get_repos_frontend(sort_by)
        if vitality_min > 0:
            repos = [r for r in repos if (r.get("vitality_score") or 0) >= vitality_min]
        if q:
            ql = q.lower()
            repos = [r for r in repos if ql in (r.get("name") or "").lower()
                     or ql in (r.get("desc") or "").lower()
                     or ql in (r.get("lang") or "").lower()]
        total = len(repos)
        offset = (page - 1) * per_page
        page_repos = repos[offset:offset + per_page]
        return page_repos, total
    except Exception as e:
        logging.error(f"Erreur search_repos_frontend: {e}")
        return [], 0


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


def get_repos_without_sast(limit=20):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, full_name, html_url
            FROM repositories
            WHERE security_verdict IS NULL
            LIMIT %s
            """,
            (limit,)
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    except Exception as e:
        logging.error(f"Erreur get_repos_without_sast: {e}")
        return []


def update_repo_security_verdict(repo_id, verdict, details=None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE repositories
            SET security_verdict = %s,
                security_details = %s,
                security_scan_date = CURRENT_TIMESTAMP
            WHERE id = %s
            """,
            (verdict, details, repo_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        logging.error(f"Erreur update_repo_security_verdict: {e}")
