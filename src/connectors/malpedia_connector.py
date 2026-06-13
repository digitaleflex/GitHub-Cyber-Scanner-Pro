import logging
from datetime import datetime
from .base_connector import BaseConnector

class MalpediaConnector(BaseConnector):
    """
    Connecteur pour Malpedia.
    Récupère la liste des familles de malwares répertoriées.
    """
    
    # API pour lister les familles
    FAMILIES_API_URL = "https://malpedia.caad.fkie.fraunhofer.de/api/list/families"
    # Base URL pour les détails (Web)
    BASE_WEB_URL = "https://malpedia.caad.fkie.fraunhofer.de/details/"

    def __init__(self):
        super().__init__("Malpedia")

    def fetch_new_items(self):
        """Récupère la liste des familles de malwares."""
        self.logger.info("🦠 Récupération des familles de malwares depuis Malpedia...")
        response = self.stealth_get(self.FAMILIES_API_URL)
        
        if not response or response.status_code != 200:
            self.logger.error("❌ Impossible de récupérer la liste Malpedia.")
            return []

        try:
            families = response.json()
            # C'est généralement une liste de chaînes (ex: "win.asyncrat")
            self.logger.info(f"✅ {len(families)} familles identifiées.")
            return families
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du parsing JSON Malpedia : {e}")
            return []

    def parse_item(self, item):
        """
        Transforme une entrée Malpedia (ID de famille) en ressource standard.
        Item est une chaîne comme 'win.asyncrat'
        """
        family_id = item
        # On essaie de rendre le titre plus lisible (ex: Asyncrat)
        readable_name = family_id.split('.')[-1].capitalize() if '.' in family_id else family_id.capitalize()
        
        title = f"[Malware] {readable_name} ({family_id})"
        description = f"Famille de malware répertoriée sur Malpedia. Identifiant technique : {family_id}."
        url = f"{self.BASE_WEB_URL}{family_id}"
        
        return {
            "external_id": family_id,
            "title": title,
            "description": description,
            "url": url,
            "raw_content_url": self.FAMILIES_API_URL,
            "type_ressource": "Intelligence / Malware Family",
            "language": "en",
            "discovered_at": datetime.now(),
            "security_details": {
                "family_id": family_id,
                "platform": family_id.split('.')[0] if '.' in family_id else "unknown",
                "malpedia_url": url
            }
        }

if __name__ == "__main__":
    # Test rapide
    logging.basicConfig(level=logging.INFO)
    connector = MalpediaConnector()
    items = connector.fetch_new_items()
    if items:
        # On ne traite que les 5 premiers pour le test
        for i in range(min(5, len(items))):
            print(f"Exemple {i+1} : {connector.parse_item(items[i])}")
    else:
        print("Aucun item récupéré.")
