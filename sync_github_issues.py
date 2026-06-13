import os
import json
import requests
import time
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
# Remplacez par votre repo: 'username/repo_name'
REPO = os.getenv("GITHUB_REPO", "VOTRE_USERNAME/cyber_scan_books")
TOKEN = os.getenv("GITHUB_ADMIN_TOKEN") # Nécessite un PAT avec les droits 'repo'

if not TOKEN:
    print("❌ Erreur: GITHUB_ADMIN_TOKEN manquant dans le fichier .env")
    print("ℹ️ Note: Ce token doit avoir les droits d'écriture (scope 'repo') sur votre dépôt.")
    exit(1)

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

API_URL = f"https://api.github.com/repos/{REPO}"

def load_backlog():
    with open("github_issues.json", "r", encoding="utf-8") as f:
        return json.load(f)

def create_milestone(title, description, due_on):
    url = f"{API_URL}/milestones"
    data = {"title": title, "description": description, "due_on": due_on, "state": "open"}
    response = requests.post(url, headers=HEADERS, json=data)
    if response.status_code == 201:
        print(f"✅ Milestone créé : {title}")
        return response.json()["number"]
    else:
        # Si le milestone existe déjà, on récupère son numéro
        response = requests.get(url, headers=HEADERS)
        for m in response.json():
            if m["title"] == title:
                print(f"ℹ️ Milestone existant : {title} (ID: {m['number']})")
                return m["number"]
    return None

def create_label(name, color, description):
    url = f"{API_URL}/labels"
    data = {"name": name, "color": color, "description": description}
    response = requests.post(url, headers=HEADERS, json=data)
    if response.status_code == 201:
        print(f"✅ Label créé : {name}")
    else:
        print(f"ℹ️ Label ignoré (existe déjà ?) : {name}")

def create_issue(title, body, milestone_number, labels):
    url = f"{API_URL}/issues"
    data = {
        "title": title,
        "body": body,
        "milestone": milestone_number,
        "labels": labels
    }
    response = requests.post(url, headers=HEADERS, json=data)
    if response.status_code == 201:
        print(f"🚀 Issue créée : {title}")
    else:
        print(f"❌ Erreur lors de la création de l'issue {title} : {response.text}")

def main():
    backlog = load_backlog()
    
    print(f"🔍 Début de la synchronisation sur le dépôt : {REPO}")
    
    # 1. Création des Labels
    print("\n--- Étape 1 : Labels ---")
    for label in backlog["labels"]:
        create_label(label["name"], label["color"], label["description"])
    
    # 2. Création des Milestones
    print("\n--- Étape 2 : Milestones ---")
    milestone_map = {}
    for m in backlog["milestones"]:
        m_num = create_milestone(m["title"], m["description"], m["due_on"])
        if m_num:
            milestone_map[m["title"]] = m_num
            
    # 3. Création des Issues
    print("\n--- Étape 3 : Issues ---")
    for issue in backlog["issues"]:
        m_title = issue.get("milestone")
        m_num = milestone_map.get(m_title)
        create_issue(issue["title"], issue["body"], m_num, issue["labels"])
        time.sleep(1) # Petit délai pour éviter les limites de l'API GitHub

    print("\n✨ Synchronisation terminée ! Votre tableau de bord GitHub est prêt.")

if __name__ == "__main__":
    main()
