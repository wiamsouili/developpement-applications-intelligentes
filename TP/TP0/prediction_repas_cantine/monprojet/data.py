"""Chargement et découpage des données.

load_data() lit le CSV et vérifie la cible. split() sépare entraînement et test, soit au hasard,
soit dans l'ordre du temps. Les tests de tests/test_data.py disent ce qui est attendu.
"""
import pandas as pd
from sklearn.model_selection import train_test_split

from monprojet import config


def load_data(path=None) -> pd.DataFrame:
    if path is None:
        path = config.DATA_PATH

    df = pd.read_csv(path)

    if config.TARGET not in df.columns:
        raise ValueError(
            f"La colonne cible '{config.TARGET}' est absente du fichier CSV."
        )

    if config.SPLIT == "chronologique" and config.TIME_COLUMN not in df.columns:
        raise ValueError(
            f"La colonne de date '{config.TIME_COLUMN}' est absente du fichier CSV : "
            "elle est nécessaire pour un découpage chronologique."
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
        # Le tirage est stratifié seulement pour une classification (il garde la part de chaque classe).
        stratifier = y if config.TASK == "classification" else None
        return train_test_split(
            X,
            y,
            test_size=config.TEST_SIZE,
            random_state=config.SEED,
            stratify=stratifier,
        )

    if config.SPLIT == "chronologique":
        # On trie les jours du plus ancien au plus récent : l'entraînement prend le passé,
        # le test prend les derniers jours. Aucun jour du test n'est antérieur à l'entraînement.
        dates = pd.to_datetime(df[config.TIME_COLUMN])
        ordre = dates.sort_values(kind="stable").index
        n_test = int(round(len(df) * config.TEST_SIZE))
        idx_train = ordre[:-n_test]
        idx_test = ordre[-n_test:]

        return X.loc[idx_train], X.loc[idx_test], y.loc[idx_train], y.loc[idx_test]

    raise ValueError(
        f"Découpage inconnu : {config.SPLIT}. Utilisez 'random' ou 'chronologique'."
    )
