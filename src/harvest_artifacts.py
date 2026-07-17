import json
import logging
import os
import time

from src import database
from src import github_client

PER_PAGE = 100
PAGE_DELAY = 0.3

STATUS_FILE = os.getenv("DATA_DIR", "data") + "/harvest_status.json"


def _write_status(status):
    try:
        os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)
        with open(STATUS_FILE, "w") as f:
            json.dump(status, f)
    except Exception:
        pass


def get_harvest_status():
    try:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE) as f:
                return json.load(f)
    except Exception:
        pass
    return {"running": False, "issues": 0, "commits": 0, "repos": 0, "current": None, "error": None}


def _api_get(url, params=None, max_retries=6):
    return github_client.get_json(url, params=params)


def harvest_repo(repo_id, full_name, max_issues_pages=3, max_commits_pages=3):
    """Récupère issues + commits ouverts/fermés pour un repo et les stocke."""
    new_issues = 0
    new_commits = 0

    # Issues (state=all pour couvrir ouvert+fermé)
    for page in range(1, max_issues_pages + 1):
        items, rate_hit = _api_get(
            f"https://api.github.com/repos/{full_name}/issues",
            params={"state": "all", "per_page": PER_PAGE, "page": page,
                    "sort": "updated", "direction": "desc"}
        )
        if rate_hit:
            break
        # Filtrer les PR (issues avec pull_request)
        issues = [i for i in items if "pull_request" not in i]
        if not issues:
            break
        saved = database.save_repo_issues(repo_id, issues)
        new_issues += saved
        if len(issues) < PER_PAGE:
            break
        time.sleep(PAGE_DELAY)

    # Commits
    for page in range(1, max_commits_pages + 1):
        items, rate_hit = _api_get(
            f"https://api.github.com/repos/{full_name}/commits",
            params={"per_page": PER_PAGE, "page": page}
        )
        if rate_hit:
            break
        if not items:
            break
        saved = database.save_repo_commits(repo_id, items)
        new_commits += saved
        if len(items) < PER_PAGE:
            break
        time.sleep(PAGE_DELAY)

    return new_issues, new_commits


def harvest_batch(limit=50, max_issues_pages=3, max_commits_pages=3, continuous=True, max_repos=None):
    """Récolte artifacts pour les repos non encore récoltés.

    Boucle par tranches de `limit` jusqu'à épuisement (ou max_repos atteint)
    pour monter en charge vers 1M de données.
    """
    total_issues = 0
    total_commits = 0
    total_repos = 0
    error = None
    _write_status({"running": True, "issues": 0, "commits": 0, "repos": 0, "current": None, "error": None})

    try:
        while True:
            repos = database.get_unharvested_repositories(limit)
            if not repos:
                break
            for repo_id, full_name in repos:
                ni, nc = harvest_repo(repo_id, full_name, max_issues_pages, max_commits_pages)
                total_issues += ni
                total_commits += nc
                total_repos += 1
                _write_status({"running": True, "issues": total_issues, "commits": total_commits,
                               "repos": total_repos, "current": full_name, "error": None})
                logging.info(f"🌾 {full_name}: +{ni} issues, +{nc} commits ({total_issues}/{total_commits} cumul)")
                time.sleep(0.3)
                if max_repos and total_repos >= max_repos:
                    break
            if max_repos and total_repos >= max_repos:
                break
    except Exception as e:
        error = str(e)
        logging.error(f"❌ Erreur harvest: {e}")

    _write_status({"running": False, "issues": total_issues, "commits": total_commits,
                   "repos": total_repos, "current": None, "error": error})
    logging.info(f"✅ Harvest batch: {total_issues} issues, {total_commits} commits sur {total_repos} repos")
    return {"issues": total_issues, "commits": total_commits, "repos": total_repos}
