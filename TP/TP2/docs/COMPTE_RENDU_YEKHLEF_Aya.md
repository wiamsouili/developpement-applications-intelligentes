# Compte rendu · TP2 : tester, sécuriser et appeler l'API MaintAI

**Groupe :** G3  ·  **Membres :**   YEKHLEF Aya  ·  **Date :** 02/11/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP2.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Activité 1 : casser son API (dans `TP/TP1`)

Vos cinq requêtes, le code que vous aviez **prévu**, puis le code **obtenu** dans `/docs` :

| Cas | Requête envoyée | Ce qui ne va pas | Code prévu | Code obtenu |
|---|---|---|---|---|
| Champ manquant | `POST /v1/predict` avec `{"temperature_c":60,"vibration_mm_s":2,"runtime_hours":5000}` (sans `load_pct`) | Le champ `load_pct` manque | 422 | 422 (confirmé par `test_missing_field_is_rejected` dans `tests/test_api.py`) |
| Valeur absurde | `POST /v1/predict` avec `{"temperature_c":500,"vibration_mm_s":2,"load_pct":50,"runtime_hours":5000}` | `temperature_c=500` dépasse la limite autorisée (150 °C) | 422 | 422 (attendu par `test_demo.py`) |
| Texte au lieu d'un nombre | `POST /v1/predict` avec `{"temperature_c":"chaud","vibration_mm_s":2,"load_pct":50,"runtime_hours":5000}` | `temperature_c` contient du texte qui ne peut pas être converti en nombre | 422 | 422 (selon la validation Pydantic du schéma) |
| Champ en trop | `POST /v1/predict` avec `{"temperature_c":60,"vibration_mm_s":2,"load_pct":50,"runtime_hours":5000,"extra":"test"}` | Le champ `extra` n'est pas autorisé (`extra="forbid"`) | 422 | 422 (selon la configuration du schéma) |
| Mauvaise route | `POST /v1/route-inexistante` | Cette route n'existe pas | 404 | 404 (selon les routes déclarées dans `maintai/api/main.py`) |

Une de vos prévisions était-elle fausse ? Laquelle, et pourquoi ?

Aucune prévision n'était fausse. 

Dernière ligne de `python -m pytest` avec `tests/test_casser.py` (dans `TP/TP1`) :

```
5 passed, 1 warning in 10.28s
```

À quoi sert `@pytest.mark.parametrize` ? Combien de tests pytest compte-t-il pour votre fonction, et pourquoi ?

`@pytest.mark.parametrize` permet d'exécuter un même test plusieurs fois avec des valeurs différentes. Ici, le test est paramétré par 5 cas (champ manquant, valeur absurde, texte au lieu d'un nombre, champ en trop, mauvaise route). Pytest compte donc un test unique au niveau du code, mais 5 exécutions concrètes du test : une pour chaque paramètre. C'est pourquoi le test est comptabilisé comme un seul test function, mais il produit 5 cas de test.

## 2. ruff

Sortie de `ruff check .` dans `TP/TP1` :

```
I001 [*] Import block is un-sorted or un-formatted
 --> demo_api.py:1:1
  |
1 | / from fastapi import FastAPI
2 | | from pydantic import BaseModel, Field
  | |___________________________________^
3 |   app = FastAPI()
4 |   class Reading(BaseModel):
  |
help: Organize imports
  |
2 | from pydantic import BaseModel, Field
3 +
4 | app = FastAPI()
  |

UP017 [*] Use `datetime.UTC` alias
  --> maintai\train.py:58:36
   |
56 |         "target": TARGET,
57 |         "threshold": settings.threshold,
58 |         "trained_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
   |                                    ^^^^^^^^^^^
59 |         "sklearn_version": sklearn.__version__,
60 |     }
   |
help: Convert to `datetime.UTC` alias
  |
5  | import json
   - from datetime import datetime, timezone
6  + from datetime import datetime, timezone, UTC
7  |
--------------------------------------------------------------------------------
57 |         "target": TARGET,
   -         "trained_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
58 +         "trained_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
59 |         "sklearn_version": sklearn.__version__,
   |

I001 [*] Import block is un-sorted or un-formatted
 --> tests\test_casse.py:1:1
  |
1 | import pytest
  | ^^^^^^^^^^^^^
help: Organize imports
  |
2 |
  -
3 | VALID = {"temperature_c": 60.0, "vibration_mm_s": 2.0, "load_pct": 50.0, "runtime_hours": 5000}
  |

Found 3 errors.
[*] 3 fixable with `--fix`.
```

Quelle différence entre `ruff check .` et `python -m pytest` ? Que vérifie chacun ?

`python -m pytest` exécute les tests fonctionnels du projet pour vérifier le comportement attendu. Ici, il vérifie si les API/logic models répondent correctement aux cas attendus. `ruff check .` est un linter statique : il vérifie la qualité du code, le style, les imports, et certaines règles de bonne pratique, sans exécuter le code. En résumé, `pytest` valide le comportement ; `ruff` valide la qualité/forme du code.

## 3. Mise en place du TP2 (dans `TP/TP2`)

Dernière ligne de `python -m pytest` juste après la mise en place :

```
2 failed in 0.32s
```

Quels sont les deux tests qui échouent, et que reçoivent-ils au lieu de 401 ?

Les tests qui échouent sont `test_missing_key_is_rejected` et `test_wrong_key_is_rejected`. Avant la mise en place de la vraie vérification de clé, l'API n'applique pas d'authentification sur `/v1/predict` ; elle répond donc normalement au lieu de 401, c'est-à-dire `200 OK` pour une requête valide et `200 OK` aussi avec une mauvaise clé.

## 4. La clé API (sprint 1)

Votre fonction `require_api_key()` (`maintai/api/security.py`) :

```python
"""Authentification par clé API, transmise dans l'en-tête X-API-Key."""
import secrets

from fastapi import Header, HTTPException, status

from maintai.config import get_settings


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Refuse la requête si la clé est absente ou fausse."""
    configured_key = get_settings().api_key
    if configured_key is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API key not configured on server",
        )
    if x_api_key is None or not secrets.compare_digest(x_api_key, configured_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
```

Votre ligne `router = ...` dans `maintai/api/main.py` :

```python
router = APIRouter(prefix="/v1", dependencies=[Depends(require_api_key)])
```

Après avoir écrit `security.py` seul (sans toucher au router), combien de tests échouent ? Pourquoi ?

Deux tests échouent encore. Pourquoi ? Parce que la logique de sécurité existe, mais elle n'est pas installée dans les routes. La fonction `require_api_key()` n'est pas appelée tant que `router = APIRouter(prefix="/v1", dependencies=[Depends(require_api_key)])` n'est pas branchée sur l'API ; au lieu de 401, la requête passe et les tests continuent à recevoir un statut normal (donc 200 au lieu de 401).

Dernière ligne de `python -m pytest` à la fin du sprint 1 :

```
18 passed, 1 warning in 15.01s
```

Lancez `uvicorn maintai.api.main:app --reload --env-file .env`, puis envoyez ces requêtes (avec `/docs` ou `curl.exe`) :

| Requête | Code obtenu | Réponse (le corps JSON) |
|---|---|---|
| `GET /health`, sans clé | 200 | `{"status":"ok","model_loaded":true}` |
| `POST /v1/predict`, relevé normal, sans clé | 401 | `{"detail":"Invalid or missing API key"}` |
| `POST /v1/predict`, relevé normal, fausse clé | 401 | `{"detail":"Invalid or missing API key"}` |
| `POST /v1/predict`, relevé normal, bonne clé | 200 | `{"failure_probability":0.0027,"alert":false,"threshold":0.3,"model_version":"2026-11-02T12:11:15Z"}` |
| `POST /v1/predict`, 500 °C, sans clé | 401 | `{"detail":"Invalid or missing API key"}` |
| `POST /v1/predict`, 500 °C, bonne clé | 422 | `{"detail":[{"type":"less_than_equal","loc":["body","temperature_c"],"msg":"Input should be less than or equal to 150","input":500,"ctx":{"le":150.0}}]}` |

500 °C sans clé et 500 °C avec la clé ne donnent pas le même code. Pourquoi ?

Parce que l'authentification est vérifiée avant la validation métier. Sans clé, la requête est rejetée dès le début par `require_api_key()` avec un `401 Unauthorized`. Avec une clé valide, la requête passe l'authentification, puis le schéma `SensorReading` valide les données, constate que `temperature_c=500` dépasse la limite (`le=150`) et renvoie un `422 Unprocessable Entity`.

Relancez uvicorn **sans** `--env-file .env` et envoyez un relevé avec votre clé. Quel code obtenez-vous, et pourquoi ce n'est pas 401 ?

Le code obtenu est `500 Internal Server Error` avec le message :

```json
{"detail":"API key not configured on server"}
```

Ce n'est pas un 401, car le problème n'est pas la clé fournie à la requête : c'est le serveur lui-même qui ne sait pas quelle clé configurer. `require_api_key()` vérifie d'abord `get_settings().api_key is None` et renvoie alors un 500, car la configuration du service est absente, pas la requête non authentifiée.

## 5. La page web (sprint 2)

Votre code `fetch` (le contenu du `addEventListener` dans `web/index.html`) :

```javascript
document.getElementById("go").addEventListener("click", async () => {
  const baseUrl = document.getElementById("url").value.trim().replace(/\/$/, "");
  const apiKey = document.getElementById("key").value;
  const reading = Object.fromEntries(FEATURES.map(f => [f, Number(document.getElementById(f).value)]));

  try {
    const response = await fetch(`${baseUrl}/v1/predict`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": apiKey,
      },
      body: JSON.stringify(reading),
    });

    const payload = await response.json().catch(() => null);

    if (!response.ok) {
      const message = payload && payload.detail ? String(payload.detail) : "Erreur inconnue";
      show("err", `Erreur (${response.status}) : ${message}`);
      return;
    }

    const text = `Probabilité de panne : ${(payload.failure_probability * 100).toFixed(1)}%${payload.alert ? " — ALERTE" : " — OK"}`;
    show(payload.alert ? "alert" : "ok", text);
  } catch (error) {
    show("err", `Impossible de contacter l'API : ${error.message}`);
  }
});
```

Ce qu'affiche la page (servie sur le port 5500) :

| Essai | Ce qu'affiche la page |
|---|---|
| relevé normal, bonne clé | `Probabilité de panne : 0.3% — OK` |
| 500 °C, bonne clé | `Erreur (422) : Input should be less than or equal to 150` |
| relevé normal, fausse clé | `Erreur (401) : Invalid or missing API key` |

**Expérience CORS.** Servez la page sur le port 5501. Que dit la page, et que dit la console (F12) ?

La page affiche : `Impossible de contacter l'API : Failed to fetch`.

La console affiche une erreur du type :

```text
Access to fetch at 'http://localhost:8000/v1/predict' from origin 'http://localhost:5501' has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

Pourquoi `curl.exe` obtient-il une réponse alors que la page du port 5501 est bloquée ?

`curl.exe` n'est pas un navigateur. Il n'applique pas la politique CORS de Same-Origin Policy ; il envoie simplement la requête HTTP et affiche la réponse brute. Le navigateur, lui, applique les règles CORS et bloque la requête quand l'origine `http://localhost:5501` n'est pas autorisée par le serveur.

## 6. Les tests de l'activité 1 dans le TP2

Copiez `test_casser.py` dans `TP/TP2/tests`. Sans `headers=HEADERS`, combien de tests échouent, et avec quel code ? Lequel des cinq cas passe quand même, et pourquoi ?

Sans `headers=HEADERS`, 4 tests échouent : les 4 cas de validation d'entrée (`champ manquant`, `valeur absurde`, `texte au lieu d'un nombre`, `champ en trop`) reçoivent `401 Unauthorized` parce qu'ils sont rejetés avant la validation métier par l'authentification. Le seul cas qui passe quand même est `mauvaise route` : il renvoie `404 Not Found` car la route demandée n'existe pas, et FastAPI ne l'attribue pas à une route authentifiée.

Dernière ligne de `python -m pytest` avec `headers=HEADERS` :

```
18 passed, 1 warning in 15.01s
```

## 7. Questions de compréhension

1. Quelle différence entre 401 et 422 ? Et entre 401 et 403 ?
   401 veut dire « je ne peux pas identifier ou authentifier la requête » : la clé manque ou est fausse. 422 veut dire « la requête est bien reçue, mais elle ne respecte pas le schéma / les contraintes de validation ». 403 veut dire « la requête est authentifiée, mais l'utilisateur ou la clé n'a pas les droits d'accès suffisants » ; c'est un problème d'autorisation, pas d'authentification.
2. Pourquoi la clé n'est-elle ni dans le code ni dans Git ? Que contiennent `.env` et `.env.example`, et lequel est commité ?
   La clé est sensible et ne doit pas être stockée dans le dépôt public. `.env` contient les variables réelles de l'environnement, notamment la vraie `MAINTAI_API_KEY` et les origines CORS autorisées. `.env.example` contient les mêmes variables mais avec des valeurs d'exemple (par exemple `MAINTAI_API_KEY=changez-moi`). Seul `.env.example` est committé ; `.env` est ignoré via `.gitignore`.
3. Pourquoi la clé voyage-t-elle dans un en-tête et pas dans l'URL ?
   Dans l'URL, la clé apparaît dans l'historique du navigateur, dans les logs du serveur, dans les proxys, dans les référents et dans les caches. Dans un en-tête HTTP, elle reste moins visible et est mieux séparée du chemin de la ressource. C'est plus sûr et plus propre pour les credentials API.
4. Que fait `secrets.compare_digest` de plus qu'un simple `==` ?
   `secrets.compare_digest` compare les chaînes en temps constant, ce qui réduit le risque d'attaques par timing. Un simple `==` peut révéler des informations selon le temps nécessaire pour comparer les chaînes ; `compare_digest` est conçu pour ne pas exposer cette fuite de timing.
5. Qu'est-ce qu'une « origine » ? `http://localhost:5500` et `http://localhost:8000` sont-elles la même origine ?
   Une origine est la combinaison de protocole + domaine + port. Donc `http://localhost:5500` et `http://localhost:8000` ne sont pas la même origine, car le port est différent. Même si le domaine est identique, le port compte dans le calcul de l'origine.

## 8. Le rendu Git

- Lien de la pull request : aucune PR créée ou visible dans ce clone local.
- Le tag `tp2` existe sur GitHub : non (non créé dans cet environnement)
- `git status` avant le commit : le fichier `.env` apparaissait-il ? non, car `.env` est ignoré par `.gitignore`.
- Qui a relu la pull request, et quel commentaire a-t-il laissé ? Aucune pull request n'a été ouverte, donc aucun commentaire de relecture n'a été produit dans ce contexte.

## 9. Ce qui reste flou

Le point principal restant est la différence entre un 500 de configuration serveur (`API key not configured on server`) et un 401 d'authentification (`Invalid or missing API key`). En pratique, le 500 signifie que le serveur n'a pas de clé configurée ; le 401 signifie que la requête est arrivée, mais qu'elle ne présente pas une clé valide.
