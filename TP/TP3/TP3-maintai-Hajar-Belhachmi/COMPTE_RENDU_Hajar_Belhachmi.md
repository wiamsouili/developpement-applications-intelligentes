# Compte rendu — TP3 : Une interface Streamlit pour MaintAI

**Module :** Développement d'applications intelligentes  
**Projet :** MaintAI — Prédiction de panne  
**Étudiante :** Hajar Belhachmi  
**Groupe :** 2  
**Date :** 09/11/2026

---

## 1. Prise en main et état initial

### 1.1 Exécution des tests

Pour commencer, nous avons activé l'environnement virtuel et exécuté les tests automatisés avec la commande suivante :

```powershell
python -m pytest
```

Lors de la première exécution, nous avons obtenu **4 tests échoués et 19 tests réussis**.

Les erreurs concernaient principalement la méthode `predict()` de la classe `MaintaiClient`, qui était absente ou incorrectement implémentée.

### 1.2 Analyse et correction des erreurs

Après analyse du code, nous avons identifié plusieurs problèmes :

- La méthode `predict()` devait être correctement implémentée dans le client.
- Le chemin de l'endpoint devait être `/v1/predict`.
- L'authentification devait utiliser l'en-tête `X-API-Key`.
- L'interface Streamlit utilisait des noms de champs différents de ceux retournés par l'API.

Nous avons corrigé ces problèmes dans les fichiers `maintai/client.py` et `ui/app.py`.

### 1.3 Résultat final des tests

Après les corrections, nous avons relancé les tests avec la commande :

```powershell
python -m pytest
```

Le résultat final obtenu est :

```text
23 passed, 1 warning in 2.73s
```

Bilan :

- **23 tests réussis.**
- **0 test échoué.**
- **1 avertissement.**
- **Durée d'exécution : 2,73 secondes.**

L'avertissement `StarletteDeprecationWarning` concerne l'utilisation de `httpx` avec `starlette.testclient`. Il s'agit d'un avertissement de dépréciation et non d'une erreur bloquant les tests.

Tous les tests ont donc été validés.

---

## 2. Lancement de l'application Streamlit

Pour lancer l'application, nous utilisons la commande suivante depuis la racine du projet :

```powershell
python -m streamlit run ui/app.py
```

L'application est ensuite accessible depuis le navigateur à l'adresse :

```text
http://localhost:8501
```

L'interface comporte deux onglets :

- **Données :** exploration et visualisation des données des équipements.
- **Prédiction :** saisie des caractéristiques d'un équipement et affichage du résultat de la prédiction.

---

## 3. Construction de l'interface de données

### 3.1 Indicateurs principaux

Dans l'onglet **Données**, nous avons ajouté trois indicateurs permettant de résumer le jeu de données.

Les résultats obtenus sont les suivants :

| Indicateur | Valeur obtenue |
|---|---:|
| Nombre de relevés | 5 000 |
| Taux de panne | 13,6 % |
| Température moyenne | 59,8 °C |

Le jeu de données contient donc 5 000 relevés. Parmi eux, 13,6 % sont associés à une panne.

La température moyenne enregistrée est de 59,8 °C.

### 3.2 Graphique du taux de panne selon la température

Nous avons créé un graphique en barres qui représente le taux de panne selon les intervalles de température.

La température est divisée en dix tranches afin de faciliter l'analyse des données.

Ce graphique permet de comparer les taux de panne entre les différentes plages de température et d'observer comment le risque de panne varie selon la température.

### 3.3 Nuage de points : température et vibration

Nous avons également ajouté un nuage de points représentant :

- La température sur l'axe horizontal.
- Le niveau de vibration sur l'axe vertical.
- La présence ou l'absence d'une panne grâce à deux couleurs distinctes.

Cette visualisation permet de comparer les relevés avec panne et sans panne et d'explorer les relations possibles entre la température, les vibrations et les pannes.

### 3.4 Chargement et mise en cache des données

La fonction `charger()` permet de lire le fichier CSV contenant les relevés.

Le décorateur `@st.cache_data` permet de mettre en cache les données chargées afin d'éviter de relire inutilement le fichier à chaque réexécution du script.

Streamlit réexécute le script lorsqu'un utilisateur modifie un widget, par exemple une liste déroulante ou un curseur. Cela permet d'actualiser automatiquement les graphiques et les indicateurs.

---

## 4. Construction de l'interface de prédiction

### 4.1 Formulaire de saisie

Dans l'onglet **Prédiction**, nous avons créé un formulaire permettant de saisir les caractéristiques d'un équipement :

- Température en degrés Celsius.
- Vibration en mm/s.
- Pourcentage de charge.
- Nombre d'heures de fonctionnement.

Les composants Streamlit utilisés sont :

- `st.slider()` pour saisir les valeurs numériques à l'aide de curseurs.
- `st.number_input()` pour saisir les heures de fonctionnement.
- `st.form()` pour regrouper les champs du formulaire.
- `st.form_submit_button()` pour envoyer les informations.

### 4.2 Communication avec l'API

Pour communiquer avec l'API MaintAI, nous utilisons la méthode `predict()` de la classe `MaintaiClient`.

Voici son implémentation :

```python
def predict(self, releve: dict) -> dict:
    """Envoie un relevé à l'API MaintAI et retourne la prédiction."""

    headers = {}

    if self.api_key:
        headers["X-API-Key"] = self.api_key

    r = self.http.post(
        "/v1/predict",
        json=releve,
        headers=headers
    )

    if r.status_code != 200:
        raise APIError(r.status_code, r.json().get("detail"))

    return r.json()
```

La méthode envoie les données à l'endpoint `/v1/predict` avec une requête HTTP POST.

L'authentification est effectuée à l'aide de l'en-tête `X-API-Key`.

### 4.3 Affichage du résultat

Après réception de la réponse de l'API, l'interface affiche :

- La probabilité de panne sous forme de pourcentage.
- Un message d'alerte si un risque de panne est détecté.
- Un message de succès lorsque le fonctionnement est considéré comme normal.

Nous avons également prévu la gestion des erreurs :

- `APIError` : permet de traiter les erreurs retournées par l'API, notamment une clé API invalide.
- `httpx.HTTPError` : permet de gérer les problèmes de communication, par exemple lorsque le serveur API est inaccessible.

### 4.4 Vérification des scénarios

| Scénario | Résultat attendu |
|---|---|
| Clé API valide et données correctes | Affichage de la prédiction |
| Clé API invalide | Affichage d'une erreur 401 |
| API arrêtée | Affichage d'un message indiquant que l'API est inaccessible |
| Risque de panne détecté | Affichage d'une alerte |
| Fonctionnement normal | Affichage d'un message de succès |

---

## 5. Questions de réflexion

### 5.1 Quelle est la différence entre l'interface TP2 et l'interface Streamlit ?

Dans le TP2, l'interface HTML/JavaScript communique avec l'API depuis le navigateur de l'utilisateur.

Avec Streamlit, le code Python s'exécute côté serveur. C'est donc Python qui effectue les appels HTTP vers l'API MaintAI.

Streamlit permet ainsi de créer rapidement une interface interactive en Python, sans avoir besoin de développer séparément le HTML, le CSS et le JavaScript.

### 5.2 Pourquoi les tests fonctionnent-ils sans lancer Uvicorn ?

Les tests peuvent utiliser `TestClient` de FastAPI ou Starlette.

Cet outil permet de simuler des requêtes HTTP directement vers l'application FastAPI, sans démarrer un véritable serveur Uvicorn.

Cela rend les tests plus rapides et facilite la vérification des endpoints.

### 5.3 Quelle technologie choisir pour une application professionnelle ?

Le choix dépend des besoins du projet.

**Streamlit :**

- Développement rapide.
- Utilisation simple de Python.
- Adapté aux prototypes, démonstrations et outils internes de visualisation.

**HTML/CSS/JavaScript :**

- Personnalisation complète de l'interface.
- Plus grande liberté dans la conception.
- Adapté aux applications web destinées à un grand nombre d'utilisateurs.

Pour une démonstration de MaintAI, Streamlit est un choix adapté. Pour une application professionnelle destinée à être utilisée quotidiennement par des techniciens, une interface web personnalisée pourrait être plus appropriée.

---

## 6. Livraison Git

Les modifications doivent être enregistrées dans le dépôt Git du projet.

Commandes utilisées :

```powershell
git status
git add .
git commit -m "TP3 : ajout de l'interface Streamlit"
git push
```


**Tag de livraison :** `tp3` oui.


---

## 7. Bilan du TP

Ce TP nous a permis de découvrir Streamlit et de l'utiliser pour construire une interface interactive autour de l'application MaintAI.

Nous avons appris à :

- Charger et explorer des données avec Pandas.
- Afficher des indicateurs et des graphiques avec Streamlit.
- Créer des formulaires interactifs.
- Communiquer avec une API FastAPI à l'aide de HTTPX.
- Gérer les erreurs de communication et d'authentification.
- Tester le fonctionnement du client et de l'interface.
- Organiser et livrer les modifications avec Git.

Les résultats obtenus dans l'onglet Données montrent que le jeu de données contient 5 000 relevés, avec un taux de panne de 13,6 % et une température moyenne de 59,8 °C.

Les tests automatisés ont également été validés avec 23 tests réussis et aucun échec.

Ce travail nous a permis de comprendre comment intégrer une interface utilisateur à une application intelligente existante et de relier la visualisation des données à un service de prédiction basé sur le Machine Learning.
