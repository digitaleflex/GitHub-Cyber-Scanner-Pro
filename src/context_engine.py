"""Context Engine — construit le profil personnalise de chaque utilisateur (organisation, assets, role).

Remplace le build_stack_keywords() global par un contexte individuel.
Le reranker semantique utilise ce contexte comme query au lieu des 18k repos globaux.
"""
import json
import logging
from datetime import datetime, timezone

from src import database


def ensure_profile(user_id: int | None = None, profile_id: int | None = None) -> dict:
    """Cree ou recupere un profil utilisateur. Retourne {id, role, preferences, org_id, onboarding_completed}."""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    if profile_id:
        cursor.execute("SELECT id, role, display_name, preferences, org_id, onboarding_completed FROM user_profiles WHERE id = %s", (profile_id,))
    elif user_id:
        cursor.execute("SELECT id, role, display_name, preferences, org_id, onboarding_completed FROM user_profiles WHERE id = %s", (user_id,))
    else:
        cursor.execute("INSERT INTO user_profiles (role) VALUES ('non_defini') RETURNING id, role, preferences, org_id, onboarding_completed")
        row = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        return _row_to_profile(row)
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO user_profiles (role) VALUES ('non_defini') RETURNING id, role, preferences, org_id, onboarding_completed")
        row = cursor.fetchone()
        conn.commit()
    cursor.close()
    conn.close()
    return _row_to_profile(row)


def _row_to_profile(row):
    if not row:
        return {"id": 0, "role": "non_defini", "preferences": {}, "org_id": None, "onboarding_completed": False}
    return {
        "id": row[0],
        "role": row[1],
        "display_name": row[2] or "",
        "preferences": row[3] if isinstance(row[3], dict) else json.loads(row[3] or "{}"),
        "org_id": row[4],
        "onboarding_completed": row[5] or False,
    }


def init_profile(profile_id: int, role: str, assets: list[dict], org_name: str = "", sector: str = "", compliance: str = "") -> dict:
    """Onboarding: configure le role, les assets, l'organisation en une etape."""
    conn = database.get_db_connection()
    cursor = conn.cursor()

    org_id = None
    if org_name:
        cursor.execute(
            "INSERT INTO organizations (name, sector, compliance_frameworks) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING RETURNING id",
            (org_name, sector, compliance),
        )
        row = cursor.fetchone()
        if row:
            org_id = row[0]
        else:
            cursor.execute("SELECT id FROM organizations WHERE name = %s", (org_name,))
            row = cursor.fetchone()
            if row:
                org_id = row[0]
                cursor.execute("UPDATE organizations SET sector = %s, compliance_frameworks = %s WHERE id = %s", (sector, compliance, org_id))

    if org_id:
        cursor.execute("UPDATE user_profiles SET org_id = %s WHERE id = %s", (org_id, profile_id))

    cursor.execute(
        "UPDATE user_profiles SET role = %s, onboarding_completed = true, display_name = %s, last_active = %s WHERE id = %s",
        (role, org_name or role, datetime.now(timezone.utc), profile_id),
    )
    if cursor.rowcount == 0:
        cursor.execute(
            """INSERT INTO user_profiles (id, role, display_name, org_id, onboarding_completed, last_active)
               VALUES (%s, %s, %s, %s, true, %s)""",
            (profile_id, role, org_name or role, org_id, datetime.now(timezone.utc)),
        )

    if org_id and assets:
        for asset in assets:
            cursor.execute(
                """INSERT INTO asset_inventory (org_id, asset_type, name, vendor, version, exposed, criticality)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (
                    org_id,
                    asset.get("asset_type") or asset.get("type", "product"),
                    asset.get("name", "")[:200],
                    asset.get("vendor", ""),
                    asset.get("version", ""),
                    bool(asset.get("exposed", False)),
                    asset.get("criticality", 3),
                ),
            )
        cursor.execute("DELETE FROM asset_inventory WHERE org_id = %s AND id NOT IN (SELECT id FROM asset_inventory WHERE org_id = %s ORDER BY id DESC LIMIT 1000)", (org_id, org_id))

    conn.commit()
    cursor.close()
    conn.close()
    return {"profile_id": profile_id, "role": role, "org_id": org_id, "assets_count": len(assets)}


def build_user_context(profile_id: int | None = None) -> tuple[set, str]:
    """Construit le contexte personnel (keywords + texte) depuis le profil utilisateur.
    
    Tombe sur le contexte global (repos) si pas de profil.
    """
    if not profile_id:
        return _fallback_global_context()

    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """SELECT role, preferences, org_id
           FROM user_profiles WHERE id = %s""",
        (profile_id,),
    )
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        return _fallback_global_context()

    role = row[0] or "non_defini"
    prefs = row[1] if isinstance(row[1], dict) else {}
    org_id = row[2]

    keywords = set()
    context_parts = []

    context_parts.append(f"Role: {role}")
    keywords.add(role)

    if org_id:
        cursor.execute("SELECT name, sector, compliance_frameworks FROM organizations WHERE id = %s", (org_id,))
        org = cursor.fetchone()
        if org:
            context_parts.append(f"Organisation: {org[0]}, Secteur: {org[1] or 'non defini'}")
            if org[2]:
                context_parts.append(f"Compliance: {org[2]}")
                for tok in org[2].lower().replace(",", " ").split():
                    if len(tok) > 2:
                        keywords.add(tok)

        cursor.execute(
            """SELECT asset_type, name, vendor, version, criticality
               FROM asset_inventory WHERE org_id = %s ORDER BY criticality DESC""",
            (org_id,),
        )
        techs = []
        for asset_type, name, vendor, version, _crit in cursor.fetchall():
            techs.append(f"{name}" + (f" {vendor}" if vendor else "") + (f" v{version}" if version else ""))
            if asset_type in ("product", "vendor"):
                keywords.add(name.lower())
                if vendor:
                    keywords.add(vendor.lower())
            elif asset_type in ("language", "framework"):
                keywords.add(name.lower())

        if techs:
            context_parts.append("Technologies: " + ", ".join(techs[:50]))

    if prefs and prefs.get("objectives"):
        goals = prefs["objectives"]
        context_parts.append("Objectifs: " + (", ".join(goals) if isinstance(goals, list) else str(goals)))

    context_parts.append("Priorites recommandees: CVE avec exploit public, CISA KEV, CVSS eleve, EPSS eleve")

    cursor.close()
    conn.close()

    context_str = ". ".join(context_parts)
    return keywords, context_str


def _fallback_global_context():
    from src.priority_engine import build_stack_keywords as bsk
    return bsk()


def get_user_role(profile_id: int | None) -> str:
    if not profile_id:
        return "non_defini"
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role FROM user_profiles WHERE id = %s", (profile_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row[0] if row else "non_defini"
