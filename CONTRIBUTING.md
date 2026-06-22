# Guide de Contribution

Bienvenue sur CyberBook Collector ! Ce document explique comment contribuer au projet.

## Workflow

1. **Issue d'abord** : Toute modification commence par une Issue GitHub
2. **Branche dediee** : Creer une branche `feature/nom-tache` ou `fix/nom-bug`
3. **Pull Request** : Soumettre une PR vers `main` avec une description claire

## Standards de code

- **Langage** : Python 3.11+
- **Style** : PEP 8 (verifie avec `ruff check src/`)
- **Securite** : Jamais de cles API en dur, toujours utiliser `.env`
- **Tests** : Ajouter des tests pour les nouvelles fonctionnalites

## Conventions de commits

```
feat: ajout d'une nouvelle fonctionnalite
fix: correction d'un bug
docs: mise a jour de la documentation
refactor: amelioration du code sans changement de comportement
test: ajout de tests
chore: taches de maintenance
```

Exemple : `feat: ajout de la categorie forensique`

## Lancer localement

```bash
# Installer les dependances
pip install -r requirements.txt

# Configurer l'environnement
cp .env.example .env
# Editer .env avec vos tokens

# Lancer le scanner
python src/scanner.py
```

## Linter

```bash
ruff check src/
ruff format src/
```

## Securite

Les vulnerabilites critiques ne doivent pas etre signalees en public. Contactez les mainteneurs en prive.
