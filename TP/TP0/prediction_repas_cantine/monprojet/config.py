"""Configuration du projet : c'est le seul fichier à adapter à votre sujet."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# --- Vos données -------------------------------------------------------------
DATA_PATH = ROOT / "data" / "cantine_repas.csv"     # remplacez par votre fichier CSV
TARGET = "repas_servis"                             # la colonne à prédire
FEATURES = None              # None = toutes les colonnes sauf la cible et la date ; sinon une liste de noms
TEXT_COLUMN = None           # le nom d'une colonne de texte libre (réclamations…), sinon None

# --- Type de problème --------------------------------------------------------
TASK = "regression"          # "classification" ou "regression"
MAIN_METRIC = "mae"          # classification : "accuracy", "recall", "precision", "f1"
                             # regression : "mae", "rmse", "r2"
# Toutes les métriques à calculer
METRICS = ["mae", "rmse", "r2"]
# --- Découpage entraînement / test -------------------------------------------
SPLIT = "chronologique"      # "random" ; ou "chronologique" pour une série temporelle
TIME_COLUMN = "date"         # colonne de date, obligatoire si SPLIT = "chronologique"
TEST_SIZE = 0.2              # part des données gardée pour le test
SEED = 42                    # graine : mêmes résultats à chaque lancement

# --- Référence métier (facultatif) ---------------------------------------------
# Colonne contenant la prévision de la méthode actuelle (ici : les repas servis le même
# jour une semaine avant). Sert uniquement à comparer les modèles à la pratique actuelle.
# None si le projet n'a pas de référence de ce type.
REFERENCE_COLUMN = "repas_semaine_precedente"

MODELS_DIR = ROOT / "models"
