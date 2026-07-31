import logging
import src.db.connection as _conn
from psycopg2.extras import RealDictCursor
from typing import Dict
import datetime


def save_repositories(items):
    if not items:
        return 0

    from semantic_classifier import classify_semantic

    conn = _conn.get_db_connection()
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


SECURITY_ISSUE_KEYWORDS = [
    "vulnerability", "cve", "exploit", "security", "xss", "sqli", "rce", "csrf",
    "ssrf", "injection", "overflow", "malware", "backdoor", "auth", "bypass",
    "leak", "secret", "token", "credential", "payload", "0day", "zeroday",
    "vuln", "breach", "attack", "threat", "ransomware", "trojan", "rootkit",
]

def save_repo_issues(repo_id, issues):
    if not issues:
        return 0
    conn = _conn.get_db_connection()
    cursor = conn.cursor()
    count = 0
    for it in issues:
        title = (it.get("title") or "")
        body = (it.get("body") or "")[:5000]
        text = (title + " " + body).lower()
        is_sec = any(k in text for k in SECURITY_ISSUE_KEYWORDS)
        labels = ",".join(l.get("name", "") for l in (it.get("labels") or []) if isinstance(l, dict))
        author = (it.get("user") or {}).get("login", "")
        try:
            cursor.execute(
                """
                INSERT INTO repo_issues
                    (repo_id, issue_number, title, body, state, labels, author, created_at, updated_at, html_url, is_security)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (repo_id, issue_number) DO NOTHING
                """,
                (
                    repo_id, it.get("number"), title, body, it.get("state"),
                    labels, author, it.get("created_at"), it.get("updated_at"),
                    it.get("html_url"), is_sec,
                )
            )
            if cursor.rowcount > 0:
                count += 1
        except Exception as e:
            logging.error(f"Erreur save issue {repo_id}: {e}")
    cursor.execute("UPDATE repositories SET issues_harvested = (SELECT COUNT(*) FROM repo_issues WHERE repo_id=%s) WHERE id=%s", (repo_id, repo_id))
    conn.commit()
    cursor.close()
    conn.close()
    return count

def save_repo_commits(repo_id, commits):
    if not commits:
        return 0
    conn = _conn.get_db_connection()
    cursor = conn.cursor()
    count = 0
    for c in commits:
        sha = c.get("sha")
        if not sha:
            continue
        commit = c.get("commit", {})
        msg = (commit.get("message") or "")[:2000]
        author = (commit.get("author") or {}).get("name", "") if commit.get("author") else (c.get("author") or {}).get("login", "")
        date = commit.get("committer", {}).get("date", "") if commit.get("committer") else c.get("commit", {}).get("committer", {}).get("date", "")
        try:
            cursor.execute(
                """
                INSERT INTO repo_commits (repo_id, sha, message, author, date, html_url)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (repo_id, sha) DO NOTHING
                """,
                (repo_id, sha, msg, author, date, c.get("html_url"))
            )
            if cursor.rowcount > 0:
                count += 1
        except Exception as e:
            logging.error(f"Erreur save commit {repo_id}: {e}")
    cursor.execute("UPDATE repositories SET commits_harvested = (SELECT COUNT(*) FROM repo_commits WHERE repo_id=%s) WHERE id=%s", (repo_id, repo_id))
    conn.commit()
    cursor.close()
    conn.close()
    return count

def get_unharvested_repositories(limit=50):
    conn = _conn.get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, full_name FROM repositories WHERE issues_harvested = 0 ORDER BY stars DESC NULLS LAST LIMIT %s",
        (limit,)
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def get_unprocessed_repositories():
    conn = _conn.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name FROM repositories WHERE readme_parsed = 0")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def mark_repo_as_parsed(repo_id, readme_parsed=1):
    conn = _conn.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE repositories SET readme_parsed = %s WHERE id = %s", (readme_parsed, repo_id))
    conn.commit()
    cursor.close()
    conn.close()

def recalculate_vitality_scores():
    """Recalcule le score de vitalité pour tous les dépôts."""
    try:
        conn = _conn.get_db_connection()
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

def get_repos_without_sast(limit=20):
    try:
        conn = _conn.get_db_connection()
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
        conn = _conn.get_db_connection()
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

def get_repositories():
    try:
        conn = _conn.get_db_connection()
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
        conn = _conn.get_db_connection()
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

def search_repos_frontend(q: str = "", page: int = 1, per_page: int = 50, sort_by: str = "stars", vitality_min: int = 0, security_verdict: str = None):
    """Recherche et pagination des repos pour le frontend React."""
    try:
        repos = get_repos_frontend(sort_by)
        if vitality_min > 0:
            repos = [r for r in repos if (r.get("vitality_score") or 0) >= vitality_min]
        if security_verdict:
            repos = [r for r in repos if (r.get("security_verdict") or "") == security_verdict]
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
