# Prédiction des pannes industrielles par apprentissage automatique

**Groupe 3 :** SOUILI Wiam, ELAOUAZI Hafsa, YEKHLEF Aya, BELHACHMI Hajar

Ce projet compare plusieurs modèles de classification pour repérer les machines qui présentent un risque de panne, à partir de leurs mesures de fonctionnement (température, vibrations, charge, durée de fonctionnement). Il s'adresse à un ingénieur de maintenance qui doit décider quelles machines inspecter en priorité.

## 1. Résumé

| Élément | Contenu |
|---|---|
| Problème | Classification binaire : `failure` = 0 (pas de panne) ou 1 (panne) |
| Données | `data/exemple_pannes.csv` : 5 000 observations, 4 variables d'entrée, aucune valeur manquante |
| Classes | 4 122 observations sans panne (82,4 %), 878 avec panne (17,6 %) : jeu déséquilibré |
| Découpage | 80 % entraînement (4 000) / 20 % test (1 000), aléatoire et stratifié, graine 42 |
| Métrique principale | Recall de la classe « panne » |
| Modèles comparés | Baseline, régression logistique, arbre de décision, Random Forest, KNN |
| Modèle retenu | Arbre de décision (recall de 0,597 sur le test) |
| Critère d'acceptation | Recall d'au moins 0,80 visé : **non atteint** |

## 2. Données

| Variable | Signification | Minimum | Moyenne | Maximum |
|---|---|---:|---:|---:|
| `temperature_c` | Température de fonctionnement (°C) | 35,8 | 64,8 | 92,6 |
| `vibration_mm_s` | Intensité des vibrations (mm/s) | 0,02 | 3,0 | 22,2 |
| `load_pct` | Charge de la machine (%) | 20 | 60,4 | 100 |
| `runtime_hours` | Heures de fonctionnement | 5 | 15 002 | 29 999 |
| `failure` | Cible : 0 = pas de panne, 1 = panne | 0 | 0,18 | 1 |

Le fichier ne contient pas de colonne de date : le découpage est donc aléatoire et non chronologique.

## 3. Organisation du projet

```
prediction_pannes_industrielles/
├── data/
│   └── exemple_pannes.csv        Jeu de données
├── docs/
│   ├── etude-de-conception.md    Cadrage : utilisateurs, décision, métriques, risques
│   └── choix-modele.md           Résultats, modèle retenu, critères d'acceptation
├── monprojet/
│   ├── config.py                 Réglages : fichier, cible, métrique, découpage, graine
│   ├── data.py                   load_data(), feature_columns(), split()
│   ├── models.py                 candidates() : la baseline puis quatre modèles
│   └── train.py                  evaluate(), main() : entraînement et comparaison
├── tests/                        8 tests pytest (données, modèles, entraînement)
├── models/                       Produit par l'entraînement (ignoré par git)
│   ├── model.joblib              Meilleur modèle selon la métrique principale
│   └── metrics.json              Métrique principale, meilleur modèle, scores de tous les modèles
├── requirements.txt              Versions des bibliothèques
├── pytest.ini                    Configuration des tests
└── README.md
```

## 4. Installation

Python 3.14 a été utilisé pour le développement. Depuis la racine du projet :

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

La commande affiche le tableau de comparaison, indique le meilleur modèle, puis écrit `models/model.joblib` et `models/metrics.json`. Ces deux fichiers sont ignorés par git : il faut donc relancer l'entraînement après un clonage du dépôt.

**Réutiliser le modèle sauvegardé :**

```python
import joblib
import pandas as pd

modele = joblib.load("models/model.joblib")
mesures = pd.DataFrame([{
    "temperature_c": 75.0,
    "vibration_mm_s": 6.5,
    "load_pct": 85.0,
    "runtime_hours": 20000,
}])
print(modele.predict(mesures))   # 1 = risque de panne, 0 = pas de panne
```

Le pipeline sauvegardé contient déjà la préparation des données (imputation et standardisation) : il reçoit les mesures brutes.

## 6. Configuration

Tous les réglages sont dans `monprojet/config.py` :

| Paramètre | Valeur actuelle | Rôle |
|---|---|---|
| `DATA_PATH` | `data/exemple_pannes.csv` | Fichier CSV à charger |
| `TARGET` | `failure` | Colonne à prédire |
| `TASK` | `classification` | `classification` ou `regression` |
| `MAIN_METRIC` | `recall` | Métrique qui désigne le meilleur modèle |
| `SPLIT` | `random` | Type de découpage |
| `TEST_SIZE` | 0,2 | Part des données réservée au test |
| `SEED` | 42 | Graine : mêmes résultats à chaque lancement |

## 7. Méthode

1. `load_data()` lit le CSV, vérifie la présence de la cible et supprime les lignes dont la cible est manquante.
2. `split()` sépare les données en entraînement et test, en conservant la proportion de pannes dans les deux parties (`stratify`).
3. Chaque modèle est placé dans un pipeline : imputation par la médiane, standardisation, puis modèle. La préparation est donc apprise sur l'entraînement uniquement.
4. `evaluate()` calcule accuracy, recall, précision et F1 sur le test.
5. `main()` classe les modèles selon le recall et sauvegarde le meilleur.

## 8. Résultats sur le jeu de test (1 000 observations dont 176 pannes)

| Modèle | Accuracy | Recall | Précision | F1-score |
|---|---:|---:|---:|---:|
| Baseline (classe majoritaire) | 0,824 | 0,000 | 0,000 | 0,000 |
| Régression logistique | 0,889 | 0,574 | 0,737 | 0,645 |
| **Arbre de décision** | 0,839 | **0,597** | 0,538 | 0,566 |
| Random Forest | 0,873 | 0,545 | 0,671 | 0,602 |
| KNN | 0,878 | 0,540 | 0,699 | 0,609 |

Matrice de confusion de l'arbre de décision : 105 pannes détectées, 71 pannes manquées, 90 fausses alertes, 734 machines correctement classées sans panne.

La baseline atteint 82,4 % d'accuracy sans détecter aucune panne : l'accuracy seule ne permet pas de juger le système, d'où le choix du recall comme métrique principale.

L'arbre de décision est retenu parce qu'il a le meilleur recall, mais son avance sur la régression logistique est faible (4 pannes de plus détectées, au prix de 54 fausses alertes supplémentaires). Le détail de l'analyse figure dans `docs/choix-modele.md`.

## 9. Limites

- Le recall de 0,597 reste loin de l'objectif de 0,80 : environ 40 % des pannes ne sont pas détectées. Le modèle ne peut pas être utilisé seul pour des décisions de maintenance.
- Les données sont un fichier d'exemple dont l'origine et la licence ne sont pas précisées. Les résultats ne disent rien de la performance sur des machines réelles.
- Le jeu ne contient pas d'horodatage : aucune évaluation chronologique n'a pu être faite.
- Les modèles utilisent leurs réglages par défaut, sans optimisation des hyperparamètres ni ajustement du seuil de décision.
- Dans `data.py`, `split()` ne gère que `SPLIT = "random"`. Un découpage chronologique demanderait d'ajouter cette branche.

## 10. Pistes d'amélioration

- Ajuster le seuil de décision, ou pondérer la classe « panne » (`class_weight`), pour augmenter le recall.
- Régler les hyperparamètres par validation croisée.
- Obtenir des données horodatées et passer à un découpage chronologique.
- Valider sur des données de machines réelles avant tout usage opérationnel.

## 11. Documentation

- `docs/etude-de-conception.md` : utilisateurs, décision à aider, approche par sous-problème, données, critères d'acceptation, architecture, risques.
- `docs/choix-modele.md` : résultats détaillés, analyse, modèle retenu, bilan des critères d'acceptation.
