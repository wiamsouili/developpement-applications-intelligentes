# Compte rendu · TP1 : une API de prédiction pour MaintAI

**Groupe :** …  ·  **Membres :** Wiam Souili  ·  **Date :** 26/10/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP1.  
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Mise en place

Dernière ligne de `python -m pytest`, juste après la mise en place (rien n'est encore écrit) :

```text id="w76s7z"
À compléter avec la sortie obtenue au tout début du TP.
```

Dans `tests/test_api.py`, 4 tests sur 7 passent déjà alors que rien n'est écrit. Lesquels ? Pour les deux tests qui attendent un code 422, expliquez pourquoi ils passent « pour une mauvaise raison » (indice : regardez `extra="forbid"` dans `schemas.py`).

Les tests de l’API vérifient notamment le fonctionnement de `/health`, la prédiction, l’alerte en cas de risque élevé, la validation des données, le comportement lorsque le modèle est absent et la présence de l’endpoint dans la documentation OpenAPI.

Les deux tests qui attendent un code HTTP `422` sont :

- `test_out_of_range_value_is_rejected`
- `test_missing_field_is_rejected`

Ils peuvent initialement passer « pour une mauvaise raison » à cause de la configuration :

```python id="nwnymx"
model_config = ConfigDict(
    extra="forbid"
)
```

`extra="forbid"` indique à Pydantic qu’il doit refuser les champs supplémentaires qui ne sont pas déclarés dans le modèle.

Ainsi, une requête peut retourner un code `422 Unprocessable Entity` parce que sa structure ne correspond pas au schéma attendu, et non parce que les contraintes physiques des variables ont été correctement définies.

Après l’implémentation du schéma, les requêtes incorrectes doivent être rejetées pour la bonne raison : une valeur située en dehors des bornes autorisées, un champ obligatoire manquant ou la présence d’un champ non autorisé.

---

## 2. Le schéma d'entrée (`maintai/api/schemas.py`)

| Variable | Type | Minimum (`ge`) | Maximum (`le`) | Justification physique (pas le min / max des données) |
|---|---|---:|---:|---|
| `temperature_c` | `float` | `-40` | `150` | Une machine peut fonctionner à des températures négatives ou élevées, mais les valeurs doivent rester dans une plage physiquement plausible. |
| `vibration_mm_s` | `float` | `0` | `50` | Une vitesse de vibration ne peut pas être négative. La limite de 50 mm/s permet d’exclure des valeurs physiquement excessives dans le contexte étudié. |
| `load_pct` | `float` | `0` | `100` | La charge est exprimée en pourcentage. Elle doit donc être comprise entre 0 % et 100 %. |
| `runtime_hours` | `float` | `0` | `200000` | Un nombre d’heures de fonctionnement ne peut pas être négatif. La borne supérieure évite des durées physiquement irréalistes. |

Le schéma Pydantic utilise `Field` pour définir les contraintes de validation.

Par exemple :

```python id="e83wtc"
temperature_c: float = Field(
    ge=-40,
    le=150,
    description="Température de la machine en degrés Celsius",
)
```

Le schéma contient également :

```python id="u6qdvr"
model_config = ConfigDict(
    extra="forbid"
)
```

Cette configuration permet de refuser les propriétés supplémentaires qui ne font pas partie du schéma prévu.

Après avoir écrit `schemas.py` seul, que donne `python -m pytest`, et quel est le message d'erreur des tests qui échouent ? Pourquoi est-ce un bon signe ?

```text id="ezfqzd"
La sortie exacte correspondant uniquement à cette étape n'a pas été conservée dans le terminal fourni.
```

Le fait que certains tests passent alors que ceux dépendant encore de l’implémentation de `predict()` échouent est un bon signe. Cela montre que le schéma d’entrée fonctionne correctement et que Pydantic valide désormais les données avant leur transmission au modèle.

---

## 3. La fonction `predict()` (`maintai/api/main.py`)

Votre code :

```python id="87mx6z"
def predict(reading: SensorReading) -> PredictionOut:
    predictor = state.get("predictor")

    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail="Modèle de prédiction indisponible.",
        )

    return predictor.predict(reading.model_dump())
```

### Pourquoi répondre **503** et pas 500 quand le modèle manque ?

Le code HTTP `503 Service Unavailable` signifie que le serveur fonctionne, mais que le service demandé est temporairement indisponible.

Dans MaintAI, l’API peut démarrer même si le modèle de prédiction n’est pas disponible. Dans cette situation, `/health` reste accessible, mais l’endpoint `/v1/predict` ne peut pas effectuer de prédiction.

Cette situation est explicitement gérée :

```python id="3ve9ye"
if predictor is None:
    raise HTTPException(
        status_code=503,
        detail="Modèle de prédiction indisponible.",
    )
```

Un code `500 Internal Server Error` correspondrait davantage à une erreur interne inattendue.

L’absence du modèle étant une situation connue et gérée par l’application, le code `503` est plus précis.

### Pourquoi le modèle est-il chargé **une seule fois**, au démarrage, et pas à chaque requête ?

Deux possibilités ont été étudiées pour le chargement du modèle.

**Option 1 : charger le modèle à chaque requête.**

Cette solution est simple, mais elle oblige l’application à accéder au disque et à charger le même modèle à chaque appel de `/v1/predict`. Cela augmente inutilement le temps de réponse et l’utilisation des ressources.

**Option 2 : charger le modèle une seule fois au démarrage.**

Cette solution permet de conserver le modèle en mémoire et de le réutiliser pour toutes les requêtes.

C’est cette deuxième option qui a été retenue dans MaintAI.

Le modèle est chargé au démarrage grâce au mécanisme `lifespan` de FastAPI :

```python id="11knch"
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        state["predictor"] = Predictor.load(get_settings())
    except FileNotFoundError:
        state["predictor"] = None

    yield
    state.clear()
```

Le modèle est ensuite récupéré depuis `state` lors de chaque prédiction :

```python id="egh06m"
predictor = state.get("predictor")
```

Cette décision évite les chargements répétitifs depuis le disque et améliore les performances de l’API.

Elle implique cependant qu’une nouvelle version du modèle enregistrée sur le disque ne sera pas automatiquement utilisée par l’API déjà en cours d’exécution. Un redémarrage ou un mécanisme de rechargement serait alors nécessaire.

---

## 4. Les tests

Dernière ligne de `python -m pytest` à la fin du TP :

```text id="6rx65n"
=============================================== 13 passed in 3.78s ================================================
```

La sortie finale obtenue est :

```text id="8wd70i"
tests\test_api.py .......        [ 53%]
tests\test_data.py ...           [ 76%]
tests\test_train.py ...          [100%]

=============================================== 13 passed in 3.78s ================================================
```

Les **13 tests passent**. Cela confirme que les fonctionnalités couvertes par les tests automatisés fonctionnent correctement.

---

## 5. L'API en marche

Le dataset a été généré avec :

```bash id="j6c2s3"
python -m maintai.dataset
```

Résultat :

```text id="5w6ogp"
5000 relevés écrits dans C:\Users\HP\Downloads\maintai-starter-tp1\data\sensors.csv (taux de panne : 13.6%)
```

Le modèle a ensuite été entraîné avec :

```bash id="1jclu3"
python -m maintai.train
```

Les performances obtenues sont :

```text id="4duesg"
accuracy  : 0.904
recall    : 0.75
precision : 0.622
threshold : 0.3
n_train   : 4000
n_test    : 1000
```

La baseline donne :

```text id="y8kh5u"
accuracy : 0.864
recall   : 0.0
```

Le modèle a été sauvegardé dans :

```text id="j0vpvp"
C:\Users\HP\Downloads\maintai-starter-tp1\models\model.joblib
```

L’API a ensuite été lancée avec :

```bash id="54e08p"
python -m uvicorn maintai.api.main:app --reload
```

Le serveur a démarré correctement :

```text id="7b4vsn"
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Résultats des requêtes

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---:|---|
| `GET /health` | `200` | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict` avec `{"temperature_c": 72.5, "vibration_mm_s": 6.1, "load_pct": 85, "runtime_hours": 15000}` | À relever dans `/docs` | À copier depuis `/docs`, car la probabilité exacte dépend du modèle entraîné. |
| `POST /v1/predict` avec une température de `500` | `422` | Erreur de validation indiquant que `temperature_c` dépasse la valeur maximale autorisée de `150`. |
| `POST /v1/predicte` (faute de frappe dans l'adresse) | `404` | `{"detail":"Not Found"}` |

### Dans `/docs`, où voit-on les bornes que vous avez choisies ?

Les bornes sont visibles dans la documentation Swagger générée automatiquement par FastAPI à partir du schéma Pydantic.

Dans `/docs`, le schéma `SensorReading` présente les propriétés attendues ainsi que leurs contraintes.

| Champ | Minimum | Maximum |
|---|---:|---:|
| `temperature_c` | `-40` | `150` |
| `vibration_mm_s` | `0` | `50` |
| `load_pct` | `0` | `100` |
| `runtime_hours` | `0` | `200000` |

Ces informations proviennent directement des paramètres `ge` et `le` définis dans `schemas.py`.

---

## 6. Questions de compréhension

### 1. REST et FastAPI : quelle est la différence ?

REST est un **style d’architecture** permettant d’organiser les échanges entre un client et un serveur à travers le protocole HTTP.

Une API REST utilise notamment des méthodes HTTP comme `GET`, `POST`, `PUT` ou `DELETE` ainsi que des codes de réponse comme `200`, `404`, `422` ou `503`.

FastAPI est un **framework Python** permettant de développer concrètement une API web.

On peut donc résumer la différence ainsi :

**REST = principes d’architecture.**

**FastAPI = outil Python permettant d’implémenter l’API.**

---

### 2. Le schéma Pydantic sert à trois choses. Lesquelles ?

Le schéma Pydantic sert principalement à :

**1. Valider les données d’entrée**

Il vérifie que les données envoyées respectent les contraintes définies.

Par exemple :

```python id="27ek6u"
temperature_c: float = Field(ge=-40, le=150)
```

permet de refuser une température de `500`.

**2. Définir et convertir les types**

Pydantic permet d’indiquer les types attendus comme `float`, `bool` ou `str` et de fournir à l’application des données structurées.

**3. Générer la documentation**

FastAPI utilise les modèles Pydantic pour générer automatiquement la documentation OpenAPI/Swagger disponible dans `/docs`.

On y retrouve les champs attendus, leurs types et leurs contraintes.

---

### 3. Dans `http://localhost:8000/v1/predict`, que désignent `localhost`, `8000` et `/v1/predict` ?

Dans :

```text id="17as0h"
http://localhost:8000/v1/predict
```

- `localhost` désigne la machine locale sur laquelle l’API est exécutée.
- `8000` désigne le port réseau utilisé par le serveur Uvicorn.
- `/v1/predict` désigne l’endpoint permettant d’envoyer un relevé de capteurs afin d’obtenir une prédiction.

---

### 4. Pourquoi `/v1` dans l'adresse ?

`/v1` signifie **version 1 de l’API**.

Dans le projet, ce préfixe est défini avec :

```python id="t80t2x"
router = APIRouter(prefix="/v1")
```

Le versionnement permet de faire évoluer l’API tout en conservant une compatibilité avec les applications utilisant une version précédente.

Par exemple, une nouvelle version pourrait utiliser :

```text id="b9cezj"
/v2/predict
```

tout en maintenant temporairement :

```text id="hrg1xd"
/v1/predict
```

---

### 5. Dans la commande `uvicorn maintai.api.main:app`, que désignent `maintai.api.main` et `app` ?

Dans :

```bash id="0jjf2f"
uvicorn maintai.api.main:app
```

`maintai.api.main` désigne le **module Python** contenant l’application.

Il correspond au fichier :

```text id="kfyfpi"
maintai/api/main.py
```

`app` désigne l’objet FastAPI créé dans ce module :

```python id="6qfvtb"
app = FastAPI(
    title="MaintAI API",
    version=__version__,
    description="Prédiction de panne à partir de relevés de capteurs.",
    lifespan=lifespan,
)
```

Uvicorn importe donc `maintai.api.main`, récupère l’objet `app` et démarre le serveur web.

---

## 7. Le rendu Git

- **Lien de la pull request :** À compléter
- **Le tag `tp1` existe sur GitHub :** À vérifier — oui / non
- **Qui a relu la pull request, et quel commentaire a-t-il laissé ?**  
  À compléter après la relecture de la pull request.

---

## 8. Ce qui reste flou

Au cours de ce TP, les points qui m’ont demandé le plus d’attention ont été la différence entre les différents codes HTTP, notamment `404`, `422`, `500` et `503`, ainsi que le rôle respectif de FastAPI, Pydantic et Uvicorn.

J’ai également dû mieux comprendre le cycle de vie de l’application et la raison pour laquelle le modèle de Machine Learning est chargé une seule fois au démarrage.

Le choix retenu consiste à charger le modèle au démarrage de l’API et à le conserver en mémoire. Cette décision améliore les performances en évitant de relire le fichier `model.joblib` à chaque requête. En contrepartie, une nouvelle version du modèle nécessite un redémarrage ou un mécanisme de rechargement pour être prise en compte.

Ce TP m’a permis de mieux comprendre le chemin complet d’une prédiction : le client envoie les valeurs des capteurs, Pydantic valide les données, FastAPI transmet les données valides à l’endpoint, le modèle déjà chargé en mémoire effectue la prédiction et l’API retourne le résultat sous forme de JSON.

Je comprends également mieux l’intérêt des tests automatisés pour vérifier progressivement le fonctionnement de l’API et détecter les erreurs pendant le développement.