# Compte rendu · TP1 : une API de prédiction pour MaintAI

**Groupe :*G3* …  ·  **Membres :*ELAOUAZI-SOUILI-YEKHLEF-BELHACHMI* …  ·  **Date :*26/10/2026* …

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP1.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place

DDernière ligne de python -m pytest, juste après la mise en place (avant toute modification du code API) :
=========================== 3 failed, 10 passed   ===========================
Les 4 tests de tests/test_api.py qui passent déjà doivent être nommés d’après les intitulés exacts du fichier de tests. Je ne dispose pas ici du contenu complet de tests/test_api.py, donc je ne peux pas les identifier avec certitude sans inventer leurs noms.

Les deux tests qui attendent un code 422 passent pour une mauvaise raison : le schéma SensorReading est encore vide et la configuration extra="forbid" interdit les champs qui ne sont pas déclarés. Ainsi, même une requête correcte contenant les quatre variables est rejetée parce que ces champs sont considérés comme inconnus. Le code 422 obtenu ne prouve donc pas encore que les bornes de validation fonctionnent correctement.

…

## 2. Le schéma d'entrée (`maintai/api/schemas.py`)


Variable	|Type	|Minimum (ge)	|Maximum (le)	|Justification physique
temperature_c	|float	|-40	|150	|Plage large de températures possibles autour d’une machine, permettant de rejeter des valeurs irréalistes sans se limiter aux seules données d’entraînement.

vibration_mm_s	|float	|0	|50	|Une vitesse vibratoire ne peut pas être négative ; 50 mm/s est une limite haute choisie pour rejeter les valeurs excessives.

load_pct	|float	|0	|100	|Le taux de charge est exprimé en pourcentage et doit donc rester entre 0 % et 100 %.

runtime_hours	|float	|0	|200000	|Le nombre cumulé d’heures ne peut pas être négatif ; la limite supérieure est large pour représenter une longue durée de fonctionnement.

Après avoir écrit schemas.py seul, python -m pytest échoue encore sur 3 tests, mais l’erreur est désormais NotImplementedError dans la fonction predict() :
================3 failed, 10 passed =====================
C’est un bon signe : le schéma accepte désormais les relevés valides et la requête atteint la fonction predict(). Les échecs ne sont donc plus causés par le schéma vide ; il reste à implémenter la prédiction.

## 3. La fonction `predict()` (`maintai/api/main.py`)

Votre code :

```python
@router.post("/predict", response_model=PredictionOut)
def predict(reading: SensorReading) -> PredictionOut:
    predictor = state.get("predictor")

    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail="Modèle de prédiction indisponible.",
        )

    return predictor.predict(reading.model_dump())
```

On répond 503 et non 500 quand le modèle manque, car le problème est une indisponibilité connue du service : le modèle n’est pas chargé. Le code 503 décrit mieux la situation et donne une réponse contrôlée, plutôt qu’une erreur interne inattendue 500 provoquée par l’utilisation d’un objet inexistant.

Le modèle est chargé une seule fois au démarrage pour éviter de relire le fichier et de reconstruire le prédicteur à chaque requête. Cela réduit le temps de réponse et le travail inutile ; toutes les requêtes réutilisent le prédicteur déjà chargé dans state.

…

## 4. Les tests

Dernière ligne de `python -m pytest` à la fin du TP :

```
==============13 passed in 4.07s ====================
```

## 5. L'API en marche

Le serveur a été lancé avec python -m uvicorn maintai.api.main:app --reload, puis l’interface Swagger a été ouverte à http://127.0.0.1:8000/docs.

| Requête | Code obtenu | Réponse (le corps JSON) |

GET /health    	|200 — testé	         |Recopier le JSON exact affiché par Swagger. Le résultat attendu indique que l’API répond et si le modèle est chargé.

POST /v1/predict avec {"temperature_c": 72.5, "vibration_mm_s": 6.1, "load_pct": 85, "runtime_hours": 15000}	    |200 — testé	   |Recopier le JSON exact affiché par Swagger, notamment failure_probability, alert et threshold. La probabilité exacte n’est pas disponible dans les informations transmises.

POST /v1/predict avec une température de 500	   |422 — attendu, à tester pour confirmer   |	Réponse de validation FastAPI/Pydantic indiquant que temperature_c dépasse la borne maximale de 150.

POST /v1/predicte (faute de frappe dans l’adresse)	  |404 — attendu, à tester pour confirmer	        |Réponse FastAPI signalant que la route n’existe pas, généralement {"detail":"Not Found"}.

…
Dans /docs, les bornes apparaissent dans la documentation du corps de requête de POST /v1/predict : ouvrir le schéma SensorReading ou cliquer sur Try it out pour consulter les champs et leurs contraintes/descriptions.

## 6. Questions de compréhension

1. REST et FastAPI : quelle est la différence ?
REST est un style d’architecture qui définit des principes pour concevoir des API HTTP. FastAPI est un framework Python permettant de construire des API, notamment en appliquant ces principes.

2. Le schéma Pydantic sert à trois choses. Lesquelles ?
Il décrit les champs attendus et leurs types ; il valide les données et leurs contraintes (bornes comprises) ; il fournit à FastAPI les informations nécessaires pour documenter automatiquement le contrat de l’API dans OpenAPI/Swagger.

3. Dans http://localhost:8000/v1/predict, que désignent localhost, 8000 et /v1/predict ?
localhost désigne la machine locale ; 8000 est le port sur lequel le serveur écoute ; /v1/predict est le chemin de la route de prédiction.

4. Pourquoi /v1 dans l’adresse ?
Il indique la version 1 de l’API. Une version permet de faire évoluer l’API plus tard en limitant les risques de casser les clients qui utilisent l’ancienne version.

5. Dans la commande uvicorn maintai.api.main:app, que désignent maintai.api.main et app ?
maintai.api.main est le chemin du module Python qui contient le code de l’API ; app est l’objet application ASGI créé dans ce module et servi par Uvicorn.
   …

## 7. Le rendu Git

- Lien de la pull request : …
- Le tag `tp1` existe sur GitHub : oui / non
- Qui a relu la pull request, et quel commentaire a-t-il laissé ?
  …

## 8. Ce qui reste flou

Je comprends le rôle du schéma Pydantic, la différence entre les codes HTTP 422, 404 et 503, et le chemin d’une requête jusqu’au prédicteur. Je dois encore mieux comprendre comment la probabilité produite par le modèle est convertie en alerte à partir du seuil de 0,3, ainsi que la façon dont le chargement du modèle est organisé au démarrage de l’application.
