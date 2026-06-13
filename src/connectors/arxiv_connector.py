import logging
import xml.etree.ElementTree as ET # nosec B405
from datetime import datetime
from .base_connector import BaseConnector

class ArxivConnector(BaseConnector):
    """
    Connecteur pour arXiv (Section cs.CR - Cryptography and Security).
    Récupère les dernières thèses, articles et livres blancs.
    """
    
    # API Atom d'arXiv pour la cybersécurité, triée par date de soumission
    API_URL = "http://export.arxiv.org/api/query?search_query=cat:cs.CR&sortBy=submittedDate&sortOrder=descending&max_results=50"

    def __init__(self):
        super().__init__("arXiv")

    def fetch_new_items(self):
        """Interroge l'API arXiv pour récupérer les publications récentes."""
        self.logger.info("📚 Interrogation de l'API arXiv (cs.CR)...")
        response = self.stealth_get(self.API_URL)
        
        if not response or response.status_code != 200:
            self.logger.error("❌ Impossible de joindre l'API arXiv.")
            return []

        try:
            # Parser le flux XML Atom
            root = ET.fromstring(response.content) # nosec B314
            # Les namespaces Atom
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            entries = root.findall('atom:entry', ns)
            self.logger.info(f"✅ {len(entries)} articles académiques trouvés.")
            return entries
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du parsing XML arXiv : {e}")
            return []

    def parse_item(self, entry):
        """
        Transforme une entrée Atom arXiv en ressource standard.
        """
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        arxiv_id = entry.find('atom:id', ns).text.split('/')[-1]
        title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
        summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')
        published = entry.find('atom:published', ns).text
        
        # Trouver le lien PDF
        pdf_url = ""
        for link in entry.findall('atom:link', ns):
            if link.get('title') == 'pdf':
                pdf_url = link.get('href')
                break
        
        # Si pas de lien PDF explicite, on le déduit de l'ID
        if not pdf_url:
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

        return {
            "external_id": f"ARXIV-{arxiv_id}",
            "title": title,
            "description": summary[:500] + "...", # On limite la description pour la table
            "url": f"https://arxiv.org/abs/{arxiv_id}",
            "raw_content_url": pdf_url,
            "type_ressource": "Livre / Thèse / Papier",
            "language": "en",
            "discovered_at": datetime.now()
        }

if __name__ == "__main__":
    # Test rapide
    connector = ArxivConnector()
    articles = connector.fetch_new_items()
    if articles:
        print(f"Exemple : {connector.parse_item(articles[0])}")
