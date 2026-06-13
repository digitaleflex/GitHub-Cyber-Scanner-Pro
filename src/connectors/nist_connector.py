import logging
from datetime import datetime
from bs4 import BeautifulSoup
from .base_connector import BaseConnector

class NistConnector(BaseConnector):
    """
    Connecteur pour NIST CSRC (Computer Security Resource Center).
    Cible les publications de la série SP 800 (Special Publications).
    """
    
    BASE_URL = "https://csrc.nist.gov"
    PUB_URL = "https://csrc.nist.gov/publications/sp800"

    def __init__(self):
        super().__init__("NIST-CSRC")

    def fetch_new_items(self):
        """Récupère la liste des publications NIST SP 800."""
        self.logger.info(f"📚 Récupération des publications NIST sur {self.PUB_URL}...")
        response = self.stealth_get(self.PUB_URL)
        
        if not response or response.status_code != 200:
            self.logger.error("❌ Impossible de récupérer la page NIST CSRC.")
            return []

        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Les publications sont généralement dans des tableaux ou des listes avec la classe 'search-result-item'
            items = soup.select('.search-result-item') or soup.select('tr')
            self.logger.info(f"✅ {len(items)} entrées potentielles trouvées sur NIST.")
            return items
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du parsing HTML NIST : {e}")
            return []

    def parse_item(self, item):
        """Transforme une entrée HTML NIST en ressource standard."""
        try:
            # Recherche du lien et du titre
            link_tag = item.find('a', href=True)
            if not link_tag:
                return None
            
            title = link_tag.get_text(strip=True)
            href = link_tag['href']
            url = self.BASE_URL + href if href.startswith('/') else href
            
            # Recherche de la description (souvent dans un paragraphe suivant)
            desc_tag = item.find('p') or item.find_next('p')
            description = desc_tag.get_text(strip=True) if desc_tag else "Pas de description disponible."
            
            # Recherche de l'ID externe (ex: SP 800-53)
            # Souvent présent dans un span ou le texte du titre
            ext_id = title.split(':')[0] if ':' in title else title
            
            return {
                "external_id": ext_id,
                "title": title,
                "description": description,
                "url": url,
                "raw_content_url": self.PUB_URL,
                "type_ressource": "Standard / Publication Technique",
                "language": "en",
                "discovered_at": datetime.now(),
                "security_details": {
                    "source": "NIST CSRC",
                    "series": "SP 800"
                }
            }
        except Exception as e:
            self.logger.debug(f"⚠️ Erreur lors du parsing d'un item NIST : {e}")
            return None

if __name__ == "__main__":
    # Test rapide
    logging.basicConfig(level=logging.INFO)
    connector = NistConnector()
    items = connector.fetch_new_items()
    if items:
        for i in range(min(3, len(items))):
            parsed = connector.parse_item(items[i])
            if parsed:
                print(f"--- Item {i+1} ---\n{parsed}\n")
