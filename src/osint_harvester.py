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
        except Exception:
            logging.debug("Init failed safely")

    def extract_text_from_pdf(self, pdf_content):
        """Extrait le texte d'un PDF à partir de son contenu binaire (via PyMuPDF)."""
        import fitz
        try:
            doc = fitz.open(stream=pdf_content, filetype="pdf")
            text = ""
            # On extrait les 5 premières pages pour éviter les documents trop lourds
            for page in doc[:5]:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            logging.error(f"❌ Erreur lors de l'extraction PDF : {e}")
            return ""

    async def process_url(self, client, url, title, repo_id="OSINT_DISCOVERY"):
        """
        Traite une URL unique trouvée via un Dork : Scrape (PDF ou HTML), Analyse, Score et Sauvegarde.
        """
        try:
            # 1. Scraping Furtif du contenu
            response = await client.get(url, timeout=20)
            if not response or response.status_code != 200:
                return False

            # Gestion différenciée selon le type de fichier
            if url.lower().endswith(".pdf") or "application/pdf" in response.headers.get("Content-Type", ""):
                content = self.extract_text_from_pdf(response.content)
                is_pdf = True
            else:
                content = response.text
                is_pdf = False

            if not content or len(content.strip()) < 100:
                return False

            # On limite à 4000 caractères pour l'analyse sémantique
            content_sample = content[:4000]

            # 2. Analyse Sémantique & Scoring IA
            analysis = self.analyzer.process_repository({
                "description": content_sample,
                "full_name": title,
                "stars": 50 # On simule une autorité moyenne pour les découvertes web
            })

            # 3. Filtrage : On ne garde que les pépites (Score > 60)
            if analysis["score_qualite"] < 60:
                logging.info(f"⏩ Ressource ignorée (Score {analysis['score_qualite']}) : {title}")
                return False

            # 4. Catégorisation & Typage
            lemmas = clean_and_lemmatize(content_sample)
            category = categorize_by_semantic_ontology(title, content_sample, lemmas)
            resource_type = "Livre PDF" if is_pdf else detect_resource_type(title, content_sample, url, category)

            # 5. Sauvegarde en Base de Données (Postgres + Qdrant via task_nlp_analysis)
            # On utilise task_nlp_analysis pour s'assurer que les vecteurs vont dans Qdrant
            from src.tasks import task_nlp_analysis
            
            repo_data = {
                "full_name": title,
                "description": content_sample,
                "html_url": url,
                "stargazers_count": 50,
                "language": "PDF" if is_pdf else "HTML",
                "category": category,
                "type_ressource": resource_type
            }
            
            # On lance l'analyse NLP asynchrone qui va tout sauvegarder
            task_nlp_analysis.delay(repo_data)

            logging.info(f"💎 Pépite envoyée au pipeline IA [{analysis['score_qualite']}/100] : {title} ({resource_type})")
            return True

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
                    await asyncio.sleep(random.uniform(10, 20)) # nosec B311

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
