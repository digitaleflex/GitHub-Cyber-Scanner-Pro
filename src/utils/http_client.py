import asyncio
import logging
import random

from curl_cffi.requests import AsyncSession
from fake_useragent import UserAgent

# Configuration du logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class StealthClient:
    """
    Client HTTP asynchrone ultra-furtif conçu pour le contournement des WAF (Cloudflare, etc.).
    Utilise curl_cffi pour usurper l'empreinte TLS (JA3) et gère le Backoff exponentiel.
    """

    def __init__(self, impersonate="chrome120", max_retries=5):
        self.ua = UserAgent()
        self.impersonate = impersonate
        self.max_retries = max_retries
        self.session = None

    async def __aenter__(self):
        self.session = AsyncSession(impersonate=self.impersonate)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def request(self, method, url, **kwargs):
        """
        Exécute une requête avec rotation de User-Agent et gestion du Rate-Limit (429).
        """
        retries = 0
        base_delay = 5  # Secondes

        while retries < self.max_retries:
            # 1. Rotation dynamique du User-Agent si non spécifié
            headers = kwargs.get("headers", {})
            if "User-Agent" not in headers:
                headers["User-Agent"] = self.ua.random
            kwargs["headers"] = headers

            try:
                logging.info(f"🌐 [{method}] {url} (Essai {retries + 1}/{self.max_retries})")
                response = await self.session.request(method, url, **kwargs)

                # 2. Gestion intelligente du Rate-Limit (429 Too Many Requests)
                if response.status_code == 429:
                    # Calcul du délai exponentiel avec Jitter (aléatoire) pour paraître humain
                    delay = (base_delay * (2 ** retries)) + random.uniform(0, 5)
                    logging.warning(f"⚠️ Rate Limit (429) détecté sur {url}. Pause de {delay:.2f}s...")
                    await asyncio.sleep(delay)
                    retries += 1
                    continue

                # 3. Gestion des erreurs de type Forbidden (403) - Souvent un blocage WAF
                if response.status_code == 403:
                    logging.error(f"❌ Accès refusé (403) sur {url}. Le WAF a peut-être détecté une anomalie.")
                    # On tente quand même un retry après une longue pause
                    await asyncio.sleep(base_delay * 3)
                    retries += 1
                    continue

                return response

            except Exception as e:
                logging.error(f"🔥 Erreur réseau sur {url} : {e}")
                retries += 1
                await asyncio.sleep(base_delay)

        logging.critical(f"💀 Échec définitif après {self.max_retries} tentatives sur {url}")
        return None

    async def get(self, url, **kwargs):
        return await self.request("GET", url, **kwargs)

    async def post(self, url, **kwargs):
        return await self.request("POST", url, **kwargs)

# --- EXEMPLE D'UTILISATION ---
async def test_stealth():
    async with StealthClient() as client:
        # Test sur un site avec protection
        response = await client.get("https://httpbin.org/headers")
        if response:
            print(f"✅ Status: {response.status_code}")
            print(f"🔍 Empreinte détectée par le serveur : {response.json().get('headers', {}).get('User-Agent')}")

if __name__ == "__main__":
    asyncio.run(test_stealth())
