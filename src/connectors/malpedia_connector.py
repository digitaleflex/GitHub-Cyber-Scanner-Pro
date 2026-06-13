import logging
from datetime import datetime
from .base_connector import BaseConnector

class MalpediaConnector(BaseConnector):
    """
    Connecteur pour Malpedia.
    Inventaire des familles de malwares.
    """
    
    LIST_URL = "https://malpedia.caad.fkie.fraunhofer.de/api/list/families"

    def __init__(self):
        super().__init__("Malpedia")

    def fetch_new_items(self):
        """Récupère la liste des familles de malwares."""
        self.logger.info("🦠 Récupération de l'inventaire Malpedia...")
        
        response = self.stealth_get(self.LIST_URL)
        
        if not response or response.status_code != 200:
            self.logger.error("❌ Impossible de récupérer la liste Malpedia.")
            return []

        try:
            families = response.json()
            # Malpedia retourne une liste de chaînes (les IDs des familles)
            self.logger.info(f"✅ {len(families)} familles de malwares listées.")
            return families
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du parsing JSON Malpedia : {e}")
            return []

    def parse_item(self, item_id):
        """
        Transforme un ID de famille Malpedia en ressource standard.
        Note : item_id est une chaîne de caractères (ex: 'win.cobalt_strike')
        """
        # Construction de l'URL pour plus de détails
        url = f"https://malpedia.caad.fkie.fraunhofer.de/details/{item_id}"
        
        return {
            "external_id": item_id,
            "title": f"Malware Family: {item_id}",
            "description": f"Détails de la famille de malware '{item_id}' sur Malpedia.",
            "url": url,
            "raw_content_url": self.LIST_URL,
            "type_ressource": "Malware / Taxonomy",
            "language": "en",
            "discovered_at": datetime.now(),
            "security_details": {
                "malpedia_id": item_id,
                "category": item_id.split('.')[0] if '.' in item_id else "unknown"
            }
        }

if __name__ == "__main__":
    # Test rapide
    logging.basicConfig(level=logging.INFO)
    connector = MalpediaConnector()
    items = connector.fetch_new_items()
    if items:
        print(f"Exemple : {connector.parse_item(items[0])}")
