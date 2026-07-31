import logging
import src.db.connection as _conn



def count_total_data_points():
    try:
        conn = _conn.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM repositories")
        repos = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM repo_issues")
        issues = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM repo_commits")
        commits = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM books")
        books = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM discovered_keywords")
        keywords = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM cve_entries")
        cves = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return {
            "repositories": repos, "issues": issues, "commits": commits,
            "books": books, "keywords": keywords, "cves": cves,
            "total": repos + issues + commits + books + keywords + cves,
        }
    except Exception as e:
        logging.error(f"Erreur count_total_data_points: {e}")
        return {"total": 0}

def get_stats():
    try:
        conn = _conn.get_db_connection()
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

def get_frontend_stats():
    """Retourne les stats au format attendu par le frontend React."""
    try:
        conn = _conn.get_db_connection()
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
        cursor.execute("SELECT COUNT(*) FROM cve_entries")
        total_cves = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM discovered_keywords WHERE status='pending'")
        pending_keywords = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM repositories WHERE discovered_at >= NOW() - INTERVAL '24 hours'")
        new_repos_24h = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return (total_repos, int(total_stars), languages, lang_dist, last_scan,
                critique, suspect, unscanned, avg_vitality, top_vitality, low_vitality, dead_vitality,
                total_cves, pending_keywords, new_repos_24h)
    except Exception as e:
        logging.error(f"Erreur get_frontend_stats: {e}")
        return 0, 0, 0, {}, None, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
