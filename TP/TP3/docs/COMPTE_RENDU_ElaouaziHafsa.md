# Compte rendu · TP3 : Tableau de bord Streamlit pour l'application MaintAI

**Module :** Développement et déploiement d'applications intelligentes  
**Projet :** MaintAI — Prédiction des pannes industrielles  
**Étudiante :** ELAOUAZI Hafsa  
**Groupe :** G3  
**Date :** 09/11/2026  

---

## 1. Prise en main et exécution des tests

### 1.1 Objectif de la séance
Ce TP3 est consacré au développement d'une interface graphique interactive complète sous **Streamlit** pour exploiter le modèle de prédiction MaintAI. Elle combine l'analyse exploratoire des données d'équipements et un simulateur d'inférence en direct connecté à notre API REST sécurisée.

### 1.2 Analyse initiale des tests
À l'initialisation du projet, la commande :
```powershell
python -m pytest
```
a produit un bilan de **4 tests échoués et 19 tests réussis**.

Les points bloquants identifiés :
- La méthode `predict()` de la classe `MaintaiClient` (`maintai/client.py`) devait structurer la requête HTTP POST vers l'endpoint `/v1/predict` et injecter la clé secrète via l'en-tête `X-API-Key`.
- L'interface `ui/app.py` devait être alignée avec les champs retournés par l'API (`failure_probability`, `alert`, `threshold`).
- La capture des anomalies HTTP nécessitait l'utilisation de l'exception personnalisée `APIError`.

### 1.3 Bilan final après corrections
Après avoir apporté les corrections nécessaires, l'ensemble des 23 tests automatisés a été validé avec succès :

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
*Avertissement :* `StarletteDeprecationWarning` est un warning de dépréciation mineur lié à `TestClient`, sans conséquence sur la conformité de l'application.

---

## 2. Déploiement et exécution de l'interface

Le lancement de l'application s'effectue via :
```powershell
python -m streamlit run ui/app.py
```
L'interface est accessible depuis le navigateur à l'adresse :
```text
http://localhost:8501
```

L'application s'articule autour de deux onglets :
- **Données :** Restitution statistique et graphique pour explorer les relevés capteurs.
- **Prédiction :** Formulaire interactif pour configurer une machine et interroger le modèle.

---

## 3. Exploration des données (Onglet 1)

### 3.1 Métriques de synthèse
L'onglet Données affiche trois indicateurs calculés sur le jeu de données :

| Indicateur | Valeur obtenue | Interprétation |
|---|---:|---|
| **Nombre total de relevés** | **5 000** | Base statistique représentative du parc industriel. |
| **Taux de panne moyen** | **13,6 %** | Les pannes restent des événements rares (déséquilibre de classe). |
| **Température moyenne** | **59,8 °C** | Niveau thermique normal d'exploitation. |

### 3.2 Taux de défaillance selon la température
- La température a été discrétisée en **10 plages égales** via `pd.cut()`.
- Le taux de défaillance par tranche est projeté dans un graphique en barres `st.bar_chart()`.
- **Observation :** On constate une transition marquée : le risque de panne reste inférieur à 10 % en deçà de 65 °C, puis augmente drastiquement pour dépasser 50 % au-delà de 80 °C.

### 3.3 Nuage de points bivarié (Température vs Vibrations)
- Un diagramme de dispersion `st.scatter_chart` croise la température (axe X) et l'amplitude vibratoire (axe Y).
- La couleur différencie les machines opérationnelles (`0`) de celles en panne (`1`).
- **Observation :** Les pannes se concentrent dans les zones simultanées de fortes températures et de vibrations élevées.

### 3.4 Optimisation du chargement avec `@st.cache_data`
```python
@st.cache_data
def get_data():
    return load_data()
```
Grâce à `@st.cache_data`, Streamlit met en cache le DataFrame chargé en RAM. Les réexécutions automatiques du script induites par la manipulation des widgets s'effectuent sans relire le fichier CSV sur disque.

---

## 4. Module d'inférence en direct (Onglet 2)

### 4.1 Formulaire interactif
Le formulaire regroupe les paramètres des équipements :
- Curseurs `st.slider` pour la **température** (-40 °C à 150 °C), les **vibrations** (0 à 100 mm/s) et la **charge** (0 % à 100 %).
- Champ `st.number_input` pour les **heures de fonctionnement** (0 à 200 000 h).
- Soumission atomique via `st.form_submit_button`.

### 4.2 Client HTTP API (`MaintaiClient`)
Dans `maintai/client.py` :
```python
def predict(self, releve: dict) -> dict:
    """Envoie le relevé à l'API MaintAI et retourne la prédiction."""
    headers = {}
    if self.api_key:
        headers["X-API-Key"] = self.api_key

    r = self.http.post("/v1/predict", json=releve, headers=headers)

    if r.status_code != 200:
        raise APIError(r.status_code, r.json().get("detail"))

    return r.json()
```

### 4.3 Restitution des alertes et gestion des erreurs
- Formatage de la probabilité d'incident en pourcentage.
- Affichage d'un bandeau rouge `st.error` en cas de dépassement du seuil critique (0,3), ou d'un bandeau vert `st.success` en fonctionnement normal.
- Gestion robuste des exceptions :
  - Interception des erreurs d'authentification `401` (`APIError`).
  - Capture des pannes réseau ou d'indisponibilité du serveur (`httpx.HTTPError`).

### 4.4 Synthèse des scénarios testés

| Cas testé | Entrées simulées | Comportement applicatif |
|---|---|---|
| **État sain** | T: 50 °C, Vib: 2 mm/s, Charge: 40 %, Heures: 1 500 | Code 200, probabilité faible (< 0.3), alerte verte |
| **Surchauffe & vibrations** | T: 92 °C, Vib: 11 mm/s, Charge: 92 %, Heures: 17 500 | Code 200, probabilité élevée (> 0.8), alerte rouge de panne |
| **Clé incorrecte** | Clé erronée dans l'environnement | Erreur 401 interceptée, message de sécurité |
| **API arrêtée** | Serveur FastAPI non lancé | Erreur de connexion interceptée, invitation à démarrer l'API |

---

## 5. Questions de réflexion

### 5.1 Différence entre interface TP2 (HTML/JS) et TP3 (Streamlit) ?
Dans le TP2, le frontend s'exécute côté client (navigateur web). C'est le navigateur qui effectue les requêtes vers l'API, ce qui requiert la gestion des politiques CORS et expose la clé API au client.
Dans le TP3, le code Streamlit s'exécute côté serveur en Python. Les appels à l'API sont effectués en interne par le serveur Streamlit. Le navigateur de l'utilisateur n'accède qu'au rendu visuel, éliminant tout blocage CORS et protégeant les identifiants.

### 5.2 Pourquoi les tests fonctionnent-ils sans lancer Uvicorn ?
La bibliothèque `TestClient` (Starlette/FastAPI) invoque directement l'application ASGI en mémoire sans ouvrir de port réseau réel. Cela évite d'instancier un serveur HTTP externe Uvicorn et permet des tests ultra-rapides et déterministes.

### 5.3 Quelle technologie recommander en contexte industriel ?
- **Streamlit :** Adapté aux outils internes, prototypes et dashboards de maintenance pour techniciens. Développement rapide et intégration Python directe.
- **Stack Web découplée (React/Vue + API) :** Indispensable pour des plateformes industrielles à grande échelle, à forte fréquentation simultanée ou nécessitant une personnalisation graphique pointue.

---

## 6. Conclusion

Ce TP3 finalise la chaîne complète de MaintAI :
- Analyse descriptive des capteurs via Streamlit et Pandas.
- Communication réseau robuste et sécurisée via `MaintaiClient`.
- Validation par 23 tests automatisés garantissant la qualité de l'application.
