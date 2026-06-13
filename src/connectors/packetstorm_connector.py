import logging
import re
from datetime import datetime
from bs4 import BeautifulSoup
from .base_connector import BaseConnector

class PacketStormConnector(BaseConnector):
    """
    Connecteur pour Packet Storm Security.
    Scraper pour les derniers outils, exploits et bulletins.
    """
    
    BASE_URL = "https://packetstormsecurity.com"
    FILES_URL = "https://packetstormsecurity.com/files/page/1/"

    def __init__(self):
        super().__init__("PacketStorm")

    def fetch_new_items(self):
        """Récupère les derniers fichiers depuis Packet Storm."""
        self.logger.info("🌪️ Scraping de Packet Storm Security...")
        
        # Le cookie 'AGREE=1' est souvent nécessaire pour bypasser le ToS wall
        headers = {
            "Referer": "https://packetstormsecurity.com/files/"
        }
        # Note: BaseConnector.stealth_get simple, on va lui passer les cookies si possible
        # Mais stealth_get ne supporte pas les cookies nativement dans sa signature actuelle
        # On va utiliser une approche directe si stealth_get est trop limité, 
        # ou enrichir l'appel si on peut.
        
        # Pour Packet Storm, on va tenter le coup avec stealth_get et espérer que l'UA suffise
        # ou que le ToS ne soit pas systématique pour l'UA utilisé.
        response = self.stealth_get(self.FILES_URL, headers=headers)
        
        if not response or response.status_code != 200:
            self.logger.error("❌ Impossible de scraper Packet Storm.")
            return []

        # Si on est redirigé vers le ToS, on réessaie avec le cookie
        if "frequently asked questions" in response.text.lower():
            self.logger.info("🛡️ ToS détecté, tentative de bypass avec cookie...")
            import requests
            # On utilise requests directement car stealth_get ne gère pas les cookies
            response = requests.get(self.FILES_URL, headers=headers, cookies={"AGREE": "1"}, timeout=30)
            if response.status_code != 200:
                return []

        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Les fichiers sont dans des balises <dl id="files">
            dl_files = soup.find('dl', id='files')
            if not dl_files:
                # Fallback sur tous les <dl> si l'ID a changé
                dl_files = soup.find_all('dl')
            else:
                dl_files = [dl_files]

            items = []
            for dl in dl_files:
                # Chaque fichier a un <dt> (titre/lien) et des <dd> (détails)
                dts = dl.find_all('dt')
                for dt in dts:
                    item = {"dt": dt}
                    # Les <dd> qui suivent le <dt> actuel jusqu'au prochain <dt>
                    next_node = dt.next_sibling
                    item["dds"] = []
                    while next_node and next_node.name != 'dt':
                        if next_node.name == 'dd':
                            item["dds"].append(next_node)
                        next_node = next_node.next_sibling
                    items.append(item)
            
            self.logger.info(f"✅ {len(items)} fichiers trouvés sur Packet Storm.")
            return items
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du parsing Packet Storm : {e}")
            return []

    def parse_item(self, item):
        """
        Transforme un bloc Packet Storm en ressource standard.
        """
        dt = item["dt"]
        dds = item["dds"]
        
        a_tag = dt.find('a')
        title = a_tag.text if a_tag else "Sans titre"
        link = self.BASE_URL + a_tag['href'] if a_tag else ""
        
        description = ""
        external_id = "PS-" + link.split('/')[-2] if '/' in link else "PS-Unknown"
        
        # Extraction de la description et de la date dans les <dd>
        for dd in dds:
            if 'class' in dd.attrs:
                if 'detail' in dd['class']:
                    description += dd.text.strip() + " "
                elif 'datetime' in dd['class']:
                    # La date est souvent "Feb 10, 2026"
                    pass # On peut l'extraire si besoin
            else:
                description += dd.text.strip() + " "

        return {
            "external_id": external_id,
            "title": title.strip(),
            "description": description.strip()[:500],
            "url": link,
            "raw_content_url": link, # Packet Storm propose des téléchargements directs sur la page
            "type_ressource": "Outil / Bulletin",
            "language": "en",
            "discovered_at": datetime.now()
        }

if __name__ == "__main__":
    # Test rapide
    logging.basicConfig(level=logging.INFO)
    connector = PacketStormConnector()
    files = connector.fetch_new_items()
    if files:
        print(f"Exemple : {connector.parse_item(files[0])}")
