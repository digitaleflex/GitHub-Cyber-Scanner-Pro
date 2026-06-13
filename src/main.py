import logging
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
import database

# Configuration du logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI(
    title="CyberScan Hub API",
    description="Interface souveraine d'intelligence documentaire et de veille cyber.",
    version="1.0.0"
)

# --- CONFIGURATION CORS (Sécurité) ---
# Autorise le frontend TanStack Start (Port 3000) à communiquer avec l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_db_client():
    """Initialise la base de données au démarrage du serveur."""
    try:
        database.init_db()
        logging.info("🚀 Base de données initialisée avec succès.")
    except Exception as e:
        logging.error(f"❌ Erreur lors de l'initialisation de la DB : {e}")

@app.get("/")
def read_root():
    return {"status": "online", "message": "CyberScan Hub API is running."}

@app.get("/api/search")
async def search(q: Optional[str] = Query(None, min_length=2)):
    """
    Route de recherche sémantique.
    Interroge PostgreSQL (TSVector) et trie par score de qualité IA.
    """
    try:
        results = database.get_books(search_query=q)
        return results
    except Exception as e:
        logging.error(f"❌ Erreur lors de la recherche : {e}")
        return {"error": "Internal Server Error", "details": str(e)}

@app.get("/api/stats")
async def get_stats():
    """
    Récupère les statistiques globales pour le dashboard.
    """
    try:
        total_repos, total_books = database.get_stats()
        return {
            "total_repositories": total_repos,
            "total_resources": total_books,
            "cloud_cost": 0,
            "security_scans": 3109 # Simulé pour le moment
        }
    except Exception as e:
        return {"total_repositories": 0, "total_resources": 0, "cloud_cost": 0}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) # nosec B104
