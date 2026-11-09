# Compte rendu · TP3 : Conception d'une interface de supervision Streamlit pour MaintAI

**Module :** Développement et déploiement d'applications intelligentes  
**Projet :** MaintAI — Maintenance prédictive par Machine Learning  
**Étudiante :** SOUILI Wiam  
**Groupe :** G3  
**Date :** 09/11/2026  

---

## 1. Initialisation, diagnostic et validation des tests

### 1.1 Objectif général du TP
Ce troisième TP a pour but de développer une interface utilisateur moderne et réactive en Python pur avec **Streamlit**, destinée au pilotage et à la visualisation des prédictions de panne générées par le modèle MaintAI. L'application offre une double fonctionnalité :
- L'analyse exploratoire et descriptive du jeu de données des équipements industriels.
- Un panneau de contrôle interactif pour tester l'API FastAPI en soumettant des relevés télémétriques et en observant les alarmes déclenchées.

### 1.2 Analyse des anomalies au démarrage
Lors du premier lancement de la suite de tests via :
```powershell
python -m pytest
```
Nous avons relevé **4 tests en échec pour 19 tests réussis**. L'inspection des traces d'erreur a mis en lumière les causes suivantes :
1. **Implémentation incomplète de `MaintaiClient` :** La fonction `predict()` dans `maintai/client.py` n'envoyait pas correctement la charge utile JSON vers l'URI `/v1/predict` et omettait le header d'autorisation `X-API-Key`.
2. **Décalage dans la structure des données reçues :** Les variables exploitées dans l'interface Streamlit (`ui/app.py`) ne correspondaient pas exactement aux clés retournées par le schéma de sortie de l'API.
3. **Absence de traitement standardisé des exceptions :** Nécessité de formaliser la capture des erreurs HTTP à l'aide de la classe `APIError`.

### 1.3 Validation de la conformité (23 tests au vert)
Une fois ces ajustements réalisés, l'exécution complète du banc de tests a confirmé le bon fonctionnement de tous les modules :

```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.7.0
rootdir: C:\Users\hp\Downloads\TP1_YEKHLEF_Aya\TP\TP3\TP3-maintai-Hajar-Belhachmi
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.15.1
collected 23 items

tests\test_api.py .......                                                [ 30%]
tests\test_client.py ...                                                 [ 43%]
tests\test_data.py ...                                                   [ 56%]
tests\test_security.py .....                                             [ 78%]
tests\test_train.py ...                                                  [ 91%]
tests\test_ui.py ..                                                      [100%]

======================== 23 passed, 1 warning in 8.86s ========================
```
*Remarque :* L'avertissement `StarletteDeprecationWarning` provient de l'intégration interne entre `httpx` et `starlette.testclient` ; il n'impacte en rien la validité fonctionnelle des tests.

---

## 2. Déploiement local de l'application

Le démarrage du serveur Streamlit s'effectue via la ligne de commande :
```powershell
python -m streamlit run ui/app.py
```
L'interface web se charge automatiquement dans le navigateur sur le port standard :
```text
http://localhost:8501
```

L'application est structurée de manière intuitive grâce à deux onglets principaux :
1. **Données :** Restitution statistique et graphique pour explorer les tendances d'usure des équipements.
2. **Prédiction :** Simulateur interactif permettant de configurer un profil machine et de requêter l'API en direct.

---

## 3. Volet analytique : Exploration des données capteurs

### 3.1 Indicateurs macroscopiques
La vue analytique met en évidence les métriques fondamentales du parc machines :

| Indicateur | Valeur mesurée | Rôle opérationnel |
|---|---:|---|
| **Effectif total** | **5 000 relevés** | Volume historique disponible pour l'apprentissage et l'analyse. |
| **Fréquence des pannes** | **13,6 %** | Confirme la rareté relative des pannes et la nécessité de privilégier le rappel. |
| **Température moyenne** | **59,8 °C** | Niveau thermique de référence en conditions d'exploitation standard. |

### 3.2 Corrélation thermique : Risque d'avarie par classe de température
- L'intervalle de température a été découpé en **10 sous-ensembles réguliers** au moyen de la méthode `pd.cut`.
- Un diagramme en barres (`st.bar_chart`) synthétise le taux d'avarie calculé sur chaque plage.
- **Interprétation :** Les données révèlent un seuil critique très net : le taux de défaillance reste inférieur à 10 % jusqu'à 65 °C, puis franchit rapidement la barre des 50 % au-delà de 80 °C, démontrant le rôle déterminant de la température comme signal précurseur d'incident.

### 3.3 Visualisation combinée : Nuage de points Température / Vibrations
- Un graphique de dispersion (`st.scatter_chart`) croise les valeurs de température (abscisses) avec l'amplitude vibratoire (ordonnées).
- Une coloration binaire distingue les observations saines (`0`) de celles ayant conduit à un dysfonctionnement (`1`).
- **Constat :** Les cas de défaillance forment un cluster distinct caractérisé par des vibrations élevées associées à de fortes températures, confirmant l'interaction forte entre ces deux contraintes physiques.

### 3.4 Optimisation du pipeline avec `@st.cache_data`
Le chargement du jeu de données s'appuie sur le mécanisme de cache Streamlit :
```python
@st.cache_data
def load_cached_data():
    return load_data()
```
* **Utilité technique :** Chaque manipulation de widget dans Streamlit entraîne une réévaluation séquentielle du script. 
* **Bénéfice :** Le décorateur `@st.cache_data` stocke en mémoire vive le DataFrame Pandas après sa première lecture. Ainsi, les rechargements ultérieurs sont instantanés et éliminent les accès disques redondants.

---

## 4. Volet prédictif : Simulation et inférence en direct

### 4.1 Interface de saisie paramétrique
L'onglet de prédiction propose un ensemble de composants interactifs cadrés par les bornes physiques définies dans le schéma de validation :
- Curseurs dynamiques (`st.slider`) pour régler la **température** (-40 °C à 150 °C), les **vibrations** (0 à 100 mm/s) et la **charge** (0 % à 100 %).
- Champ numérique (`st.number_input`) pour les **heures cumulées** (jusqu'à 200 000 heures).
- Regroupement sous `st.form` avec bouton de soumission (`st.form_submit_button`) pour éviter tout appel réseau intempestif avant la fin de la saisie utilisateur.

### 4.2 Architecture du client HTTP (`MaintaiClient`)
Le dialogue réseau avec l'API FastAPI est centralisé dans la méthode `predict` de `maintai/client.py` :
```python
def predict(self, releve: dict) -> dict:
    """Envoie un relevé à l'API MaintAI et retourne la prédiction."""
    headers = {}
    if self.api_key:
        headers["X-API-Key"] = self.api_key

    r = self.http.post("/v1/predict", json=releve, headers=headers)

    if r.status_code != 200:
        raise APIError(r.status_code, r.json().get("detail"))

    return r.json()
```

### 4.3 Exploitation des résultats et sécurité
À la réception du payload de prédiction :
- Le score de risque est formaté et affiché en pourcentage.
- Une bannière visuelle informe l'utilisateur :
  - **Alerte critique (`st.error`) :** Activée si le seuil d'intervention (0,3) est dépassé, signalant un besoin de maintenance urgente.
  - **Statut normal (`st.success`) :** Indique que les paramètres machine sont dans la zone sécurisée.
- Les dysfonctionnements sont rigoureusement interceptés :
  - Erreur `401` levée en cas de clé API non reconnue ou absente.
  - Exception réseau `httpx.HTTPError` interceptée avec un message invitant à vérifier si l'API FastAPI est bien active sur le port 8000.

### 4.4 Synthèse des tests de validation opérationnelle

| Cas de figure | Configuration testée | Comportement de l'application |
|---|---|---|
| **Régime nominal** | T: 55 °C, Vib: 2.5 mm/s, Charge: 50 %, Heures: 4 000 | Réponse 200, risque faible (< 0.3), confirmation de bon fonctionnement |
| **Conditions extrêmes** | T: 90 °C, Vib: 10 mm/s, Charge: 90 %, Heures: 16 000 | Réponse 200, probabilité élevée (> 0.7), déclenchement d'alerte rouge |
| **Clé d'accès incorrecte** | Clé erronée dans l'environnement | Capture `APIError(401)`, message d'authentification refusée |
| **Serveur éteint** | Uvicorn non démarré | Interception de l'erreur réseau, notification claire d'indisponibilité |

---

## 5. Questions de réflexion et analyse architecturale

### 5.1 En quoi l'approche Streamlit (TP3) diffère-t-elle de l'approche HTML/JS (TP2) ?
* **Dans le TP2 :** L'architecture est de type SPA côté client. Le code HTML/JS est exécuté dans le navigateur de l'utilisateur final. Les requêtes partent directement de la machine cliente vers l'API, ce qui nécessite une configuration CORS rigoureuse sur le serveur et expose potentiellement la logique d'appel.
* **Dans le TP3 :** L'architecture est centralisée côté serveur. C'est l'interpréteur Python exécutant Streamlit qui communique en backend avec l'API FastAPI. Les règles CORS ne s'appliquent plus entre l'utilisateur et l'API, et la clé secrète reste confinée sur le serveur sans transiter dans le navigateur du client.

### 5.2 Pourquoi les tests d'API s'exécutent-ils sans instancier Uvicorn ?
Les tests s'appuient sur `TestClient` (fourni par Starlette/FastAPI), qui effectue des appels directs en mémoire vers l'application WSGI/ASGI via le protocole ASGI mocké. Il n'y a donc pas de socket réseau ouvert ni de processus serveur externe à démarrer. Les tests sont ainsi déterministes, extrêmement véloces et indépendants de la disponibilité des ports réseau sur la machine hôte.

### 5.3 Quelle orientation choisir dans un cadre industriel ?
* **Streamlit :** Représente la solution idéale pour le prototypage rapide, les tableaux de bord pour data scientists et les outils de supervision interne d'atelier. Il permet de déployer une solution complète en quelques dizaines de lignes de Python sans compétences web approfondies.
* **Architecture Web moderne (Frontend dédié React/Vue + API REST) :** Doit être privilégiée pour les applications industrielles critiques grand public ou déployées auprès de milliers d'opérateurs simultanés. Elle permet une séparation stricte des responsabilités, une maîtrise absolue des performances côté client et une adaptabilité graphique totale.

---

## 6. Conclusion du travail réalisé

La réalisation de ce TP3 a permis de concrétiser le déploiement d'une application d'intelligence artificielle de bout en bout :
- Maîtrise des composants Streamlit pour l'exploration de données et la restitution visuelle.
- Sécurisation des flux de données et gestion fine des erreurs grâce à un client HTTP structuré.
- Garantie de fiabilité validée par le succès des 23 tests automatisés du projet.

