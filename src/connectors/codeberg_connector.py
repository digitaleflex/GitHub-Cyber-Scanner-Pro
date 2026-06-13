import logging
from datetime import datetime
from .base_connector import BaseConnector

class CodebergConnector(BaseConnector):
    """
    Connecteur pour Codeberg (API Git).
    Recherche des projets liés à la cybersécurité (exploits, outils, etc.).
    """
    
    API_URL = "https://codeberg.org/api/v1/repos/search"

    def __init__(self):
        super().__init__("Codeberg")

    def fetch_new_items(self):
        """Recherche des dépôts de sécurité sur Codeberg."""
        self.logger.info("🔍 Recherche de dépôts sur Codeberg...")
        
        # Mots-clés de recherche pour la cybersécurité
        keywords = ["exploit", "cve", "security-tools", "pentest", "vulnerability"]
        all_repos = []
        
        for kw in keywords:
            params = {
                "q": kw,
                "sort": "updated",
                "order": "desc",
                "limit": 10
            }
            response = self.stealth_get(self.API_URL, headers={"Accept": "application/json"})
            
            # Note: stealth_get in BaseConnector uses requests.get without params support easily
            # I'll construct the URL manually or assume stealth_get can be improved
            full_url = f"{self.API_URL}?q={kw}&sort=updated&order=desc&limit=10"
            response = self.stealth_get(full_url)

            if response and response.status_code == 200:
                data = response.json()
                repos = data.get("data", [])
                all_repos.extend(repos)
                self.logger.info(f"✅ {len(repos)} dépôts trouvés pour '{kw}'.")
            else:
                self.logger.warning(f"⚠️ Erreur lors de la recherche Codeberg pour '{kw}'.")

        # Déduplication par ID
        unique_repos = {repo['id']: repo for repo in all_repos}.values()
        return list(unique_repos)

    def parse_item(self, repo):
        """
        Transforme un dépôt Codeberg en ressource standard.
        """
        return {
            "external_id": f"CB-{repo['id']}",
            "title": repo['full_name'],
            "description": repo.get('description', 'Pas de description')[:500],
            "url": repo['html_url'],
            "raw_content_url": f"{repo['html_url']}/archive/main.zip",
            "type_ressource": "Code / Outil",
            "language": "en",
            "discovered_at": datetime.now()
        }

if __name__ == "__main__":
    # Test rapide
    logging.basicConfig(level=logging.INFO)
    connector = CodebergConnector()
    repos = connector.fetch_new_items()
    if repos:
        print(f"Exemple : {connector.parse_item(repos[0])}")
