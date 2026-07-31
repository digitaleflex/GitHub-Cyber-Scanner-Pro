import logging
import src.db.connection as _conn
from psycopg2.extras import RealDictCursor
from typing import Dict


_SEARCH_TYPES = ("repo", "cve", "book", "keyword")

_SELECT_FROM = {
    "repo": "repositories",
    "cve": "cve_entries",
    "book": "books b LEFT JOIN repositories r ON b.repo_id = r.id",
    "keyword": "discovered_keywords",
}

_SELECT_COLS = {
    "repo": "full_name AS name, description AS desc, stars, language AS lang, "
            "html_url AS url, security_verdict, vitality_score, 'repo' AS result_type",
    "cve": "cve_id AS name, description AS desc, severity, cvss_score, "
           "published, 'cve' AS result_type",
    "book": "b.title AS name, b.url, b.category, r.full_name AS repo_name, "
            "'book' AS result_type",
    "keyword": "term AS name, category_guess AS category, score, status, "
               "'keyword' AS result_type",
}

def _search_clauses(rt, q, like, language=None, severity=None, security_verdict=None, category=None):
    """Construit la clause WHERE (et ses parametres) pour un type de resultat."""
    if rt == "repo":
        clauses, params = ["full_name ILIKE %s OR description ILIKE %s"], [like, like]
        if language:
            clauses.append("language ILIKE %s")
            params.append(f"%{language}%")
        if security_verdict:
            clauses.append("security_verdict = %s")
            params.append(security_verdict)
    elif rt == "cve":
        clauses, params = ["cve_id ILIKE %s OR description ILIKE %s OR weaknesses ILIKE %s"], [like, like, like]
        if severity:
            clauses.append("severity ILIKE %s")
            params.append(f"%{severity}%")
    elif rt == "book":
        clauses, params = ["b.tsv_content @@ plainto_tsquery('simple', %s) OR b.title ILIKE %s"], [q, like]
        if category:
            clauses.append("b.category ILIKE %s")
            params.append(f"%{category}%")
    elif rt == "keyword":
        clauses, params = ["term ILIKE %s"], [like]
        if category:
            clauses.append("category_guess ILIKE %s")
            params.append(f"%{category}%")
    else:
        return "1 = 0", []
    return " AND ".join(clauses), params

def _order_for(rt, sort, q):
    """Retourne (ORDER BY, params) selon le type et le tri. La pertinence utilise la similarite pg_trgm."""
    if rt == "repo":
        if sort == "stars":
            return "stars DESC, updated_at DESC NULLS LAST", []
        if sort == "updated":
            return "updated_at DESC NULLS LAST, stars DESC", []
        return "GREATEST(similarity(full_name, %s), similarity(description, %s)) DESC, stars DESC", [q, q]
    if rt == "cve":
        if sort == "cvss":
            return "cvss_score DESC NULLS LAST, published DESC NULLS LAST", []
        if sort == "published":
            return "published DESC NULLS LAST", []
        return "GREATEST(similarity(cve_id, %s), similarity(description, %s)) DESC, cvss_score DESC NULLS LAST", [q, q]
    if rt == "book":
        return "b.title ASC", []
    return "score DESC NULLS LAST, term ASC", []

def unified_search(q="", limit=20, page=1, types=None, language=None, severity=None,
                   security_verdict=None, category=None, sort="relevance"):
    """Recherche unifiee intelligente sur repos/CVEs/books/keywords.

    Retourne un dict : {query, total, page, per_page, pages, results, facets}.
    Filtres : types, language, severity, security_verdict, category.
    Tri : relevance (similarite pg_trgm), stars, updated, cvss, published.
    """
    per_page = max(1, min(int(limit), 100))
    page = max(1, int(page))
    empty = {
        "query": q, "total": 0, "page": page, "per_page": per_page, "pages": 0,
        "results": [],
        "facets": {"types": {t: 0 for t in _SEARCH_TYPES}, "languages": [], "severities": {}, "categories": []},
    }
    if not q or len(q) < 2:
        return empty
    like = f"%{q}%"
    allowed = set(types or list(_SEARCH_TYPES)) & set(_SEARCH_TYPES)
    offset = (page - 1) * per_page
    try:
        conn = _conn.get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        results = []
        total = 0
        type_counts = {t: 0 for t in _SEARCH_TYPES}

        for rt in _SEARCH_TYPES:
            where, wparams = _search_clauses(rt, q, like, language, severity, security_verdict, category)
            cursor.execute(f"SELECT COUNT(*) AS c FROM {_SELECT_FROM[rt]} WHERE {where}", wparams)
            type_counts[rt] = cursor.fetchone()["c"] or 0

        for rt in _SEARCH_TYPES:
            if rt not in allowed:
                continue
            where, wparams = _search_clauses(rt, q, like, language, severity, security_verdict, category)
            order, oparams = _order_for(rt, sort, q)
            cursor.execute(
                f"SELECT {_SELECT_COLS[rt]} FROM {_SELECT_FROM[rt]} WHERE {where} ORDER BY {order} LIMIT %s OFFSET %s",
                wparams + oparams + [per_page, offset],
            )
            results.extend(cursor.fetchall())
            total += type_counts[rt]

        facets = {"types": type_counts, "languages": [], "severities": {}, "categories": []}

        if type_counts["repo"] > 0 or "repo" in allowed:
            where, wparams = _search_clauses("repo", q, like, None, None, security_verdict, None)
            cursor.execute(
                f"SELECT language AS lang, COUNT(*) AS count FROM repositories WHERE {where} "
                "GROUP BY language ORDER BY count DESC LIMIT 10",
                wparams,
            )
            facets["languages"] = [dict(r) for r in cursor.fetchall()]

        if type_counts["cve"] > 0 or "cve" in allowed:
            where, wparams = _search_clauses("cve", q, like, None, severity, None, None)
            cursor.execute(
                f"SELECT COALESCE(severity, 'N/A') AS severity, COUNT(*) AS count FROM cve_entries WHERE {where} "
                "GROUP BY severity ORDER BY count DESC",
                wparams,
            )
            facets["severities"] = {r["severity"]: r["count"] for r in cursor.fetchall()}

        if "book" in allowed or "keyword" in allowed:
            cursor.execute(
                "SELECT category, COUNT(*) AS count FROM books GROUP BY category ORDER BY count DESC LIMIT 8"
            )
            facets["categories"] = [dict(r) for r in cursor.fetchall()]

        cursor.close()
        conn.close()

        return {
            "query": q,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": max(1, (total + per_page - 1) // per_page) if total else 0,
            "results": [dict(r) for r in results],
            "facets": facets,
        }
    except Exception as e:
        logging.error(f"Erreur unified_search: {e}")
        return empty
