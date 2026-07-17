import logging
import os
import random
import time

import requests

# Ordre de préférence : les tokens sont lus depuis l'env GH_TOKENS (séparés par virgule)
# ou GITHUB_TOKEN (unique).
_TOKENS_ENV = os.getenv("GH_TOKENS", "")
_PRIMARY = os.getenv("GITHUB_TOKEN", "")

TOKENS = []
if _PRIMARY:
    TOKENS.append(_PRIMARY)
if _TOKENS_ENV:
    for t in _TOKENS_ENV.split(","):
        t = t.strip()
        if t and t not in TOKENS:
            TOKENS.append(t)

if not TOKENS:
    logging.warning("⚠️ Aucun token GitHub configuré (GITHUB_TOKEN / GITHUB_TOKENS)")

# État de quota par token : on mémorise le timestamp de reset pour éviter de retenter un token bloqué
_token_reset = dict.fromkeys(TOKENS, 0.0)
_token_lock = None  # pas de verrou strict nécessaire pour le round-robin simple


def _available_tokens():
    now = time.time()
    avail = [t for t in TOKENS if _token_reset[t] <= now]
    return avail


def _request(url, params=None, headers_extra=None, max_retries=6, timeout=20):
    """Requête GitHub avec rotation de tokens et gestion de rate-limit (core + search)."""
    base_headers = {"Accept": "application/vnd.github.v3+json"}
    if headers_extra:
        base_headers.update(headers_extra)

    if not TOKENS:
        logging.error("❌ Aucun token GitHub configuré (GITHUB_TOKEN / GH_TOKENS)")
        return [], True

    for attempt in range(max_retries):
        avail = _available_tokens()
        if not avail:
            # Tous les tokens sont au repo : on attend le prochain reset
            wait = max(1.0, min(_token_reset.values()) - time.time()) + 2.0
            logging.warning(f"⏸️ Tous les tokens saturés. Pause {int(wait)}s")
            time.sleep(wait)
            continue

        token = random.choice(avail)
        headers = dict(base_headers)
        headers["Authorization"] = f"token {token}"

        try:
            r = requests.get(url, params=params, headers=headers, timeout=timeout)
            remaining = r.headers.get("X-RateLimit-Remaining")
            reset = r.headers.get("X-RateLimit-Reset")

            if r.status_code == 200:
                return r.json(), False

            if r.status_code == 403:
                # Rate limit secondaire (abuse) ou quota épuisé
                retry_after = r.headers.get("Retry-After")
                if retry_after:
                    wait = float(retry_after) + 2
                    logging.warning(f"⏸️ Abuse limit (token {token[:10]}...). Pause {int(wait)}s")
                    time.sleep(wait)
                    continue
                if reset:
                    try:
                        _token_reset[token] = float(reset) + 5.0
                        wait = max(1.0, float(reset) - time.time()) + 5.0
                        logging.warning(f"⏸️ Quota token {token[:10]}... épuisé. Pause {int(wait)}s")
                    except ValueError:
                        pass
                    continue
                time.sleep(3)
                continue

            if r.status_code in (404, 410):
                return [], False

            if r.status_code >= 500:
                time.sleep(2 * (attempt + 1))
                continue

            # Autre erreur
            logging.error(f"❌ API GitHub {r.status_code}: {r.text[:200]}")
            return [], False

        except requests.exceptions.RequestException as e:
            logging.error(f"🔌 Erreur réseau: {e}")
            time.sleep(3)
            continue

    logging.error(f"❌ Échec après {max_retries} tentatives: {url}")
    return [], True


def get_json(url, params=None, headers=None):
    """Retourne (data, rate_hit)."""
    return _request(url, params=params, headers_extra=headers)


def token_count():
    return len(TOKENS)


def active_tokens():
    return _available_tokens()
