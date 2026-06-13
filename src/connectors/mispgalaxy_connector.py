import logging
from datetime import datetime
from .base_connector import BaseConnector

class MispGalaxyConnector(BaseConnector):
    """
    Connecteur pour MISP Galaxy.
    Importe les définitions de clusters (ex: Threat Actors, Ransomware).
    """
    
    # URL du cluster Threat Actor par défaut
    GALAXY_URL = "https://raw.githubusercontent.com/MISP/misp-galaxy/main/clusters/threat-actor.json"

    def __init__(self):
        super().__init__("MISP-Galaxy")

    def fetch_new_items(self):
        """Récupère les définitions JSON depuis le dépôt MISP Galaxy."""
        self.logger.info(f"🌌 Importation des définitions depuis {self.GALAXY_URL}...")
        response = self.stealth_get(self.GALAXY_URL)
        
        if not response or response.status_code != 200:
            self.logger.error("❌ Impossible de récupérer les données MISP Galaxy.")
            return []

        try:
            data = response.json()
            # Les items sont dans la clé 'values'
            items = data.get("values", [])
            self.logger.info(f"✅ {len(items)} entrées importées.")
            return items
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du parsing JSON MISP Galaxy : {e}")
            return []

    def parse_item(self, item):
        """
        Transforme une entrée MISP Galaxy en ressource standard.
        Champs : value (nom), description, meta (synonymes, pays, etc.)
        """
        name = item.get("value", "Inconnu")
        description = item.get("description", "Pas de description.")
        meta = item.get("meta", {})
        
        # On utilise le nom comme ID externe s'il n'y a pas d'UUID
        external_id = item.get("uuid", name)
        
        title = f"[Threat Actor] {name}"
        if meta.get("country"):
            title += f" ({meta.get('country')})"
            
        return {
            "external_id": str(external_id),
            "title": title,
            "description": description,
            "url": "https://github.com/MISP/misp-galaxy",
            "raw_content_url": self.GALAXY_URL,
            "type_ressource": "Intelligence / Threat Actor",
            "language": "en",
            "discovered_at": datetime.now(),
            "security_details": {
                "name": name,
                "synonyms": meta.get("synonyms", []),
                "refs": meta.get("refs", []),
                "attribution": meta.get("attribution", [])
            }
        }

if __name__ == "__main__":
    # Test rapide
    logging.basicConfig(level=logging.INFO)
    connector = MispGalaxyConnector()
    items = connector.fetch_new_items()
    if items:
        print(f"Exemple d'acteur de menace parsé : {connector.parse_item(items[0])}")
    else:
        print("Aucun item récupéré.")
