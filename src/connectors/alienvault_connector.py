import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from .base_connector import BaseConnector

class AlienVaultConnector(BaseConnector):
    """
    Connecteur pour AlienVault OTX (Open Threat Exchange).
    Récupère les "Pulses" de menaces via le flux RSS public.
    """
    
    RSS_URL = "https://otx.alienvault.com/rss/all/pulses"

    def __init__(self):
        super().__init__("AlienVault")

    def fetch_new_items(self):
        """Récupère les pulses récents via RSS."""
        self.logger.info("👽 Récupération des pulses AlienVault OTX...")
        
        response = self.stealth_get(self.RSS_URL)
        
        if not response or response.status_code != 200:
            self.logger.error("❌ Impossible de récupérer le flux AlienVault.")
            return []

        try:
            root = ET.fromstring(response.content)
            items = root.findall(".//item")
            self.logger.info(f"✅ {len(items)} pulses récupérés.")
            return items
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du parsing RSS AlienVault : {e}")
            return []

    def parse_item(self, item):
        """
        Transforme une entrée RSS AlienVault en ressource standard.
        """
        title = item.find("title").text if item.find("title") is not None else "Untitled Pulse"
        link = item.find("link").text if item.find("link") is not None else ""
        description = item.find("description").text if item.find("description") is not None else ""
        guid = item.find("guid").text if item.find("guid") is not None else link
        
        # Extraction simplifiée des indicateurs de la description si possible
        # La description RSS d'OTX contient souvent du HTML avec les types d'indicateurs
        
        return {
            "external_id": guid,
            "title": title,
            "description": description[:500] + ("..." if len(description) > 500 else ""),
            "url": link,
            "raw_content_url": self.RSS_URL,
            "type_ressource": "Threat Pulse / Intelligence",
            "language": "en",
            "discovered_at": datetime.now(),
            "security_details": {
                "source": "AlienVault OTX",
                "full_description": description
            }
        }

if __name__ == "__main__":
    # Test rapide
    logging.basicConfig(level=logging.INFO)
    connector = AlienVaultConnector()
    items = connector.fetch_new_items()
    if items:
        print(f"Exemple : {connector.parse_item(items[0])}")
