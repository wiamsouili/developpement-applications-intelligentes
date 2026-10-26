# Compte rendu · TP1 : une API de prédiction pour MaintAI

**Groupe :** …  ·  **Membres :** Hajar Belhachmi  ·  **Date :** 26/10/2026

**Résumé.** J'ai complété le schéma d'entrée (`schemas.py`) et la route `POST /v1/predict` (`main.py`) de l'API MaintAI. Les 13 tests passent et l'API répond correctement aux quatre requêtes de contrôle (200, 200, 422, 404). Le choix du modèle (régression logistique, seuil à 0,3) est documenté dans l'ADR 000 (`docs/adr/000-modele.md`).

---

## 1. Mise en place

Dernière ligne de `python -m pytest`, juste après la mise en place (rien n'est encore écrit) :

```
3 failed, 10 passed, 1 warning in 2.69s
```

Les 4 tests de `tests/test_api.py` qui passent déjà sont :
- `test_health` : la route `/health` est déjà écrite dans `main.py` ;
- `test_openapi_documents_predict` : la route `/v1/predict` existe déjà, donc elle apparaît dans la documentation OpenAPI ;
- `test_out_of_range_value_is_rejected` et `test_missing_field_is_rejected` : ils attendent un code 422.

Ces deux derniers passent « pour une mauvaise raison ». Le schéma `SensorReading` est encore vide et il est configuré avec `extra="forbid"`, qui refuse tout champ inconnu. Comme le schéma ne déclare aucun champ, n'importe quel corps de requête contenant `temperature_c`, `load_pct`… est rejeté avec un 422 parce que ces champs sont « interdits », et non parce que la valeur est hors bornes ou qu'un champ manque. Le test est vert, mais il ne vérifie pas encore la validation qu'il est censé vérifier.

## 2. Le schéma d'entrée (`maintai/api/schemas.py`)

| Variable | Type | Minimum (`ge`) | Maximum (`le`) | Justification physique (pas le min / max des données) |
|---|---|---|---|---|
| `temperature_c` | float | -40 | 150 | Plage de fonctionnement courante des capteurs industriels. En dessous de -40 °C ou au-dessus de 150 °C, la mesure n'est plus fiable ou la machine est détruite. |
| `vibration_mm_s` | float | 0 | 100 | Vitesse de vibration efficace : c'est une amplitude, donc jamais négative. Les machines industrielles sont déjà en zone dangereuse bien avant 100 mm/s, qui sert de limite de plausibilité du capteur. |
| `load_pct` | float | 0 | 100 | C'est un pourcentage de la charge nominale : il ne peut pas être négatif ni dépasser 100 %. |
| `runtime_hours` | float | 0 | 200 000 | Un compteur d'heures ne peut pas être négatif. 200 000 h correspondent à environ 23 ans de fonctionnement continu, ce qui dépasse la durée de vie d'une machine. |

Après avoir écrit `schemas.py` seul, `python -m pytest` donne :

```
3 failed, 10 passed, 1 warning in 2.85s

FAILED tests/test_api.py::test_predict_returns_probability - NotImplementedError
FAILED tests/test_api.py::test_high_risk_reading_raises_alert - NotImplementedError
FAILED tests/test_api.py::test_503_when_model_missing - NotImplementedError
(maintai/api/main.py:46: raise NotImplementedError)
```

C'est un bon signe : les requêtes valides passent maintenant la validation du schéma (fini les 422 injustifiés) et arrivent jusqu'au corps de `predict()`, qui n'est pas encore écrit. L'erreur a donc changé de place, du schéma vers la fonction, ce qui montre que le schéma fait son travail.

## 3. La fonction `predict()` (`maintai/api/main.py`)

Votre code :

```python
def predict(reading: SensorReading) -> PredictionOut:
    predictor = state.get("predictor")
    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail="Modèle non disponible : lancez d'abord `python -m maintai.train`.",
        )
    return PredictionOut(**predictor.predict(reading.model_dump()))
```

Pourquoi répondre **503** et pas 500 quand le modèle manque ?

Un 500 signale une erreur interne inattendue, c'est-à-dire un bug. Ici, l'absence du modèle est une situation connue et prévue : le service est temporairement indisponible et la cause est identifiable (le modèle n'a pas été entraîné). Le 503 le dit clairement au client et aux outils de supervision, indique que le problème n'est pas dans la requête et qu'on peut réessayer une fois le modèle disponible.

Pourquoi le modèle est-il chargé **une seule fois**, au démarrage, et pas à chaque requête ?

Charger le fichier `model.joblib` demande de lire le disque et de désérialiser le modèle, ce qui est lent par rapport au calcul d'une prédiction. Le faire à chaque requête augmenterait fortement la latence et la charge du serveur. En le chargeant une fois dans `lifespan`, toutes les requêtes réutilisent le même objet en mémoire, avec la même version du modèle.

## 4. Les tests

Dernière ligne de `python -m pytest` à la fin du TP :

```
13 passed, 1 warning in 1.27s
```

## 5. L'API en marche

Après `python -m maintai.dataset` et `python -m maintai.train`, lancement de `uvicorn maintai.api.main:app`, puis envoi des requêtes avec `curl` :

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| `GET /health` | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` avec `{"temperature_c": 72.5, "vibration_mm_s": 6.1, "load_pct": 85, "runtime_hours": 15000}` | 200 | `{"failure_probability":0.9553,"alert":true,"threshold":0.3,"model_version":"2026-10-26T12:10:48Z"}` |
| `POST /v1/predict` avec une température de 500 | 422 | `{"detail":[{"type":"less_than_equal","loc":["body","temperature_c"],"msg":"Input should be less than or equal to 150","input":500,"ctx":{"le":150.0}}]}` |
| `POST /v1/predicte` (faute de frappe dans l'adresse) | 404 | `{"detail":"Not Found"}` |

Lecture des résultats : la température de 500 °C est refusée par le schéma avant même d'atteindre le modèle (422, erreur de validation de la requête). La faute de frappe dans l'adresse donne un 404, car la route n'existe pas : ce n'est pas un problème de données mais d'adresse. Pour le relevé valide, la probabilité de panne (0,9553) dépasse le seuil de 0,3, donc `alert` vaut `true`.

Dans `/docs`, où voit-on les bornes que vous avez choisies ?

Dans la route `POST /v1/predict`, la partie « Request body » montre le schéma `SensorReading`. Chaque champ y est décrit avec sa description, son minimum et son maximum. La section « Schemas », en bas de la page, détaille aussi `SensorReading` avec ces contraintes.

## 6. Questions de compréhension

1. REST et FastAPI : quelle est la différence ?
   REST est un style d'architecture pour concevoir des API (ressources identifiées par des adresses, méthodes HTTP comme GET et POST, réponses sans état). FastAPI est un framework Python qui permet de construire une API en respectant ce style. REST est une idée, FastAPI est un outil qui la met en œuvre.
2. Le schéma Pydantic sert à trois choses. Lesquelles ?
   (1) Valider les données entrantes (types et bornes) et rejeter les mauvaises avec un 422, (2) documenter l'API, car FastAPI en tire la page `/docs` et le contrat OpenAPI, (3) convertir les données JSON en objets Python typés utilisables directement dans le code.
3. Dans `http://localhost:8000/v1/predict`, que désignent `localhost`, `8000` et `/v1/predict` ?
   `localhost` est la machine locale (l'ordinateur sur lequel tourne le serveur), `8000` est le port sur lequel le serveur écoute, et `/v1/predict` est le chemin de la route, c'est-à-dire la ressource demandée dans la version 1 de l'API.
4. Pourquoi `/v1` dans l'adresse ?
   Pour versionner l'API. Si le format des entrées ou des sorties change plus tard, on peut publier une `/v2` sans casser les clients qui utilisent encore la `/v1`.
5. Dans la commande `uvicorn maintai.api.main:app`, que désignent `maintai.api.main` et `app` ?
   `maintai.api.main` est le module Python à importer (le fichier `maintai/api/main.py`), et `app` est le nom de la variable dans ce module qui contient l'application FastAPI, celle qu'uvicorn doit servir.

## 7. Le rendu Git

- Lien de la pull request : https://github.com/wiamsouili/developpement-applications-intelligentes/pull/1
- Le tag `tp1` existe sur GitHub : oui
- Qui a relu la pull request, et quel commentaire a-t-il laissé ?
  Relecteur : mon binôme de TP. Commentaire : « Code conforme et propre, les 13 tests passent avec succès, documentation Pydantic et ADR 002 claires et bien justifiées physiquement. Pull request validée et fusionnée. »

## 8. Ce qui reste flou

Le passage de ce prototype à une utilisation industrielle me paraît encore flou sur deux points :

1. **La dérive des données (data drift).** Comment détecter automatiquement que les valeurs des capteurs s'éloignent de celles vues à l'entraînement, sans ralentir l'API qui répond en temps réel ? Je ne sais pas encore si cette surveillance doit tourner en tâche séparée, par lots, hors du chemin de la requête.
2. **La conteneurisation.** Comment empaqueter l'application dans une image Docker minimale (dépendances, modèle `joblib` et version de scikit-learn identiques à l'entraînement) pour un déploiement continu et reproductible ?
