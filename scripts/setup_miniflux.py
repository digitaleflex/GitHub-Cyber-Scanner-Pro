"""
Setup du collecteur RSS Miniflux pour CyberScan Pro.

- Verifie que Miniflux repond (healthcheck).
- S'authentifie via HTTP Basic Auth (admin/user + password) et genere un token API.
- Ecrit MINIFLUX_TOKEN dans le .env (sans ecraser les autres variables).
- Pousse les flux RSS (src/rss_feed.RSS_FEEDS) vers Miniflux.

Attention: depuis Miniflux 2.3, /v1/auth/login et /v1/me/api-key ont disparu.
L'auth passe par HTTP Basic Auth, et les cles API se creent via POST /v1/api-keys.

Usage:
    python scripts/setup_miniflux.py
    python scripts/setup_miniflux.py --url http://localhost:8080
"""

import argparse
import base64
import os
import sys

try:
    import requests
except ImportError:
    print("❌ 'requests' requis: pip install requests")
    sys.exit(1)

ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")


def load_env(path: str) -> dict:
    env = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def save_env_key(path: str, key: str, value: str) -> None:
    """Met a jour/ajoute une cle dans .env sans toucher au reste."""
    lines = []
    found = False
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
    out = []
    for line in lines:
        if line.strip().startswith(f"{key}="):
            out.append(f"{key}={value}\n")
            found = True
        else:
            out.append(line if line.endswith("\n") else line + "\n")
    if not found:
        out.append(f"{key}={value}\n")
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=None, help="URL API Miniflux (defaut: MINIFLUX_URL du .env)")
    args = ap.parse_args()

    env = load_env(ENV_PATH)
    base = (args.url or env.get("MINIFLUX_URL", "http://localhost:8080")).rstrip("/")
    user = env.get("MINIFLUX_ADMIN_USER", "admin")
    password = env.get("MINIFLUX_ADMIN_PASSWORD", "")

    if not password:
        print("❌ MINIFLUX_ADMIN_PASSWORD absent du .env")
        return 1

    print(f"🔗 Connexion a Miniflux: {base}")
    try:
        hc = requests.get(f"{base}/healthcheck", timeout=10)
        if hc.status_code != 200:
            print(f"❌ Miniflux non operationnel (HTTP {hc.status_code}). Lance 'docker compose up -d' d'abord.")
            return 1
    except Exception as e:
        print(f"❌ Miniflux inaccessible: {e}")
        return 1

    # Auth via HTTP Basic Auth (Miniflux >= 2.3)
    b64 = base64.b64encode(f"{user}:{password}".encode()).decode()
    headers = {"Authorization": f"Basic {b64}", "Content-Type": "application/json"}
    r = requests.get(f"{base}/v1/me", headers=headers, timeout=10)
    if r.status_code != 200:
        print(f"❌ Echec authentification ({r.status_code}): {r.text[:120]}")
        print("   Verifiez MINIFLUX_ADMIN_USER / MINIFLUX_ADMIN_PASSWORD dans le .env.")
        return 1
    print(f"✅ Authentifie en tant que '{r.json().get('username')}' (Basic Auth)")

    # Genere un token API dedie (endpoint /v1/api-keys)
    ak = requests.post(
        f"{base}/v1/api-keys",
        headers=headers,
        json={"description": "CyberScan-Pro bridge"},
        timeout=10,
    )
    if ak.status_code != 201:
        print(f"❌ Creation de la cle API impossible ({ak.status_code}): {ak.text[:120]}")
        return 1
    api_token = ak.json().get("token") or ak.json().get("api_key")
    if not api_token:
        print(f"❌ Reponse inattendue de /v1/api-keys: {ak.text[:200]}")
        return 1
    print(f"🔑 Token API genere.")

    # Ecrit le token dans .env
    save_env_key(ENV_PATH, "MINIFLUX_TOKEN", api_token)
    save_env_key(ENV_PATH, "MINIFLUX_ENABLED", "true")
    save_env_key(ENV_PATH, "MINIFLUX_URL", base)
    print(f"✅ MINIFLUX_TOKEN enregistre dans {ENV_PATH}")

    # Pousse les flux RSS vers Miniflux
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    try:
        import src.miniflux_bridge as bridge
        bridge.MINIFLUX_URL = base
        bridge.MINIFLUX_TOKEN = api_token
        bridge.MINIFLUX_ENABLED = True
        nb = bridge.sync_feeds()
        bridge.refresh_all_feeds()
        print(f"📡 {nb} flux configures dans Miniflux. Refresh lance en arriere-plan.")
    except Exception as e:
        print(f"⚠️  Impossible de pousser les flux depuis ce script: {e}")
        print(f"    Le scanner les synchronisera automatiquement au prochain run.")

    print("\n✅ Setup Miniflux termine. Relance le scanner: python scripts/scan.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
