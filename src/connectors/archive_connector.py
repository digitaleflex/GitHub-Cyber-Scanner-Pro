import logging
from datetime import datetime
from .base_connector import BaseConnector

class ArchiveConnector(BaseConnector):
    """
    Connecteur pour Internet Archive (archive.org).
    Recherche des manuels et livres sur la cybersécurité via l'API Advanced Search.
    """
    
    API_URL = "https://archive.org/advancedsearch.php"

    def __init__(self):
        super().__init__("Internet-Archive")

    def fetch_new_items(self):
        """Recherche des ressources cyber sur Internet Archive."""
        params = {
            "q": 'subject:"cybersecurity" AND mediatype:"texts"',
            "fl[]": ["identifier", "title", "description", "date"],
            "sort[]": "date desc",
            "output": "json",
            "rows": 50,
            "page": 1
        }
        
        # Construction de l'URL avec paramètres pour stealth_get
        query_string = "&".join([f"{k}={v}" if not isinstance(v, list) else "&".join([f"{k}={item}" for item in v]) for k, v in params.items()])
        full_url = f"{self.API_URL}?{query_string}"
        
        self.logger.info(f"🏛️ Recherche sur Internet Archive : {full_url}")
        response = self.stealth_get(full_url)
        
        if not response or response.status_code != 200:
            self.logger.error("❌ Impossible de contacter l'API Internet Archive.")
            return []

        try:
            data = response.json()
            docs = data.get("response", {}).get("docs", [])
            self.logger.info(f"✅ {len(docs)} documents trouvés sur Internet Archive.")
            return docs
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du parsing JSON Internet Archive : {e}")
            return []

    def parse_item(self, item):
        """Transforme une entrée API Archive.org en ressource standard."""
        identifier = item.get("identifier")
        title = item.get("title", "Sans titre")
        description = item.get("description", "Pas de description.")
        
        # Nettoyage de la description (parfois contient du HTML)
        if isinstance(description, list):
            description = " ".join(description)
        
        return {
            "external_id": identifier,
            "title": title,
            "description": description[:500] + "..." if len(description) > 500 else description,
            "url": f"https://archive.org/details/{identifier}",
            "raw_content_url": self.API_URL,
            "type_ressource": "Livre / Manuel / Archive",
            "language": "en",
            "discovered_at": datetime.now(),
            "security_details": {
                "source": "Internet Archive",
                "identifier": identifier,
                "date_published": item.get("date")
            }
        }

if __name__ == "__main__":
    # Test rapide
    logging.basicConfig(level=logging.INFO)
    connector = ArchiveConnector()
    items = connector.fetch_new_items()
    if items:
        for i in range(min(3, len(items))):
            parsed = connector.parse_item(items[i])
            if parsed:
                print(f"--- Item {i+1} ---\n{parsed}\n")
