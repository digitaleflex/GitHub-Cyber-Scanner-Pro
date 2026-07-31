"""Database access layer — re-exports all domain modules for backward compat."""

from .connection import get_db_connection
from .schema import init_db
from .etag import save_etag_to_cache, get_etag_from_cache
from .repos import (
    save_repositories, save_repo_issues, save_repo_commits,
    get_unharvested_repositories, get_unprocessed_repositories,
    mark_repo_as_parsed, recalculate_vitality_scores,
    get_repos_without_sast, update_repo_security_verdict,
    get_repositories, get_repos_frontend, search_repos_frontend,
)
from .cves import save_cve_entries, search_cves
from .books import save_book, get_books, get_books_to_verify, update_book_status
from .keywords import (
    save_discovered_keywords, get_keywords, get_pending_keywords,
    get_approved_keywords, approve_keyword, auto_approve_keywords,
    backfill_semantic_categories,
)
from .stats import count_total_data_points, get_stats, get_frontend_stats
from .search import (
    _SEARCH_TYPES, _SELECT_FROM, _SELECT_COLS,
    _search_clauses, _order_for, unified_search,
)
