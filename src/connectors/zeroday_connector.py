import logging
from datetime import datetime
from bs4 import BeautifulSoup
from .base_connector import BaseConnector

class ZeroDayConnector(BaseConnector):
    """
    Connecteur pour 0day.today (Inj3ct0r Exploit Database).
    Scraper furtif pour les exploits récents.
    """
    
    BASE_URL = "https://0day.today"

    def __init__(self):
        super().__init__("0day.today")

    def fetch_new_items(self):
        """Récupère les derniers exploits depuis 0day.today."""
        self.logger.info("🕵️ Scraping furtif de 0day.today...")
        
        # 0day.today est protégé par Cloudflare et demande souvent un cookie d'acceptation
        headers = {
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://0day.today/"
        }
        
        # Tentative avec stealth_get
        response = self.stealth_get(self.BASE_URL, headers=headers)
        
        if not response or response.status_code != 200:
            self.logger.error("❌ Impossible de joindre 0day.today.")
            return []

        # Si on détecte une page de ToS, on essaie d'ajouter le cookie 'agree'
        if "agree" in response.text.lower() and "terms" in response.text.lower():
            self.logger.info("🛡️ Page de conditions détectée sur 0day.today, ajout du cookie...")
            import requests
            response = requests.get(self.BASE_URL, headers=headers, cookies={"agree": "1"}, timeout=30)
            if response.status_code != 200:
                return []

        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Recherche du tableau des exploits
            # La classe peut varier, on cherche un tableau avec 'exploit_list' ou similaire
            table = soup.find('table', class_='exploit_list')
            if not table:
                # Fallback sur une recherche plus large
                table = soup.find('div', id='content')
            
            if not table:
                self.logger.error("❌ Structure de 0day.today non reconnue.")
                return []

            # Extraction des lignes (tr)
            rows = soup.select("table.exploit_list tr")
            if not rows:
                # Essayer via des sélecteurs CSS alternatifs
                rows = soup.select(".exploit_list tr")
            
            items = []
            for row in rows:
                cols = row.find_all('td')
                # Une ligne valide a généralement 5+ colonnes
                if len(cols) >= 3:
                    # On ignore les lignes d'en-tête (souvent sans liens)
                    if cols[2].find('a'):
                        items.append(row)
            
            self.logger.info(f"✅ {len(items)} exploits potentiels trouvés sur 0day.today.")
            return items
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du parsing 0day.today : {e}")
            return []

    def parse_item(self, row):
        """
        Transforme une ligne de tableau 0day.today en ressource standard.
        Colonnes classiques : ID | Date | Description/Titre | Auteur | Catégorie
        """
        cols = row.find_all('td')
        
        external_id = "0DAY-" + cols[0].text.strip() if len(cols) > 0 else "0DAY-Unknown"
        title_col = cols[2] if len(cols) > 2 else None
        
        title = "Sans titre"
        url = self.BASE_URL
        if title_col:
            a_tag = title_col.find('a')
            if a_tag:
                title = a_tag.text.strip()
                url = self.BASE_URL + a_tag['href']

        author = cols[3].text.strip() if len(cols) > 3 else "Inconnu"
        category = cols[4].text.strip() if len(cols) > 4 else "Exploit"

        return {
            "external_id": external_id,
            "title": title,
            "description": f"Auteur: {author} | Catégorie: {category}",
            "url": url,
            "raw_content_url": url, # Le contenu brut demande souvent un paiement/compte
            "type_ressource": "Exploit",
            "language": "en",
            "discovered_at": datetime.now()
        }

if __name__ == "__main__":
    # Test rapide
    logging.basicConfig(level=logging.INFO)
    connector = ZeroDayConnector()
    items = connector.fetch_new_items()
    if items:
        print(f"Exemple : {connector.parse_item(items[0])}")
