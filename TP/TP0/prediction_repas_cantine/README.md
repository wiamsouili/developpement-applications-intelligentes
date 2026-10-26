# CantineAI : prévoir le nombre de repas à la cantine

Réalisée par : BELHACHMI Hajar

Ce projet prévoit le nombre de repas servis à la cantine d'un lycée (environ 650 élèves inscrits) pour un jour donné, à partir de ce que le gestionnaire sait la veille : le menu, la météo prévue, le calendrier des examens et des sorties scolaires. Il remplace la méthode actuelle, qui consiste à reprendre le chiffre du même jour de la semaine précédente. C'est une régression sur une série temporelle.

## 1. Résumé

| Élément | Contenu |
|---|---|
| Problème | Régression : prédire `repas_servis`, un nombre de repas par jour |
| Utilisateur | Le gestionnaire de la cantine, qui commande les repas à la cuisine chaque jour à 10 h |
| Données | `data/cantine_repas.csv` : 340 jours d'école (09/09/2024 au 19/06/2026), 9 variables d'entrée, données synthétiques générées pour le cours |
| Découpage | Chronologique : 272 jours d'entraînement (jusqu'au 24/02/2026), 68 jours de test (du 25/02/2026 au 19/06/2026) |
| Métrique principale | MAE, l'erreur absolue moyenne, exprimée en repas |
| Modèles comparés | Baseline (moyenne), régression linéaire, arbre de décision, Random Forest, KNN |
| Modèle retenu | Régression linéaire : MAE de 22,2 repas sur le test |
| Méthode actuelle | Reprise de la semaine précédente : MAE de 79,0 repas sur les 58 jours du test où elle existe |
| Critère d'acceptation | MAE d'au plus 30 repas et inférieure à la moitié de celle de la méthode actuelle : **atteint** |

## 2. Données

| Variable | Signification | Valeurs |
|---|---|---|
| `date` | Le jour d'école (sert au découpage, pas au modèle) | 2024-09-09 à 2026-06-19 |
| `jour` | Jour de la semaine | lundi à vendredi |
| `inscrits` | Élèves inscrits à la cantine | 620 à 697 |
| `menu` | Plat principal | poulet, viande, poisson, végétarien, couscous |
| `temperature_c` | Température prévue (°C) | 3,8 à 32,1 |
| `pluie_mm` | Pluie prévue (mm) | 0 à 28,2 |
| `examens` | Période d'examens | 0 ou 1 |
| `sortie_scolaire` | Un niveau entier est en sortie | 0 ou 1 |
| `veille_vacances` | Dernier jour avant des vacances | 0 ou 1 |
| `repas_semaine_precedente` | Repas servis le même jour, une semaine avant | 248 à 695, vide pour 60 jours |
| `repas_servis` | **Cible** : repas servis ce jour-là | 248 à 695 |

Toutes les variables d'entrée sont connues la veille, au moment de la commande : le modèle n'utilise aucune information postérieure au jour à prévoir.

Les 60 valeurs manquantes de `repas_semaine_precedente` correspondent à la première semaine d'école et à la semaine qui suit chaque période de vacances. Elles sont remplacées par la médiane de l'entraînement dans le pipeline.

## 3. Organisation du projet

```
prediction_repas_cantine/
├── data/
│   └── cantine_repas.csv         Jeu de données
├── docs/
│   ├── etude-de-conception.md    Cadrage : utilisateur, décision, coût des erreurs, métriques, risques
│   ├── choix-modele.md           Résultats, modèle retenu, bilan du critère d'acceptation
│   └── grille-seance-3.md        Grille de la séance 3 : sections 1 à 5, réglages, question finale
├── monprojet/
│   ├── config.py                 Réglages : fichier, cible, tâche, métrique, découpage
│   ├── data.py                   load_data(), feature_columns(), split()
│   ├── models.py                 candidates() : la baseline puis quatre modèles
│   └── train.py                  evaluate(), comparer_a_la_reference(), main()
├── tests/                        8 tests pytest (données, modèles, entraînement)
├── models/                       Produit par l'entraînement (ignoré par git)
│   ├── model.joblib              Meilleur modèle selon la métrique principale
│   └── metrics.json              Métrique principale, meilleur modèle, scores, comparaison à la méthode actuelle
├── requirements.txt              Versions des bibliothèques
├── pytest.ini                    Configuration des tests
└── README.md
```

## 4. Installation

Depuis la racine du projet :

```
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows ; macOS/Linux : source .venv/bin/activate
pip install -r requirements.txt
```

Bibliothèques : numpy 2.4.4, pandas 3.0.2, scikit-learn 1.8.0, joblib 1.5.3, pytest 9.1.1.

## 5. Utilisation

**Lancer les tests :**

```
python -m pytest
```

Résultat attendu : `8 passed`.

**Entraîner et comparer les modèles :**

```
python -m monprojet.train
```

La commande affiche le tableau de comparaison classé par MAE, le meilleur modèle, puis la comparaison avec la méthode actuelle sur les mêmes jours. Elle écrit `models/model.joblib` et `models/metrics.json`. Ces fichiers sont ignorés par git : il faut relancer l'entraînement après un clonage du dépôt.

**Prévoir les repas d'un jour :**

```python
import joblib
import pandas as pd

modele = joblib.load("models/model.joblib")
demain = pd.DataFrame([{
    "jour": "jeudi",
    "inscrits": 690,
    "menu": "couscous",
    "temperature_c": 18.0,
    "pluie_mm": 0.0,
    "examens": 0,
    "sortie_scolaire": 0,
    "veille_vacances": 0,
    "repas_semaine_precedente": 540,
}])
print(round(modele.predict(demain)[0]))   # nombre de repas à commander
```

Le pipeline sauvegardé contient la préparation des données (imputation, standardisation, encodage des catégories) : il reçoit les valeurs brutes. La colonne `date` ne doit pas être fournie. `repas_semaine_precedente` peut être laissée vide (`None`) après des vacances.

## 6. Configuration

Tous les réglages sont dans `monprojet/config.py` :

| Paramètre | Valeur actuelle | Rôle |
|---|---|---|
| `DATA_PATH` | `data/cantine_repas.csv` | Fichier CSV à charger |
| `TARGET` | `repas_servis` | Colonne à prédire |
| `TASK` | `regression` | `classification` ou `regression` |
| `MAIN_METRIC` | `mae` | Métrique qui désigne le meilleur modèle |
| `METRICS` | `mae`, `rmse`, `r2` | Métriques calculées |
| `SPLIT` | `chronologique` | Type de découpage |
| `TIME_COLUMN` | `date` | Colonne de date, utilisée pour trier les jours |
| `TEST_SIZE` | 0,2 | Part des derniers jours réservée au test |
| `SEED` | 42 | Graine, utilisée par les modèles aléatoires |
| `REFERENCE_COLUMN` | `repas_semaine_precedente` | Prévision de la méthode actuelle, pour la comparaison |

## 7. Méthode

1. `load_data()` lit le CSV, vérifie la présence de la cible et de la colonne de date, et supprime les lignes sans cible.
2. `split()` trie les jours du plus ancien au plus récent : les 80 % les plus anciens servent à l'entraînement, les 20 % les plus récents au test. Aucun jour du test n'est antérieur à l'entraînement.
3. Chaque modèle est placé dans un pipeline : imputation par la médiane puis standardisation pour les nombres, imputation puis encodage one-hot pour `jour` et `menu`. La préparation est apprise sur l'entraînement uniquement.
4. `evaluate()` calcule MAE, RMSE et R2 sur le test.
5. `comparer_a_la_reference()` mesure la MAE de la méthode actuelle et celle de chaque modèle sur les jours du test où la méthode actuelle existe.
6. `main()` classe les modèles selon la MAE (la plus basse est la meilleure) et sauvegarde le meilleur.

## 8. Résultats sur le jeu de test (68 derniers jours)

| Modèle | MAE (repas) | RMSE (repas) | R2 |
|---|---:|---:|---:|
| Baseline (moyenne de l'entraînement) | 70,3 | 88,4 | -0,151 |
| **Régression linéaire** | **22,2** | **28,2** | **0,883** |
| Arbre de décision | 46,0 | 59,7 | 0,475 |
| Random Forest | 31,8 | 41,5 | 0,746 |
| KNN | 36,2 | 46,0 | 0,688 |

Comparaison avec la méthode actuelle, sur les 58 jours du test où `repas_semaine_precedente` est renseignée :

| Méthode | MAE (repas) |
|---|---:|
| Reprise de la semaine précédente (méthode actuelle) | 79,0 |
| Baseline (moyenne) | 72,3 |
| Régression linéaire | 23,4 |

La régression linéaire réduit l'erreur moyenne d'environ 70 % par rapport à la méthode actuelle. Le détail de l'analyse, y compris l'estimation des repas en trop et manquants, figure dans `docs/choix-modele.md`.

## 9. Limites

- Les données sont synthétiques : le très bon résultat de la régression linéaire peut venir de la façon dont elles ont été générées. Il ne garantit rien sur une vraie cantine.
- Le test ne couvre que 68 jours, de février à juin 2026, avec 10 jours d'examens, 4 jours de sortie scolaire et 2 veilles de vacances. Les cas rares sont peu représentés.
- Le nombre d'inscrits augmente dans le temps (650 en moyenne à l'entraînement, 694 au test). Les arbres, la Random Forest et le KNN ne savent pas dépasser les valeurs vues à l'entraînement, ce qui explique probablement leurs moins bons résultats que la régression linéaire.
- Sur les jours de test, le modèle commande en moyenne 8,5 repas de moins que nécessaire : il manque plus de repas qu'il n'en jette. Le coût d'un repas manquant n'est pas chiffré dans l'énoncé.
- Les modèles utilisent leurs réglages par défaut, sans validation croisée temporelle.

## 10. Pistes d'amélioration

- Chiffrer le coût d'un repas manquant et ajouter une marge de sécurité à la prévision si ce coût dépasse celui d'un repas jeté.
- Réentraîner régulièrement le modèle, pour suivre l'évolution du nombre d'inscrits.
- Valider avec une validation croisée temporelle (`TimeSeriesSplit`) plutôt qu'un seul découpage.
- Tester le modèle sur des données réelles de cantine avant de remplacer la méthode actuelle.

## 11. Documentation

- `docs/etude-de-conception.md` : utilisateur, décision, coût des erreurs, approche, données, baseline, métriques, architecture, risques.
- `docs/choix-modele.md` : résultats détaillés, analyse des erreurs, modèle retenu, bilan du critère d'acceptation.
- `docs/grille-seance-3.md` : grille de la séance 3 (sections 1 à 5), réglages de `config.py` et réponse à la question finale.
