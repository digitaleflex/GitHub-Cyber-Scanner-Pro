import logging
from datetime import datetime
from .base_connector import BaseConnector

class AlienVaultConnector(BaseConnector):
    """
    Connecteur pour AlienVault OTX (Open Threat Exchange).
    Récupère les "Pulses" de menaces via l'API publique.
    """
    
    # API publique générale
    API_URL = "https://otx.alienvault.com/api/v1/pulses/general"

    def __init__(self):
        super().__init__("AlienVault")

    def fetch_new_items(self):
        """Récupère les pulses récents via l'API JSON."""
        self.logger.info("👽 Récupération des pulses AlienVault OTX...")
        
        response = self.stealth_get(self.API_URL)
        
        if not response or response.status_code != 200:
            self.logger.error(f"❌ Impossible de récupérer les données AlienVault (Status: {response.status_code if response else 'None'}).")
            return []

        try:
            data = response.json()
            pulses = data.get("results", [])
            self.logger.info(f"✅ {len(pulses)} pulses récupérés.")
            return pulses
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du parsing JSON AlienVault : {e}")
            return []

    def parse_item(self, item):
        """
        Transforme un pulse AlienVault en ressource standard.
        """
        pulse_id = item.get("id")
        name = item.get("name", "Untitled Pulse")
        description = item.get("description", "")
        author = item.get("author_name", "Unknown")
        
        return {
            "external_id": str(pulse_id),
            "title": f"Pulse: {name} (by {author})",
            "description": description[:1000],
            "url": f"https://otx.alienvault.com/pulse/{pulse_id}",
            "raw_content_url": self.API_URL,
            "type_ressource": "Threat Pulse / Intelligence",
            "language": "en",
            "discovered_at": datetime.now(),
            "security_details": {
                "author": author,
                "tags": item.get("tags", []),
                "indicator_count": item.get("indicator_count", 0),
                "modified": item.get("modified")
            }
        }

if __name__ == "__main__":
    # Test rapide
    logging.basicConfig(level=logging.INFO)
    connector = AlienVaultConnector()
    items = connector.fetch_new_items()
    if items:
        print(f"Exemple : {connector.parse_item(items[0])}")
