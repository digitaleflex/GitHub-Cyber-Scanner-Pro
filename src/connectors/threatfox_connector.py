import logging
from datetime import datetime
from .base_connector import BaseConnector

class ThreatFoxConnector(BaseConnector):
    """
    Connecteur pour ThreatFox (abuse.ch).
    Une plateforme de partage d'Indicateurs de Compromission (IoC).
    """
    
    API_URL = "https://threatfox-api.abuse.ch/api/v1/"

    def __init__(self):
        super().__init__("ThreatFox")

    def fetch_new_items(self):
        """Récupère les IoC récents (dernières 24h)."""
        self.logger.info("🦊 Récupération des IoC récents depuis ThreatFox...")
        
        payload = {
            "query": "get_iocs",
            "days": 1
        }
        
        response = self.stealth_post(self.API_URL, json_data=payload)
        
        if not response or response.status_code != 200:
            self.logger.error("❌ Impossible de récupérer les données ThreatFox.")
            return []

        try:
            data = response.json()
            if data.get("query_status") != "ok":
                self.logger.warning(f"⚠️ Statut API ThreatFox anormal : {data.get('query_status')}")
                return []
                
            iocs = data.get("data", [])
            self.logger.info(f"✅ {len(iocs)} IoC récupérés.")
            return iocs
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du parsing JSON ThreatFox : {e}")
            return []

    def parse_item(self, item):
        """
        Transforme un IoC ThreatFox en ressource standard.
        Champs : id, ioc, ioc_type, threat_type, malware, malware_printable, malware_alias, malware_link, confidence_level, first_seen, last_seen, reference, tags
        """
        ioc_value = item.get("ioc")
        ioc_type = item.get("ioc_type")
        malware = item.get("malware_printable") or "Unknown Malware"
        confidence = item.get("confidence_level")
        
        title = f"[{ioc_type.upper()}] {ioc_value} - Malware: {malware}"
        
        return {
            "external_id": item.get("id"),
            "title": title,
            "description": f"IoC de type {ioc_type} associé à {malware}. Niveau de confiance : {confidence}%.",
            "url": item.get("reference") or f"https://threatfox.abuse.ch/ioc/{item.get('id')}/",
            "raw_content_url": self.API_URL,
            "type_ressource": "IoC / Threat Intelligence",
            "language": "en",
            "discovered_at": datetime.now(),
            "security_details": {
                "ioc_type": ioc_type,
                "threat_type": item.get("threat_type"),
                "malware": malware,
                "confidence_level": confidence,
                "tags": item.get("tags", [])
            }
        }

if __name__ == "__main__":
    # Test rapide
    logging.basicConfig(level=logging.INFO)
    connector = ThreatFoxConnector()
    items = connector.fetch_new_items()
    if items:
        print(f"Exemple : {connector.parse_item(items[0])}")
