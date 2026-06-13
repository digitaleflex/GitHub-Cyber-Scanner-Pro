import logging
from datetime import datetime
from .base_connector import BaseConnector

class MispGalaxyConnector(BaseConnector):
    """
    Connecteur pour MISP Galaxy.
    Importe les clusters de connaissances ( Threat Actors, Malwares, etc.).
    """
    
    # On cible les Threat Actors par défaut pour cet import
    GALAXY_URL = "https://raw.githubusercontent.com/MISP/misp-galaxy/main/clusters/threat-actor.json"

    def __init__(self):
        super().__init__("MISP-Galaxy")

    def fetch_new_items(self):
        """Récupère les définitions du Galaxy depuis GitHub."""
        self.logger.info("🌌 Récupération des définitions MISP Galaxy (Threat Actors)...")
        
        response = self.stealth_get(self.GALAXY_URL)
        
        if not response or response.status_code != 200:
            self.logger.error("❌ Impossible de récupérer le fichier MISP Galaxy.")
            return []

        try:
            data = response.json()
            values = data.get("values", [])
            self.logger.info(f"✅ {len(values)} définitions récupérées.")
            return values
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du parsing JSON MISP Galaxy : {e}")
            return []

    def parse_item(self, item):
        """
        Transforme une entrée MISP Galaxy en ressource standard.
        """
        name = item.get("value")
        description = item.get("description", "Pas de description disponible.")
        uuid = item.get("uuid")
        
        meta = item.get("meta", {})
        synonyms = meta.get("synonyms", [])
        
        return {
            "external_id": uuid,
            "title": f"Threat Actor: {name}",
            "description": description[:1000],
            "url": "https://github.com/MISP/misp-galaxy",
            "raw_content_url": self.GALAXY_URL,
            "type_ressource": "Intelligence / Threat Actor",
            "language": "en",
            "discovered_at": datetime.now(),
            "security_details": {
                "name": name,
                "uuid": uuid,
                "synonyms": synonyms,
                "country": meta.get("country"),
                "refs": meta.get("refs", [])
            }
        }

if __name__ == "__main__":
    # Test rapide
    logging.basicConfig(level=logging.INFO)
    connector = MispGalaxyConnector()
    items = connector.fetch_new_items()
    if items:
        print(f"Exemple : {connector.parse_item(items[0])}")
