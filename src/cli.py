import os
import sys
import argparse
import requests
import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000/api")
console = Console()

def get_stats():
    """Affiche les statistiques globales."""
    try:
        res = requests.get(f"{API_URL}/stats")
        data = res.json()
        
        table = Table(title="📊 Statistiques de la Plateforme", title_style="bold magenta")
        table.add_column("Métrique", style="cyan")
        table.add_column("Valeur", style="green")
        
        table.add_row("Dépôts GitHub", str(data.get("total_repos", 0)))
        table.add_row("Ressources OSINT", str(data.get("total_books", 0)))
        table.add_row("Statut Scanner", data.get("status", "Inconnu"))
        
        console.print(table)
    except Exception as e:
        console.print(f"[bold red]❌ Erreur : Impossible de joindre l'API sur {API_URL}[/]")

def search_repos(query):
    """Recherche des dépôts GitHub."""
    try:
        res = requests.get(f"{API_URL}/repositories")
        repos = res.json()
        
        # Filtrage simple pour la démo CLI
        if query:
            repos = [r for r in repos if query.lower() in r['full_name'].lower() or query.lower() in (r['description'] or "").lower()]

        table = Table(title=f"🔍 Résultats Recherche : {query if query else 'Tous'}")
        table.add_column("Nom du Dépôt", style="bold blue")
        table.add_column("Étoiles", justify="right")
        table.add_column("Sécurité", justify="center")
        table.add_column("Score IA", justify="right")

        for r in repos[:15]: # Top 15
            verdict = r.get("security_verdict", "N/A")
            sec_color = "green" if verdict == "SAIN" else "yellow" if verdict == "SUSPECT" else "red" if verdict == "CRITIQUE" else "white"
            
            table.add_row(
                r['full_name'],
                f"★ {r['stars']}",
                f"[{sec_color}]{verdict}[/]",
                str(r.get("score_qualite", 0))
            )
        
        console.print(table)
    except Exception as e:
        console.print(f"[bold red]❌ Erreur lors de la recherche : {e}[/]")

def search_intel(query):
    """Recherche dans les ressources OSINT (Exploits, NIST, etc.)."""
    try:
        res = requests.get(f"{API_URL}/resources")
        items = res.json()
        
        if query:
            items = [i for i in items if query.lower() in i['title'].lower() or query.lower() in (i['description'] or "").lower()]

        table = Table(title=f"🌍 Intelligence OSINT : {query if query else 'Dernières découvertes'}")
        table.add_column("Source", style="bold yellow")
        table.add_column("Référence / Titre", style="white")
        table.add_column("Type", style="cyan")

        for i in items[:15]:
            ext_id = f"[{i['external_id']}] " if i.get('external_id') else ""
            table.add_row(
                i['source_name'],
                f"{ext_id}{i['title'][:60]}...",
                i.get('type_ressource', 'Général')
            )
        
        console.print(table)
    except Exception as e:
        console.print(f"[bold red]❌ Erreur lors de la récupération OSINT : {e}[/]")

def show_flash(repo_name):
    """Affiche la fiche flash IA d'un dépôt."""
    try:
        res = requests.get(f"{API_URL}/repositories")
        repos = res.json()
        
        target = next((r for r in repos if repo_name.lower() in r['full_name'].lower()), None)
        
        if not target:
            console.print(f"[bold red]❌ Dépôt '{repo_name}' non trouvé.[/]")
            return

        summary = target.get("llm_summary")
        if not summary:
            console.print(f"[yellow]⏳ Fiche IA en cours de génération pour {target['full_name']}...[/]")
            return

        panel = Panel(
            f"[bold cyan]Objectif :[/]\n{summary.get('objectif')}\n\n"
            f"[bold cyan]Prérequis :[/]\n{summary.get('prerequis')}\n\n"
            f"[bold green]🚀 COMMANDE FLASH :[/]\n[black on green] {summary.get('commande_flash')} [/]",
            title=f"⚡ FICHE FLASH IA : {target['full_name']}",
            border_style="orange1"
        )
        console.print(panel)
        
    except Exception as e:
        console.print(f"[bold red]❌ Erreur fiche flash : {e}[/]")

def main():
    parser = argparse.ArgumentParser(description="🚀 Cyber Scanner CLI - Intelligence Souveraine")
    subparsers = parser.add_subparsers(dest="command", help="Commandes disponibles")

    # Command: stats
    subparsers.add_parser("stats", help="Afficher les stats globales")

    # Command: search
    search_parser = subparsers.add_parser("search", help="Chercher un dépôt GitHub")
    search_parser.add_argument("query", nargs="?", default="", help="Terme de recherche")

    # Command: intel
    intel_parser = subparsers.add_parser("intel", help="Chercher des exploits/alertes OSINT")
    intel_parser.add_argument("query", nargs="?", default="", help="Terme de recherche")

    # Command: flash
    flash_parser = subparsers.add_parser("flash", help="Voir la fiche IA d'un outil")
    flash_parser.add_argument("repo", help="Nom du dépôt (partiel ou complet)")

    args = parser.parse_args()

    if args.command == "stats":
        get_stats()
    elif args.command == "search":
        search_repos(args.query)
    elif args.command == "intel":
        search_intel(args.query)
    elif args.command == "flash":
        show_flash(args.repo)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
