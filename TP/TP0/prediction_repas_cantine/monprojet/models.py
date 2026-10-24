"""Les modèles à comparer.

À vous d'écrire candidates(). Les tests de tests/test_models.py disent ce qui est attendu.
"""
from monprojet import config  # noqa: F401  (config.TASK, config.SEED)
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor

def candidates() -> dict:
    if config.TASK == "classification":
        return {
            "baseline": DummyClassifier(strategy="most_frequent"),
            "logistic_regression": LogisticRegression(
                random_state=config.SEED,
                max_iter=1000
            ),
            "decision_tree": DecisionTreeClassifier(
                random_state=config.SEED
            ),
            "random_forest": RandomForestClassifier(
                random_state=config.SEED
            ),
            "knn": KNeighborsClassifier()
        }

    elif config.TASK == "regression":
        return {
            "baseline": DummyRegressor(strategy="mean"),
            "linear_regression": LinearRegression(),
            "decision_tree": DecisionTreeRegressor(
                random_state=config.SEED
            ),
            "random_forest": RandomForestRegressor(
                random_state=config.SEED
            ),
            "knn": KNeighborsRegressor()
        }

    else:
        raise ValueError(
            f"Tâche inconnue : {config.TASK}. "
            "Utilisez 'classification' ou 'regression'."
        )
