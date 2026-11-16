"""Chargement et découpage des données.

À vous d'écrire load_data() et split(). Les tests de tests/test_data.py disent ce qui est attendu.
"""
import pandas as pd
from sklearn.model_selection import train_test_split  # noqa: F401  (utile pour split)

from monprojet import config


def load_data(path=None) -> pd.DataFrame:
    if path is None:
        path = config.DATA_PATH

    df = pd.read_csv(path)

    if config.TARGET not in df.columns:
        raise ValueError(
            f"La colonne cible '{config.TARGET}' est absente du fichier CSV."
        )

    df = df.dropna(subset=[config.TARGET]).reset_index(drop=True)

    return df

def feature_columns(df: pd.DataFrame) -> list:
    if config.FEATURES is not None:
        return list(config.FEATURES)

    excluded = {config.TARGET, config.TIME_COLUMN}

    return [c for c in df.columns if c not in excluded]

def split(df: pd.DataFrame):
    features = feature_columns(df)

    X = df[features]
    y = df[config.TARGET]

    if config.SPLIT == "random":
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=config.TEST_SIZE,
            random_state=config.SEED,
            stratify=y
        )

        return X_train, X_test, y_train, y_test
