import logging
from bs4 import BeautifulSoup
from datetime import datetime
from .base_connector import BaseConnector

class CISBenchmarksConnector(BaseConnector):
    """
    Connecteur pour les CIS Benchmarks.
    Récupère la liste des checklists de durcissement (Hardening).
    """
    
    URL = "https://www.cisecurity.org/cis-benchmarks/"

    def __init__(self):
        super().__init__("CISBenchmarks")

    def fetch_new_items(self):
        """Scrape la liste des benchmarks sur le site du CIS."""
        self.logger.info("🛡️ Récupération des CIS Benchmarks...")
        response = self.stealth_get(self.URL)
        
        if not response or response.status_code != 200:
            self.logger.error("❌ Impossible de charger la page des benchmarks.")
            return []

        try:
            soup = BeautifulSoup(response.content, 'lxml')
            benchmarks = []
            
            # Recherche des noms de benchmarks (souvent dans des cartes ou des listes)
            # Sur CIS, ils sont souvent dans des éléments avec une classe spécifique
            # On va chercher les titres qui pointent vers les pages de benchmarks
            for a in soup.find_all('a', href=True):
                if '/benchmark/' in a['href']:
                    name = a.text.strip()
                    # Si le texte est générique ou vide, on utilise le slug de l'URL
                    if not name or name.lower() in ['click here', 'learn more', 'download']:
                        name = a['href'].split('/')[-1].replace('_', ' ').replace('-', ' ').title()
                    
                    if name and name not in [b['name'] for b in benchmarks]:
                        benchmarks.append({
                            'name': name,
                            'url': a['href'] if a['href'].startswith('http') else "https://www.cisecurity.org" + a['href']
                        })
            
            self.logger.info(f"✅ {len(benchmarks)} benchmarks trouvés.")
            return benchmarks
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du scraping CIS : {e}")
            return []

    def parse_item(self, item):
        """Formatage d'un benchmark."""
        return {
            "external_id": f"CIS-BM-{hash(item['url'])}",
            "title": f"CIS Benchmark: {item['name']}",
            "description": f"Guide de durcissement officiel CIS pour {item['name']}.",
            "url": item['url'],
            "raw_content_url": item['url'],
            "type_ressource": "Checklist de Durcissement",
            "language": "en",
            "discovered_at": datetime.now()
        }

if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    connector = CISBenchmarksConnector()
    items = connector.fetch_new_items()
    if items:
        print(f"Exemple : {connector.parse_item(items[0])}")
