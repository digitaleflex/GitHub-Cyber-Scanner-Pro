import asyncio
import os
import sys
import time
import aiohttp
import pandas as pd
from dotenv import load_dotenv

# Configurer l'encodage de la console sous Windows pour éviter les plantages avec les émojis
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

load_dotenv()

# --- CONFIGURATION AVANCÉE ---
KEYWORDS = "cybersecurity OR hacking OR pentest OR 'infosec' OR 'red team' OR 'blue team'"
CONTENT_TYPES = "books OR awesome OR list OR resources OR catalogue OR tools"
BASE_QUERY = f"{KEYWORDS} {CONTENT_TYPES}"

# Gestion du Pool de Tokens depuis le .env (Séparés par des virgules)
# Exemple dans le .env : GITHUB_TOKENS=ghp_token1,ghp_token2,ghp_token3
TOKENS_RAW = os.getenv("GITHUB_TOKENS", "")
if not TOKENS_RAW:
    # Fallback sur le GITHUB_TOKEN simple
    TOKENS_RAW = os.getenv("GITHUB_TOKEN", "")

GITHUB_TOKENS = [t.strip() for t in TOKENS_RAW.split(",") if t.strip()]

# Définition des tranches d'étoiles (Slicing) pour contourner la limite des 1000 résultats
# On affine les tranches là où il y a le plus de micro-projets (entre 0 et 100 stars)
STAR_SLICES = [
    "0..2", "3..5", "6..10", "11..20", "21..35", "36..50", 
    "51..75", "76..100", "101..150", "151..250", "251..500", 
    "501..1000", "1001..3000", "3001..5000", ">5000"
]

class GitHubMassScanner:
    def __init__(self):
        self.all_repositories = {}
        self.token_index = 0

    def get_active_token(self):
        """Assure la rotation des jetons d'API pour éviter le blocage."""
        if not GITHUB_TOKENS:
            return None
        token = GITHUB_TOKENS[self.token_index]
        # Alterne vers le token suivant pour la prochaine requête
        self.token_index = (self.token_index + 1) % len(GITHUB_TOKENS)
        return token

    async def fetch_page(self, session, slice_range, page):
        """Télécharge de manière asynchrone une page spécifique d'une tranche d'étoiles."""
        url = "https://api.github.com/search/repositories"
        query = f"{BASE_QUERY} stars:{slice_range}"
        
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": 100,  # Maximum autorisé par page
            "page": page
        }
        
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        token = self.get_active_token()
        if token:
            headers["Authorization"] = f"token {token}"

        try:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("items", [])
                elif response.status == 403:
                    # Lecture des en-têtes de réinitialisation si limite atteinte
                    reset_time = response.headers.get("X-RateLimit-Reset", "inconnu")
                    print(f"⚠️ Rate limit atteint pour la tranche {slice_range} (Page {page}). Reset prévu à : {reset_time}")
                    return []
                else:
                    print(f"❌ Erreur API GitHub [{response.status}] sur la tranche {slice_range}")
                    return []
        except Exception as e:
            print(f"❌ Échec de la connexion réseau : {e}")
            return []

    async def scan_slice(self, session, slice_range):
        """Scanne les 10 pages autorisées (1000 résultats max) pour une tranche donnée."""
        print(f"🚀 Initialisation du scan pour la tranche d'étoiles : [stars:{slice_range}]")
        
        # On lance les requêtes pour les 10 pages simultanément en arrière-plan
        tasks = [self.fetch_page(session, slice_range, page) for page in range(1, 11)]
        pages_results = await asyncio.gather(*tasks)
        
        slice_count = 0
        for items in pages_results:
            for item in items:
                repo_id = str(item.get("id"))
                if repo_id not in self.all_repositories:
                    self.all_repositories[repo_id] = {
                        "Nom du Dépôt": item.get("full_name"),
                        "Étoiles (Stars)": item.get("stargazers_count"),
                        "Description": item.get("description") if item.get("description") else "Aucune description.",
                        "Lien GitHub": item.get("html_url"),
                        "Langue Principale": item.get("language") if item.get("language") else "Non spécifiée",
                        "Dernière Mise à Jour": item.get("updated_at")
                    }
                    slice_count += 1
        
        print(f"✅ Tranche [stars:{slice_range}] terminée : +{slice_count} dépôts uniques ajoutés.")

    async def start_mass_harvesting(self):
        """Orchestre le scan de toutes les tranches en parallèle."""
        start_time = time.time()
        
        # Limite le nombre de connexions TCP simultanées pour ne pas saturer la machine
        connector = aiohttp.TCPConnector(limit_per_host=10)
        
        async with aiohttp.ClientSession(connector=connector) as session:
            # Création de la liste de tâches pour chaque tranche d'étoiles
            tasks = [self.scan_slice(session, slice_range) for slice_range in STAR_SLICES]
            # Exécution de l'asynchronisme de masse
            await asyncio.gather(*tasks)
            
        duration = time.time() - start_time
        print(f"\n🎯 Extraction de masse achevée en {duration:.2f} secondes !")
        print(f"📊 Nombre total de ressources uniques en mémoire : {len(self.all_repositories)}")
        
        # Sauvegarde d'urgence au format Excel / Prêt pour insertion en base de données
        if self.all_repositories:
            # Assurer que le dossier local de données de sauvegarde temporaire existe
            os.makedirs("data", exist_ok=True)
            df = pd.DataFrame(list(self.all_repositories.values()))
            df.to_excel("data/mass_cyber_raw_data.xlsx", index=False)
            print("💾 Fichier temporaire [data/mass_cyber_raw_data.xlsx] généré avec succès.")

if __name__ == "__main__":
    scanner = GitHubMassScanner()
    asyncio.run(scanner.start_mass_harvesting())
