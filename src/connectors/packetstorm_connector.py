import logging
import xml.etree.ElementTree as ET # nosec B405
from datetime import datetime
from .base_connector import BaseConnector

class PacketStormConnector(BaseConnector):
    """
    Connecteur pour Packet Storm Security.
    Récupère les outils, exploits et avis de sécurité via le flux RSS.
    """
    
    RSS_URL = "http://rss.packetstormsecurity.com/files/"

    def __init__(self):
        super().__init__("PacketStorm")

    def fetch_new_items(self):
        """Récupère les nouvelles entrées du flux RSS Packet Storm."""
        self.logger.info(f"📥 Récupération du flux RSS Packet Storm: {self.RSS_URL}")
        response = self.stealth_get(self.RSS_URL)
        
        if not response or response.status_code != 200:
            self.logger.error("❌ Impossible de récupérer le flux RSS Packet Storm.")
            return []

        try:
            root = ET.fromstring(response.content)
            items = root.findall('.//item')
            self.logger.info(f"✅ {len(items)} items trouvés dans le flux Packet Storm.")
            return items
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du parsing XML Packet Storm : {e}")
            return []

    def parse_item(self, item):
        """
        Transforme un item RSS Packet Storm en ressource standard.
        """
        title = item.find('title').text.strip() if item.find('title') is not None else "Sans titre"
        link = item.find('link').text.strip() if item.find('link') is not None else ""
        description = item.find('description').text.strip() if item.find('description') is not None else ""
        
        # Extraction de l'ID depuis l'URL (ex: https://packetstormsecurity.com/files/178550/...)
        external_id = "PS-unknown"
        if "/files/" in link:
            parts = link.split("/")
            try:
                # L'ID est généralement après /files/
                idx = parts.index("files")
                if len(parts) > idx + 1:
                    external_id = f"PS-{parts[idx+1]}"
            except ValueError:
                pass

        return {
            "external_id": external_id,
            "title": title,
            "description": description[:500] + "..." if len(description) > 500 else description,
            "url": link,
            "raw_content_url": "", # Pas d'URL directe simple vers le fichier brut via RSS
            "type_ressource": "Outil / Bulletin",
            "language": "en",
            "discovered_at": datetime.now()
        }

if __name__ == "__main__":
    # Test rapide
    logging.basicConfig(level=logging.INFO)
    connector = PacketStormConnector()
    items = connector.fetch_new_items()
    if items:
        print(f"✅ Exemple d'item parsé : {connector.parse_item(items[0])}")
    else:
        print("❌ Aucun item trouvé ou erreur lors de la récupération.")
