import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from .base_connector import BaseConnector

class CXSecurityConnector(BaseConnector):
    """
    Connecteur pour CXSecurity WLB (World Laboratory of Bugtraq).
    Récupère les dernières vulnérabilités et exploits via le flux RSS.
    """
    
    RSS_URL = "https://cxsecurity.com/wlb/rss/vulnerability/"

    def __init__(self):
        super().__init__("CXSecurity")

    def fetch_new_items(self):
        """Récupère les dernières vulnérabilités depuis le flux RSS de CXSecurity."""
        self.logger.info("📡 Récupération du flux RSS CXSecurity...")
        response = self.stealth_get(self.RSS_URL)
        
        if not response or response.status_code != 200:
            self.logger.error("❌ Impossible de récupérer le flux RSS CXSecurity.")
            return []

        try:
            root = ET.fromstring(response.content)
            items = root.findall('.//item')
            self.logger.info(f"✅ {len(items)} entrées trouvées sur CXSecurity.")
            return items
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du parsing RSS CXSecurity : {e}")
            return []

    def parse_item(self, item):
        """
        Transforme une entrée RSS CXSecurity en ressource standard.
        """
        title = item.find('title').text if item.find('title') is not None else "Sans titre"
        link = item.find('link').text if item.find('link') is not None else ""
        description = item.find('description').text if item.find('description') is not None else ""
        guid = item.find('guid').text if item.find('guid') is not None else ""
        
        # Le format de description CXSecurity contient souvent des métadonnées
        # On tente d'extraire le CVE si présent
        external_id = f"WLB-{guid}"
        if "CVE:" in description:
            import re
            cve_match = re.search(r'CVE: (CVE-\d+-\d+)', description)
            if cve_match:
                external_id = cve_match.group(1)

        return {
            "external_id": external_id,
            "title": title.strip(),
            "description": description.strip()[:500] + "...",
            "url": link,
            "raw_content_url": link,
            "type_ressource": "Vulnérabilité / Exploit",
            "language": "en",
            "discovered_at": datetime.now()
        }

if __name__ == "__main__":
    # Test rapide
    logging.basicConfig(level=logging.INFO)
    connector = CXSecurityConnector()
    items = connector.fetch_new_items()
    if items:
        print(f"Exemple : {connector.parse_item(items[0])}")
