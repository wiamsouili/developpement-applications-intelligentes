# Séance 3 : grille de conception du projet de prédiction de pannes

**Groupe 3 :** SOUILI Wiam, ELAOUAZI Hafsa, YEKHLEF Aya, BELHACHMI Hajar

Cette grille reprend les sections 1 à 5 de l'étude de conception, les réglages de `config.py` qui en découlent et la réponse à la question finale.

## 1. Sections 1 à 5

| Section | Projet de prédiction de pannes |
|---|---|
| **1. Utilisateur principal** | Un technicien ou responsable de l'équipe de maintenance de l'usine |
| **2. Décision et fréquence** | Choisir les machines à inspecter, chaque matin |
| **2. Coût d'une erreur** | Panne manquée (faux négatif) : une ligne de production arrêtée pendant une journée, au détriment de l'usine. Fausse alerte (faux positif) : une heure d'inspection inutile, au détriment de l'équipe de maintenance. |
| **3. Approche** | ML de classification tabulaire (régression logistique, arbre de décision, Random Forest, KNN). Pas plus simple : une règle à seuil sur un seul capteur ne combine pas les quatre mesures, et la charge seule ne détecte presque aucune panne (recall de 0 à 0,04). Pas de deep learning ni de LLM : 5 000 lignes de nombres, sans texte libre. |
| **4. Données** | `data/exemple_pannes.csv` : relevés de capteurs synthétiques, licence non précisée. 5 000 relevés, 4 variables d'entrée (température, vibration, charge, heures de fonctionnement) et la cible `failure`, dont 17,6 % de pannes. Aucune donnée personnelle. |
| **5. Baseline** | `DummyClassifier(strategy="most_frequent")` : elle prédit toujours « pas de panne », la classe la plus fréquente. |
| **5. Métrique principale** | Recall de la classe « panne » : une panne manquée coûte une journée d'arrêt, beaucoup plus qu'une heure d'inspection. Il faut donc détecter le plus de pannes possible. |
| **5. Critère d'acceptation** | Un recall de la classe « panne » d'au moins 0,80 sur le jeu de test (20 % des relevés, soit 1 000 relevés, tirage aléatoire stratifié, graine 42), avec une précision d'au moins 0,50 pour limiter les fausses alertes. |

Le critère contient bien une métrique (recall), un nombre (0,80), un jeu de données de mesure (les 1 000 relevés du test) et une condition (précision d'au moins 0,50).

Situation actuelle du projet : le meilleur recall obtenu est de 0,597 (arbre de décision), donc le critère n'est pas encore atteint.

## 2. Réglages de `config.py`

| Réglage | Projet de prédiction de pannes |
|---|---|
| `DATA_PATH` | `data/exemple_pannes.csv` |
| `TARGET` | `failure` |
| `TASK` | `classification` |
| `MAIN_METRIC` | `recall` |
| `SPLIT` | `random` |
| `TIME_COLUMN` | `None` |

Le jeu de données n'a pas de colonne de date : le découpage est donc aléatoire et non chronologique.

## 3. Question finale

**Un modèle qui ne prédit jamais de panne aurait quelle accuracy ? Pourquoi cette métrique ne convient-elle pas ?**

Il aurait une accuracy de 82,4 % : 4 122 relevés sur 5 000 se terminent sans panne, et 824 sur 1 000 dans le jeu de test. Il ne détecterait pourtant aucune panne : son recall est de 0. L'accuracy compte toutes les prédictions de la même manière, alors que les pannes sont rares (17,6 %) et que les manquer est l'erreur la plus coûteuse. Elle récompense un modèle inutile ; c'est pourquoi le recall de la classe « panne » est retenu comme métrique principale.
