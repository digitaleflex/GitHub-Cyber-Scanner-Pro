FROM python:3.11-slim

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    git \
    curl \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Installer les outils SAST (Bandit et Semgrep) via pip
RUN pip install --no-cache-dir bandit semgrep

# Éviter la génération de fichiers pyc et forcer l'unbuffered mode pour Docker logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONUTF8=1

WORKDIR /app

# Installer les dépendances Python
COPY requirements.txt .

# Installer torch en version CPU d'abord, puis le reste pour minimiser la taille de l'image
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt

# Télécharger les modèles de langue Spacy et le modèle d'embeddings de sentence-transformers
RUN python -m spacy download en_core_web_sm
RUN python -m spacy download fr_core_news_sm
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Copier le code source et les templates
COPY src/ src/
COPY templates/ templates/

# Créer le répertoire de données pour le volume persistant
RUN mkdir -p /app/data

# Lancer l'application
CMD ["python", "-u", "src/scanner.py"]
