# 🔍 Architecture Modulaire - Connecteurs OSINT Spécialisés

Pour transformer le scanner en véritable plateforme CTEM (Continuous Threat Exposure Management) et OSINT, le projet intègre des API spécialisées de moteurs de recherche de la cybersécurité.

## 1. Moteurs Spécialisés Incontournables

* **Shodan** : Moteur de recherche d'objets connectés et serveurs. Permet de trouver des serveurs exposant des bases de données ouvertes ou des ports vulnérables.
* **Censys** : Concurrent de Shodan, ultra-performant pour analyser les certificats SSL/TLS.
* **LeakIX** : Détecte les fuites d'informations et mauvaises configurations (fichiers `.env` exposés, dossiers `.git`).
* **GreyNoise / Criminal IP** : Analyse le "bruit de fond" d'Internet pour filtrer les scanners automatisés et qualifier la réputation IP.

## 2. Architecture Modulaire (Plugins)

Le développeur doit utiliser une approche modulaire en créant des connecteurs indépendants dans le dossier `src/connectors/`.

```text
src/connectors/
├── __init__.py
├── base_connector.py       <-- Classe parente (Interfaces, gestion des erreurs)
├── shodan_connector.py     <-- Appelle l'API de Shodan
├── censys_connector.py     <-- Appelle l'API de Censys
└── leakix_connector.py     <-- Appelle l'API de LeakIX
```

## 3. Exemple d'Implémentation (LeakIX)

```python
# src/connectors/leakix_connector.py
import os
import requests

class LeakixConnector:
    def __init__(self):
        # Clé API stockée en toute sécurité dans le fichier .env
        self.api_key = os.getenv("LEAKIX_API_KEY")
        self.base_url = "https://leakix.net"

    def search_leaks(self, keyword):
        """
        Cherche des vulnérabilités ou fuites réelles liées à un mot-clé.
        """
        if not self.api_key:
            return []

        headers = {
            "Accept": "application/json",
            "api-key": self.api_key,
        }
        params = {"q": f'"{keyword}" +country:"FR"', "scope": "leak"}

        try:
            response = requests.get(self.base_url, headers=headers, params=params)
            if response.status_code == 200:
                return response.json()
            return []
        except Exception as e:
            print(f"❌ Erreur lors de la requête LeakIX : {e}")
            return []
```

## 4. Stratégie Commerciale

* **Version Standard** : Recherche GitHub basique.
* **Version PRO** : "Recherche OSINT étendue" activée. Agrégation simultanée de GitHub, SearXNG, Shodan et LeakIX, avec injection dans la base vectorielle Qdrant.
