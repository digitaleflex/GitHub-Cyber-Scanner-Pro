"""Cyber Risk Engine (v2) — contextualise la decision par l'environnement utilisateur.

Principe (modele hybride, cf. revue d'architecture) :

    Risk = Threat  ×  Exposure × Business

La decision `score_cve()` fournit la dimension *Threat* (CVSS, KEV, EPSS, exploits...).
Ce module ajoute le contexte *asset* : si des actifs de l'organisation correspondent
a la CVE (nom/fournisseur/version), le score est multiplie selon leur **criticalite**
(1-5) et leur **exposition** (Internet/DMZ). Une CVE sur un actif critique expose
vaut plus qu'une CVE sur un serveur de test.

Regles de transparence :
- pas de match asset -> multiplicateur neutre (1.0), pas de penalite si l'inventaire
  est incomplet (eviter les faux negatifs) ;
- chaque multiplicateur est justifie (matched_assets, factors) ;
- le score de base reste disponible, `contextual_score` est l'alea decisionnel.
"""
import logging
import re

from src.database import get_db_connection

_TOKEN_RE = re.compile(r"[a-z0-9]{3,}")

# Poids du contexte sur le score de base (bornes max)
CRITICALITY_STEP = 0.06      # +0.06 par point de criticalite au-dessus de 1
EXPOSED_BONUS = 0.15         # +0.15 si actif expose
KEV_EXPOSED_BONUS = 0.15     # +0.15 supplementaire si KEV + actif expose
MAX_MULTIPLIER = 1.5

_IGNORED_TOKENS = {
    "the", "and", "for", "with", "from", "tool", "tools", "security", "software",
    "server", "service", "services", "system", "systems", "application", "apps",
    "vulnerability", "vulnerabilities", "remote", "local", "via", "allow", "allows",
    "cause", "execute", "execution", "code", "arbitrary", "attack", "attacker",
    "could", "may", "this", "that", "with", "before", "after", "version", "versions",
    "information", "disclosure", "user", "users", "web", "http", "https", "affected",
}


class RiskContext:
    """Contexte utilisateur charge une fois (evite N requetes par CVE en batch)."""

    def __init__(self, profile_id: int | None, role: str, assets: list[dict]):
        self.profile_id = profile_id
        self.role = role
        self.assets = assets

    @property
    def has_assets(self) -> bool:
        return bool(self.assets)

    @property
    def max_criticality(self) -> int:
        return max((a.get("criticality") or 1) for a in self.assets) if self.assets else 1


def load_context(profile_id: int | None = None) -> RiskContext:
    """Charge le contexte utilisateur (profil + inventaire d'actifs)."""
    if not profile_id:
        return RiskContext(None, "non_defini", [])

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT role, org_id FROM user_profiles WHERE id = %s", (profile_id,)
        )
        row = cursor.fetchone()
        if not row:
            return RiskContext(profile_id, "non_defini", [])
        role, org_id = row[0] or "non_defini", row[1]
        assets = []
        if org_id:
            cursor.execute(
                """SELECT asset_type, name, vendor, version, exposed, criticality
                   FROM asset_inventory WHERE org_id = %s ORDER BY criticality DESC""",
                (org_id,),
            )
            for asset_type, name, vendor, version, exposed, crit in cursor.fetchall():
                assets.append({
                    "asset_type": asset_type,
                    "name": name or "",
                    "vendor": vendor or "",
                    "version": version or "",
                    "exposed": bool(exposed),
                    "criticality": crit if crit else 3,
                })
        return RiskContext(profile_id, role, assets)
    finally:
        cursor.close()
        conn.close()


def _tokens(text: str) -> set:
    return {t for t in _TOKEN_RE.findall((text or "").lower()) if t not in _IGNORED_TOKENS}


def _match_score(asset: dict, cve_tokens: set, products: list[dict]) -> tuple[int, dict]:
    """Score de correspondance asset <-> CVE (0..3) + detail du match."""
    detail = {"mode": None, "matched": [], "version_ok": None}
    score = 0

    name_tokens = _tokens(asset.get("name") or "")
    vendor_tokens = _tokens(asset.get("vendor") or "")
    all_asset = name_tokens | vendor_tokens
    if not all_asset:
        return 0, detail

    # 1) Produits affectes declares (cve_affected_products)
    for p in products:
        prod_tokens = _tokens(p.get("product") or "") | _tokens(p.get("vendor") or "")
        if all_asset & prod_tokens:
            score = max(score, 3)
            detail["mode"] = "product"
            detail["matched"].append(f"{p.get('product') or ''} {p.get('vendor') or ''}".strip())
            if asset.get("version") and p.get("version"):
                detail["version_ok"] = asset["version"] in str(p["version"]) or str(p["version"]) in asset["version"]
            break

    # 2) Description CVE (token match, plus faible que le produit declare)
    if score < 3 and all_asset & cve_tokens:
        score = max(score, 1)
        detail["mode"] = "description"
        detail["matched"] = sorted(all_asset & cve_tokens)[:4]

    return score, detail


def contextualize_decision(decision: dict, cve_id: str, context: RiskContext) -> dict:
    """Applique le contexte asset a une decision. Retourne la decision enrichie."""
    out = dict(decision)
    out["contextual_score"] = out.get("score", 0)
    out["contextual_level"] = out.get("level")
    out["context_multiplier"] = 1.0
    out["matched_assets"] = []
    out["context_factors"] = {}
    out["context_note"] = ""

    if not context.has_assets:
        out["context_note"] = "Aucun inventaire d'actifs — decision basee uniquement sur la menace."
        return out

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT product, vendor, version FROM cve_affected_products WHERE cve_id = %s",
            (cve_id.upper(),),
        )
        products = [
            {"product": r[0], "vendor": r[1], "version": r[2]}
            for r in cursor.fetchall()
        ]
    finally:
        cursor.close()
        conn.close()

    cve_tokens = _tokens(decision.get("description") or "")

    matched = []
    for asset in context.assets:
        s, det = _match_score(asset, cve_tokens, products)
        if s > 0:
            matched.append({
                "name": asset["name"],
                "vendor": asset["vendor"],
                "version": asset["version"],
                "criticality": asset["criticality"],
                "exposed": asset["exposed"],
                "match_mode": det["mode"],
                "version_ok": det["version_ok"],
            })

    if not matched:
        out["context_note"] = "Aucun actif de l'organisation ne correspond a cette CVE."
        return out

    max_crit = max((m["criticality"] for m in matched), default=1)
    any_exposed = any(m["exposed"] for m in matched)
    is_kev = bool(out.get("is_kev"))

    multiplier = 1.0 + CRITICALITY_STEP * (max_crit - 1)
    if any_exposed:
        multiplier += EXPOSED_BONUS
    if is_kev and any_exposed:
        multiplier += KEV_EXPOSED_BONUS
    multiplier = min(multiplier, MAX_MULTIPLIER)

    base = out.get("score", 0)
    contextual = max(0, min(100, round(base * multiplier)))
    level = "CRITIQUE" if contextual >= 75 else "ELEVE" if contextual >= 50 else "MOYEN" if contextual >= 25 else "BAS"

    out["contextual_score"] = contextual
    out["contextual_level"] = level
    out["context_multiplier"] = round(multiplier, 3)
    out["matched_assets"] = matched
    out["context_factors"] = {
        "max_criticality": max_crit,
        "any_exposed": any_exposed,
        "kev": is_kev,
        "assets_matched": len(matched),
        "multiplier": round(multiplier, 3),
    }
    parts = [f"{len(matched)} actif(s) impacte(s) (criticalite max {max_crit})"]
    if any_exposed:
        parts.append("expose(s) a Internet/DMZ")
    if is_kev and any_exposed:
        parts.append("KEV + exposition -> sur-multiplication")
    out["context_note"] = ", ".join(parts) + "."

    return out


def get_context_summary(profile_id: int | None = None) -> dict:
    """Resume du contexte asset pour l'UI (couverture, criticalite max, exposition)."""
    context = load_context(profile_id)
    if not context.has_assets:
        return {
            "profile_id": profile_id,
            "role": context.role,
            "assets": 0,
            "assets_exposed": 0,
            "max_criticality": None,
        }
    return {
        "profile_id": profile_id,
        "role": context.role,
        "assets": len(context.assets),
        "assets_exposed": sum(1 for a in context.assets if a.get("exposed")),
        "max_criticality": context.max_criticality,
        "sample": context.assets[:10],
    }
