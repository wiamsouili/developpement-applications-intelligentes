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
