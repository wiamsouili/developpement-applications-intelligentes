# ADR 005 : Contenu de l'image Docker de MaintAI

Date : 23/11/2026 · Auteurs : [noms du groupe]

## Contexte
MaintAI doit tourner sur un serveur où personne ne prépare de `.venv`, avec la même version de scikit-learn que celle qui a écrit le modèle (1.8.0). Le modèle et les données changent plus souvent que le code (séance 7), et la clé API est un secret : l'image, qu'on peut partager, ne doit contenir aucun des trois par accident.

## Options étudiées
### Décision A : le modèle dans l'image ou par un volume ?
1. **Modèle copié dans l'image** : l'image est autonome (un seul `docker run`, rien à monter) et le couple code/modèle est figé ensemble. Mais chaque ré-entraînement oblige à reconstruire et republier une image de plus d'un Go, un modèle d'essai se retrouve partout où l'image est partagée, et l'image dépend d'un fichier qui n'est pas dans Git.
2. **Modèle monté par un volume (`-v ./models:/app/models:ro`)** : l'image ne change que quand le code change ; un nouveau modèle se déploie en remplaçant un fichier, sans rebuild ; l'image reste petite et sans donnée. Mais le lancement dépend d'un dossier extérieur : si l'on oublie `-v`, l'API démarre avec `model_loaded: false` et répond 503 ; il faut aussi vérifier que la version du modèle correspond à celle des bibliothèques de l'image.

### Décision B : que laisse dehors `.dockerignore` ?
1. **Tout copier** (`COPY . .`) : plus simple à écrire, mais l'image embarque le secret `.env`, les données, le `.venv`, l'historique `.git` ; le contexte de build est lourd et le cache est invalidé à chaque modification sans rapport.
2. **Exclure explicitement** `.venv/`, `data/`, `models/`, `.env`, `mlflow.db`, `mlruns/`, `.dvc/`, `.git/`, `tests/` et les caches : on écrit une liste de plus à entretenir, et un oubli futur reste possible, mais le secret ne peut pas fuiter, l'image est plus légère et le build plus rapide.

## Décision
- **Le modèle arrive par un volume en lecture seule, pas dans l'image.** Raison principale : le modèle change à son propre rythme (ré-entraînement, TP5) et doit pouvoir être remplacé sans nouveau code ni nouveau build. Ce que l'autre option aurait fait gagner (autonomie de l'image) ne compense pas le rebuild à chaque modèle.
- **`.dockerignore` exclut données, modèle, secret, fichiers MLflow, cache DVC, `.venv`, `.git` et tests.** Raison principale : un secret ne doit jamais entrer dans une image qu'on peut partager ; la légèreté et le cache en sont des bénéfices secondaires.
- La clé API arrive avec `env_file: .env` (ou `--env-file .env`), jamais écrite dans le Dockerfile ni dans `compose.yaml`.

## Conséquences
- Facilite : des images reproductibles construites depuis le Dockerfile (elles ne vont pas dans Git), un déploiement de modèle sans rebuild, un build de quelques secondes quand seul le code change (couche `pip install` en cache).
- Complique : le lancement exige le volume et le fichier `.env` ; sans eux l'API répond 503 ou 401, ce qui doit figurer dans la documentation d'exploitation.
- À surveiller : la cohérence entre la version de scikit-learn de l'image (figée dans `requirements-docker.txt`) et celle du modèle ; l'ajout futur de fichiers sensibles qui devraient rejoindre `.dockerignore` ; l'adresse `0.0.0.0` dans le conteneur, qui n'est sûre que parce que Docker ne publie que les ports demandés avec `-p`.
