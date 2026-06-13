#!/bin/bash

# Script Maître de Démarrage (Linux/macOS)
echo "============================================================"
echo "🚀 GITHUB CYBER SCANNER PRO - ONE-CLICK LAUNCH 🚀"
echo "============================================================"
echo ""

# 1. Lancer Docker Compose
echo "[1/4] Construction et lancement de l'infrastructure..."
docker compose up --build -d

# 2. Configurer Ollama
echo "[2/4] Configuration du modèle IA (Mistral)..."
docker exec -it cyber_ollama_ai ollama run mistral "Prêt pour l'analyse."

# 3. Lancer la synchro OSINT initiale
echo "[3/4] Activation du Grand Orchestrateur..."
docker exec -d cyber_github_scanner python src/orchestrator.py

# 4. Succès
echo ""
echo "============================================================"
echo "🎉 TOUT EST OPÉRATIONNEL !"
echo "🌐 URL Dashboard : http://localhost:8000"
echo "📊 URL Celery/Flower : http://localhost:5555"
echo "============================================================"
echo ""
