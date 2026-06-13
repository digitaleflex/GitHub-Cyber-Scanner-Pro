FROM python:3.11-slim

# Éviter la génération de fichiers pyc et forcer l'unbuffered mode pour Docker logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONUTF8=1

WORKDIR /app

# Installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source et les templates
COPY cyber_scanner.py .
COPY templates templates

# Créer le répertoire de données pour le volume persistant
RUN mkdir -p /app/data

# Lancer l'application
CMD ["python", "-u", "cyber_scanner.py"]
