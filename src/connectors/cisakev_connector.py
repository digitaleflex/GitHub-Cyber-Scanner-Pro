import logging
from datetime import datetime
from .base_connector import BaseConnector

class CisaKevConnector(BaseConnector):
    """
    Connecteur pour CISA Known Exploited Vulnerabilities (KEV).
    La référence mondiale des failles activement exploitées par des attaquants.
    """
    
    # Flux JSON officiel de la CISA
    JSON_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"

    def __init__(self):
        super().__init__("CISA-KEV")

    def fetch_new_items(self):
        """Télécharge le catalogue complet des vulnérabilités exploitées."""
        self.logger.info("🔥 Téléchargement du catalogue CISA KEV...")
        response = self.stealth_get(self.JSON_URL)
        
        if not response or response.status_code != 200:
            self.logger.error("❌ Impossible de récupérer le flux CISA KEV.")
            return []

        try:
            data = response.json()
            vulnerabilities = data.get("vulnerabilities", [])
            self.logger.info(f"✅ {len(vulnerabilities)} vulnérabilités critiques récupérées.")
            return vulnerabilities
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du parsing JSON CISA : {e}")
            return []

    def parse_item(self, item):
        """
        Transforme une entrée CISA KEV en ressource standard.
        Champs JSON : cveID, vendorProject, product, vulnerabilityName, dateAdded, shortDescription, requiredAction, dueDate, notes
        """
        cve_id = item.get("cveID")
        vendor = item.get("vendorProject")
        product = item.get("product")
        name = item.get("vulnerabilityName")
        
        title = f"[{cve_id}] {name} ({vendor} {product})"
        
        return {
            "external_id": cve_id,
            "title": title,
            "description": item.get("shortDescription"),
            "url": f"https://nvd.nist.gov/vuln/detail/{cve_id}",
            "raw_content_url": self.JSON_URL, # Source de vérité
            "type_ressource": "Intelligence / Alerte Critique",
            "language": "en",
            "discovered_at": datetime.now(),
            # Données spécifiques pour la table security_intel
            "security_details": {
                "cve_id": cve_id,
                "required_action": item.get("requiredAction"),
                "date_added": item.get("dateAdded")
            }
        }

if __name__ == "__main__":
    # Test rapide
    connector = CisaKevConnector()
    vulns = connector.fetch_new_items()
    if vulns:
        print(f"Exemple : {connector.parse_item(vulns[0])}")
