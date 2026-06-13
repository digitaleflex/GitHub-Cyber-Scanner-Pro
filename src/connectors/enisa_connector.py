import logging
from datetime import datetime
from bs4 import BeautifulSoup
from .base_connector import BaseConnector

class EnisaConnector(BaseConnector):
    """
    Connecteur pour l'ENISA (European Union Agency for Cybersecurity).
    Récupère les derniers rapports et guides.
    """
    
    BASE_URL = "https://www.enisa.europa.eu"
    PUB_URL = "https://www.enisa.europa.eu/publications"

    def __init__(self):
        super().__init__("ENISA")

    def fetch_new_items(self):
        """Récupère les publications récentes de l'ENISA."""
        self.logger.info(f"🇪🇺 Récupération des publications ENISA sur {self.PUB_URL}...")
        response = self.stealth_get(self.PUB_URL)
        
        if not response or response.status_code != 200:
            self.logger.error("❌ Impossible de récupérer la page ENISA.")
            return []

        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Les articles sont généralement dans des balises <article> ou des div avec la classe 'tileItem'
            items = soup.find_all('article') or soup.select('.tileItem')
            self.logger.info(f"✅ {len(items)} entrées trouvées sur ENISA.")
            return items
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du parsing HTML ENISA : {e}")
            return []

    def parse_item(self, item):
        """Transforme une entrée HTML ENISA en ressource standard."""
        try:
            title_tag = item.find(['h2', 'h3']) or item.find('a', class_='summary')
            if not title_tag:
                return None
                
            title = title_tag.get_text(strip=True)
            link_tag = title_tag.find('a') if hasattr(title_tag, 'find') else title_tag
            if not link_tag or not link_tag.has_attr('href'):
                link_tag = item.find('a', href=True)
                
            if not link_tag:
                return None
                
            href = link_tag['href']
            url = href if href.startswith('http') else self.BASE_URL + href
            
            desc_tag = item.find(class_='description') or item.find('p')
            description = desc_tag.get_text(strip=True) if desc_tag else "Rapport technique ENISA."
            
            return {
                "external_id": url.split('/')[-1],
                "title": title,
                "description": description,
                "url": url,
                "raw_content_url": self.PUB_URL,
                "type_ressource": "Guide / Rapport Européen",
                "language": "en",
                "discovered_at": datetime.now(),
                "security_details": {
                    "source": "ENISA",
                    "region": "EU"
                }
            }
        except Exception as e:
            self.logger.debug(f"⚠️ Erreur lors du parsing d'un item ENISA : {e}")
            return None

if __name__ == "__main__":
    # Test rapide
    logging.basicConfig(level=logging.INFO)
    connector = EnisaConnector()
    items = connector.fetch_new_items()
    if items:
        for i in range(min(3, len(items))):
            parsed = connector.parse_item(items[i])
            if parsed:
                print(f"--- Item {i+1} ---\n{parsed}\n")
