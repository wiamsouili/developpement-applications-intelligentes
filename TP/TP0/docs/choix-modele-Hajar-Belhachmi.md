# Choix du modèle : prédiction des pannes industrielles 

Date :** 26/10/2026
Réalisée par : BELHACHMI Hajar

## 1. Contexte

**Objectif :** choisir, parmi plusieurs modèles d'apprentissage automatique, celui qui détecte le mieux les machines susceptibles de tomber en panne, à partir de leurs données de fonctionnement.

**Type de problème :** classification binaire. La variable cible `failure` vaut 0 (absence de panne) ou 1 (panne). Ces deux valeurs ont été vérifiées dans le fichier.

**Décision à prendre :** retenir le modèle le plus pertinent pour détecter les pannes, en privilégiant le rappel (*recall*), car une panne non détectée coûte plus cher qu'une inspection inutile.

## 2. Données et découpage

- **Fichier de données :** `data/exemple_pannes.csv`, 5 000 observations, aucune valeur manquante.
- **Variable cible :** `failure`.
- **Variables explicatives (4) :** `temperature_c` (température, °C), `vibration_mm_s` (vibrations, mm/s), `load_pct` (charge, %) et `runtime_hours` (heures de fonctionnement).
- **Répartition des classes :** 4 122 observations sans panne (82,4 %) et 878 avec panne (17,6 %). Les classes sont déséquilibrées.
- **Découpage :** 80 % entraînement (4 000 observations) et 20 % test (1 000 observations), aléatoire et stratifié pour conserver la proportion de pannes, avec la graine 42. Le test contient 176 pannes. Le fichier n'a pas de colonne de date, un découpage chronologique n'était donc pas possible.
- **Préparation :** imputation par la médiane puis standardisation, apprises sur l'entraînement seulement et intégrées au pipeline de chaque modèle.
- **Métrique principale :** recall de la classe « panne ».
- **Métriques complémentaires :** accuracy, précision et F1-score.

## 3. Résultats sur l'ensemble de test

| Modèle | Accuracy | Recall | Précision | F1-score |
|---|---:|---:|---:|---:|
| Baseline | 0,824 | 0,000 | 0,000 | 0,000 |
| Régression logistique | 0,889 | 0,574 | 0,737 | 0,645 |
| Arbre de décision | 0,839 | 0,597 | 0,538 | 0,566 |
| Random Forest | 0,873 | 0,545 | 0,671 | 0,602 |
| KNN | 0,878 | 0,540 | 0,699 | 0,609 |

La baseline prédit toujours « pas de panne ». Elle obtient 82,4 % d'accuracy, qui correspond simplement à la part des machines sans panne, mais son recall est nul : elle ne détecte aucune panne. L'accuracy seule ne suffit donc pas à évaluer le système.

L'arbre de décision obtient le meilleur recall (0,597). La régression logistique obtient la meilleure accuracy (0,889), la meilleure précision (0,737) et le meilleur F1-score (0,645).

## 4. Analyse

### 4.1 Matrice de confusion des deux modèles en tête

| | Arbre de décision | Régression logistique |
|---|---:|---:|
| Pannes détectées (vrais positifs) | 105 | 101 |
| Pannes manquées (faux négatifs) | 71 | 75 |
| Fausses alertes (faux positifs) | 90 | 36 |
| Machines saines bien classées (vrais négatifs) | 734 | 788 |

L'avantage de l'arbre sur la régression logistique est de 4 pannes détectées de plus (recall de 0,597 contre 0,574), mais il déclenche 54 fausses alertes de plus (90 contre 36). Cet écart de recall est faible sur un jeu de test de 176 pannes : il ne permet pas d'affirmer que l'arbre est durablement meilleur.

### 4.2 Contribution des variables

L'étude de conception prévoyait de considérer la charge comme variable principale. Les mesures ne confirment pas cette hypothèse. Comparaison sur le même découpage, avec la régression logistique et l'arbre de décision :

| Variables utilisées | Modèle | Accuracy | Recall | Précision | F1-score |
|---|---|---:|---:|---:|---:|
| Charge seule | Régression logistique | 0,824 | 0,000 | 0,000 | 0,000 |
| Charge seule | Arbre de décision | 0,811 | 0,040 | 0,259 | 0,069 |
| Charge, température, vibrations | Régression logistique | 0,888 | 0,534 | 0,758 | 0,627 |
| Charge, température, vibrations | Arbre de décision | 0,831 | 0,540 | 0,519 | 0,529 |
| Les 4 variables | Régression logistique | 0,889 | 0,574 | 0,737 | 0,645 |
| Les 4 variables | Arbre de décision | 0,839 | 0,597 | 0,538 | 0,566 |

- Avec la charge seule, les modèles ne détectent presque aucune panne (recall de 0 et de 0,04), à peine mieux que la baseline.
- Ajouter la température et les vibrations fait passer le recall à environ 0,53 et 0,54.
- Ajouter les heures de fonctionnement apporte un gain supplémentaire de 0,04 à 0,06 de recall.
- À titre descriptif, la corrélation linéaire de chaque variable avec `failure`, calculée sur l'ensemble du fichier, est de 0,56 pour les vibrations, 0,21 pour la température, 0,15 pour la charge et 0,14 pour les heures de fonctionnement. Les vibrations sont la variable la plus liée aux pannes dans ces données.

Ces résultats viennent d'un seul découpage et de réglages par défaut : ils indiquent une tendance et non une mesure précise.

## 5. Décision

Selon la métrique principale retenue, **l'arbre de décision est le meilleur des quatre modèles évalués face à la baseline**, avec un recall de 0,597. Il détecte 105 des 176 pannes du jeu de test.

Le gain de recall par rapport à la baseline est de **59,7 points de pourcentage** (0,597 contre 0).

Ce résultat reste insuffisant pour un usage industriel réel : le modèle manque 71 pannes sur 176, soit environ 40,3 % des pannes réelles, et il émet 90 fausses alertes pour 105 détections (précision de 0,538).

Si l'équipe de maintenance juge les fausses alertes trop coûteuses, la régression logistique est une alternative défendable : son recall est proche (0,574) et sa précision est nettement meilleure (0,737). Le choix final dépend du coût relatif d'une panne manquée et d'une inspection inutile, que le jeu de données ne permet pas de chiffrer.

## 6. Critères d'acceptation

Les critères sont ceux de l'étude de conception.

| Critère | Résultat | Statut |
|---|---|---|
| 1. Recall supérieur à celui de la baseline sur un jeu de test indépendant | 0,597 contre 0,000 | Atteint |
| 2. Recall d'au moins 80 % | 0,597 | Non atteint |
| 3. Précision et fausses alertes maîtrisées | Précision de 0,538, soit 90 fausses alertes pour 105 détections | Partiellement atteint |
| 4. Découpage chronologique pour des données temporelles | Pas de colonne de date, découpage aléatoire | Non applicable |
| 5. Comparaison charge seule et trois variables | Voir le tableau du paragraphe 4.2 : les capteurs complémentaires apportent l'essentiel du recall | Réalisé |

**Bilan :** le modèle est meilleur que la baseline, mais l'objectif de recall de 80 % n'est pas atteint. Le modèle n'est donc pas validé pour une utilisation opérationnelle.

## 7. Limites et suites

Les résultats dépendent de la qualité et de la représentativité du jeu de données, de la répartition des classes et du découpage. Le fichier est un jeu d'exemple dont l'origine n'est pas documentée : les performances sur des machines réelles peuvent être différentes. Les modèles utilisent leurs réglages par défaut et un seul découpage a été évalué.

Avant toute utilisation, il est recommandé de :

- ajuster le seuil de décision ou pondérer la classe « panne » pour augmenter le recall, en mesurant l'effet sur le nombre de fausses alertes ;
- régler les hyperparamètres par validation croisée, afin de vérifier que l'écart entre l'arbre de décision et la régression logistique n'est pas dû au découpage ;
- valider le modèle sur des données horodatées et représentatives des conditions industrielles réelles ;
- fixer le seuil de recall acceptable avec le responsable de maintenance, en fonction du coût des pannes manquées et des fausses alertes.

**Conclusion :** l'arbre de décision est retenu comme meilleur candidat selon le recall (0,597), mais l'écart avec la régression logistique est faible. Ce choix reste provisoire : l'objectif de 80 % de recall n'est pas atteint, et le modèle doit être amélioré et validé sur des données adaptées avant d'aider réellement la maintenance.



#

# Choix du modèle : prévision du nombre de repas à la cantine

**Date :** 24/10/2026
**Réalisé par : BELHACHMI Hajar

## 1. Contexte

**Objectif :** choisir, parmi plusieurs modèles de régression, celui qui prévoit le mieux le nombre de repas servis un jour donné, afin d'aider le gestionnaire de la cantine à commander à la cuisine le bon nombre de repas.

**Type de problème :** régression sur une série temporelle. La cible `repas_servis` est un nombre, de 248 à 695 repas.

**Décision à prendre :** retenir le modèle qui se trompe le moins, en moyenne, sur les jours les plus récents, et vérifier qu'il fait nettement mieux que la méthode actuelle (reprendre le chiffre du même jour de la semaine précédente).

## 2. Données et découpage

- **Fichier de données :** `data/cantine_repas.csv`, 340 jours d'école du 09/09/2024 au 19/06/2026, données synthétiques.
- **Variable cible :** `repas_servis`.
- **Variables explicatives (9) :** `jour`, `inscrits`, `menu`, `temperature_c`, `pluie_mm`, `examens`, `sortie_scolaire`, `veille_vacances` et `repas_semaine_precedente`. La colonne `date` sert au tri et n'est pas donnée aux modèles.
- **Découpage chronologique :** 272 jours d'entraînement (du 09/09/2024 au 24/02/2026) et 68 jours de test (du 25/02/2026 au 19/06/2026). Tout le test est postérieur à l'entraînement. Le test contient 10 jours d'examens, 4 jours de sortie scolaire et 2 veilles de vacances.
- **Préparation :** imputation par la médiane puis standardisation pour les nombres, imputation puis encodage one-hot pour `jour` et `menu`. Elle est apprise sur l'entraînement seulement et fait partie du pipeline de chaque modèle. Les 10 valeurs manquantes de `repas_semaine_precedente` dans le test sont remplacées par la médiane de l'entraînement.
- **Métrique principale :** MAE, en repas.
- **Métriques complémentaires :** RMSE et R2.

## 3. Résultats sur l'ensemble de test

| Modèle | MAE (repas) | RMSE (repas) | R2 |
|---|---:|---:|---:|
| Baseline (moyenne) | 70,3 | 88,4 | -0,151 |
| Régression linéaire | 22,2 | 28,2 | 0,883 |
| Arbre de décision | 46,0 | 59,7 | 0,475 |
| Random Forest | 31,8 | 41,5 | 0,746 |
| KNN | 36,2 | 46,0 | 0,688 |

La baseline prédit toujours la moyenne de l'entraînement (492,6 repas). Elle a un R2 négatif, c'est-à-dire qu'elle est moins bonne qu'une prédiction constante égale à la moyenne du test : le niveau moyen de repas a augmenté entre l'entraînement (493) et le test (525).

La régression linéaire obtient les meilleurs résultats sur les trois métriques. Elle est suivie de la Random Forest, du KNN puis de l'arbre de décision.

### 3.1 Comparaison avec la méthode actuelle

La méthode actuelle n'existe que pour 58 des 68 jours du test (elle est vide après des vacances). La comparaison porte sur ces 58 jours.

| Méthode | MAE (repas) |
|---|---:|
| Reprise de la semaine précédente (méthode actuelle) | 79,0 |
| Baseline (moyenne) | 72,3 |
| Régression linéaire | 23,4 |
| Random Forest | 32,9 |
| KNN | 36,7 |
| Arbre de décision | 44,8 |

La méthode actuelle est moins bonne que la simple moyenne. Elle reproduit un chiffre qui peut être faussé par un événement de la semaine précédente (examens, sortie, menu différent). La régression linéaire réduit son erreur moyenne d'environ 70 % (23,4 contre 79,0).

## 4. Analyse

### 4.1 Erreurs de la régression linéaire sur le test

- L'erreur absolue moyenne est de 22,2 repas ; l'erreur maximale est de 68,8 repas.
- 48 jours sur 68 ont une erreur d'au plus 30 repas, et 6 jours ont une erreur supérieure à 50 repas.
- L'erreur moyenne signée est de -8,5 repas : le modèle prévoit en moyenne 8,5 repas de moins que le nombre réel, donc il tend à sous-estimer.

Estimation des repas en trop et manquants si le gestionnaire commandait exactement la prévision, sur les 58 jours où la comparaison est possible :

| Commande | Repas en trop par jour | Repas manquants par jour | Coût des repas en trop (15 DH par repas) |
|---|---:|---:|---:|
| Régression linéaire | 7,0 | 16,3 | environ 106 DH par jour |
| Reprise de la semaine précédente | 39,4 | 39,6 | environ 591 DH par jour |

Le modèle réduit à la fois les repas jetés et les repas manquants. Le coût indiqué ne compte que la matière première perdue : le coût des repas manquants n'étant pas chiffré, il n'est pas inclus. Comme le modèle manque plus de repas qu'il n'en jette, une marge de sécurité ajoutée à la prévision serait à étudier.

### 4.2 Pourquoi la régression linéaire est la meilleure

Le coefficient de la régression linéaire indique, toutes choses égales par ailleurs, l'effet de chaque variable en repas :

- une période d'examens : environ 110 repas de moins ;
- une sortie scolaire d'un niveau : environ 91 repas de moins ;
- la veille de vacances : environ 147 repas de moins ;
- le menu : le couscous donne environ 95 repas de plus que le poisson ;
- le jour : le mercredi donne environ 67 repas de moins que le lundi, le vendredi environ 41 de plus ;
- chaque inscrit supplémentaire : environ 0,7 repas de plus ; chaque millimètre de pluie prévu : environ 2 repas de plus.

Ces valeurs sont indicatives (réglages par défaut, un seul découpage). Elles concordent avec les moyennes brutes du fichier : 513 repas hors examens contre 394 pendant les examens, 566 pour le couscous contre 424 pour le poisson, 431 le mercredi contre 566 le vendredi.

Deux raisons expliquent probablement l'avantage de la régression linéaire sur les modèles à arbres et sur le KNN. D'abord, les effets sont additifs : chaque facteur retranche ou ajoute un nombre de repas à peu près fixe. Ensuite, le nombre d'inscrits augmente dans le temps (650 en moyenne à l'entraînement, 694 au test) : un arbre, une forêt ou un KNN ne peuvent prévoir que des valeurs déjà vues à l'entraînement, alors qu'une droite prolonge la tendance. Le fait que les données soient synthétiques peut aussi favoriser le modèle linéaire.

### 4.3 Effet du découpage

À titre de contrôle, les mêmes modèles ont été évalués avec un tirage au hasard des jours de test. La MAE y est plus basse : 18,3 repas pour la régression linéaire (22,2 en chronologique), 24,1 pour la Random Forest (31,8), 27,7 pour le KNN (36,2) et 36,1 pour l'arbre de décision (46,0). Le tirage au hasard donne donc des résultats trop optimistes, d'où le choix du découpage chronologique.

## 5. Décision

**La régression linéaire est retenue**, avec une MAE de 22,2 repas sur le test chronologique. Elle bat la baseline (70,3), la méthode actuelle (79,0 contre 23,4 sur les mêmes jours) et les trois autres modèles. Elle est aussi la plus simple et la plus facile à expliquer au gestionnaire.

## 6. Critère d'acceptation

Critère de l'étude de conception : une MAE d'au plus 30 repas sur le jeu de test chronologique (68 derniers jours), et inférieure à la moitié de la MAE de la reprise de la semaine précédente sur les mêmes jours.

| Condition | Résultat | Statut |
|---|---|---|
| MAE d'au plus 30 repas sur les 68 jours du test | 22,2 repas | Atteint |
| MAE inférieure à la moitié de celle de la méthode actuelle sur les mêmes jours | 23,4 contre 79,0 : moitié de 79,0 = 39,5 | Atteint |

**Bilan :** le critère est atteint. Cela vaut pour ces données synthétiques ; il faut le confirmer sur des données réelles avant de remplacer la méthode actuelle.

## 7. Limites et suites

- Les données sont synthétiques et leur structure est peut-être plus simple que celle d'une vraie cantine.
- Le test porte sur 68 jours, d'une seule période (février à juin 2026), et contient peu de jours d'examens, de sorties et de veilles de vacances.
- Les modèles utilisent leurs réglages par défaut, avec un seul découpage : l'écart entre la Random Forest et la régression linéaire pourrait changer avec un réglage ou une validation croisée temporelle.
- Le modèle sous-estime en moyenne de 8,5 repas : il faut chiffrer le coût d'un repas manquant et décider d'une marge de sécurité avec le gestionnaire.
- L'effectif d'inscrits évolue : le modèle doit être réentraîné régulièrement.

Avant toute utilisation, il est recommandé de :

- chiffrer le coût d'un repas manquant et ajuster la commande en conséquence ;
- valider le modèle avec une validation croisée temporelle (`TimeSeriesSplit`) ;
- comparer le modèle à la méthode actuelle sur plusieurs semaines réelles ;
- réentraîner le modèle à chaque rentrée et à chaque changement important d'effectif.

**Conclusion :** la régression linéaire est retenue (MAE de 22,2 repas) et le critère d'acceptation est atteint sur les données du cours. Ce résultat reste à confirmer sur des données réelles avant de remplacer la méthode actuelle.
