# Compte rendu · TP6 : conteneuriser MaintAI (Docker, Docker Compose)

**Groupe :*G3*  ·  **Membres :*El aouazi hafsa  ·  **Date :*23/11/2026* 2026-11-23

---

## 1. Mise en place (dans `TP/TP6`)

Sortie de `docker run hello-world` (première ligne) et de `docker version` (lignes Client et Server) :

Hello from Docker!
This message shows that your installation appears to be working correctly.


C:\Users\hp>docker --version
Docker version 29.2.1, build a5c7197


À COMPLÉTER : collez la sortie (Hello from Docker! ... puis Client / Server de docker version)
```

Dernière ligne de `python -m pytest` après la mise en place :
============= 3 failed, 35 passed, 6 warnings in 84.83s (0:01:24) ========
```
À COMPLÉTER : attendu « 5 failed, 33 passed »
```

## 2. Image et conteneur (pendant le premier build)

1. Quelle différence entre une image et un conteneur ?
   L'image est le résultat figé et nommé de la recette (le Dockerfile) : Linux, Python, bibliothèques et code emballés ensemble. Le conteneur est une copie de cette image qui tourne, isolée (ses fichiers, son réseau, ses processus). Une image peut donner autant de conteneurs qu'on veut.
2. Pourquoi `COPY requirements-docker.txt` est-il placé avant `COPY maintai` ?
   Chaque instruction crée une couche, et Docker réutilise toutes les couches jusqu'à la première qui change. Les bibliothèques (`pip install`, lent) changent rarement ; le code change souvent. En copiant d'abord la liste des bibliothèques, une modification du code ne relance pas le `pip install`.
3. Pourquoi `requirements-docker.txt` contient-il `scikit-learn==1.8.0` et pas `scikit-learn>=1.5` ?
   Le modèle est un objet sérialisé qui dépend de la version de scikit-learn qui l'a produit. Avec `>=`, un build futur pourrait installer une autre version, et le modèle ne se rechargerait plus ou donnerait d'autres résultats. La version exacte rend l'image reproductible et identique à celle de l'entraînement.
4. Pourquoi ni `mlflow`, ni `dvc`, ni `pytest` dans l'image ?
   Ce sont des outils d'entraînement, de suivi et de test. L'image ne sert qu'à faire tourner l'API et l'interface. Les exclure rend l'image plus légère, le build plus rapide et réduit la surface d'attaque.

## 3. Sprint 1 : le Dockerfile

Votre `Dockerfile` :

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

COPY maintai ./maintai
COPY ui ./ui

ENV MAINTAI_MODELS_DIR=/app/models
ENV MAINTAI_DATA_PATH=/app/data/sensors.csv

EXPOSE 8000

CMD ["uvicorn", "maintai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

| Build | Durée | Taille de l'image (`docker images`) |
|---|---|---|
| premier build | À COMPLÉTER (l'étape `pip install` a duré 42,2 s) | 1,13 Go |
| après une modification de `maintai/predict.py` | À COMPLÉTER (mesurer avec `Measure-Command { docker build -t maintai:0.4.0 . }`) | 1,13 Go |

Que signifie `CACHED` dans le journal du second build ?

Docker a reconnu que l'instruction et tout ce qui la précède n'ont pas changé, et il réutilise la couche déjà construite au lieu de la refaire. Seules les couches à partir de la première modification (ici `COPY maintai`) sont reconstruites. Le `pip install` reste `CACHED`, d'où un build en quelques secondes au lieu de plusieurs minutes.

## 4. Sprint 1 : lancer un conteneur

Votre commande `docker run` :

```
docker run -d --name maintai-api -p 8000:8000 --env-file .env -v "${PWD}\models:/app/models:ro" maintai:0.4.0
```

| Essai | Réponse |
|---|---|
| `GET /health` | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` sans clé |  (attendu : 401) |
| `POST /v1/predict` avec la clé |  (attendu : une probabilité, avec `failure_probability` et `alert`) |

**Piège 1.** Sans l'option `-v ...models...`, que répondent `/health` et `/v1/predict` ? Pourquoi ?

À VÉRIFIER avec votre essai : `/health` répond `{"status":"ok","model_loaded":false}` et `/v1/predict` répond 503 (« Modèle non chargé »). Le modèle n'est pas dans l'image (il est exclu par `.dockerignore`) : il arrive par le volume. Sans volume, l'API démarre mais n'a aucun modèle à charger.

**Piège 2.** Avec `--host 127.0.0.1`, que disent `docker logs test` et `http://localhost:8002/health` ? Pourquoi ?

À VÉRIFIER avec votre essai : les logs disent « Uvicorn running on http://127.0.0.1:8000 », mais `http://localhost:8002/health` ne répond rien. Dans un conteneur, `127.0.0.1` veut dire « ce conteneur seulement » : le trafic que Docker relaie depuis le PC arrive par une autre interface réseau, où uvicorn n'écoute pas. Il faut `--host 0.0.0.0`, qui écoute sur toutes les interfaces.

## 5. Sprint 2 : Docker Compose

Votre `compose.yaml` :

```yaml
# MaintAI en deux conteneurs : l'API et l'interface Streamlit.
# Lancer : docker compose up --build      Arreter : docker compose down

services:
  api:
    build: .
    image: maintai:0.4.0
    env_file: .env
    ports:
      - "8000:8000"
    volumes:
      - ./models:/app/models:ro

  ui:
    image: maintai:0.4.0
    command: ["python", "-m", "streamlit", "run", "ui/app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
    environment:
      MAINTAI_API_URL: http://api:8000
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data:ro
    depends_on:
      - api
```

Sortie de `docker compose ps` :

```
NAME        IMAGE           COMMAND                  SERVICE   CREATED         STATUS                  PORTS
tp6-api-1   maintai:0.4.0   "uvicorn maintai.api…"   api       2 seconds ago   Up 1 second             0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
tp6-ui-1    maintai:0.4.0   "python -m streamlit…"   ui        2 seconds ago   Up Less than a second   0.0.0.0:8501->8501/tcp, [::]:8501->8501/tcp
```

Quelle URL affiche la barre latérale de l'interface ? D'où vient-elle ?

`http://api:8000`. Elle vient de la variable d'environnement `MAINTAI_API_URL`, définie dans `compose.yaml` pour le service `ui` et lue dans `ui/app.py` par `os.getenv("MAINTAI_API_URL", "http://localhost:8000")`. Sans variable, l'interface garde `http://localhost:8000` par défaut.

Résultat des deux commandes `docker compose exec ui ...` (avec `api` puis avec `localhost`). Pourquoi la seconde échoue-t-elle ?

```
http://api:8000/health        -> {"status":"ok","model_loaded":true}
http://localhost:8000/health  -> httpx.ConnectError: [Errno 111] Connection refused
```

Dans Compose, chaque service se joint par son nom sur le réseau `tp6_default`. Dans le conteneur `ui`, `localhost` désigne le conteneur `ui` lui-même, où aucune API n'écoute. Le navigateur, lui, tourne sur le PC, où Docker publie le port 8000 de l'API (`-p 8000:8000`) : `http://localhost:8000` y fonctionne.

Dernière ligne de `python -m pytest` à la fin du sprint 2 :

```
======================= 38 passed, 6 warnings in 46.29s ========================
```

`docker compose down` supprime les conteneurs `tp6-api-1` et `tp6-ui-1` et le réseau `tp6_default`. Elle garde l'image `maintai:0.4.0` et les dossiers `models/` et `data/` du PC.

## 6. Décision : l'ADR 005

Dans `docs/adr/005-image-docker.md`. Résumez ici votre décision en deux phrases :

Le modèle n'est pas dans l'image : il arrive par un volume au lancement, ce qui permet de le remplacer sans rebuild, au prix d'une image qui ne démarre pas seule. `.dockerignore` laisse dehors les données, le modèle, le secret `.env`, MLflow et DVC, pour une image légère et sans secret, ce qui oblige à les fournir autrement (volume, `--env-file`).

## 7. Questions de compréhension

1. Qu'est-ce qui entre dans l'image, et qu'est-ce qui arrive au lancement ? Donnez le moyen pour chaque élément.
   Dans l'image (par `docker build`) : Linux, Python 3.11, les bibliothèques figées (`requirements-docker.txt`), le code `maintai/` et `ui/`. Au lancement : le modèle (`models/`, par volume `-v`), les données (`data/`, par volume) et la clé API (`.env`, par `--env-file`).
2. Pourquoi la clé API n'est-elle jamais dans l'image ?
   Une image se partage et se copie ; tout ce qu'elle contient se retrouve chez celui qui la reçoit. Un secret dans l'image fuit avec elle. On le donne au lancement, ce qui permet aussi de changer de clé sans rebuild.
3. Livrer un modèle (TP4, TP5) : qu'est-ce que Docker ajoute à la liste ?
   Docker ajoute l'environnement d'exécution : le système, la version de Python et les bibliothèques exactes. Le paquet des TP précédents porte le code ; l'image le rend exécutable de la même façon sur tout PC ou serveur où Docker est installé, sans `.venv`. Le modèle reste apporté à part, par un volume.

## 8. Le rendu Git

- Lien de la pull request : À COMPLÉTER
- Le tag `tp6` existe sur GitHub : oui 
- `git status` avant le commit : `.env`, `models/` ou `data/*.csv` apparaissaient-ils ? 

## 9. Ce qui reste flou

