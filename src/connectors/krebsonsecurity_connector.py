import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from .base_connector import BaseConnector

class KrebsOnSecurityConnector(BaseConnector):
    """
    Connecteur pour KrebsOnSecurity.
    Récupère les derniers articles d'investigation technique via le flux RSS.
    """
    
    RSS_URL = "https://krebsonsecurity.com/feed/"

    def __init__(self):
        super().__init__("KrebsOnSecurity")

    def fetch_new_items(self):
        """Récupère les articles depuis le flux RSS de KrebsOnSecurity."""
        self.logger.info("🕵️ Récupération du flux RSS KrebsOnSecurity...")
        response = self.stealth_get(self.RSS_URL)
        
        if not response or response.status_code != 200:
            self.logger.error("❌ Impossible de récupérer le flux RSS.")
            return []

        try:
            root = ET.fromstring(response.content)
            items = root.findall('.//item')
            self.logger.info(f"✅ {len(items)} articles trouvés.")
            return items
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du parsing RSS : {e}")
            return []

    def parse_item(self, item):
        """Transforme un item RSS en ressource standard."""
        title = item.find('title').text if item.find('title') is not None else "Sans titre"
        link = item.find('link').text if item.find('link') is not None else ""
        description = item.find('description').text if item.find('description') is not None else ""
        pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
        
        # Nettoyage sommaire du titre et de la description
        title = title.strip()
        description = description.strip() if description else ""

        return {
            "external_id": f"KREBS-{hash(link)}",
            "title": title,
            "description": description[:500] + "..." if len(description) > 500 else description,
            "url": link,
            "raw_content_url": link,
            "type_ressource": "Rapport / Investigation",
            "language": "en",
            "discovered_at": datetime.now()
        }

if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    connector = KrebsOnSecurityConnector()
    items = connector.fetch_new_items()
    if items:
        print(f"Exemple : {connector.parse_item(items[0])}")
