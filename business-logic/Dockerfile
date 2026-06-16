# Image de base Python ultra-légère
FROM python:3.11-slim

# Définir le dossier de travail dans le conteneur
WORKDIR /app

# Éviter que Python écrive des fichiers .pyc et forcer l'affichage des logs en temps réel
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Installer les dépendances de base pour FastAPI et les appels HTTP
# (On installe tout d'un coup ici pour simplifier l'exercice sans fichier requirements.txt séparé)
RUN pip install --no-cache-dir fastapi uvicorn httpx pydantic sqlmodel databases

# Copier le code du service local vers le conteneur
COPY . /app/

# Exposer le port par défaut (Uvicorn utilise généralement 8000)
EXPOSE 8000

# Commande pour lancer FastAPI avec Uvicorn et activer le reload automatique pour le dev
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]