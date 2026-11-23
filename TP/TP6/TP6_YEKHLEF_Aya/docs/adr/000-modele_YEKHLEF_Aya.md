# ADR : Architecture de l'image Docker, gestion des modèles et exclusions .dockerignore

Date : 23/11/2026 · Auteur : YEKHLEF Aya

## Contexte
MaintAI doit être conteneurisé afin d'être déployable de manière reproductible sur n'importe quel serveur ou machine sans préparation manuelle d'un environnement virtuel Python (`.venv`). L'application comprend une API FastAPI et une interface utilisateur Streamlit, exploitant un modèle d'apprentissage automatique (`model.joblib`) et des variables d'environnement confidentielles (clés d'API). Deux contraintes majeures se posent :
1. Le modèle prédictif doit-il être embarqué directement dans l'image Docker ou injecté au lancement par un volume ?
2. Quels éléments doivent être formellement exclus du contexte de build via `.dockerignore` ?

## Options étudiées

### Option A : Embarquer le modèle et les données dans l'image Docker (`COPY models/ /app/models`)
- **Avantages** : L'image est complètement autonome ("self-contained"), aucune dépendance vers le système de fichiers hôte ni montage de volume au lancement (`docker run -p 8000:8000 maintai:0.4.0`).
- **Inconvénients** : Taille d'image excessivement alourdie ; chaque réentraînement de modèle (itération MLOps) oblige à reconstruire et redistribuer l'intégralité de l'image Docker ; couplage fort et indésirable entre le cycle de vie du code applicatif et le cycle de vie des artefacts de données / modèles ; risque d'embarquer des données sensibles ou obsolètes.

### Option B (Retenue) : Découpler l'image applicative et injecter le modèle via un volume en lecture seule (`-v ./models:/app/models:ro`), avec exclusion stricte via `.dockerignore`
- **Avantages** : 
  - Image applicative légère, standardisée et stable (817 Mo), focalisée uniquement sur l'exécution du code Python et ses dépendances.
  - Séparation nette des responsabilités : le code applicatif est figé dans l'image, tandis que le modèle et les données évoluent indépendamment (MLOps / DVC / MLflow).
  - Possibilité de mettre à jour le modèle à chaud ou de tester différentes versions du modèle sans jamais reconstruire l'image.
  - Sécurité renforcée : exclusion garantie des secrets (`.env`), des caches locaux (`.venv`, `__pycache__`) et des historiques de tracking (`mlflow.db`, `mlruns/`, `.dvc/`).
- **Inconvénients** : 
  - Exige le montage explicite du dossier des modèles au lancement (`-v ./models:/app/models:ro`). Si le volume est omis, l'API démarre mais signale `"model_loaded": false` sur `/health` et retourne un statut `503 Service Unavailable` sur `/v1/predict`.

## Décision
Nous retenons l'**Option B**.
1. L'image `maintai:0.4.0` embarque uniquement l'environnement système Linux (`python:3.11-slim`), les dépendances de production (`requirements-docker.txt`) et le code source de l'application (`maintai/` et `ui/`).
2. Le modèle est injecté au runtime via un volume monté en lecture seule (`./models:/app/models:ro`).
3. Le fichier `.dockerignore` exclut explicitement :
   - `.venv/` (dépendances hôte Windows non compatibles avec le conteneur Linux)
   - `models/` et `data/` (artefacts volumineux gérés séparément par les pipelines MLOps)
   - `.env` (secrets et clés d'API transmis exclusivement au runtime par `--env-file` ou variables d'environnement)
   - `mlflow.db` et `mlruns/` (base de données SQLite et artefacts de tracking locaux)
   - `.dvc/` (cache et configuration interne DVC)
   - `tests/`, `.pytest_cache/`, `.ruff_cache/`, `*.egg-info/` (fichiers de test et de packaging non requis en production).

## Conséquences
- **Ce que cette décision facilite** :
  - Déploiements rapides et agiles avec réutilisation maximale du cache Docker lors des modifications de code (~2.5s de build).
  - Portabilité et conformité avec les 12-factor apps (séparation stricte code / configuration / données).
  - Absence de fuite de secrets dans les images partagées sur les registres (Docker Hub / Artifact Registry).
- **Ce qu'elle rend plus difficile / ce qu'il faudra surveiller** :
  - Nécessité de documenter et d'automatiser (via Docker Compose) le montage des volumes vers les répertoires de modèles valides.
  - Surveillance active de l'état du modèle via la sonde de vivacité `/health` avant de router le trafic utilisateur.
