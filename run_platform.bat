@echo off
SETLOCAL EnableDelayedExpansion

echo ============================================================
echo 🚀 GITHUB CYBER SCANNER PRO - BOUTON TURBO 🚀
echo ============================================================
echo.

:: 1. Vérifier si Docker tourne
echo [1/5] Verification de Docker...
docker ps >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Erreur : Docker n'est pas lance. Veuillez demarrer Docker Desktop.
    pause
    exit /b
)
echo ✅ Docker est pret.

:: 2. Lancer l'infrastructure (DB, Redis, SearXNG, Ollama, Scanner)
echo [2/5] Lancement de l'infrastructure Docker (compose)...
docker compose up --build -d
if %errorLevel% neq 0 (
    echo ❌ Erreur lors du lancement des conteneurs.
    pause
    exit /b
)
echo ✅ Infrastructure en ligne.

:: 3. Preparer l'IA (Ollama)
echo [3/5] Configuration de l'IA (Ollama + Mistral)...
echo ⏳ Cela peut prendre du temps selon votre connexion internet (4 Go)...
docker exec -it cyber_ollama_ai ollama run mistral "Bonjour, pret pour l'analyse cyber."
echo ✅ IA operationnelle.

:: 4. Lancer la premiere synchronisation OSINT
echo [4/5] Declenchement de la synchronisation Multi-Sources...
docker exec -d cyber_github_scanner python src/orchestrator.py
echo ✅ Agents OSINT deployes en tache de fond.

:: 5. Finalisation
echo [5/5] Ouverture du Dashboard...
start http://localhost:8000
echo.
echo ============================================================
echo 🎉 PLATEFORME TOTALEMENT DEPLOYEE ET OPERATIONNELLE !
echo 🌐 Dashboard : http://localhost:8000
echo 📊 Supervision : http://localhost:5555 (Flower)
echo ============================================================
echo.
echo Appuyez sur une touche pour fermer cette fenêtre, les conteneurs resteront actifs.
pause
