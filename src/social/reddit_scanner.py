"""Reddit Scanner — surveille r/netsec, r/cybersecurity, etc. (API gratuite, .json)."""
import logging
import re
import time

import requests

SUBREDDITS = [
    "netsec", "cybersecurity", "blueteamsec", "redteamsec",
    "osint", "malware", "ReverseEngineering", "hacking",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json",
}


def fetch_posts(subreddit: str, limit: int = 25) -> list[dict]:
    """Recupere les posts recents d'un subreddit."""
    try:
        r = requests.get(
            f"https://www.reddit.com/r/{subreddit}/new.json",
            params={"limit": limit},
            headers=HEADERS,
            timeout=15,
        )
        if r.status_code != 200:
            logging.warning(f"Reddit r/{subreddit}: HTTP {r.status_code}")
            return []
        posts = r.json().get("data", {}).get("children", [])
        results = []
        for p in posts:
            data = p["data"]
            if data.get("stickied"):
                continue
            results.append({
                "title": data["title"],
                "url": data["url"],
                "permalink": f"https://reddit.com{data['permalink']}",
                "score": data["score"],
                "subreddit": data["subreddit"],
                "created": data["created_utc"],
                "selftext": (data.get("selftext") or "")[:500],
            })
        return results
    except Exception as e:
        logging.warning(f"Reddit r/{subreddit}: {e}")
        return []


def extract_github_urls(posts: list[dict]) -> list[str]:
    """Extrait les URLs GitHub des posts."""
    urls = []
    for p in posts:
        text = p["title"] + " " + p["selftext"] + " " + p["url"]
        found = re.findall(r"https?://github\.com/[\w.-]+/[\w.-]+", text)
        urls.extend(found)
    return list(set(urls))


def run(limit_per_sub: int = 15) -> int:
    """Execute le scan Reddit. Retourne le nb de repos decouverts."""
    from src import database
    import src.github_client as gc

    all_urls = []
    for sub in SUBREDDITS:
        posts = fetch_posts(sub, limit_per_sub)
        gh_urls = extract_github_urls(posts)
        all_urls.extend(gh_urls)
        logging.info(f"📱 r/{sub}: {len(posts)} posts, {len(gh_urls)} URLs GitHub")
        time.sleep(1)

    # Decouvrir les repos GitHub mentionnes
    found = 0
    seen = set()
    for url in all_urls[:20]:
        # Extraire full_name
        m = re.search(r"github\.com/([\w.-]+/[\w.-]+)", url)
        if not m:
            continue
        full_name = m.group(1).rstrip("/")
        if full_name in seen:
            continue
        seen.add(full_name)
        # Verifier si deja en base
        conn = database.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM repositories WHERE full_name = %s", (full_name,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            continue
        cursor.close()
        conn.close()
        # Recuperer via GitHub API
        if gc.TOKENS:
            import random
            token = random.choice(gc.TOKENS)
            r = requests.get(
                f"https://api.github.com/repos/{full_name}",
                headers={"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"},
                timeout=10,
            )
            if r.status_code == 200:
                repo = r.json()
                database.save_repositories([{
                    "id": repo["id"],
                    "full_name": repo["full_name"],
                    "description": repo.get("description") or "",
                    "html_url": repo["html_url"],
                    "stargazers_count": repo.get("stargazers_count", 0),
                    "language": repo.get("language") or "",
                    "updated_at": repo.get("updated_at", ""),
                }])
                found += 1
    logging.info(f"📱 Reddit: {found} nouveaux repos decouverts")
    return found
