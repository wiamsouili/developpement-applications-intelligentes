# Compte rendu · TP2 : tester, sécuriser et appeler l'API MaintAI

**Groupe :** 2 ·  **Membres :** Hajar Belhachmi  ·  **Date :** 02/10/2026

> Remplissez chaque partie dans ce fichier, puis rendez-le avec la pull request du TP2.
> Collez les sorties du terminal entre les lignes ``` (trois accents graves).

---

## 1. Activité 1 : casser son API (dans `TP/TP1`)

Vos cinq requêtes, le code que vous aviez **prévu**, puis le code **obtenu** dans `/docs` :

| Cas                       | Requête (corps ou URL)                         | Prévu | Obtenu |
|---------------------------|------------------------------------------------|-------|--------|
| Champ manquant            | temperature_c absent                           | 422   | 422    |
| Valeur absurde            | temperature_c = 500                            | 422   | 422    |
| Texte au lieu d'un nombre | temperature_c = "abc"                          | 422   | 422    |
| Champ en trop             | Ajout de "pressure": 10 dans le JSON           | 422   | 422    |
| Mauvaise route            | POST /v1/predic (au lieu de /v1/predict)       | 404   | 404    |

Une de vos prévisions était-elle fausse ? Laquelle, et pourquoi ?

…

Dernière ligne de `python -m pytest` avec `tests/test_casser.py` (dans `TP/TP1`) :

```
 19 passed, 1 warning in 1.12s 
```

À quoi sert `@pytest.mark.parametrize` ? Combien de tests pytest compte-t-il pour votre fonction, et pourquoi ?


…

## 2. ruff

Sortie de `ruff check .` dans `TP/TP1` :

```
I001 [*] Import block is un-sorted or un-formatted
--> demo_api.py:1:1

UP017 [*] Use `datetime.UTC` alias
--> maintai\train.py:58:36

Found 2 errors.
[*] 2 fixable with `--fix`.
```

Quelle différence entre `ruff check .` et `python -m pytest` ? Que vérifie chacun ?


ruff check . et python -m pytest sont deux outils complémentaires.

Ruff (ruff check .) analyse le code source sans l'exécuter. Il détecte les problèmes de qualité du code, comme les imports mal organisés (I001), les imports inutiles ou les mauvaises pratiques (UP017).

Pytest (python -m pytest) exécute les tests automatisés pour vérifier que le programme fonctionne correctement et que les résultats obtenus correspondent aux résultats attendus.

Ainsi, Ruff vérifie la qualité et la présentation du code, tandis que Pytest vérifie son fonctionnement.

## 3. Mise en place du TP2 (dans `TP/TP2`)

### Dernière ligne de `python -m pytest` juste après la mise en place

    18 passed, 1 warning in 3.15s

### Quels sont les deux tests qui échouent, et que reçoivent-ils au lieu de 401 ?

À compléter avec les noms des deux tests et les codes HTTP obtenus lors de la première exécution.

---

## 4. La clé API (sprint 1)

### Votre fonction `require_api_key()` (`maintai/api/security.py`)

    """Authentification par clé API, transmise dans l'en-tête X-API-Key."""

    import secrets

    from fastapi import Header, HTTPException, status

    from maintai.config import get_settings


    def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
        """
        Vérifie la validité de la clé API envoyée par le client.

        La clé est transmise dans l'en-tête HTTP X-API-Key.

        Codes d'erreur :
            - 401 : clé API absente ou incorrecte.
            - 500 : clé API non configurée côté serveur.
        """

        # Étape 1 : récupérer les paramètres de configuration du serveur.
        settings = get_settings()
        expected_api_key = settings.api_key

        # Étape 2 : vérifier que le serveur possède une clé API configurée.
        if not expected_api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="La clé API n'est pas configurée sur le serveur.",
            )

        # Étape 3 : vérifier que le client a envoyé une clé API.
        if not x_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Clé API manquante.",
            )

        # Étape 4 : comparer la clé du client avec celle du serveur.
        if not secrets.compare_digest(x_api_key, expected_api_key):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Clé API invalide.",
            )

        # Étape 5 : autoriser la requête si les deux clés correspondent.
        return None


### Votre ligne `router = ...` dans `maintai/api/main.py`

    router = APIRouter(
        prefix="/v1",
        dependencies=[Depends(require_api_key)],
    )

Cette configuration applique l'authentification à toutes les routes du routeur `/v1`. La route `/health`, située en dehors de ce routeur, reste accessible sans clé API.

### Après avoir écrit `security.py` seul (sans toucher au router), combien de tests échouent ? Pourquoi ?

La fonction `require_api_key()` est créée, mais elle n'est pas encore associée aux routes de l'API. FastAPI ne l'exécute donc pas automatiquement.

Il faut ajouter `Depends(require_api_key)` dans les dépendances du routeur pour activer la vérification de la clé API.

Nombre exact de tests échoués : à compléter avec le résultat de l'exécution correspondante de `pytest`.

### Dernière ligne de `python -m pytest` à la fin du sprint 1

    18 passed, 1 warning in 3.15s

### Résultats des requêtes HTTP

| Requête | Code obtenu | Réponse / explication |
|---|---:|---|
| `GET /health`, sans clé | 200 | Réponse indiquant que l'API fonctionne. |
| `POST /v1/predict`, relevé normal, sans clé | 401 | `{"detail":"Clé API manquante."}` |
| `POST /v1/predict`, relevé normal, fausse clé | 401 | `{"detail":"Clé API invalide."}` |
| `POST /v1/predict`, relevé normal, bonne clé | 200 après entraînement | Réponse contenant la prédiction du modèle. |
| `POST /v1/predict`, 500 °C, sans clé | 401 | `{"detail":"Clé API manquante."}` |
| `POST /v1/predict`, 500 °C, bonne clé | 422 | Erreur de validation : la température dépasse la limite de 150 °C. |

Remarque : avant l'entraînement du modèle, une requête avec la bonne clé avait renvoyé 503, car le modèle n'était pas encore chargé. Après l'exécution de `python -m maintai.train`, le modèle a été entraîné.

### 500 °C sans clé et 500 °C avec la clé ne donnent pas le même code. Pourquoi ?

Sans clé API, la requête est rejetée par le mécanisme d'authentification. Le serveur retourne donc **401 Unauthorized**.

Avec la bonne clé API, l'authentification passe. Cependant, la température de 500 °C dépasse la limite maximale autorisée de 150 °C. FastAPI et Pydantic rejettent donc les données avec le code **422 Unprocessable Entity**.

L'authentification est vérifiée avant la validation des données de la requête.

### Relancez Uvicorn sans `--env-file .env` et envoyez un relevé avec votre clé. Quel code obtenez-vous, et pourquoi ce n'est pas 401 ?

Si aucune clé API n'est chargée dans la configuration du serveur, le résultat attendu est **500 Internal Server Error**.

Ce n'est pas 401, car le problème ne vient pas de la clé envoyée par le client, mais de l'absence de clé configurée côté serveur.

---

## 5. La page web (sprint 2)

### Votre code `fetch` (contenu du `addEventListener` dans `web/index.html`)

À compléter avec le code réel présent dans le fichier `web/index.html`.

### Ce qu'affiche la page (servie sur le port 5500)

| Essai | Ce qu'affiche la page |
|---|---|
| Relevé normal, bonne clé | Le résultat de la prédiction du modèle. |
| 500 °C, bonne clé | Une erreur de validation HTTP 422. |
| Relevé normal, fausse clé | Une erreur d'authentification HTTP 401. |

### Expérience CORS : servez la page sur le port 5501. Que dit la page, et que dit la console (F12) ?

La page servie sur le port 5501 ne peut pas accéder à l'API si cette origine n'est pas autorisée dans la configuration CORS.

La page peut afficher une erreur réseau. Dans la console du navigateur (F12), un message indique que la requête a été bloquée par la politique CORS, car l'origine `http://localhost:5501` n'est pas autorisée.

### Pourquoi `curl.exe` obtient-il une réponse alors que la page du port 5501 est bloquée ?

CORS est une politique de sécurité appliquée par les navigateurs web.

`curl.exe` n'applique pas cette politique. Il peut donc envoyer directement une requête HTTP à l'API et recevoir sa réponse, même si l'origine n'est pas autorisée par CORS.

---

## 6. Les tests de l'activité 1 dans le TP2

### Sans `headers=HEADERS`, combien de tests échouent, et avec quel code ? Lequel des cinq cas passe quand même, et pourquoi ?

Sans `headers=HEADERS`, les requêtes vers les routes protégées ne transmettent pas la clé API. Elles reçoivent donc normalement le code **401 Unauthorized**.

Le cas qui passe quand même est celui qui appelle `/health`, car cette route est publique et ne nécessite pas d'authentification.

Nombre exact de tests échoués : à compléter après l'exécution de `python -m pytest` sans `headers=HEADERS`.

### Dernière ligne de `python -m pytest` avec `headers=HEADERS`

À compléter avec le résultat réel de l'exécution après avoir ajouté les en-têtes d'authentification dans les tests.

---

## 7. Questions de compréhension

### 1. Quelle différence entre 401 et 422 ? Et entre 401 et 403 ?

- **401 Unauthorized :** le client n'est pas authentifié. Par exemple, la clé API est absente ou incorrecte.
- **422 Unprocessable Entity :** le client a envoyé des données qui ne respectent pas les règles de validation. Par exemple, une température de 500 °C alors que la limite maximale est de 150 °C.
- **403 Forbidden :** le client est authentifié, mais il ne possède pas les autorisations nécessaires pour accéder à la ressource demandée.

### 2. Pourquoi la clé n'est-elle ni dans le code ni dans Git ? Que contiennent `.env` et `.env.example`, et lequel est commité ?

La clé API est une information confidentielle. Si elle est écrite directement dans le code ou publiée sur GitHub, d'autres personnes peuvent la récupérer et l'utiliser.

- `.env` contient la vraie clé API et les paramètres de configuration locaux. Il ne doit pas être envoyé sur Git.
- `.env.example` contient un exemple de configuration avec des valeurs fictives ou à remplacer. Il sert de modèle aux autres développeurs.

C'est le fichier `.env.example` qui est commité dans Git. Le fichier `.env` est normalement ignoré grâce au fichier `.gitignore`.

### 3. Pourquoi la clé voyage-t-elle dans un en-tête et pas dans l'URL ?

La clé API est transmise dans l'en-tête HTTP `X-API-Key`.

Cela évite de l'exposer directement dans l'URL, qui peut être enregistrée dans l'historique du navigateur, les journaux des serveurs ou d'autres outils.

L'en-tête HTTP est donc une manière plus adaptée de transmettre une information d'authentification. Il faut également utiliser HTTPS pour protéger la clé pendant son transport.

### 4. Que fait `secrets.compare_digest` de plus qu'un simple `==` ?

`secrets.compare_digest()` effectue une comparaison sécurisée qui limite les risques d'attaques par analyse temporelle (*timing attacks*).

Contrairement à une comparaison classique avec `==`, elle évite autant que possible que le temps de comparaison révèle des informations sur les caractères de la clé API.

### 5. Qu'est-ce qu'une « origine » ? `http://localhost:5500` et `http://localhost:8000` sont-elles la même origine ?

Une origine est définie par trois éléments :

- Le protocole : HTTP ou HTTPS.
- Le nom d'hôte : par exemple `localhost`.
- Le port : par exemple `5500` ou `8000`.

`http://localhost:5500` et `http://localhost:8000` ne sont pas de la même origine, car leurs ports sont différents.

Le navigateur applique donc la politique CORS lorsqu'une page servie sur le port 5500 communique avec une API sur le port 8000.

---

## 8. Le rendu Git

- **Lien de la pull request :** Aucune Pull Request n'a été créée. Les modifications ont été directement envoyées sur la branche `main`.
- **Le tag `tp2` existe sur GitHub :** Oui. Le tag `tp2` a été créé et envoyé avec succès sur GitHub.
- **Commit envoyé :** `b1c0b950213943b4957e2ee48ec97040733ae4b2`.
- **État du dépôt :** La branche `main` est synchronisée avec `origin/main` et le répertoire de travail est propre.
- **Fichier `.env` :** Non suivi par Git. Son exclusion par `.gitignore` reste à vérifier.
- **Relecture de la pull request :** Non applicable, aucune Pull Request n'ayant été créée.

---

## 9. Ce qui reste flou

Tout est clair. Les différentes étapes du TP, le fonctionnement de l'authentification par clé API, la gestion des erreurs HTTP et le mécanisme CORS sont bien compris.