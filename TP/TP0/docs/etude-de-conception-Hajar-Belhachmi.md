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