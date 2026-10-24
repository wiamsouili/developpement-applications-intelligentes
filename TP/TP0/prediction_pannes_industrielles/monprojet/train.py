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

    # 5. Sauvegarder le modèle et les métriques
    config.MODELS_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(
        meilleur_modele,
        config.MODELS_DIR / "model.joblib"
    )

    with open(config.MODELS_DIR / "metrics.json", "w", encoding="utf-8") as f:
        json.dump({
            "main_metric": config.MAIN_METRIC,
            "best": meilleur_nom,
            "results": resultats
        }, f, ensure_ascii=False, indent=4)

    print(f"\nModèle sauvegardé dans : {config.MODELS_DIR / 'model.joblib'}")
    print(f"Métriques sauvegardées dans : {config.MODELS_DIR / 'metrics.json'}")


if __name__ == "__main__":
    main()
