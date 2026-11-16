# Étude de conception — Détection de pannes par Machine Learning

Groupe : [G3]  
Version : Brouillon à valider  
Date : 26/10/2026

## 1. Contexte et utilisateurs

Le projet vise à détecter les pannes d’équipements à partir de données historiques afin d’aider à identifier les situations nécessitant une intervention de maintenance.

- Utilisateur principal : le technicien de maintenance industrielle chargé de surveiller l’état des équipements et de planifier les interventions.
- Utilisateurs secondaires : le responsable de maintenance et le responsable de production.
- Objectif : exploiter les données disponibles pour prédire si une panne est susceptible de se produire et faciliter la prise de décision.
- Bénéfices attendus : réduire les interruptions imprévues, améliorer la planification de la maintenance et limiter les coûts associés aux défaillances.

## 2. Problème et décision

- Décision que l’utilisateur prend avec le système : déterminer si un équipement doit faire l’objet d’une vérification ou d’une intervention préventive.
- Fréquence : lors de la réception de nouvelles observations sur les équipements, selon la fréquence de collecte des données.
- Coût d’une fausse alerte : une intervention inutile, des contrôles supplémentaires et une mobilisation de ressources.
- Coût d’une panne non détectée : un arrêt imprévu, une perte de production, des coûts de réparation et d’éventuels risques pour la sécurité.
- Priorité : limiter les pannes non détectées, tout en maintenant un niveau raisonnable de fausses alertes.

Le modèle fournit une prédiction destinée à assister le technicien. Il ne remplace ni l’inspection technique ni les procédures de sécurité.

## 3. Approche par sous-problème

| Sous-problème | Approche | Pourquoi ne pas utiliser une approche plus simple ? |
|---|---|---|
| Détecter une panne | Machine Learning supervisé — classification binaire | Une règle fixe peut être insuffisante lorsque plusieurs variables contribuent au risque de panne. |
| Établir une référence | Baseline | Elle permet de vérifier que les modèles apprennent réellement quelque chose d’utile par rapport à une référence simple. |
| Comparer les modèles | Logistic Regression, Decision Tree, Random Forest et KNN | La comparaison permet d’évaluer différentes méthodes de classification sur les mêmes données. |
| Évaluer la détection des pannes | Recall, precision, F1-score et accuracy | Ces métriques permettent de mesurer la détection des pannes, la fiabilité des alertes et la qualité globale des prédictions. |
| Sauvegarder le modèle | Pipeline de préparation et modèle sérialisé | Cela permet de reproduire le traitement et de réutiliser le modèle entraîné. |

Le projet utilise une approche de classification supervisée : la cible indique si une panne est survenue. Une approche de Deep Learning n’est pas nécessairement justifiée sans davantage de données ou un besoin plus complexe démontré.

## 4. Données

| Jeu de données | Source et licence | Volume | Données personnelles ? |
|---|---|---|---|
| Dataset de détection de pannes | Fichier CSV du projet ; nom exact, provenance et licence à confirmer | À compléter à partir du fichier utilisé | À vérifier selon les colonnes du fichier |

- Variable cible : `failure`, selon la configuration initiale du projet.
- Type de problème : classification binaire.
- Variables explicatives : les colonnes disponibles dans le fichier, à l’exception de la cible et des éventuelles colonnes exclues par la configuration.
- Préparation des données : chargement du CSV, vérification de la présence de la cible, traitement des valeurs manquantes et préparation des variables numériques, catégorielles ou textuelles selon leur nature.
- Découpage : aléatoire, avec 80 % des données pour l’entraînement et 20 % pour le test, selon la configuration initiale du projet.
- Graine aléatoire : 42.

Le fichier et sa structure doivent être vérifiés avant de figer cette section, notamment si la configuration actuelle du projet a été modifiée depuis la première version.

## 5. Métriques, baseline et critères d’acceptation

- Baseline : modèle de référence simple, utilisé pour mesurer les performances minimales à dépasser.
- Résultats de la baseline : accuracy = 0,824 ; recall = 0 ; precision = 0 ; F1-score = 0.
- Métrique principale : recall.
- Justification : le recall mesure la proportion de pannes réelles correctement détectées. Un recall faible signifie que de nombreuses pannes ne sont pas identifiées. Dans un contexte de maintenance, manquer une panne peut être plus coûteux qu’émettre une fausse alerte.
- Métriques secondaires : precision, F1-score et accuracy.
- Critères d’acceptation : le modèle doit dépasser la baseline, atteindre un recall minimal défini avec le responsable de maintenance et conserver un niveau de precision compatible avec la capacité de traitement des alertes.

Le seuil d’acceptation doit être défini avant une utilisation opérationnelle. Il ne peut pas être déterminé uniquement à partir des résultats d’entraînement.

## 6. Architecture prévue

Le système suit les étapes suivantes :

1. Chargement : lecture du fichier de données contenant les observations des équipements.
2. Validation : vérification de la présence de la cible `failure` et des colonnes nécessaires.
3. Préparation : traitement des valeurs manquantes, mise à l’échelle des variables numériques si nécessaire et encodage des variables catégorielles.
4. Découpage : séparation des données en ensembles d’entraînement et de test.
5. Entraînement : apprentissage de plusieurs modèles de classification.
6. Évaluation : calcul de l’accuracy, du recall, de la precision et du F1-score.
7. Sélection : choix du modèle selon le recall et les autres contraintes du projet.
8. Sauvegarde : enregistrement du modèle retenu dans `models/model.joblib` et des métriques dans `models/metrics.json`.
9. Utilisation future : chargement du modèle sauvegardé pour classer de nouvelles observations et signaler les cas présentant un risque de panne.

Si les données représentent une évolution temporelle des équipements, un découpage chronologique devra être envisagé pour éviter qu’une information future ne contribue à prédire une situation passée.

## 7. Choix technologiques

- Python : langage principal.
- Pandas : chargement et manipulation des données.
- Scikit-learn : préparation des données, entraînement, séparation et évaluation des modèles.
- Logistic Regression : modèle de classification linéaire et interprétable servant de référence parmi les modèles entraînés.
- Decision Tree : modèle capable de représenter des règles de décision.
- Random Forest : ensemble d’arbres permettant de capturer des relations plus complexes.
- KNN : modèle fondé sur la proximité entre observations.
- Joblib : sauvegarde du modèle.
- JSON : sauvegarde des métriques.
- Pytest : tests automatisés du chargement des données, du découpage et de l’entraînement.

## 8. Risques, éthique et confidentialité

- Pannes non détectées : un faux négatif peut entraîner une interruption imprévue ou un risque opérationnel.
- Fausses alertes : un nombre excessif de faux positifs peut réduire la confiance des techniciens dans le système.
- Déséquilibre des classes  si les pannes sont rares, l’accuracy peut être élevée sans que les pannes soient correctement détectées.
- Qualité des données : les valeurs manquantes, erreurs de mesure et données peu représentatives peuvent dégrader les performances.
- Évolution des équipements : les performances peuvent diminuer lorsque les conditions de fonctionnement changent.
- Sécurité : le modèle ne doit pas être utilisé comme unique mécanisme de sécurité ni remplacer les contrôles obligatoires.
- Confidentialité : les colonnes du fichier doivent être examinées afin de vérifier qu’aucune donnée personnelle ou information industrielle sensible n’est exposée.
- Traçabilité : les versions des données, du modèle et des métriques doivent être conservées pour faciliter le suivi.

## 9. Limites et hors périmètre

- Les performances dépendent de la qualité et de la représentativité du jeu de données.
- Le recall mesuré sur le jeu de test ne garantit pas la même capacité de détection dans un environnement industriel réel.
- Les résultats ne suffisent pas à démontrer une réduction effective des coûts de maintenance.
- La source et la licence des données doivent être documentées.
- Le projet ne comprend pas nécessairement une connexion directe aux capteurs, une surveillance en temps réel, une intégration à un système de gestion de maintenance ou un mécanisme automatique de planification des interventions.
- Une validation par des spécialistes de la maintenance reste indispensable avant tout déploiement.

Conclusion : le projet vise à assister la maintenance en détectant les observations susceptibles de correspondre à une panne. Le recall est privilégié pour limiter les pannes manquées, mais la sélection finale doit également tenir compte des fausses alertes, des contraintes opérationnelles et de la validation sur des données représentatives.

# Étude de conception — Prédiction du nombre de repas servis à la cantine

Groupe : [G3]  
Version : Brouillon à valider  
Date : 26/10/2026

## 1. Contexte et utilisateurs

- Utilisateur principal : le responsable de la restauration scolaire chargé de planifier les quantités de repas à préparer.
- Utilisateurs secondaires : l’équipe de cuisine et le personnel chargé des achats et de la gestion des stocks.
- Contexte : la fréquentation de la cantine peut varier selon le nombre d’inscrits, le jour de la semaine, le menu, les conditions météorologiques et les événements scolaires.
- Objectif : fournir une estimation du nombre de repas à préparer pour faciliter la planification et réduire les excédents ainsi que les risques de repas insuffisants.

## 2. Problème et décision

- Décision prise avec le système : estimer le nombre de repas à préparer pour une journée donnée, afin d’aider à organiser les achats, les stocks et la production en cuisine.
- Fréquence : quotidienne, avant la préparation des repas.
- Coût d’une surestimation : préparation excessive, gaspillage alimentaire et dépenses inutiles.
- Coût d’une sous-estimation : manque de repas disponibles, insatisfaction des usagers et nécessité d’une préparation supplémentaire.
- Personnes concernées : le responsable de la cantine, l’équipe de cuisine, les usagers et l’établissement.

La prédiction constitue une aide à la décision. Le responsable conserve la possibilité de corriger l’estimation en fonction des informations connues qui ne figurent pas dans les données.

## 3. Approche par sous-problème

| Sous-problème | Approche | Pourquoi ne pas utiliser une approche plus simple ? |
|---|---|---|
| Estimer le nombre de repas servis | Machine Learning supervisé — régression | Une règle fixe ne tient pas suffisamment compte des variations de fréquentation et des facteurs associés. |
| Établir une référence de performance | Baseline | Elle permet de vérifier si les modèles apportent une amélioration réelle par rapport à une référence simple. |
| Comparer les modèles | Ridge, Decision Tree, Random Forest et KNN | La comparaison permet d’évaluer différentes relations entre les variables et la cible. |
| Évaluer les prédictions | MAE, RMSE et R² | Ces métriques mesurent respectivement l’erreur absolue moyenne, pénalisent davantage les grandes erreurs et indiquent la part de variance expliquée par le modèle. |
| Produire une estimation utilisable | Pipeline de préparation et modèle sauvegardé | Un traitement reproductible facilite les futures prédictions et évite de reconstruire manuellement les étapes. |

Une approche de Deep Learning ou de LLM n’est pas nécessaire à ce stade : le problème porte sur la prédiction d’une valeur numérique à partir d’un jeu de données tabulaire de taille limitée.

## 4. Données

| Jeu de données | Source et licence | Volume | Données personnelles ? |
|---|---|---|---|
| `cantine_repas.csv` | Fichier CSV fourni pour le projet ; source initiale et licence à confirmer | 340 lignes, 11 colonnes | Aucune donnée personnelle directement identifiable n’apparaît dans les colonnes examinées. |

### Variables utilisées

- `jour` : jour de la semaine.
- `inscrits` : nombre d’inscrits.
- `menu` : catégorie du menu proposé.
- `temperature_c` : température.
- `pluie_mm` : quantité de pluie.
- `examens` : indicateur d’examens.
- `sortie_scolaire` : indicateur de sortie scolaire.
- `veille_vacances` : indicateur de veille de vacances.
- `repas_semaine_precedente` : nombre de repas servis lors de la période de référence précédente.
- Cible : `repas_servis`.

La colonne `date` est utilisée pour ordonner chronologiquement les observations et séparer l’entraînement du test. Elle n’est pas utilisée directement comme variable explicative dans la configuration actuelle.

Le fichier contient des valeurs manquantes dans `repas_semaine_precedente`. Leur traitement doit être assuré par la préparation des données et contrôlé avant toute mise en production.

## 5. Métriques, baseline et critères d’acceptation

- Baseline : modèle de référence sans apprentissage prédictif avancé.
- Score de la baseline : MAE = 70,271 ; RMSE = 88,416 ; R² = -0,151.
- Métrique principale : MAE (Mean Absolute Error).
- Justification : la MAE s’exprime dans la même unité que la cible, c’est-à-dire en nombre de repas. Elle permet au responsable de comprendre directement l’écart moyen entre les prédictions et les valeurs observées. Plus elle est faible, mieux c’est.
- Métriques secondaires : RMSE, qui pénalise davantage les erreurs importantes, et R², qui évalue la qualité explicative du modèle sur le jeu de test.
- Résultat du modèle retenu : Ridge obtient une MAE de 22,623, une RMSE de 28,545 et un R² de 0,880.
- Amélioration par rapport à la baseline : réduction de la MAE d’environ 67,8 %.

### Critères d’acceptation proposés

1. Le modèle doit être évalué sur des données plus récentes que celles utilisées pour l’entraînement, au moyen d’un découpage chronologique.
2. La MAE du modèle doit être inférieure à celle de la baseline.
3. Le responsable de la cantine doit définir une erreur moyenne maximale acceptable en nombre de repas.
4. Les performances doivent être vérifiées sur plusieurs périodes, notamment celles présentant des variations importantes de fréquentation.
5. Les valeurs manquantes et les éventuelles anomalies doivent être traitées de manière documentée et reproductible.

Statut : les deux premiers critères sont satisfaits par les résultats actuels. Le seuil opérationnel de MAE et la validation sur plusieurs périodes restent à définir ou à réaliser.

## 6. Architecture prévue

Le système suit le processus suivant :

1. **Chargement des données :** lecture du fichier `data/cantine_repas.csv`.
2. Validation : vérification de la présence de la cible `repas_servis` et des colonnes nécessaires.
3. Préparation : traitement des valeurs manquantes et transformation des variables catégorielles ou numériques selon le pipeline.
4. Découpage chronologique : utilisation des premières observations pour l’entraînement et des observations les plus récentes pour le test.
5. Entraînement : comparaison de la baseline, de Ridge, de Decision Tree, de Random Forest et de KNN.
6. Évaluation : calcul de la MAE, de la RMSE et du R² sur le jeu de test.
7. Sélection : choix du modèle présentant la plus faible MAE.
8. Sauvegarde : enregistrement du modèle dans `models/model.joblib` et des métriques dans `models/metrics.json`.
9. **Utilisation future :** chargement du modèle sauvegardé pour estimer le nombre de repas à partir des informations disponibles avant le service.

Le système ne doit utiliser que des informations réellement disponibles au moment où la prédiction est effectuée. Les variables qui ne seraient connues qu’après le service ne doivent pas être utilisées pour prédire les repas à préparer.

## 7. Choix technologiques

- Python : langage de développement du projet.
- Pandas : chargement et manipulation des données tabulaires.
- Scikit-learn : préparation des données, entraînement, séparation des données et évaluation des modèles.
- *Ridge Regression : modèle retenu à ce stade, car il obtient la meilleure MAE parmi les modèles testés.
- Joblib : sauvegarde du modèle entraîné.
- CSV : format de stockage des données d’entrée.
- JSON : format de sauvegarde des métriques.
- Pytest : tests automatisés du chargement des données, du découpage et de l’entraînement.

## 8. Risques, éthique et confidentialité

- Qualité des données : des données incomplètes ou incorrectes peuvent dégrader les prédictions.
- Évolution des habitudes : les performances peuvent diminuer si la fréquentation, les menus ou le calendrier changent.
- Erreurs de prévision : le modèle peut surestimer ou sous-estimer les quantités nécessaires. Une vérification humaine reste nécessaire.
- Gaspillage alimentaire : les prédictions doivent contribuer à réduire les excédents sans entraîner systématiquement des quantités insuffisantes.
- Confidentialité : le fichier examiné ne semble pas contenir de données directement identifiantes. Cette vérification devra être renouvelée si de nouvelles sources sont ajoutées.
- Traçabilité : la version des données, les métriques et le modèle retenu doivent être conservés pour faciliter le suivi.
- Biais et représentativité : les observations disponibles peuvent ne pas couvrir tous les types de journées ou toutes les situations exceptionnelles.

## 9. Limites et hors périmètre

- Le projet utilise 340 observations, ce qui limite la diversité des situations observées.
- Le jeu de test représente 68 observations ; les résultats ne garantissent pas les mêmes performances sur toutes les périodes futures.
- Le jeu de données comporte 60 valeurs manquantes dans la variable `repas_semaine_precedente`.
- La source initiale et la licence du jeu de données doivent être précisées.
- Les résultats actuels ne prouvent pas encore la performance du modèle en fonctionnement réel.
- Le projet ne comprend pas, à ce stade, une application web, une intégration au système de gestion de la cantine, une optimisation automatique des achats ni un mécanisme de réentraînement en production.
- Le modèle fournit une estimation et ne remplace pas la décision du responsable de la cantine.

Conclusion : le modèle Ridge est le meilleur des modèles évalués sur le jeu de test chronologique. Il réduit nettement l’erreur par rapport à la baseline. Avant une utilisation opérationnelle, il reste nécessaire de définir un seuil d’erreur acceptable, de documenter la provenance des données et de vérifier les performances sur de nouvelles périodes.
