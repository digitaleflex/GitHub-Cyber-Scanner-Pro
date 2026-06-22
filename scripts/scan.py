"""
Scan des nouveaux outils cybersecurite sur GitHub.
Configure GITHUB_TOKEN dans les secrets du repo.
"""

import requests
import json
import os
import hashlib
import sys
from datetime import datetime, timedelta

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
DB_FILE = "data/seen.json"


def load_seen():
    try:
        with open(DB_FILE) as f:
            return json.load(f)
    except:
        return []


def save_seen(seen):
    os.makedirs("data", exist_ok=True)
    with open(DB_FILE, "w") as f:
        json.dump(seen, f)


def github_search(query):
    r = requests.get(
        "https://api.github.com/search/repositories",
        params={"q": query, "sort": "stars", "per_page": 30},
        headers=HEADERS,
        timeout=30,
    )
    if r.status_code == 403:
        print(f"  Rate limit, skip: {query[:40]}")
        return []
    if r.status_code != 200:
        print(f"  Erreur {r.status_code}: {query[:40]}")
        return []
    return r.json().get("items", [])


def is_noise(repo):
    if not repo.get("description"):
        return True
    if repo["stargazers_count"] == 0 and repo["forks_count"] == 0:
        return True
    if repo.get("fork"):
        return True
    noise = ["awesome", "cheatsheet", "course", "tutorial",
             "interview", "roadmap", "notes", "list", "collection",
             "learning", "beginner", "resources"]
    desc = repo["description"].lower()
    return any(w in desc for w in noise)


def content_hash(repo):
    raw = f"{repo['full_name']}|{repo.get('description','')}"
    return hashlib.md5(raw.encode()).hexdigest()


def get_queries(days=7):
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    return [
        f"C2 framework pushed:>{since} stars:>1",
        f"phishing kit pushed:>{since} stars:>1",
        f"reverse shell pushed:>{since} stars:>1",
        f"credential stealer pushed:>{since} stars:>1",
        f"RAT malware pushed:>{since} stars:>1",
        f"exploit tool pushed:>{since} stars:>1",
        f"red team tool pushed:>{since} stars:>2",
        f"pentest tool pushed:>{since} stars:>2",
        f"malware analysis pushed:>{since} stars:>2",
        f"threat intel pushed:>{since} stars:>2",
        f"osint tool pushed:>{since} stars:>2",
        f"security tool pushed:>{since} stars:>3 language:go",
        f"security tool pushed:>{since} stars:>3 language:rust",
    ]


def scan(days=7):
    queries = get_queries(days)
    seen = load_seen()
    new_repos = []

    print(f"Scan des {days} derniers jours")
    print(f"Token GitHub: {'OK' if GITHUB_TOKEN else 'MANQUANT (rate limit: 10 req/min)'}")
    print()

    for q in queries:
        print(f"  {q[:55]}...")
        items = github_search(q)
        for repo in items:
            h = content_hash(repo)
            if h in seen:
                continue
            if is_noise(repo):
                continue
            seen.append(h)
            new_repos.append({
                "name": repo["full_name"],
                "desc": repo.get("description", "")[:120],
                "stars": repo["stargazers_count"],
                "lang": repo.get("language", "?"),
                "url": repo["html_url"],
                "created": repo["created_at"],
                "updated": repo["updated_at"],
                "size_kb": repo.get("size", 0),
            })

    save_seen(seen)
    return new_repos


if __name__ == "__main__":
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    repos = scan(days)

    print(f"\n{'='*60}")
    print(f"RESULTATS — {len(repos)} nouveaux repos")
    print(f"{'='*60}\n")

    repos.sort(key=lambda r: r["stars"], reverse=True)

    for i, r in enumerate(repos[:20], 1):
        print(f"{i:2d}. ★{r['stars']:4d} [{r['lang'] or '?':7s}] {r['name']}")
        print(f"    {r['desc']}")
        print()

    os.makedirs("data", exist_ok=True)
    with open("data/last_scan.json", "w") as f:
        json.dump(repos, f, indent=2)
