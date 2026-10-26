# Étude de conception — Prédiction des pannes industrielles par apprentissage automatique

**Réalisée par le groupe 3 :BELHACHMI Hajar

**Version :** 1.0 · **Date :** 24/10/2026

## 1. Contexte et utilisateurs

- **Utilisateur principal :** Ingénieur de maintenance industrielle.
- **Contexte :** Les machines industrielles sont soumises à différentes conditions de fonctionnement. Une charge importante ou variable peut contribuer à une dégradation mécanique, accompagnée d'une hausse de température ou de vibrations. Le projet vise à anticiper les pannes grâce aux données de fonctionnement.
- **Utilisateurs secondaires :** Techniciens de maintenance et responsables de production.

## 2. Problème et décision

- **Problème :** Comment prédire une panne industrielle en se basant principalement sur la charge de la machine, tout en exploitant la température et les vibrations pour améliorer la détection ?
- **Décision prise par l'utilisateur :** Déterminer quelles machines doivent être inspectées en priorité, lesquelles nécessitent une surveillance renforcée et lesquelles peuvent poursuivre leur fonctionnement normal.
- **Fréquence :** Acquisition périodique des mesures par les capteurs, par exemple chaque seconde, et actualisation du risque toutes les minutes, selon les capacités du système.
- **Coût d'une erreur :**
  - Faux négatif : une panne n'est pas détectée, ce qui peut provoquer un arrêt imprévu, des coûts de réparation et des risques pour la sécurité.
  - Faux positif : une alerte injustifiée entraîne une inspection inutile, des coûts de maintenance et éventuellement une interruption de production.
- **Horizon de prédiction envisagé :** Détecter si une panne surviendra dans les prochaines 24 heures, sous réserve de disposer de données historiques adaptées. Le fichier utilisé ne contient ni date ni heure et ne précise pas la période couverte par la variable `failure` : l'horizon de 24 heures reste donc un objectif à confirmer, et non une propriété vérifiée des données.

## 3. Approche par sous-problème

| Sous-problème | Approche | Pourquoi pas une approche plus simple ? |
|---|---|---|
| Collecte et validation des mesures | Règles | Les contrôles de format, les valeurs manquantes et les limites physiques peuvent être traités sans IA. |
| Analyse de l'influence de la charge | Statistiques et visualisation | Une analyse descriptive suffit pour explorer les premières relations ; le ML intervient pour les relations plus complexes. |
| Prédiction de panne à partir de la charge seule | ML : DummyClassifier et régression logistique | Les règles fixes peuvent être insuffisantes lorsque la relation entre charge et panne est complexe. |
| Prédiction avec charge, température, vibrations et heures de fonctionnement | ML : Random Forest, arbre de décision et KNN | Ces modèles peuvent capturer des interactions non linéaires entre les variables. |
| Préparation des données | Imputation, standardisation et encodage | Les traitements classiques sont plus simples et suffisants pour des données tabulaires. |
| Explication des prédictions | Importance des variables et SHAP si nécessaire | Une analyse simple de l'importance peut suffire au départ ; SHAP sera ajouté si une interprétation plus détaillée est nécessaire. |
| Déclenchement des alertes | Règles fondées sur le risque prédit | Une logique déterministe est plus facile à contrôler qu'un LLM pour prendre une décision opérationnelle. |

## 4. Données

| Jeu de données | Source et licence | Volume | Données personnelles ? |
|---|---|---|---|
| Données de panne industrielles | Fichier CSV local `data/exemple_pannes.csv` ; origine et licence à vérifier | 5 000 observations, 5 colonnes, aucune valeur manquante ; 878 pannes (17,6 %) | Aucune colonne personnelle (identifiant, nom, lieu) |
| Mesures de charge | Colonne `load_pct` du fichier CSV ; capteurs industriels en exploitation | 5 000 valeurs, de 20 à 100 % | Non |
| Mesures de température | Colonne `temperature_c` du fichier CSV ; capteurs industriels en exploitation | 5 000 valeurs, de 35,8 à 92,6 °C | Non |
| Mesures de vibrations | Colonne `vibration_mm_s` du fichier CSV ; capteurs industriels en exploitation | 5 000 valeurs, de 0,02 à 22,2 mm/s | Non |
| Historique des pannes | Colonne `failure` du fichier CSV ; registre de maintenance en exploitation | 5 000 étiquettes : 4 122 à 0 et 878 à 1 | Non dans le fichier ; à vérifier pour un registre réel |

**Variables du fichier :**
- `load_pct` : charge de la machine, en pourcentage. Variable que l'étude considérait comme principale.
- `temperature_c` : température de fonctionnement, en °C.
- `vibration_mm_s` : niveau de vibration, en mm/s.
- `runtime_hours` : heures de fonctionnement de la machine, variable absente de la version initiale de l'étude.
- `failure` : cible, avec 0 pour l'absence de panne et 1 pour la panne. Ce codage a été confirmé dans le fichier.
- Date et heure : absentes du fichier. L'évaluation chronologique n'est donc pas possible avec ces données.

**Vérifications faites sur le fichier :** aucune valeur manquante, deux classes seulement (0 et 1), classes déséquilibrées (82,4 % sans panne). Les unités sont indiquées dans les noms de colonnes ; leur exactitude ne peut pas être confirmée sans la documentation de la source.

## 5. Métriques, baseline et critères d'acceptation

- **Baseline :** `DummyClassifier(strategy="most_frequent")`, qui prédit systématiquement la classe majoritaire. Son score sera mesuré sur le jeu de test.
- **Métrique principale :** Recall de la classe « panne », car manquer une panne peut avoir un coût industriel important.
- **Métriques secondaires :**
  - Accuracy : proportion de prédictions correctes.
  - Precision : proportion d'alertes positives correctes.
  - F1-score : compromis entre precision et recall.
- **Comparaison des modèles :** baseline, régression logistique, arbre de décision, Random Forest et KNN.
- **Critères d'acceptation proposés :**
  1. Obtenir un recall supérieur à celui de la baseline sur un jeu de test indépendant.
  2. Viser un recall d'au moins 80 %, à confirmer selon les risques métier et la difficulté du problème.
  3. Contrôler la précision et le nombre de fausses alertes afin d'éviter un système trop alarmiste.
  4. Pour des données temporelles, utiliser un découpage chronologique : apprentissage sur le passé et test sur une période future.
  5. Comparer le modèle utilisant uniquement la charge au modèle utilisant les trois variables pour mesurer la contribution des capteurs complémentaires.

Les seuils définitifs seront fixés après les échanges avec le responsable de maintenance. Ils ne constituent pas des performances obtenues.

**Suivi des critères :** le bilan chiffré figure dans `docs/choix-modele.md`. En résumé, le critère 1 est atteint (recall de 0,597 contre 0 pour la baseline), le critère 2 ne l'est pas (0,597 pour un objectif de 0,80), le critère 4 ne s'applique pas faute de dates, et la comparaison du critère 5 montre que la charge seule ne permet presque pas de détecter les pannes (recall de 0 à 0,04).

## 6. Architecture prévue

1. **Acquisition :** récupération des mesures de charge, température et vibrations.
2. **Stockage :** conservation des données et de l'historique des pannes dans des fichiers CSV ou une base de données.
3. **Prétraitement :** validation, nettoyage, traitement des valeurs manquantes et création des variables prédictives.
4. **Entraînement :** comparaison des modèles ML avec une baseline.
5. **Évaluation :** calcul des métriques sur un jeu de test indépendant.
6. **Prédiction :** estimation du risque de panne à partir des nouvelles mesures.
7. **Restitution :** affichage du risque, des principales variables contributives et des alertes destinées au personnel de maintenance.

## 7. Choix technologiques

- **Langage :** Python.
- **Manipulation des données :** Pandas et NumPy.
- **Apprentissage automatique :** scikit-learn.
- **Prétraitement :** `ColumnTransformer`, `SimpleImputer`, `StandardScaler` et `OneHotEncoder`.
- **Modèles :** DummyClassifier, régression logistique, arbre de décision, Random Forest et KNN.
- **Évaluation :** métriques scikit-learn et tableau comparatif avec Pandas.
- **Sauvegarde :** Joblib pour le modèle et JSON pour les résultats.
- **Tests :** pytest, avec 8 tests sur le chargement, le découpage, les modèles et l'entraînement.
- **Visualisation envisagée :** Matplotlib ou Seaborn pour les analyses exploratoires.

## 8. Risques, éthique, confidentialité

- **Déséquilibre des classes :** le nombre de pannes peut être faible par rapport au fonctionnement normal. L'accuracy seule serait donc insuffisante.
- **Fuite de données :** aucune information postérieure à la panne ne doit être utilisée pour prédire cette panne.
- **Généralisation limitée :** un modèle entraîné sur une machine ou un environnement donné peut être moins fiable sur d'autres équipements.
- **Fausses alertes et pannes manquées :** les seuils doivent être choisis selon les conséquences métier.
- **Interprétabilité :** la contribution de chaque variable doit être analysée explicitement. Dans les données de ce projet, la charge seule détecte presque aucune panne et les vibrations sont la variable la plus liée aux pannes.
- **Sécurité :** le modèle fournit une aide à la décision et ne remplace pas les dispositifs de sécurité industriels.
- **Confidentialité :** limiter les données aux informations nécessaires, contrôler les accès et vérifier que les historiques de maintenance ne contiennent pas d'informations personnelles.
- **Validation :** tester le modèle sur des données indépendantes avant toute utilisation réelle.

## 9. Limites et hors périmètre

- Le projet prédit un risque de panne, mais ne garantit pas qu'une panne surviendra.
- Il ne détermine pas nécessairement la cause physique exacte de la défaillance.
- Il ne remplace pas l'expertise des techniciens et ingénieurs de maintenance.
- Il ne propose pas d'alerte automatique dans cette version : les alertes décrites dans l'architecture restent à construire.
- La durée de vie restante de la machine (RUL) n'est pas prédite dans la première version.
- La commande automatique des machines et l'arrêt d'urgence ne font pas partie du périmètre.
- Le déploiement industriel en temps réel dépendra de la disponibilité des capteurs, de données fiables et de la validation du modèle.
- La qualité finale dépendra du volume, de la représentativité et de la qualité des données de panne disponibles.


#

# Étude de conception : CantineAI, prévision du nombre de repas à la cantine

Réalisée par : BELHACHMI Hajar

**Version :** 1.0 · **Date :** 24/10/2026

## 1. Contexte et utilisateurs

- **Utilisateur principal :** le gestionnaire de la cantine d'un lycée.
- **Contexte :** la cantine sert le déjeuner du lundi au vendredi à environ 650 élèves inscrits. Chaque jour à 10 h, le gestionnaire doit commander à la cuisine le nombre de repas du lendemain. Aujourd'hui, il reprend le chiffre du même jour de la semaine précédente.
- **Utilisateurs secondaires :** la cuisine, qui prépare la quantité commandée, et la direction de l'établissement, qui suit le gaspillage et les plaintes.

## 2. Problème et décision

- **Problème :** comment prévoir le nombre de repas servis un jour donné, à partir de ce que l'on sait la veille (menu, météo prévue, examens, sorties scolaires, vacances, effectif inscrit) ?
- **Décision prise avec le système :** le nombre de repas à commander à la cuisine pour le lendemain.
- **Fréquence :** une fois par jour d'école, à 10 h, soit cinq décisions par semaine.
- **Coût d'une erreur :**
  - Repas commandé en trop : environ 15 DH de matière première perdus par repas jeté, et du gaspillage alimentaire. Le coût est supporté par la cantine et l'établissement.
  - Repas manquant : un élève sans déjeuner, ou un sandwich de remplacement acheté en urgence, et des plaintes de parents. Le coût est supporté par les élèves, le gestionnaire et les parents. L'énoncé ne le chiffre pas.
- **Horizon de prédiction :** le lendemain, à partir des informations connues la veille.

Le coût d'un repas jeté est connu (15 DH), celui d'un repas manquant ne l'est pas : on ne sait donc pas si les deux erreurs pèsent autant. Ce point doit être précisé avec le gestionnaire.

## 3. Approche par sous-problème

| Sous-problème | Approche | Pourquoi pas une approche plus simple ? |
|---|---|---|
| Collecte et validation des données | Règles | Le format des dates, les valeurs hors plage et les valeurs manquantes se contrôlent sans IA. |
| Méthode actuelle : reprise de la semaine précédente | Règle | C'est la référence à battre. Elle ignore le menu, les examens, les sorties et les vacances : sur les 58 jours du test où elle existe, son erreur moyenne est de 79 repas. |
| Estimation d'un niveau moyen de repas | Statistique : moyenne | Elle ne tient compte d'aucune information du jour : erreur moyenne de 70 repas sur le test. |
| Prévision à partir du menu, de la météo, du calendrier et de l'effectif | ML de régression tabulaire : régression linéaire, arbre de décision, Random Forest, KNN | Les effets sont importants (les jours d'examens, environ 120 repas de moins en moyenne ; le couscous, environ 140 de plus que le poisson) et se combinent : une règle à la main serait longue à régler et à maintenir. |
| Préparation des données | Imputation, standardisation, encodage one-hot | Traitements classiques, suffisants pour des données tabulaires. |
| Évaluation | Découpage chronologique, MAE, comparaison à la méthode actuelle | Un tirage au hasard mélangerait le passé et le futur (voir `docs/grille-seance-3.md`). |
| Aide à la commande | Règle : prévision arrondie, éventuellement majorée d'une marge | Une règle déterministe est plus simple à contrôler et à expliquer au gestionnaire. |

Un réseau de neurones n'est pas justifié avec 340 lignes et neuf variables. Un LLM n'a pas de rôle dans ce problème : les données sont des nombres et des catégories, pas du texte libre.

## 4. Données

| Jeu de données | Source et licence | Volume | Données personnelles ? |
|---|---|---|---|
| `data/cantine_repas.csv` | Données synthétiques générées pour le cours ; licence non précisée, usage pédagogique | 340 jours d'école, du 09/09/2024 au 19/06/2026, une ligne par jour, 11 colonnes | Non : effectifs agrégés par jour, aucun élève identifié |

**Variables :**
- `date` : le jour d'école. Elle sert à ordonner les jours pour le découpage et n'est pas donnée au modèle.
- `jour`, `menu` : variables catégorielles (5 jours, 5 plats).
- `inscrits`, `temperature_c`, `pluie_mm` : variables numériques.
- `examens`, `sortie_scolaire`, `veille_vacances` : indicateurs 0 ou 1.
- `repas_semaine_precedente` : repas servis le même jour une semaine avant, c'est-à-dire la méthode actuelle.
- `repas_servis` : la cible, de 248 à 695 repas.

**Vérifications faites sur le fichier :**
- 340 lignes, dates triées et sans doublon, 68 occurrences de chaque jour de la semaine.
- Une seule colonne comporte des valeurs manquantes : `repas_semaine_precedente` (60 jours), toujours la première semaine d'école ou la semaine qui suit des vacances.
- La cible n'a aucune valeur manquante.
- Toutes les variables d'entrée sont connues la veille : il n'y a pas de fuite d'information du jour à prévoir.
- Le nombre d'inscrits augmente : 650 en moyenne sur les 272 premiers jours, 694 sur les 68 derniers. Les repas servis suivent : 493 en moyenne à l'entraînement, 525 au test.

## 5. Métriques, baseline et critères d'acceptation

- **Baseline :**
  - Dans le code : `DummyRegressor(strategy="mean")`, qui prédit toujours la moyenne des repas servis à l'entraînement.
  - Référence métier : la reprise de la semaine précédente, mesurée sur les jours du test où elle existe. Son principe : le jour de la semaine se répète, donc le chiffre d'une semaine sert de prévision pour la suivante.
- **Métrique principale :** MAE, l'erreur absolue moyenne, en repas. Elle se lit directement par le gestionnaire (« la prévision se trompe de 22 repas en moyenne ») et suit le coût : un repas d'écart coûte à peu près la même chose, quelle que soit la taille de l'écart. La RMSE pénalise davantage les gros écarts ; elle est calculée aussi, mais n'est pas retenue comme critère de choix.
- **Métriques secondaires :** RMSE (en repas) et R2.
- **Comparaison des modèles :** baseline, régression linéaire, arbre de décision, Random Forest et KNN.
- **Critère d'acceptation proposé :** une MAE d'au plus 30 repas sur le jeu de test chronologique (20 % des jours les plus récents, soit 68 jours), et inférieure à la moitié de la MAE de la reprise de la semaine précédente sur les mêmes jours.
  - Métrique : MAE. Nombre : 30 repas, soit environ 4,6 % de 650 élèves ; si toute l'erreur était en repas jetés, cela représenterait au plus 450 DH par jour. Jeu de données : les 68 derniers jours. Condition : MAE inférieure à la moitié de celle de la méthode actuelle.
  - Le seuil de 30 repas est une proposition à valider avec le gestionnaire.
- **Découpage :** chronologique. L'entraînement porte sur les jours les plus anciens, le test sur les plus récents, car le système doit prévoir l'avenir.

## 6. Architecture prévue

1. **Acquisition :** le gestionnaire (ou un export de la gestion scolaire) fournit chaque jour l'effectif inscrit, le menu, la météo prévue et le calendrier du lendemain.
2. **Stockage :** un fichier CSV qui s'enrichit chaque jour des repas réellement servis.
3. **Prétraitement :** vérification, imputation, standardisation, encodage des catégories.
4. **Entraînement :** comparaison des modèles à la baseline, avec `python -m monprojet.train`.
5. **Évaluation :** MAE, RMSE et R2 sur les derniers jours, et comparaison à la méthode actuelle.
6. **Prédiction :** estimation du nombre de repas pour le lendemain avec le modèle sauvegardé.
7. **Restitution :** le nombre de repas à commander, présenté au gestionnaire avec la prévision de la méthode actuelle pour comparaison.

## 7. Choix technologiques

- **Langage :** Python.
- **Manipulation des données :** pandas et NumPy.
- **Apprentissage automatique :** scikit-learn.
- **Prétraitement :** `ColumnTransformer`, `SimpleImputer`, `StandardScaler` et `OneHotEncoder`.
- **Modèles :** DummyRegressor, régression linéaire, arbre de décision, Random Forest et KNN.
- **Évaluation :** métriques scikit-learn et tableau comparatif avec pandas.
- **Sauvegarde :** joblib pour le modèle et JSON pour les résultats.
- **Tests :** pytest, avec 8 tests sur le chargement, le découpage chronologique, les modèles et l'entraînement.

## 8. Risques, éthique, confidentialité

- **Fuite de données :** un tirage au hasard des jours de test placerait dans l'entraînement la veille ou la semaine précédente d'un jour de test. Le découpage chronologique évite ce risque.
- **Évolution de l'effectif :** le nombre d'inscrits change avec le temps. Un modèle entraîné sur le passé peut se tromper si l'effectif sort de la plage vue à l'entraînement ; il faut le réentraîner régulièrement.
- **Erreurs asymétriques :** le modèle peut commander trop peu (élèves sans repas) ou trop (gaspillage). Il faut chiffrer le coût d'un repas manquant et ajuster la commande en conséquence.
- **Événements rares :** peu de jours d'examens, de sorties ou de veilles de vacances sont disponibles, donc les prévisions sont moins fiables ces jours-là.
- **Données synthétiques :** les performances mesurées ne prouvent pas la performance sur une vraie cantine.
- **Confidentialité :** le projet n'utilise que des effectifs agrégés. Si des données par élève étaient ajoutées, il faudrait limiter les informations et contrôler les accès.
- **Validation :** comparer le modèle à la méthode actuelle sur plusieurs semaines réelles avant de le substituer.

## 9. Limites et hors périmètre

- Le projet prévoit un nombre de repas, il ne garantit pas qu'il sera exact.
- Il ne gère pas la composition des menus, les allergies ni les approvisionnements de la cuisine.
- Il ne prévoit que le lendemain : il ne planifie pas les commandes à plusieurs semaines.
- Le coût d'un repas manquant n'est pas modélisé.
- La qualité finale dépendra de données réelles, plus nombreuses et plus représentatives que ces 340 jours synthétiques.
