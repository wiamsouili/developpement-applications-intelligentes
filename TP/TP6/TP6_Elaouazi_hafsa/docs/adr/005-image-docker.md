# ADR 005 : Le modèle arrive par un volume, l'image ne porte que le code

Date : 23/11/2026 · Auteurs : Elaouazi Hafsa

## Contexte

MaintAI ne tournait que sur un PC préparé (bon Python, `.venv`, bonne version de scikit-learn) et doit tourner sur un serveur où personne ne prépare d'environnement. On l'emballe dans l'image `maintai:0.4.0`, et il faut décider ce que l'image contient et ce qui lui est donné au lancement. Le modèle et les données changent sans nouveau code (séance 7), et la clé API est un secret : ils n'ont pas le même cycle de vie que le code.

## Options étudiées

**Décision 1 : où met-on le modèle ?**

1. **Modèle dans l'image** : l'image est autonome et démarre sans rien monter. En revanche, chaque nouveau modèle impose un `docker build` et une nouvelle version d'image, et on mélange deux cycles de vie différents (code et modèle).
2. **Modèle par un volume** (`-v ...\models:/app/models:ro`) : on remplace ou réentraîne le modèle sans reconstruire l'image, qui reste identique et garde son cache de couches. En revanche, l'image seule ne démarre pas correctement : sans le volume, `/health` répond `model_loaded: false` et `/v1/predict` répond 503.

**Décision 2 : que laisse-t-on dehors avec `.dockerignore` ?**

1. **Tout copier dans l'image** : aucun volume à fournir, mais l'image devient lourde, le build lent, et elle embarque le secret `.env`, les données et l'historique MLflow.
2. **Exclure ce qui est local, lourd ou secret** : `.venv/`, caches, `.git/`, `dist/`, `build/`, `*.egg-info/`, `tests/`, puis `data/`, `models/`, `.env`, `mlflow.db`, `mlruns/` et `.dvc/`. L'image est légère et sans secret ; en contrepartie, ce qui est exclu doit être fourni autrement (volume ou `--env-file`).

## Décision

On retient le **volume pour le modèle** et un **`.dockerignore` qui exclut ce qui est local, lourd ou secret**. La raison principale : le modèle et les données changent sans nouveau code, et une clé API qui entre dans une image fuit dès qu'on la partage. L'image porte donc seulement Linux, Python 3.11, les bibliothèques figées (`scikit-learn==1.8.0`) et le code ; le modèle et les données arrivent par volume, la clé par `--env-file`.

## Conséquences

- **Plus facile :** réentraîner et remplacer le modèle sans rebuild, partager l'image sans risque de fuite, build rapide grâce au cache de couches.
- **Plus difficile :** l'image ne démarre pas seule. Il faut le volume `models/` et le fichier `.env` au lancement, ce que `compose.yaml` automatise. On ne peut pas lancer `pytest` dans le conteneur, puisque `tests/` en est exclu.
- **À surveiller :** la version de scikit-learn dans l'image doit rester celle qui a entraîné le modèle (`==1.8.0`), sinon le modèle ne se recharge plus. Il faut aussi vérifier que `.env` reste dans `.dockerignore` et dans `.gitignore`.