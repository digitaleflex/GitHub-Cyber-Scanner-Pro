import logging
import requests
from abc import ABC, abstractmethod

class BaseConnector(ABC):
    """Classe de base pour tous les connecteurs (StealthCyberClient)."""
    
    def __init__(self, source_name):
        self.source_name = source_name
        self.logger = logging.getLogger(f"Connector.{source_name}")

    @abstractmethod
    def fetch_new_items(self):
        """Récupère les nouvelles entrées depuis la source."""
        pass

    @abstractmethod
    def parse_item(self, item):
        """Transforme l'entrée brute en format standard 'resource'."""
        pass

    def stealth_get(self, url, headers=None):
        """Requête HTTP furtive (à enrichir avec curl_cffi)."""
        # Simulation d'un client furtif
        default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        if headers:
            default_headers.update(headers)
        
        try:
            response = requests.get(url, headers=default_headers, timeout=30)
            return response
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de la requête furtive sur {url} : {e}")
            return None
