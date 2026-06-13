import os
import json
import logging
import requests

# Configuration du logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class LLMSummarizer:
    def __init__(self, host=None, model=None):
        self.host = host if host else os.getenv("OLLAMA_HOST", "localhost")
        self.model = model if model else os.getenv("LLM_MODEL", "mistral")
        self.url = f"http://{self.host}:11434/api/generate"

    def generate_summary(self, readme_text, description=""):
        """Génère une fiche de synthèse 3 lignes via Ollama."""
        if not readme_text and not description:
            return None

        prompt = f"""
        En tant qu'expert en cybersécurité, analyse le contenu suivant d'un dépôt GitHub et génère une fiche technique SYNTHÉTIQUE au format JSON STRICT.
        
        CONTENU À ANALYSER :
        Description : {description}
        Extrait du README : {readme_text[:2000]}
        
        FORMAT DE RÉPONSE (JSON UNIQUEMENT) :
        {{
            "objectif": "Une phrase claire sur l'utilité de l'outil.",
            "prerequis": "Liste courte des langages ou outils nécessaires.",
            "commande_flash": "La commande exacte pour lancer ou installer l'outil rapidement."
        }}
        
        Réponds uniquement avec le JSON, sans introduction ni conclusion.
        """

        try:
            logging.info(f"🤖 Envoi de la requête à Ollama ({self.model})...")
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json"
            }
            
            response = requests.post(self.url, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                try:
                    summary_data = json.loads(result.get("response", "{}"))
                    return summary_data
                except json.JSONDecodeError:
                    logging.error("❌ Erreur de décodage JSON de la réponse LLM.")
                    return None
            else:
                logging.error(f"❌ Erreur Ollama : {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logging.error(f"❌ Échec de la connexion à Ollama : {e}")
            return None

if __name__ == "__main__":
    # Test local
    summarizer = LLMSummarizer()
    test_text = "sqlmap is an open source penetration testing tool that automates the process of detecting and exploiting SQL injection flaws."
    # res = summarizer.generate_summary(test_text)
    # print(res)
