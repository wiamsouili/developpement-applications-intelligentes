"""Entraîne chaque modèle candidat, l'évalue sur le jeu de test et les compare.

Usage, depuis la racine du projet : python -m monprojet.train
"""
import json

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.metrics import (accuracy_score, f1_score, mean_absolute_error, mean_squared_error,
                             precision_score, r2_score, recall_score)
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from monprojet import config
from monprojet.data import load_data, split
from monprojet.models import candidates

HIGHER_IS_BETTER = {"accuracy": True, "recall": True, "precision": True, "f1": True,
                    "mae": False, "rmse": False, "r2": True}


def build_preprocessing(X: pd.DataFrame) -> ColumnTransformer:
    """Prépare les colonnes : nombres mis à l'échelle, catégories encodées, texte vectorisé. (Fournie.)"""
    text = [config.TEXT_COLUMN] if config.TEXT_COLUMN else []
    numeric = [c for c in X.columns if c not in text and pd.api.types.is_numeric_dtype(X[c])]
    categorical = [c for c in X.columns if c not in text and c not in numeric]
    steps = []
    if numeric:
        steps.append(("nombres", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), numeric))
    if categorical:
        steps.append(("categories", make_pipeline(SimpleImputer(strategy="most_frequent"),
                                                  OneHotEncoder(handle_unknown="ignore")), categorical))
    if text:
        steps.append(("texte", TfidfVectorizer(), config.TEXT_COLUMN))
    return ColumnTransformer(steps, sparse_threshold=0)

def evaluate(model, X_test, y_test) -> dict:
    y_pred = model.predict(X_test)

    if config.TASK == "classification":
        average = "binary" if y_test.nunique() == 2 else "macro"

        return {
            "accuracy": round(float(accuracy_score(y_test, y_pred)), 3),
            "recall": round(float(recall_score(
                y_test, y_pred, average=average, zero_division=0
            )), 3),
            "precision": round(float(precision_score(
                y_test, y_pred, average=average, zero_division=0
            )), 3),
            "f1": round(float(f1_score(
                y_test, y_pred, average=average, zero_division=0
            )), 3)
        }

    elif config.TASK == "regression":
        return {
            "mae": round(float(mean_absolute_error(y_test, y_pred)), 3),
            "rmse": round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 3),
            "r2": round(float(r2_score(y_test, y_pred)), 3)
        }

    else:
        raise ValueError(f"Tâche inconnue : {config.TASK}")

def comparer_a_la_reference(modeles: dict, X_test, y_test):
    """Compare les modèles à la méthode actuelle (config.REFERENCE_COLUMN) sur les mêmes jours.

    Seuls les jours où la référence existe sont gardés (elle est vide après des vacances).
    Renvoie None si le projet n'a pas de référence ou si ce n'est pas une régression.
    """
    colonne = config.REFERENCE_COLUMN
    if config.TASK != "regression" or colonne is None or colonne not in X_test.columns:
        return None

    disponible = X_test[colonne].notna()
    if not disponible.any():
        return None

    X_commun = X_test[disponible]
    y_commun = y_test[disponible]

    ecart = (X_commun[colonne] - y_commun).abs()
    return {
        "colonne": colonne,
        "nb_jours": int(disponible.sum()),
        "nb_jours_test": int(len(X_test)),
        "mae_reference": round(float(ecart.mean()), 3),
        "mae_modeles": {
            nom: round(float(mean_absolute_error(y_commun, m.predict(X_commun))), 3)
            for nom, m in modeles.items()
        },
    }


def main() -> None:
    # 1. Charger et découper les données
    df = load_data()
    X_train, X_test, y_train, y_test = split(df)

    resultats = {}
    modeles = {}

    # 2. Entraîner et évaluer chaque modèle
    for nom, estimateur in candidates().items():
        model = Pipeline([
            ("preparation", build_preprocessing(X_train)),
            ("modele", estimateur)
        ])

        model.fit(X_train, y_train)
        scores = evaluate(model, X_test, y_test)

        resultats[nom] = scores
        modeles[nom] = model

    # 3. Afficher le tableau de comparaison
    tableau = pd.DataFrame(resultats).T
    print("\nComparaison des modèles :")
    print(tableau.sort_values(
        by=config.MAIN_METRIC,
        ascending=not HIGHER_IS_BETTER[config.MAIN_METRIC]
    ))

    # 4. Trouver le meilleur modèle
    meilleur_nom = (
        tableau[config.MAIN_METRIC].idxmax()
        if HIGHER_IS_BETTER[config.MAIN_METRIC]
        else tableau[config.MAIN_METRIC].idxmin()
    )

    meilleur_modele = modeles[meilleur_nom]

    print(f"\nMeilleur modèle : {meilleur_nom}")
    print(f"Métrique principale : {config.MAIN_METRIC}")
    print(f"Score : {tableau.loc[meilleur_nom, config.MAIN_METRIC]}")

    # 5. Comparer à la méthode actuelle, si le projet en a une
    reference = comparer_a_la_reference(modeles, X_test, y_test)
    if reference is not None:
        print(f"\nComparaison avec la méthode actuelle ({reference['colonne']}), "
              f"sur {reference['nb_jours']} jours du test sur {reference['nb_jours_test']} :")
        print(f"  MAE de la méthode actuelle : {reference['mae_reference']}")
        for nom, mae in reference["mae_modeles"].items():
            print(f"  MAE {nom} : {mae}")

    # 6. Sauvegarder le modèle et les métriques
    config.MODELS_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(
        meilleur_modele,
        config.MODELS_DIR / "model.joblib"
    )

    with open(config.MODELS_DIR / "metrics.json", "w", encoding="utf-8") as f:
        json.dump({
            "main_metric": config.MAIN_METRIC,
            "best": meilleur_nom,
            "results": resultats,
            "reference": reference
        }, f, ensure_ascii=False, indent=4)

    print(f"\nModèle sauvegardé dans : {config.MODELS_DIR / 'model.joblib'}")
    print(f"Métriques sauvegardées dans : {config.MODELS_DIR / 'metrics.json'}")


if __name__ == "__main__":
    main()
