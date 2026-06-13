import logging
from datetime import datetime
from bs4 import BeautifulSoup
from .base_connector import BaseConnector

class SansConnector(BaseConnector):
    """
    Connecteur pour SANS Reading Room.
    Récupère les derniers 'White Papers' de recherche en cybersécurité.
    """
    
    BASE_URL = "https://www.sans.org"
    PUB_URL = "https://www.sans.org/white-papers/"

    def __init__(self):
        super().__init__("SANS-Institute")

    def fetch_new_items(self):
        """Récupère les derniers livres blancs du SANS."""
        self.logger.info(f"🎓 Récupération des White Papers SANS sur {self.PUB_URL}...")
        response = self.stealth_get(self.PUB_URL)
        
        if not response or response.status_code != 200:
            self.logger.error("❌ Impossible de récupérer la page SANS Reading Room.")
            return []

        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Les articles sont souvent dans des div avec des classes liées aux résultats de recherche ou listes
            items = soup.select('.content-item') or soup.find_all('div', class_='white-paper') or soup.select('li')
            self.logger.info(f"✅ {len(items)} entrées potentielles trouvées sur SANS.")
            return items
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du parsing HTML SANS : {e}")
            return []

    def parse_item(self, item):
        """Transforme une entrée HTML SANS en ressource standard."""
        try:
            link_tag = item.find('a', href=True)
            if not link_tag:
                return None
                
            title = link_tag.get_text(strip=True)
            if len(title) < 5: # Ignorer les titres trop courts/bruit
                return None
                
            href = link_tag['href']
            url = href if href.startswith('http') else self.BASE_URL + href
            
            # Recherche de la date ou de la description
            info_tag = item.find(class_='date') or item.find('p')
            description = info_tag.get_text(strip=True) if info_tag else "White Paper de recherche SANS."
            
            return {
                "external_id": url.split('/')[-1] or title[:20],
                "title": title,
                "description": description,
                "url": url,
                "raw_content_url": self.PUB_URL,
                "type_ressource": "Recherche / White Paper",
                "language": "en",
                "discovered_at": datetime.now(),
                "security_details": {
                    "source": "SANS Institute",
                    "category": "Education / Research"
                }
            }
        except Exception as e:
            self.logger.debug(f"⚠️ Erreur lors du parsing d'un item SANS : {e}")
            return None

if __name__ == "__main__":
    # Test rapide
    logging.basicConfig(level=logging.INFO)
    connector = SansConnector()
    items = connector.fetch_new_items()
    if items:
        for i in range(min(3, len(items))):
            parsed = connector.parse_item(items[i])
            if parsed:
                print(f"--- Item {i+1} ---\n{parsed}\n")
