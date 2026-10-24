# Choix du modèle : prédiction des pannes industrielles par apprentissage automatique

**Date :** 24/10/2026
**Réalisé par le groupe 3 :** SOUILI Wiam, ELAOUAZI Hafsa, YEKHLEF Aya, BELHACHMI Hajar

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
