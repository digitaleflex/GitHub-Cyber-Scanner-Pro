"""MCP Server — expose Cyber Scanner Pro data to AI agents via Model Context Protocol."""

import logging

from src import database
from src import rss_feed
from src.scanner import scanner_status

logger = logging.getLogger(__name__)


def register_tools(mcp):
    # ── TOOLS ──────────────────────────────────────────────────────────────────

    @mcp.tool()
    def search_repos(
        query: str = "",
        page: int = 1,
        sort_by: str = "stars",
        vitality_min: int = 0,
        security_verdict: str | None = None,
    ) -> str:
        """Recherche des depots GitHub d'outils cybersecurite.

        Args:
            query: Recherche par nom, description ou langage.
            page: Numero de page (20 resultats par page).
            sort_by: Tri (stars, vitality, updated, name).
            vitality_min: Score de vitalite minimum (0-100).
            security_verdict: Filtre par verdict securite (Critique, Suspect, Sain).
        """
        repos, total = database.search_repos_frontend(
            q=query, page=page, per_page=20,
            sort_by=sort_by, vitality_min=vitality_min,
            security_verdict=security_verdict,
        )
        pages = max(1, (total + 19) // 20)
        lines = [f"  {total} resultat(s) - page {page}/{pages}"]
        for r in repos:
            v = r.get("security_verdict") or "?"
            s = r.get("stars") or 0
            lang = r.get("lang") or "?"
            lines.append(f"  [{v}] *{s} {r['name']} ({lang}) - {r.get('desc', '')[:100]}")
        return "\n".join(lines) if repos else "Aucun resultat."

    @mcp.tool()
    def search_books(query: str = "") -> str:
        """Recherche des livres et ressources cybersecurite extraits.

        Args:
            query: Recherche plein-texte par titre, categorie ou depot.
        """
        books = database.get_books(search_query=query or None)
        lines = [f"  {len(books)} ressource(s)"]
        for b in books:
            status = "OK" if b.get("is_dead") != 1 else "KO"
            cat = b.get("category") or "?"
            typ = b.get("type_ressource") or "?"
            lines.append(f"  {status} [{typ}] {b['title']} - {cat}")
        return "\n".join(lines) if books else "Aucune ressource."

    @mcp.tool()
    def get_news(limit: int = 15, country: str | None = None) -> str:
        """Recupere les actualites cybersecurite des flux RSS (170+ sources).

        Args:
            limit: Nombre d'articles (max 50).
            country: Filtre par code ISO pays (ex: FR, US).
        """
        news = database.get_news_with_correlations(limit=limit, country=country)
        lines = [f"  {len(news)} actualite(s)"]
        for n in news:
            src = n.get("source_name") or "?"
            cat = n.get("category") or "general"
            lines.append(f"  [{cat}] {n['title']} - {src}")
            repos = n.get("correlated_repos", [])
            if repos:
                lines.append(f"         -> {len(repos)} depot(s) correle(s)")
        return "\n".join(lines) if news else "Aucune actualite."

    @mcp.tool()
    def get_incidents(limit: int = 10, country: str | None = None) -> str:
        """Recupere les incidents cyber unifies (CVE/IOC/produits correles).

        Args:
            limit: Nombre d'incidents.
            country: Filtre par code ISO pays.
        """
        incidents = database.get_incidents(limit=limit, country=country)
        lines = [f"  {len(incidents)} incident(s)"]
        for inc in incidents:
            cves = ", ".join(inc.get("cves", [])[:3])
            products = ", ".join(inc.get("products", [])[:3])
            lines.append(f"  {inc.get('title', '?')}")
            if cves:
                lines.append(f"     CVE: {cves}")
            if products:
                lines.append(f"     Produits: {products}")
            lines.append(f"     Score: {inc.get('severity_score', '?')}/100")
        return "\n".join(lines) if incidents else "Aucun incident."

    @mcp.tool()
    def get_stats() -> str:
        """Recupere les statistiques globales de la plateforme."""
        try:
            (total_repos, total_stars, languages, lang_dist, last_scan,
             critique, suspect, unscanned, avg_vitality,
             _top_vitality, _low_vitality, _dead_vitality) = database.get_frontend_stats()
        except Exception:
            return "Statistiques non disponibles."
        return (
            f"Statistiques Cyber Scanner Pro\n"
            f"  Depots: {total_repos}\n"
            f"  Etoiles: {int(total_stars):,}\n"
            f"  Langages: {languages}\n"
            f"  Vitalite moy.: {round(float(avg_vitality), 1)}/100\n"
            f"  Critique: {critique}\n"
            f"  Suspect: {suspect}\n"
            f"  Non scanne: {unscanned}\n"
            f"  Statut scanner: {scanner_status}"
        )

    @mcp.tool()
    def get_repo_verdict(repo_name: str) -> str:
        """Obtient le verdict de securite pour un depot GitHub specifique.

        Args:
            repo_name: Nom complet du depot (ex: 'digitaleflex/GitHub-Cyber-Scanner-Pro').
        """
        repos, _ = database.search_repos_frontend(q=repo_name, page=1, per_page=5)
        for r in repos:
            if r["name"].lower() == repo_name.lower():
                v = r.get("security_verdict") or "NON_AUDITE"
                vit = r.get("vitality_score") or 0
                stars = r.get("stars") or 0
                return (
                    f"  {repo_name}\n"
                    f"  Verdict securite: {v}\n"
                    f"  Vitalite: {vit}/100\n"
                    f"  Stars: *{int(stars):,}\n"
                    f"  Langage: {r.get('lang') or '?'}\n"
                    f"  Description: {r.get('desc', '')[:200]}"
                )
        return f"Depot '{repo_name}' introuvable."

    @mcp.tool()
    def get_feed_health() -> str:
        """Retourne l'etat de sante des flux RSS (nombre de sources actives/mortes)."""
        health = rss_feed.count_usable_feeds()
        return (
            f"Sante des flux RSS\n"
            f"  Total: {health['total']} sources\n"
            f"  Actives: {health['usable']}\n"
            f"  Morts: {len(health['dead'])}\n"
            f"  Bloques anti-bot: {len(health['blocked_antibot'])}\n"
            f"  Morts: {', '.join(health['dead'][:10]) if health['dead'] else 'aucun'}\n"
            f"  Bloques: {', '.join(health['blocked_antibot'][:10]) if health['blocked_antibot'] else 'aucun'}"
        )

    # ── RESOURCES ──────────────────────────────────────────────────────────────

    @mcp.resource("cyberscan://stats")
    def stats_resource() -> str:
        """Statistiques globales de la plateforme."""
        return get_stats()

    @mcp.resource("cyberscan://feed-health")
    def feed_health_resource() -> str:
        """Sante des flux RSS."""
        return get_feed_health()

    @mcp.resource("cyberscan://repos/{name}")
    def repo_resource(name: str) -> str:
        """Informations sur un depot specifique."""
        return get_repo_verdict(name)

    @mcp.resource("cyberscan://books/search/{query}")
    def books_search_resource(query: str) -> str:
        """Resultats de recherche de livres."""
        return search_books(query)

    @mcp.resource("cyberscan://news/latest")
    def news_latest_resource() -> str:
        """Dernieres actualites cyber."""
        return get_news(limit=20)

    @mcp.resource("cyberscan://incidents/latest")
    def incidents_latest_resource() -> str:
        """Derniers incidents cyber."""
        return get_incidents(limit=10)
