import logging
import os
import time

import requests

from src import database

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

PER_PAGE = 100
PAGE_DELAY = 0.6


def _api_get(url, params=None, max_retries=4):
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    for _ in range(max_retries):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=20)
            if r.status_code == 200:
                return r.json(), False
            if r.status_code == 403:
                reset = r.headers.get("X-RateLimit-Reset")
                wait = max(1, float(reset) - time.time()) + 5 if reset else 60
                logging.warning(f"⏸️ Rate limit artifacts. Pause {int(wait)}s")
                time.sleep(wait)
                continue
            if r.status_code in (404, 410):
                return [], False
            time.sleep(3)
        except Exception as e:
            logging.error(f"❌ Erreur API artifacts {url}: {e}")
            time.sleep(5)
    return [], True


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


def harvest_batch(limit=50, max_issues_pages=3, max_commits_pages=3):
    """Récolte artifacts pour un lot de repos non encore récoltés."""
    repos = database.get_unharvested_repositories(limit)
    total_issues = 0
    total_commits = 0
    for repo_id, full_name in repos:
        ni, nc = harvest_repo(repo_id, full_name, max_issues_pages, max_commits_pages)
        total_issues += ni
        total_commits += nc
        logging.info(f"🌾 {full_name}: +{ni} issues, +{nc} commits ({total_issues}/{total_commits} cumul)")
        time.sleep(0.3)
    logging.info(f"✅ Harvest batch: {total_issues} issues, {total_commits} commits sur {len(repos)} repos")
    return {"issues": total_issues, "commits": total_commits, "repos": len(repos)}
