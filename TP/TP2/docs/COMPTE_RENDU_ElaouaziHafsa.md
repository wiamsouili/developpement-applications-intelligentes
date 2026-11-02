# Compte rendu · TP2 : tester, sécuriser et appeler l'API MaintAI

**Groupe :**G3   ·  **Membres :** EL AOUAZI HAFSA  ·  **Date :** 02/11/2026



---

## 1. Activité 1 : casser son API (dans `TP/TP1`)

Vos cinq requêtes, le code que vous aviez **prévu**, puis le code **obtenu** dans `/docs` :

| Requête | Ce qui ne va pas | Code prévu | Code obtenu |
|---|---|---|---|
| 1 | champ manquant : `load_pct` absent du corps | 422 | 422 (`missing`, « Field required ») |
| 2 | valeur absurde : `"load_pct": 250` | 422 | 422 (`less_than_equal`, « ≤ 100 ») |
| 3 | texte au lieu d'un nombre : `"temperature_c": "chaud"` | 422 | 422 (`float_parsing`) |
| 4 | champ en trop : `"couleur": "rouge"` | 422 | 422 (`extra_forbidden`) |
| 5 | mauvaise route : `POST /v1/predict_inconnu` | 404 | 404 (« Not Found ») |

Une de vos prévisions était-elle fausse ? Laquelle, et pourquoi ?

Non, les cinq prévisions étaient justes. Une nuance : si on appelle la bonne route avec la mauvaise méthode (`GET /v1/predict` au lieu de `POST`), le code n'est pas 404 mais **405** (« Method Not Allowed »), car la route existe mais n'accepte pas cette méthode. Les quatre cas 422 sont refusés par Pydantic (`schemas.py`, avec `extra="forbid"` et les bornes `ge`/`le`) avant même que le code de `predict` ne s'exécute.

Dernière ligne de `python -m pytest` avec `tests/test_casser.py` (dans `TP/TP1`) :

```
================== 18 passed in …s ==================
```

(13 tests du TP1 + 5 cas de `test_casser.py` = 18.)

À quoi sert `@pytest.mark.parametrize` ? Combien de tests pytest compte-t-il pour votre fonction, et pourquoi ?

`parametrize` lance la même fonction de test une fois par ligne de la liste `CAS_REFUSES`, en lui passant les valeurs de la ligne (description, url, corps, code attendu). On écrit donc la logique une seule fois au lieu de cinq fonctions quasi identiques. pytest compte **5 tests** pour cette seule fonction (un par ligne de la liste), et nomme chaque cas dans le rapport (par exemple `test_requete_refusee[champ manquant-/v1/predict-corps0-422]`), ce qui permet de voir exactement quel cas échoue.

## 2. ruff

Sortie de `ruff check .` dans `TP/TP1` :

```
$ ruff check .
All checks passed!
```

Remarque : dans `TP/TP2`, avant d'avoir écrit `security.py` et ajouté la dépendance au router, `ruff check .` signalait 8 erreurs : des `F401` (« imported but unused ») sur `Depends`, `require_api_key`, `secrets`, `HTTPException`, `status` et `get_settings`, plus un `I001` (imports mal rangés) dans `main.py` et un `UP017` dans `train.py`. Ces imports sont ceux que le starter prépare pour le sprint 1 : lancer `--fix` avant d'avoir écrit le code les aurait supprimés. `ruff check . --fix` n'a été lancé qu'**après** la fin du sprint 1.

Quelle différence entre `ruff check .` et `python -m pytest` ? Que vérifie chacun ?

`ruff check .` lit le code **sans l'exécuter** : il repère ce qui est mal écrit (import inutile, imports mal rangés, variable jamais utilisée). `python -m pytest` **exécute** le code et vérifie ce qu'il fait (une requête sans clé donne-t-elle 401 ? 500 °C donne-t-il 422 ?). Les deux sont complémentaires : du code peut passer tous les tests tout en étant mal écrit, et du code propre peut se tromper. Règle : `ruff check .` avant chaque commit, `python -m pytest` avant chaque push.

## 3. Mise en place du TP2 (dans `TP/TP2`)

Dernière ligne de `python -m pytest` juste après la mise en place :

```
=================== 2 failed, 16 passed, 1 warning in 1.47s ====================
```

Quels sont les deux tests qui échouent, et que reçoivent-ils au lieu de 401 ?

Ce sont `test_missing_key_is_rejected` (requête sans clé) et `test_wrong_key_is_rejected` (requête avec la clé `wrong`), dans `tests/test_security.py`. Ils reçoivent **200** au lieu de 401 : `require_api_key` n'est pas encore écrite, et surtout rien ne l'appelle, donc l'API répond à tout le monde et renvoie une prédiction.

## 4. La clé API (sprint 1)

Votre fonction `require_api_key()` (`maintai/api/security.py`) :

```python
def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Refuse la requête si la clé est absente ou fausse."""
    expected = get_settings().api_key
    if expected is None:
        # Le serveur n'a pas de clé : c'est une erreur de configuration, pas celle du client
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Clé API non configurée sur le serveur",
        )
    # compare_digest : durée constante, pour ne pas révéler combien de caractères sont justes
    if x_api_key is None or not secrets.compare_digest(
        x_api_key.encode("utf-8"), expected.encode("utf-8")
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API absente ou invalide",
        )
```

Votre ligne `router = ...` dans `maintai/api/main.py` :

```python
router = APIRouter(prefix="/v1", dependencies=[Depends(require_api_key)])
```

Après avoir écrit `security.py` seul (sans toucher au router), combien de tests échouent ? Pourquoi ?

**2 tests échouent encore** (les mêmes). La fonction existe, mais FastAPI ne l'appelle que si elle est déclarée comme dépendance : tant que le router n'a pas `dependencies=[Depends(require_api_key)]`, les routes `/v1` ne la lancent jamais et répondent 200.

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
======================== 18 passed, 1 warning in 1.15s =========================
```

Lancez `uvicorn maintai.api.main:app --reload --env-file .env`, puis envoyez ces requêtes (avec `/docs` ou `curl.exe`) :

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| `GET /health`, sans clé | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict`, relevé normal, sans clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, relevé normal, fausse clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, relevé normal, bonne clé | 200 | `{"failure_probability":0.0027,"alert":false,"threshold":0.3,"model_version":"…"}` |
| `POST /v1/predict`, 500 °C, sans clé | 401 | `{"detail":"Clé API absente ou invalide"}` |
| `POST /v1/predict`, 500 °C, bonne clé | 422 | `{"detail":[{"type":"less_than_equal","loc":["body","temperature_c"],"msg":"Input should be less than or equal to 150",…}]}` |

(Relevé normal : `temperature_c` 60, `vibration_mm_s` 2, `load_pct` 50, `runtime_hours` 5000.)

500 °C sans clé et 500 °C avec la clé ne donnent pas le même code. Pourquoi ?

Parce que les contrôles s'enchaînent dans un ordre fixe et que le premier qui échoue donne la réponse : 1. la route existe-t-elle (404), 2. la clé est-elle bonne (401), 3. les données sont-elles valides (422), 4. le modèle est-il chargé (503). Sans clé, la requête est arrêtée à l'étape 2 : l'API ne regarde même pas les données, donc elle ne voit jamais le 500 °C et répond 401. Avec la bonne clé, elle passe l'étape 2, arrive à l'étape 3 et répond 422.

Relancez uvicorn **sans** `--env-file .env` et envoyez un relevé avec votre clé. Quel code obtenez-vous, et pourquoi ce n'est pas 401 ?

On obtient **500** avec `{"detail":"Clé API non configurée sur le serveur"}`. Sans `--env-file`, la variable `MAINTAI_API_KEY` n'est pas chargée, donc `get_settings().api_key` vaut `None`. Ce n'est pas la faute du client, qui a envoyé une clé : c'est le serveur qui est mal configuré. Un 401 serait trompeur (il ferait croire que la clé est mauvaise) et masquerait le vrai problème ; un 500 dit qu'il faut corriger le serveur. C'est aussi plus sûr : sans clé configurée, l'API refuse tout au lieu de s'ouvrir à tout le monde.

## 5. La page web (sprint 2)

Votre code `fetch` (le contenu du `addEventListener` dans `web/index.html`) :

```javascript
const reading = Object.fromEntries(FEATURES.map(f => [f, Number(document.getElementById(f).value)]));
const adresse = document.getElementById("url").value.replace(/\/$/, "") + "/v1/predict";
const cle = document.getElementById("key").value;
try {
  const resp = await fetch(adresse, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-API-Key": cle },
    body: JSON.stringify(reading),
  });
  const data = await resp.json();
  if (!resp.ok) {
    const detail = typeof data.detail === "string" ? data.detail : "relevé refusé (voir la console)";
    if (typeof data.detail !== "string") console.log(data.detail);
    show("err", `Erreur ${resp.status} : ${detail}`);
  } else {
    const pct = (data.failure_probability * 100).toFixed(1);
    show(data.alert ? "alert" : "ok",
      `${data.alert ? "ALERTE" : "OK"} : probabilité de panne ${pct} % (seuil ${data.threshold})`);
  }
} catch (e) {
  show("err", "API injoignable (serveur arrêté, ou requête bloquée par CORS)");
}
```

Ce qu'affiche la page (servie sur le port 5500) :

| Essai | Ce qu'affiche la page |
|---|---|
| relevé normal, bonne clé | Encadré vert : « OK : probabilité de panne 0.3 % (seuil 0.3) » |
| 500 °C, bonne clé | Encadré orange : « Erreur 422 : relevé refusé (voir la console) » (le détail Pydantic est dans la console) |
| relevé normal, fausse clé | Encadré orange : « Erreur 401 : Clé API absente ou invalide » |

(Avec le relevé par défaut de la page, 72 °C / 6 mm/s / 85 % / 15 000 h, on obtient l'encadré rouge « ALERTE : probabilité de panne 94.8 % ».)

**Expérience CORS.** Servez la page sur le port 5501. Que dit la page, et que dit la console (F12) ?

La page affiche l'encadré orange « API injoignable (serveur arrêté, ou requête bloquée par CORS) » : `fetch` a levé une exception, donc on passe dans le `catch`, sans réponse lisible. La console (F12) affiche une erreur de ce type : *Access to fetch at 'http://localhost:8000/v1/predict' from origin 'http://localhost:5501' has been blocked by CORS policy: Response to preflight request doesn't pass access control check…*. La requête `OPTIONS` envoyée d'abord par le navigateur (« puis-je ? ») reçoit **400** sans en-tête `Access-Control-Allow-Origin`, car `http://localhost:5501` n'est pas dans `MAINTAI_CORS_ORIGINS` (seuls 5500 et 127.0.0.1:5500 le sont). Le navigateur n'envoie donc jamais le `POST`. (Le libellé exact varie un peu selon le navigateur.)

Pourquoi `curl.exe` obtient-il une réponse alors que la page du port 5501 est bloquée ?

CORS est une règle **du navigateur** : il protège l'utilisateur contre une page qui utiliserait son navigateur pour appeler une autre origine. `curl.exe` n'est pas un navigateur : il n'envoie pas de requête `OPTIONS` préalable et n'applique aucune règle CORS, il envoie directement le `POST`. La seule chose qui compte alors est la clé API. CORS n'est donc pas une protection de l'API : c'est la clé qui la protège.

## 6. Les tests de l'activité 1 dans le TP2

Copiez `test_casser.py` dans `TP/TP2/tests`. Sans `headers=HEADERS`, combien de tests échouent, et avec quel code ? Lequel des cinq cas passe quand même, et pourquoi ?

**4 tests échouent** (champ manquant, valeur absurde, texte au lieu d'un nombre, champ en trop) : ils reçoivent **401** au lieu de 422, car la clé est vérifiée avant les données. Le cinquième, **« mauvaise route »**, passe quand même (404) : `/v1/predict_inconnu` n'existe pas, donc aucune dépendance de route n'est exécutée et l'étape 1 (la route existe-t-elle ?) répond 404 avant que la clé ne soit regardée.

Dernière ligne de `python -m pytest` avec `headers=HEADERS` :

```
======================== 23 passed, 1 warning in 1.24s =========================
```

## 7. Questions de compréhension

1. Quelle différence entre 401 et 422 ? Et entre 401 et 403 ?
   **401** : l'API ne sait pas qui appelle (clé absente ou fausse), c'est un problème d'**authentification**. **422** : la requête est bien comprise, mais les données ne respectent pas le schéma (500 °C, champ manquant…), c'est un problème de **validation**. **403** : l'appelant est identifié mais n'a pas le droit de faire cette action (**autorisation**, hors TP2). 401 = « qui es-tu ? », 403 = « tu n'as pas le droit ».
2. Pourquoi la clé n'est-elle ni dans le code ni dans Git ? Que contiennent `.env` et `.env.example`, et lequel est commité ?
   Le code est commité et poussé sur GitHub : une clé qui y passe une seule fois reste dans l'historique de Git pour toujours, même si on supprime le fichier ensuite, et il faut alors la changer. `.env` contient la **vraie** clé (propre à chaque machine), il est ignoré par `.gitignore` et **n'est pas commité**. `.env.example` contient une fausse valeur (`changez-moi`) et dit quelles variables configurer : c'est lui qui est **commité**.
3. Pourquoi la clé voyage-t-elle dans un en-tête et pas dans l'URL ?
   Une URL est enregistrée partout : journaux du serveur, historique du navigateur, proxys, liens copiés. Une clé dans l'URL fuiterait donc dans tous ces endroits. Un en-tête (`X-API-Key`) n'est pas enregistré par défaut et ne s'affiche pas dans la barre d'adresse.
4. Que fait `secrets.compare_digest` de plus qu'un simple `==` ?
   `==` s'arrête au premier caractère différent : plus la clé proposée est juste au début, plus la réponse est longue, et un attaquant pourrait deviner la clé caractère par caractère en mesurant la durée (attaque par chronométrage). `compare_digest` compare en temps constant, sans révéler combien de caractères étaient justes.
5. Qu'est-ce qu'une « origine » ? `http://localhost:5500` et `http://localhost:8000` sont-elles la même origine ?
   Une origine est l'ensemble **schéma + domaine + port**. Ici le schéma (`http`) et le domaine (`localhost`) sont identiques, mais le port diffère (5500 et 8000) : ce sont donc **deux origines différentes**. C'est pourquoi le navigateur applique CORS quand la page du port 5500 appelle l'API du port 8000.

