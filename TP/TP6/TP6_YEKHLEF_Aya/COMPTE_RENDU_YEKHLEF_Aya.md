# Compte rendu · TP6 : conteneuriser MaintAI (Docker, Docker Compose)

**Groupe :** YEKHLEF Aya  ·  **Membres :** YEKHLEF Aya  ·  **Date et heure de dépôt :** 23/11/2026 à 11:05

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP6.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place (dans `TP/TP6`)

Sortie de `docker run hello-world` (première ligne) et de `docker version` (lignes Client et Server) :

```
Hello from Docker!

Client:
 Version:           28.3.3
 API version:       1.51
 Go version:        go1.24.5
 Git commit:        980b856
 Built:             Fri Jul 25 11:36:03 2025
 OS/Arch:           windows/amd64
 Context:           desktop-linux

Server: Docker Desktop 4.45.0 (203075)
 Engine:
  Version:          28.3.3
  API version:      1.51 (minimum version 1.24)
  Go version:       go1.24.5
  Git commit:       bea959c
  Built:            Fri Jul 25 11:34:00 2025
  OS/Arch:          linux/amd64
  Experimental:     false
```

Dernière ligne de `python -m pytest` après la mise en place :

```
================== 38 passed, 4 warnings in 63.16s (0:01:03) ==================
```

## 2. Image et conteneur (pendant le premier build)

1. Quelle différence entre une image et un conteneur ?
Une image est un modèle figé, immuable et versionné (la "recette" compilée contenant le système de fichiers de base, les dépendances Python et le code applicatif). Un conteneur est une instance vivante et active de cette image, isolée avec son propre espace de processus, son propre réseau et son système de fichiers inscriptible éphémère.

2. Pourquoi `COPY requirements-docker.txt` est-il placé avant `COPY maintai` ?
Pour exploiter le mécanisme de cache en couches de Docker. L'installation des dépendances (`pip install`) prend du temps (environ 2 minutes) mais change rarement. Le code source (`maintai/` et `ui/`) change en revanche très souvent. En isolant la copie du fichier des dépendances avant la copie du code, Docker réutilise le cache (`CACHED`) pour l'installation des dépendances. Toute modification du code applicatif permet ainsi de reconstruire l'image en seulement 2,5 secondes.

3. Pourquoi `requirements-docker.txt` contient-il `scikit-learn==1.8.0` et pas `scikit-learn>=1.5` ?
Pour assurer une stricte reproductibilité de l'environnement de production. Si une version flottante était autorisée, un build ultérieur pourrait installer une version mineure ou majeure différente introduisant des incompatibilités avec le modèle sérialisé par `joblib` ou des comportements imprévus.

4. Pourquoi ni `mlflow`, ni `dvc`, ni `pytest` dans l'image ?
Ces outils sont des dépendances d'expérimentation, de gestion de données et de test (utiles en développement et MLOps), mais absolument inutiles pour l'inférence en production. Les omettre permet de réduire considérablement la taille de l'image (gain de plusieurs centaines de mégaoctets), de minimiser la surface d'attaque de sécurité et d'accélérer le temps de démarrage du conteneur.

## 3. Sprint 1 : le Dockerfile

Votre `Dockerfile` :

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 1. Dépendances de production
COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

# 2. Code applicatif
COPY maintai/ ./maintai
COPY ui/ ./ui

# 3. Variables d'environnement par défaut
ENV MAINTAI_MODELS_DIR=/app/models \
    MAINTAI_DATA_PATH=/app/data/sensors.csv

# 4. Port exposé et commande par défaut
EXPOSE 8000
CMD ["uvicorn", "maintai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

| Build | Durée | Taille de l'image (`docker images`) |
|---|---|---|
| premier build | 2 min 24 s | 817MB |
| après une modification de `maintai/predict.py` | 2.5 s | 817MB |

Que signifie `CACHED` dans le journal du second build ?

`CACHED` indique que Docker réutilise directement les couches calculées lors du build précédent car ni les instructions ni les fichiers associés (comme `requirements-docker.txt` et l'étape `pip install`) n'ont été modifiés. L'étape n'est donc pas réexécutée, ce qui permet un gain de temps considérable.

## 4. Sprint 1 : lancer un conteneur

Votre commande `docker run` :

```bash
docker run -d --name maintai-api -p 8000:8000 --env-file .env -v "%cd%\models:/app/models:ro" maintai:0.4.0
```

| Essai | Réponse |
|---|---|
| `GET /health` | 200 OK — `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` sans clé | 401 Unauthorized — `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict` avec la clé | 200 OK — `{"failure_probability":0.9998,"alert":true,"threshold":0.3,"model_version":"2026-11-23T10:47:05Z"}` |

**Piège 1.** Sans l'option `-v ...models...`, que répondent `/health` et `/v1/predict` ? Pourquoi ?

`/health` répond 200 avec `{"status":"ok","model_loaded":false}`, et `/v1/predict` répond `503 Service Unavailable` (`{"detail":"Modèle non chargé..."}`).
*Pourquoi :* Le modèle `model.joblib` a été exclu de l'image Docker par `.dockerignore`. Sans montage de volume hôte vers `/app/models`, le dossier interne reste vide et l'API ne peut charger aucun modèle en mémoire.

**Piège 2.** Avec `--host 127.0.0.1`, que disent `docker logs test` et `http://localhost:8002/health` ? Pourquoi ?

`docker logs test` indique `Uvicorn running on http://127.0.0.1:8000`, mais une requête vers `http://localhost:8002/health` depuis la machine hôte échoue avec une connexion refusée ou une réponse vide (`Empty reply from server`).
*Pourquoi :* Dans un conteneur Docker, `127.0.0.1` désigne uniquement l'interface locale interne du conteneur. Uvicorn refuse ainsi toutes les connexions venant de l'extérieur (le réseau virtuel Docker relié au port hôte 8002). Il faut obligatoirement spécifier `--host 0.0.0.0` pour écouter sur toutes les interfaces réseau du conteneur.

## 5. Sprint 2 : Docker Compose

Votre `compose.yaml` :

```yaml
services:
  api:
    build: .
    image: maintai:0.4.0
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./models:/app/models:ro
      - ./data:/app/data:ro
    restart: unless-stopped

  ui:
    build: .
    image: maintai:0.4.0
    command: ["streamlit", "run", "ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
    ports:
      - "8501:8501"
    environment:
      - MAINTAI_API_URL=http://api:8000
    depends_on:
      - api
    restart: unless-stopped
```

Sortie de `docker compose ps` :

```
NAME                    IMAGE           COMMAND                  SERVICE   CREATED         STATUS         PORTS
tp6_yekhlef_aya-api-1   maintai:0.4.0   "uvicorn maintai.api…"   api       8 seconds ago   Up 8 seconds   0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
tp6_yekhlef_aya-ui-1    maintai:0.4.0   "python -m streamlit…"   ui        8 seconds ago   Up 7 seconds   0.0.0.0:8501->8501/tcp, [::]:8501->8501/tcp
```

Quelle URL affiche la barre latérale de l'interface ? D'où vient-elle ?

La barre latérale affiche `http://api:8000`. Elle provient de la variable d'environnement `MAINTAI_API_URL=http://api:8000` injectée dans le service `ui` de `compose.yaml` et prise en compte par `ui/app.py` via `os.getenv("MAINTAI_API_URL", "http://localhost:8000")`.

Résultat des deux commandes `docker compose exec ui ...` (avec `api` puis avec `localhost`). Pourquoi la seconde échoue-t-elle ?

```
Avec http://api:8000/health :
{"status":"ok","model_loaded":true}

Avec http://localhost:8000/health :
httpx.ConnectError: [Errno 111] Connection refused
```

*Pourquoi :* Chaque conteneur possède sa propre pile réseau isolée. Dans le conteneur `ui`, `localhost` cible `ui` lui-même (qui écoute sur 8501, et non 8000). Le conteneur `api` est accessible uniquement par son nom de service sur le réseau Docker Compose via le DNS interne : `http://api:8000`.

Dernière ligne de `python -m pytest` à la fin du sprint 2 :

```
================== 38 passed, 4 warnings in 63.16s (0:01:03) ==================
```

## 6. Décision : l'ADR

Dans `docs/adr/000-modele.md`. Résumez ici votre décision en deux phrases :

Nous avons retenu de ne pas embarquer le modèle dans l'image Docker mais de l'injecter au démarrage via un volume monté en lecture seule (`./models:/app/models:ro`), tout en excluant données, modèles, secrets et caches locaux avec `.dockerignore`. Ce choix garantit une image applicative légère (817 Mo), sécurisée et découplée des cycles de réentraînement MLOps sans nécessiter de reconstruction d'image à chaque nouveau modèle.

## 7. Questions de compréhension

1. Qu'est-ce qui entre dans l'image, et qu'est-ce qui arrive au lancement ? Donnez le moyen pour chaque élément.
- **Dans l'image (au build)** :
  - Système d'exploitation et runtime Python (`FROM python:3.11-slim`)
  - Bibliothèques de production (`COPY requirements-docker.txt .` et `RUN pip install`)
  - Code applicatif de l'API et de l'interface (`COPY maintai/ ./maintai` et `COPY ui/ ./ui`)
- **Au lancement (au run)** :
  - Modèle entraîné (`-v ./models:/app/models:ro`)
  - Données capteurs (`-v ./data:/app/data:ro`)
  - Clé d'API secrète et configuration (`--env-file .env` ou `env_file: [.env]`)
  - URL de découverte des services (`-e MAINTAI_API_URL=http://api:8000`)

2. Pourquoi la clé API n'est-elle jamais dans l'image ?
Pour prévenir toute faille de sécurité. Une image Docker a vocation à être partagée et archivée sur des registres publics ou privés. Si une clé est inscrite dans l'image, elle est accessible par simple inspection des couches (`docker history`). Les secrets doivent obligatoirement être fournis au conteneur au moment de son exécution par injection de variables d'environnement.

3. Livrer un modèle (TP4, TP5) : qu'est-ce que Docker ajoute à la liste ?
Aux TPs 4 et 5, la livraison se composait du wheel Python et des artefacts sérialisés, ce qui imposait que l'hôte cible dispose d'un Python compatible et installe manuellement les paquets. Docker ajoute à cela l'emballage complet du système d'exploitation Linux, des bibliothèques C système, de la version exacte de Python et du serveur de production Uvicorn, garantissant une exécution identique et sans friction sur n'importe quel serveur ou cloud en une seule commande.

## 8. Le rendu Git

- Date et heure du dépôt : 23/11/2026 à 12:05:00 (heure locale) / 11:05:00 (UTC)
- Lien de la pull request : https://github.com/wiamsouili/developpement-applications-intelligentes/pulls
- Le tag `tp6` existe sur GitHub : oui
- `git status` avant le commit : `.env`, `models/` ou `data/*.csv` apparaissaient-ils ? non

## 9. Ce qui reste flou

La communication inter-services via le réseau Docker et la séparation code/modèle/secrets sont parfaitement claires. Il serait intéressant d'explorer comment automatiser les healthchecks avec la directive `healthcheck` de Compose pour redémarrer automatiquement les conteneurs défaillants en production.
