import logging
from datetime import datetime
from .base_connector import BaseConnector

class AlienVaultOTXConnector(BaseConnector):
    """
    Connecteur pour AlienVault Open Threat Exchange (OTX).
    Récupère les pulses (campagnes de menaces) récents.
    """
    
    # API publique pour les pulses récents
    API_URL = "https://otx.alienvault.com/api/v1/pulses/recent"

    def __init__(self):
        super().__init__("AlienVault-OTX")

    def fetch_new_items(self):
        """Récupère les nouveaux pulses depuis l'API OTX."""
        self.logger.info("🚀 Récupération des pulses récents depuis AlienVault OTX...")
        response = self.stealth_get(self.API_URL)
        
        if not response or response.status_code != 200:
            self.logger.error("❌ Impossible de récupérer les données AlienVault OTX.")
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
        Transforme un pulse OTX en ressource standard.
        Champs : id, name, description, author_name, created, references
        """
        pulse_id = item.get("id")
        name = item.get("name", "Sans titre")
        author = item.get("author_name", "Inconnu")
        
        title = f"[OTX Pulse] {name} (by {author})"
        description = item.get("description", "Pas de description fournie.")
        url = f"https://otx.alienvault.com/pulse/{pulse_id}"
        
        # On essaie de récupérer une date de création
        created_str = item.get("created", "")
        discovered_at = datetime.now()
        if created_str:
            try:
                # Format souvent ISO: 2024-01-23T12:34:56.789
                discovered_at = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
            except:
                pass

        return {
            "external_id": str(pulse_id),
            "title": title,
            "description": description,
            "url": url,
            "raw_content_url": self.API_URL,
            "type_ressource": "Intelligence / Pulse",
            "language": "en",
            "discovered_at": discovered_at,
            "security_details": {
                "author": author,
                "tags": item.get("tags", []),
                "indicators_count": item.get("indicator_count", 0),
                "references": item.get("references", [])
            }
        }

if __name__ == "__main__":
    # Test rapide
    logging.basicConfig(level=logging.INFO)
    connector = AlienVaultOTXConnector()
    items = connector.fetch_new_items()
    if items:
        print(f"Exemple de pulse parsé : {connector.parse_item(items[0])}")
    else:
        print("Aucun item récupéré.")
