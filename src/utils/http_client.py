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
    Utilise curl_cffi pour usurper l'empreinte TLS (JA3) et simule les Client Hints (Sec-CH).
    """

    def __init__(self, impersonate="chrome120", max_retries=5):
        self.ua = UserAgent(browsers=['chrome', 'firefox', 'edge'], os=['windows', 'macos'])
        self.impersonate = impersonate
        self.max_retries = max_retries
        self.session = None

    def _generate_perfect_headers(self):
        """Forge une identité humaine parfaite avec Headers et Client Hints synchronisés."""
        browser_user_agent = self.ua.random

        # Détection de la plateforme pour synchroniser les en-têtes Sec-CH
        platform = "Windows"
        if "Macintosh" in browser_user_agent:
            platform = "macOS"
        elif "Linux" in browser_user_agent:
            platform = "Linux"

        headers = {
            'User-Agent': browser_user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': f'"{platform}"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        }
        return headers

    async def __aenter__(self):
        self.session = AsyncSession(impersonate=self.impersonate)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def request(self, method, url, **kwargs):
        """
        Exécute une requête avec rotation de 'Perfect Headers' et gestion du Rate-Limit.
        """
        retries = 0
        base_delay = 5  # Secondes

        while retries < self.max_retries:
            # 1. Génération de l'identité humaine complète (Headers + Client Hints)
            if "headers" not in kwargs:
                kwargs["headers"] = self._generate_perfect_headers()

            try:
                logging.info(f"🌐 [{method}] {url} (Essai {retries + 1}/{self.max_retries})")
                response = await self.session.request(method, url, **kwargs)
                # 2. Gestion intelligente du Rate-Limit (429 Too Many Requests)
                if response.status_code == 429:
                    # Calcul du délai exponentiel avec Jitter (aléatoire) pour paraître humain
                    delay = (base_delay * (2 ** retries)) + random.uniform(0, 5) # nosec B311
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
