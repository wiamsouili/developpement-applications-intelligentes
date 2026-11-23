# Compte rendu · TP6 : conteneuriser MaintAI (Docker, Docker Compose)

**Groupe :** …  ·  **Membres :** …  ·  **Date :** 23/11/2026

> ⚠️ Les valeurs suivies de « *(réf. polycopié)* » sont les valeurs de référence données dans le polycopié de la séance 8, pas des mesures faites sur votre PC : remplacez-les par vos propres résultats avant de rendre. Les sorties **[À COMPLÉTER]** sont à coller depuis votre terminal.

---

## 1. Mise en place (dans `TP/TP6`)

Sortie de `docker run hello-world` (première ligne) et de `docker version` (lignes Client et Server) :

```
Hello from Docker!
[À COMPLÉTER : lignes Client et Server de `docker version`]
```

Dernière ligne de `python -m pytest` après la mise en place :

```
5 failed, 33 passed   (attendu d'après le polycopié : les 5 échecs sont dans tests/test_docker.py)
```

## 2. Image et conteneur (pendant le premier build)

1. Quelle différence entre une image et un conteneur ?
   L'image est le paquet figé et nommé produit par `docker build` (système, Python, bibliothèques, code) : elle ne tourne pas. Le conteneur est une copie de cette image en cours d'exécution, isolée (ses fichiers, son réseau, ses processus). D'une image on peut lancer autant de conteneurs identiques qu'on veut (plan / carte moulée / carte sous tension).
2. Pourquoi `COPY requirements-docker.txt` est-il placé avant `COPY maintai` ?
   Chaque instruction crée une couche, et Docker réutilise les couches jusqu'à la première qui change. La liste des bibliothèques change rarement et `pip install` est lent ; le code change souvent. En copiant d'abord la liste, une modification du code ne réinvalide que les couches suivantes et `pip install` reste en cache.
3. Pourquoi `requirements-docker.txt` contient-il `scikit-learn==1.8.0` et pas `scikit-learn>=1.5` ?
   Le modèle a été sérialisé (joblib) avec scikit-learn 1.8.0 ; un pickle n'est garanti que pour la version qui l'a écrit. Avec `>=`, un build futur installerait une autre version et le modèle pourrait mal se charger ou donner d'autres résultats. Versions figées = image reproductible.
4. Pourquoi ni `mlflow`, ni `dvc`, ni `pytest` dans l'image ?
   L'image sert à servir MaintAI, pas à l'entraîner (MLflow), versionner les données (DVC) ou tester (pytest). Les exclure rend l'image plus petite, le build plus rapide et réduit la surface d'attaque et les risques de conflits de versions.

## 3. Sprint 1 : le Dockerfile

Votre `Dockerfile` :

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

COPY maintai ./maintai
COPY ui ./ui

ENV MAINTAI_MODELS_DIR=/app/models \
    MAINTAI_DATA_PATH=/app/data/sensors.csv

EXPOSE 8000
CMD ["uvicorn", "maintai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

| Build | Durée | Taille de l'image (`docker images`) |
|---|---|---|
| premier build | 5 min 20 s, dont 161 s pour `pip install` *(réf. polycopié)* | 1,13 Go *(réf. polycopié)* |
| après une modification de `maintai/predict.py` | 11 s *(réf. polycopié)* | 1,13 Go *(réf. polycopié)* |

Que signifie `CACHED` dans le journal du second build ?

Docker a reconnu qu'une instruction et tout ce qui la précède n'ont pas changé : il réutilise la couche déjà construite au lieu de la refaire. Ici, `FROM`, `WORKDIR`, `COPY requirements-docker.txt` et surtout le lent `RUN pip install` sont `CACHED` ; seules les couches à partir de `COPY maintai` sont reconstruites, d'où un second build bien plus rapide.

## 4. Sprint 1 : lancer un conteneur

Votre commande `docker run` :

```
docker run -d --name maintai-api -p 8000:8000 --env-file .env -v "%cd%\models:/app/models:ro" maintai:0.4.0
```

| Essai | Réponse |
|---|---|
| `GET /health` | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` sans clé | 401 |
| `POST /v1/predict` avec la clé | `{"failure_probability":0.9475,"alert":true,...}` (la valeur exacte dépend du relevé envoyé) |

**Piège 1.** Sans l'option `-v ...models...`, que répondent `/health` et `/v1/predict` ? Pourquoi ?

`/health` répond `{"status":"ok","model_loaded":false}` et `/v1/predict` répond 503 « Modèle non chargé ». Le modèle n'est pas dans l'image (il est exclu par `.dockerignore`) : sans volume, `/app/models` est vide dans le conteneur, l'API démarre mais n'a rien à charger.

**Piège 2.** Avec `--host 127.0.0.1`, que disent `docker logs test` et `http://localhost:8002/health` ? Pourquoi ?

Les logs affichent « Uvicorn running on http://127.0.0.1:8000 » sans erreur, mais `localhost:8002/health` ne répond pas (réponse vide / connexion réinitialisée). Dans un conteneur, `127.0.0.1` veut dire « ce conteneur seulement » : uvicorn n'écoute que sur l'interface interne, alors que Docker relie le port publié à l'interface réseau du conteneur. Il faut `0.0.0.0` (toutes les interfaces).

## 5. Sprint 2 : Docker Compose

Votre `compose.yaml` :

```yaml
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
    command: ["python", "-m", "streamlit", "run", "ui/app.py",
              "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
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
[À COMPLÉTER : coller `docker compose ps` : services api et ui, état Up, ports 8000 et 8501]
```

Quelle URL affiche la barre latérale de l'interface ? D'où vient-elle ?

`http://api:8000`. Elle vient de la variable d'environnement `MAINTAI_API_URL`, définie dans `compose.yaml` pour le service `ui` et lue par `ui/app.py` avec `os.getenv("MAINTAI_API_URL", "http://localhost:8000")` ; la valeur `localhost` n'est que le défaut hors Docker.

Résultat des deux commandes `docker compose exec ui ...` (avec `api` puis avec `localhost`). Pourquoi la seconde échoue-t-elle ?

```
http://api:8000/health       -> {"status":"ok","model_loaded":true}
http://localhost:8000/health  -> ConnectError: Connection refused
```

Compose place les services sur un même réseau où chacun se joint par son nom : `api` désigne le conteneur de l'API. `localhost` désigne toujours « ce conteneur-ci » : depuis `ui`, il n'y a pas d'API sur le port 8000, d'où le refus. Dans le navigateur du PC, `localhost:8000` marche parce que Docker publie le port 8000 de l'API sur le PC (`-p`/`ports`) : c'est le PC qui est visé, pas le conteneur `ui`.

Dernière ligne de `python -m pytest` à la fin du sprint 2 (exécuté sur ces fichiers) :

```
38 passed, 4 warnings in 13.61s
```

`docker compose down` supprime les conteneurs et le réseau créés par Compose. Elle ne supprime ni l'image `maintai:0.4.0`, ni les dossiers du PC (`models/`, `data/`) montés en volumes.

## 6. Décision : l'ADR 005

Dans `docs/adr/005-image-docker.md`. Résumé : le modèle arrive par un volume en lecture seule et non dans l'image, parce qu'il change à son propre rythme et doit pouvoir être remplacé sans rebuild ; `.dockerignore` laisse dehors données, modèle, secret, fichiers MLflow/DVC, parce qu'un secret ne doit jamais entrer dans une image partageable.

## 7. Questions de compréhension

1. Qu'est-ce qui entre dans l'image, et qu'est-ce qui arrive au lancement ? Donnez le moyen pour chaque élément.
   Dans l'image (`docker build`) : Linux, Python 3.11, les bibliothèques figées (`COPY` + `pip install`), le code `maintai/` et `ui/` (`COPY`). Au lancement : le modèle (`-v ./models:/app/models:ro`), les données (`-v ./data:/app/data:ro`), la clé API (`--env-file .env` / `env_file`), et l'URL de l'API pour l'interface (variable `MAINTAI_API_URL`).
2. Pourquoi la clé API n'est-elle jamais dans l'image ?
   Une image se partage et se stocke (registre, collègues) et ses couches se lisent : un secret dedans serait exposé à quiconque la reçoit et ne pourrait être changé sans reconstruire. Donnée au lancement, la clé reste propre à chaque déploiement et peut changer sans nouvelle image.
3. Livrer un modèle (TP4, TP5) : qu'est-ce que Docker ajoute à la liste ?
   Le wheel du TP4 livrait le code, MLflow/DVC (TP5) tracent les entraînements et les données. Docker ajoute l'environnement d'exécution complet (système, version de Python, bibliothèques exactes) : le service tourne à l'identique sur tout PC ou serveur équipé de Docker, sans préparer de `.venv`.

## 8. Le rendu Git

- Lien de la pull request : [À COMPLÉTER]
- Le tag `tp6` existe sur GitHub : [À COMPLÉTER : oui / non]
- `git status` avant le commit : `.env`, `models/` ou `data/*.csv` apparaissaient-ils ? [À COMPLÉTER : normalement non, `.gitignore` les écarte]

## 9. Ce qui reste flou

[À COMPLÉTER : ce qui n'est pas clair pour vous, par exemple la différence entre `EXPOSE` et `-p`, ou comment mettre à jour le modèle dans un conteneur déjà lancé]