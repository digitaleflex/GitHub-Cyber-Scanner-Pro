import asyncio
import logging

import database
from nlp_processor import (
    CyberTextAnalyzer,
    categorize_by_semantic_ontology,
    clean_and_lemmatize,
    detect_resource_type,
)
from utils.http_client import StealthClient

# Configuration du logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class OSINTHarvester:
    """
    Orchestrateur de collecte OSINT : Dorking -> Scraping Furtif -> IA NLP -> PostgreSQL.
    """

    def __init__(self):
        self.analyzer = CyberTextAnalyzer()
        # On s'assure que la base de données est prête
        try:
            database.init_db()
        except:
            pass

    async def process_url(self, client, url, title, repo_id="OSINT_DISCOVERY"):
        """
        Traite une URL unique trouvée via un Dork : Scrape, Analyse, Score et Sauvegarde.
        """
        try:
            # 1. Scraping Furtif du contenu (On limite à 2000 caractères pour l'analyse sémantique)
            response = await client.get(url, timeout=15)
            if not response or response.status_code != 200:
                return False

            content = response.text[:2000] if response.text else ""

            # 2. Analyse Sémantique & Scoring IA
            analysis = self.analyzer.process_repository({
                "description": content,
                "full_name": title,
                "stars": 50 # On simule une autorité moyenne pour les découvertes web
            })

            # 3. Filtrage : On ne garde que les pépites (Score > 60)
            if analysis["score_qualite"] < 60:
                logging.info(f"⏩ Ressource ignorée (Score {analysis['score_qualite']}) : {title}")
                return False

            # 4. Catégorisation & Typage
            lemmas = clean_and_lemmatize(content)
            category = categorize_by_semantic_ontology(title, content, lemmas)
            resource_type = detect_resource_type(title, content, url, category)

            # 5. Sauvegarde en Base de Données
            # Note : repo_id est factice pour les découvertes OSINT pures
            success = database.save_book(
                repo_id=repo_id,
                title=title,
                url=url,
                category=category,
                lemmas_list=lemmas,
                type_ressource=resource_type
            )

            if success:
                logging.info(f"💎 Pépite enregistrée [{analysis['score_qualite']}/100] : {title} ({resource_type})")
            return success

        except Exception as e:
            logging.error(f"❌ Erreur lors du traitement de l'URL {url} : {e}")
            return False

    async def run_dork_pipeline(self, dorks_map):
        """
        Exécute une liste de Dorks via SearXNG (ou autre moteur) et traite les résultats.
        """
        # On utilise le StealthClient pour toutes les opérations réseau
        async with StealthClient() as client:
            for category, dorks in dorks_map.items():
                logging.info(f"📂 Lancement de la campagne OSINT : {category}")

                for dork in dorks:
                    # Simule une recherche via SearXNG local (Port 8080 par défaut)
                    # Note : Dans un environnement réel, on interroge l'API JSON de SearXNG
                    searx_url = "http://localhost:8080/search"
                    params = {"q": dork, "format": "json"}

                    search_res = await client.get(searx_url, params=params)
                    if not search_res or search_res.status_code != 200:
                        logging.warning(f"⚠️ SearXNG non disponible ou erreur sur le dork : {dork}")
                        continue

                    results = search_res.json().get("results", [])
                    tasks = []
                    for res in results[:5]: # On limite à 5 résultats par dork pour le test
                        tasks.append(self.process_url(client, res["url"], res["title"]))

                    # Exécution asynchrone par lots pour la vitesse
                    await asyncio.gather(*tasks)

                    # Pause "humaine" entre les dorks pour la discrétion
                    await asyncio.sleep(random.uniform(10, 20))

# --- EXEMPLE D'UTILISATION (Simulé) ---
DORKS_EXEMPLE = {
    "books": [
        'filetype:pdf "hacking" "index of"',
        'intitle:"index of" /cybersecurity/books/'
    ]
}

if __name__ == "__main__":
    import random
    harvester = OSINTHarvester()
    # asyncio.run(harvester.run_dork_pipeline(DORKS_EXEMPLE))
    print("🚀 Algorithme OSINT Harvester prêt pour l'orchestration Celery.")
