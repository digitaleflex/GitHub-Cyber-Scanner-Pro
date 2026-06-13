import logging
from datetime import datetime
from .base_connector import BaseConnector

class ThreatFoxConnector(BaseConnector):
    """
    Connecteur pour ThreatFox (par abuse.ch).
    Récupère les indicateurs de compromission (IoC) récents.
    """
    
    # URL d'exportation JSON des IoC récents (dernières 24h)
    JSON_URL = "https://threatfox.abuse.ch/export/json/recent/"

    def __init__(self):
        super().__init__("ThreatFox")

    def fetch_new_items(self):
        """Récupère les IoC récents depuis ThreatFox."""
        self.logger.info("🦊 Récupération des IoC récents depuis ThreatFox...")
        response = self.stealth_get(self.JSON_URL)
        
        if not response or response.status_code != 200:
            self.logger.error("❌ Impossible de récupérer les données ThreatFox.")
            return []

        try:
            # ThreatFox export JSON est une liste d'IoCs directe ou encapsulée
            data = response.json()
            # Dans certains cas, c'est un dictionnaire avec les clés comme IDs
            if isinstance(data, dict):
                # Si c'est un dictionnaire, on aplatit les valeurs
                items = list(data.values()) if data else []
            else:
                items = data if isinstance(data, list) else []
                
            self.logger.info(f"✅ {len(items)} IoC récupérés.")
            return items
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du parsing JSON ThreatFox : {e}")
            return []

    def parse_item(self, item):
        """
        Transforme un IoC ThreatFox en ressource standard.
        Champs : ioc_value, ioc_type, threat_type, malware, confidence_level, first_seen, reference
        """
        ioc_value = item.get("ioc_value", "N/A")
        ioc_type = item.get("ioc_type", "unknown")
        malware = item.get("malware_printable", item.get("malware", "Unknown Malware"))
        threat_type = item.get("threat_type", "N/A")
        
        title = f"[{malware}] {ioc_type}: {ioc_value}"
        description = f"Threat Type: {threat_type} | Malware: {malware} | Confidence: {item.get('confidence_level')}%"
        
        # URL de référence ou lien vers ThreatFox
        external_id = item.get("id")
        url = item.get("reference") or f"https://threatfox.abuse.ch/ioc/{external_id}/"
        
        return {
            "external_id": str(external_id),
            "title": title,
            "description": description,
            "url": url,
            "raw_content_url": self.JSON_URL,
            "type_ressource": "Intelligence / IoC",
            "language": "en",
            "discovered_at": datetime.now(),
            "security_details": {
                "ioc_type": ioc_type,
                "threat_type": threat_type,
                "malware": malware,
                "confidence": item.get("confidence_level"),
                "first_seen": item.get("first_seen")
            }
        }

if __name__ == "__main__":
    # Test rapide
    logging.basicConfig(level=logging.INFO)
    connector = ThreatFoxConnector()
    items = connector.fetch_new_items()
    if items:
        print(f"Exemple d'IoC parsé : {connector.parse_item(items[0])}")
    else:
        print("Aucun item récupéré (vérifiez la connectivité ou l'URL).")
