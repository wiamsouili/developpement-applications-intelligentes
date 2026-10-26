# Choix du modèle

Date : [26/10/2026] · Groupe : [G3]

## Contexte
[Le projet consiste à développer un modèle de Machine Learning capable de prédire la variable cible à partir des données disponibles. Plusieurs algorithmes sont évalués afin de sélectionner celui qui répond le mieux au besoin métier.

La métrique principale retenue est le recall (rappel), car il mesure la proportion de cas réellement positifs correctement détectés par le modèle. Cette métrique est particulièrement pertinente lorsque manquer un cas positif peut avoir des conséquences importantes. Ce choix doit être confirmé par l'analyse du besoin métier présentée dans la section 5 de l'étude de conception.]

## Données et découpage
[Fichier de données : [data/exemple_pannes.csv]
Nombre de lignes : [5000]
Variable cible : [failure]
Colonnes utilisées : [temperature_c,vibration_mm_s,load_pct,runtime_hours]
Méthode de découpage : [aléatoire ]
Taille du jeu de test : [20 % des données après suppression des lignes dont la cible est manquante]]

## Résultats sur le jeu de test

| Modèle   | Recall | accuracy | precision | F1
| Baseline |0,000   |  0.824   |0,000      |0,000 
| knn      |0.540   |0.878     | 0.699     |0.609 
|random_forest|  0.545|0.873   | 0.671     |0.602           
logistic_regression|0.889| 0.574 | 0.737 | 0.645 
decision_tree 0.597| 0.839 | 0.538|  0.566

## Décision
[Le modèle retenu selon la métrique principale est l'arbre de décision (Decision Tree), avec un recall de 0,597, soit 59,7 % des cas positifs correctement détectés sur le jeu de test.

Il dépasse la baseline de 59,7 points de pourcentage en recall (de 0,000 à 0,597). La baseline présente une accuracy de 82,4 %, mais un recall nul : elle ne détecte aucun cas positif. Elle constitue donc une référence insuffisante pour le besoin de détection.

La régression logistique obtient toutefois les meilleurs résultats en accuracy (88,9 %), en precision (73,7 %) et en F1-score (64,5 %). L'arbre de décision est donc retenu uniquement si la priorité donnée au recall est confirmée par le besoin métier.?]

## Limites
[La taille du jeu de test n'est pas indiquée dans les résultats fournis ; la stabilité des scores reste donc à vérifier.

Les résultats dépendent du découpage des données, de la qualité des variables et du traitement des valeurs manquantes.

Le recall de 59,7 % signifie que 40,3 % des cas positifs du jeu de test ne sont pas détectés.

La precision de 53,8 % indique qu'une partie importante des prédictions positives de l'arbre de décision est incorrecte.

Les performances globales ne garantissent pas des résultats satisfaisants pour tous les profils ou toutes les catégories de données.

Une validation supplémentaire et une analyse de la matrice de confusion sont nécessaires avant une utilisation en conditions réelles.]
                                                                                                                                                                             








                                                                                                                    
                                                                                                                    
                                                                                                                    
                                                                                                                    
                                                                                                                    
                                                                 # Choix dumodèle

Date : [26/10/2026] · Groupe : [G3]

## Contexte
[Le projet vise à prédire le nombre de repas qui seront servis à la cantine afin d’aider le responsable à mieux planifier les quantités à préparer et à limiter le gaspillage alimentaire. Il s’agit d’un problème de régression supervisée à partir de variables telles que le nombre d’inscrits, le menu, la météo et les informations relatives aux jours précédents.

La métrique principale retenue est la MAE (Mean Absolute Error), car elle mesure l’écart absolu moyen entre le nombre de repas réellement servis et le nombre prédit. Elle est facile à interpréter en nombre de repas et une valeur plus faible indique de meilleures prédictions.]

## Données et découpage
Fichier : data/cantine_repas.csv

Volume : 340 lignes et 11 colonnes.

Période couverte : du 09/09/2024 au 19/06/2026.

Variable cible : repas_servis.

Variables explicatives : jour, inscrits, menu, temperature_c, pluie_mm, examens, sortie_scolaire, veille_vacances et repas_semaine_precedente.

Découpage : chronologique, avec les premières observations utilisées pour l’entraînement et les observations les plus récentes réservées au test.

Taille du jeu de test : 68 lignes, soit 20 % du jeu de données.

## Résultats sur le jeu de test

| Modèle   | Recall | accuracy | precision | F1
                  mae    rmse     r2
ridge          22.623  28.545  0.880
random_forest  31.845  41.540  0.746
knn            36.212  46.037  0.688
decision_tree  46.000  59.710  0.475
baseline       70.271  88.416 -0.151

## Décision
[Le modèle Ridge est retenu, car il obtient les meilleurs résultats parmi les modèles évalués : une MAE de 22,623 repas, une RMSE de 28,545 repas et un coefficient de détermination R² de 0,880.

Par rapport à la baseline, la MAE diminue de 47,648 repas, soit une réduction d’environ 67,8 %. Le modèle Ridge présente donc une amélioration importante sur le jeu de test.

Le critère d’acceptation formel n’ayant pas encore été précisé, il n’est pas possible d’affirmer qu’un seuil d’acceptation prédéfini est atteint. Un seuil opérationnel doit être fixé avec le responsable de la cantine, en fonction de la marge d’erreur acceptable pour la préparation des repas.

Le modèle entraîné est sauvegardé dans models/model.joblib et les métriques sont enregistrées dans models/metrics.json.]

## Limites
[Le jeu de test contient 68 observations ; les résultats peuvent varier sur une autre période.

La colonne repas_semaine_precedente comporte 60 valeurs manquantes dans le fichier complet. Le traitement de ces valeurs doit être vérifié et documenté.

Les résultats ne garantissent pas les mêmes performances lors de changements inhabituels de menu, de météo, d’effectifs ou de calendrier scolaire.

La MAE représente une erreur moyenne : elle ne renseigne pas à elle seule sur les erreurs les plus importantes ni sur les jours où le modèle se trompe le plus.

La provenance précise du jeu de données et sa licence restent à documenter.

Les résultats doivent être réévalués sur de nouvelles données avant une utilisation opérationnelle régulière.]
