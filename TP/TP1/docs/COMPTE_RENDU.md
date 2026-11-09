# Compte rendu · TP1 : une API de prédiction pour MaintAI

**Groupe :** G3  ·  **Membres :** Wian Souili  ·  **Date :** 26/10/2026

---

## 1. Mise en place

Dernière ligne de `python -m pytest`, juste après la mise en place (rien n'est encore écrit) :

```
3 failed, 10 passed, 1 warning in 0.82s
```

Dans `tests/test_api.py`, 4 tests sur 7 passent déjà alors que rien n'est écrit : `test_health`, `test_out_of_range_value_is_rejected`, `test_missing_field_is_rejected` et `test_openapi_documents_predict`.

Les deux tests qui attendent un 422 (`test_out_of_range_value_is_rejected` et `test_missing_field_is_rejected`) passent « pour une mauvaise raison » : le schéma `SensorReading` est vide et configuré avec `extra="forbid"`. Comme il n'a aucun champ déclaré, **tout** champ envoyé est « inconnu » et la requête est refusée en 422, même un relevé parfaitement valide. Le 422 ne vient donc pas de la température de 500 ni du champ manquant, mais du schéma vide. Ces tests ne prouvent rien tant que le schéma n'est pas écrit.

## 2. Le schéma d'entrée (`maintai/api/schemas.py`)

| Variable | Type | Minimum (`ge`) | Maximum (`le`) | Justification physique (pas le min / max des données) |
|---|---|---|---|---|
| `temperature_c` | float | -40 | 150 | Plage donnée : un moteur en atelier ou en extérieur peut être très froid à l'arrêt (-40 °C) ; au-delà de 150 °C, l'isolant des bobinages (classe F/H) est détruit, donc une valeur supérieure est un capteur défaillant. |
| `vibration_mm_s` | float | 0 | 50 | Une vitesse de vibration efficace est une grandeur positive (0 = machine à l'arrêt). Les normes (ISO 10816/20816) classent « danger » à partir d'environ 11 à 18 mm/s selon la machine ; 50 mm/s laisse une grande marge pour une machine en très mauvais état sans accepter des valeurs absurdes. |
| `load_pct` | float | 0 | 120 | Pourcentage de la charge nominale : 0 % à vide. Une surcharge temporaire jusqu'à ~120 % est possible et doit pouvoir être prédite (c'est justement un cas à risque), mais pas au-delà. |
| `runtime_hours` | float | 0 | 100000 | Heures cumulées : jamais négatives. Une machine industrielle dure 10 à 11 ans en service continu (~ 87 600 à 96 000 h) ; 100 000 h couvre une machine en fin de vie. |

Les bornes sont **physiques** : elles ne sont pas copiées sur `sensors.csv` (où `runtime_hours` ne dépasse pas 20 000 et la température reste autour de 60 ± 30 °C), sinon une machine réelle un peu plus chaude ou plus ancienne serait refusée à tort. Tous les champs sont de type `float` (et non `int`) pour accepter par exemple 15000,5 heures.

Après avoir écrit `schemas.py` seul, `python -m pytest` donne :

```
FAILED tests/test_api.py::test_predict_returns_probability - NotImplementedError
FAILED tests/test_api.py::test_503_when_model_missing - NotImplementedError
3 failed, 10 passed, 1 warning in 1.57s
```

Il y a toujours 3 échecs, mais le message d'erreur a changé : on passe de `assert 422 == 200` à `NotImplementedError`. C'est un bon signe : le schéma accepte maintenant les relevés valides, la requête franchit la validation et arrive jusqu'à la fonction `predict()` (qui n'est pas encore écrite). De plus, les deux tests de 422 passent désormais **pour la bonne raison** (valeur hors bornes, champ manquant).

## 3. La fonction `predict()` (`maintai/api/main.py`)

Votre code :

```python
@router.post("/predict", response_model=PredictionOut)
def predict(reading: SensorReading) -> PredictionOut:
    predictor = state.get("predictor")
    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail="Modèle non chargé : lancez `python -m maintai.train`, puis relancez l'API.",
        )
    return PredictionOut(**predictor.predict(reading.model_dump()))
```

Pourquoi répondre **503** et pas 500 quand le modèle manque ?

Un 500 signifie « bug dans le code du serveur ». Ici le code est correct : c'est le service qui est temporairement **indisponible** parce qu'il manque un artefact (le modèle n'a pas été entraîné). Le 503 le dit exactement, indique au client que la requête est valide et qu'il pourra réessayer plus tard, et le message du `detail` dit quoi faire (lancer l'entraînement). Un 500 pousserait à chercher un bug qui n'existe pas.

Pourquoi le modèle est-il chargé **une seule fois**, au démarrage, et pas à chaque requête ?

Lire `model.joblib` sur le disque et le désérialiser coûte du temps (de l'ordre de la dizaine de millisecondes ou plus pour un gros modèle) et des accès disque. Le faire à chaque requête rendrait l'API lente et inefficace sous charge. Chargé une fois dans `state` (via `lifespan`), le modèle reste en mémoire et chaque requête ne paie que le calcul de la prédiction. Cela permet aussi de détecter le problème dès le démarrage (`/health` signale `model_loaded: false`).

## 4. Les tests

Dernière ligne de `python -m pytest` à la fin du TP :

```
13 passed, 1 warning in 0.77s
```

## 5. L'API en marche

Après `python -m maintai.dataset` et `python -m maintai.train`, `uvicorn maintai.api.main:app --reload`, puis les requêtes (envoyées avec `curl`) :

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| `GET /health` | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` avec `{"temperature_c": 72.5, "vibration_mm_s": 6.1, "load_pct": 85, "runtime_hours": 15000}` | 200 | `{"failure_probability":0.9553,"alert":true,"threshold":0.3,"model_version":"2026-10-26T21:32:17Z"}` |
| `POST /v1/predict` avec une température de 500 | 422 | `{"detail":[{"type":"less_than_equal","loc":["body","temperature_c"],"msg":"Input should be less than or equal to 150","input":500,"ctx":{"le":150.0}}]}` |
| `POST /v1/predicte` (faute de frappe dans l'adresse) | 404 | `{"detail":"Not Found"}` |

Dans `/docs`, où voit-on les bornes que vous avez choisies ?

Dans la section **Schemas** en bas de la page, à `SensorReading` : chaque champ affiche son type, son minimum, son maximum et sa description. On les retrouve aussi dans le corps de la requête de la route `POST /v1/predict` (« Request body », onglet *Schema*), avec l'exemple pré-rempli. Elles sont également dans `/openapi.json`.

## 6. Questions de compréhension

1. REST et FastAPI : quelle est la différence ?
   REST est un ensemble de **règles** de conception d'une API web (URL claires, méthodes HTTP, codes de statut précis, JSON, version). FastAPI est une **bibliothèque Python** (un outil) avec laquelle on écrit une API qui suit ces règles. On écrit une API REST *avec* FastAPI.
2. Le schéma Pydantic sert à trois choses. Lesquelles ?
   (1) **Valider** chaque requête avant d'appeler la fonction (422 si invalide) ; (2) **documenter** : générer la page `/docs` avec champs, types, bornes et exemple ; (3) **fournir un objet Python typé** (`reading.temperature_c` est un `float` déjà vérifié, `reading.model_dump()` donne un dictionnaire).
3. Dans `http://localhost:8000/v1/predict`, que désignent `localhost`, `8000` et `/v1/predict` ?
   `localhost` : la machine elle-même (le serveur tourne sur mon PC) ; `8000` : le port, la « porte » où uvicorn écoute ; `/v1/predict` : la route, un chemin défini dans le code Python (pas un dossier du disque), en version 1 de l'API.
4. Pourquoi `/v1` dans l'adresse ?
   C'est la version de l'API : le contrat (champs, réponses) pourra évoluer dans une future `/v2` sans casser les clients qui utilisent encore `/v1`.
5. Dans la commande `uvicorn maintai.api.main:app`, que désignent `maintai.api.main` et `app` ?
   `maintai.api.main` est le fichier `maintai/api/main.py` écrit avec des points et sans `.py` ; `app` est la variable de ce fichier qui contient l'application (`app = FastAPI(...)`).

## 7. Le rendu Git

- Lien de la pull request : à compléter après la création de la PR sur GitHub (branche `tp1` → `main`)
- Le tag `tp1` existe sur GitHub : à confirmer après `git push --tags` (le tag `tp1` est créé dans le dépôt local fourni)
- Qui a relu la pull request, et quel commentaire a-t-il laissé ?
  À compléter par le coéquipier relecteur (pytest passe chez lui, ni données ni modèle ni `.venv` dans les changements, ADR 002 présent, compte rendu rempli).

## 8. Ce qui reste flou

Le choix des bornes physiques reste une part de jugement : sans fiche technique du moteur réel, 50 mm/s pour les vibrations et 120 % pour la charge sont des ordres de grandeur à valider avec un technicien de maintenance. Je me demande aussi s'il faudrait un endpoint qui accepte plusieurs relevés d'un coup.
