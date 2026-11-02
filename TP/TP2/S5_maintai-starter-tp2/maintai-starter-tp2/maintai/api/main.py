
"""API MaintAI : expose le modèle de prédiction de panne.

Lancement : uvicorn maintai.api.main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from maintai import __version__
from maintai.api.schemas import HealthOut, PredictionOut, SensorReading
from maintai.api.security import require_api_key
from maintai.config import get_settings
from maintai.predict import Predictor


# Dictionnaire partagé qui conserve l'état de l'application.
# Il permet notamment de stocker le modèle de prédiction chargé.
state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gère le cycle de vie de l'application.

    Au démarrage : charge le modèle une seule fois.
    À l'arrêt : libère les ressources stockées dans state.
    """
    try:
        # Charger le modèle au démarrage de l'API.
        state["predictor"] = Predictor.load(get_settings())
    except FileNotFoundError:
        # Si le modèle est introuvable, l'API démarre quand même.
        # La route /health indiquera que le modèle n'est pas chargé.
        state["predictor"] = None

    yield

    # Nettoyer le dictionnaire lorsque l'API s'arrête.
    state.clear()


# Création de l'application FastAPI.
app = FastAPI(
    title="MaintAI API",
    version=__version__,
    description="Prédiction de panne à partir de relevés de capteurs.",
    lifespan=lifespan,
)


# Configuration CORS : autorise les origines définies dans les paramètres.
# Les méthodes GET et POST ainsi que les en-têtes Content-Type et X-API-Key
# sont autorisés pour les requêtes provenant de ces origines.
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(get_settings().cors_origins),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)


# Création d'un routeur pour regrouper les routes commençant par /v1.
# Depends(require_api_key) vérifie la clé API avant chaque requête
# adressée à une route de ce routeur.
#
# Toutes les routes /v1 seront donc protégées automatiquement.
router = APIRouter(
    prefix="/v1",
    dependencies=[Depends(require_api_key)],
)


@app.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    """
    Vérifie l'état de l'API et indique si le modèle est chargé.

    Cette route reste publique : elle ne nécessite pas de clé API.
    """
    return HealthOut(
        status="ok",
        model_loaded=state.get("predictor") is not None,
    )


@router.post("/predict", response_model=PredictionOut)
def predict(reading: SensorReading) -> PredictionOut:
    """
    Effectue une prédiction à partir des données des capteurs.

    Cette route nécessite une clé API valide grâce à la dépendance
    configurée au niveau du routeur.
    """
    predictor = state.get("predictor")

    # Vérifier que le modèle est disponible avant de prédire.
    if predictor is None:
        raise HTTPException(
            status_code=503,
            detail=(
                "Modèle non chargé : lancez python -m maintai.train "
                "puis redémarrez l'API"
            ),
        )

    # Envoyer les données au modèle et retourner le résultat.
    return PredictionOut(**predictor.predict(reading.model_dump()))


# Enregistrer le routeur dans l'application FastAPI.
app.include_router(router)
