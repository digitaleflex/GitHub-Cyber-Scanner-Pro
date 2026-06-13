import os
import json
import requests
import time
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
REPO = os.getenv("GITHUB_REPO", "VOTRE_USERNAME/cyber_scan_books")
TOKEN = os.getenv("GITHUB_ADMIN_TOKEN")

if not TOKEN:
    print("❌ Erreur: GITHUB_ADMIN_TOKEN manquant dans le fichier .env")
    exit(1)

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

API_URL = f"https://api.github.com/repos/{REPO}"

def load_backlog():
    with open("github_issues.json", "r", encoding="utf-8") as f:
        return json.load(f)

def get_existing_issues():
    """Récupère toutes les issues existantes (ouvertes et fermées)."""
    url = f"{API_URL}/issues"
    params = {"state": "all", "per_page": 100}
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code == 200:
        return response.json()
    return []

def create_milestone(title, description, due_on):
    url = f"{API_URL}/milestones"
    data = {"title": title, "description": description, "due_on": due_on, "state": "open"}
    response = requests.post(url, headers=HEADERS, json=data)
    if response.status_code == 201:
        print(f"✅ Milestone créé : {title}")
        return response.json()["number"]
    else:
        response = requests.get(url, headers=HEADERS)
        for m in response.json():
            if m["title"] == title:
                return m["number"]
    return None

def create_label(name, color, description):
    url = f"{API_URL}/labels"
    data = {"name": name, "color": color, "description": description}
    requests.post(url, headers=HEADERS, json=data)

def sync_issue(issue_data, milestone_number, existing_issues):
    """Crée ou met à jour une issue selon son état dans le JSON."""
    title = issue_data["title"]
    state = issue_data.get("state", "open")
    body = issue_data["body"]
    labels = issue_data["labels"]

    # Chercher si l'issue existe déjà
    existing = next((i for i in existing_issues if i["title"] == title), None)

    if existing:
        # Mise à jour de l'état
        url = f"{API_URL}/issues/{existing['number']}"
        data = {"state": state, "body": body}
        res = requests.patch(url, headers=HEADERS, json=data)
        if res.status_code == 200:
            status_emoji = "✅" if state == "closed" else "🔄"
            print(f"{status_emoji} Issue mise à jour ({state}) : {title}")
    else:
        # Création
        url = f"{API_URL}/issues"
        data = {
            "title": title,
            "body": body,
            "milestone": milestone_number,
            "labels": labels,
            "state": state
        }
        res = requests.post(url, headers=HEADERS, json=data)
        if res.status_code == 201:
            print(f"🚀 Issue créée : {title}")

def main():
    backlog = load_backlog()
    print(f"🔍 Synchronisation 'en ligne' sur : {REPO}")
    
    # 1. Labels
    for label in backlog["labels"]:
        create_label(label["name"], label["color"], label["description"])
    
    # 2. Milestones
    milestone_map = {}
    for m in backlog["milestones"]:
        m_num = create_milestone(m["title"], m["description"], m["due_on"])
        if m_num:
            milestone_map[m["title"]] = m_num
            
    # 3. Récupérer l'état actuel de GitHub
    existing_issues = get_existing_issues()
    
    # 4. Synchronisation Intelligente
    print("\n--- Mise à jour des Issues ---")
    for issue in backlog["issues"]:
        m_title = issue.get("milestone")
        m_num = milestone_map.get(m_title)
        sync_issue(issue, m_num, existing_issues)
        time.sleep(0.5)

    print("\n✨ La mise à jour 'en ligne' est terminée !")

if __name__ == "__main__":
    main()
