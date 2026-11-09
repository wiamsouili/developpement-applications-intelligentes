
"""Authentification par clé API, transmise dans l'en-tête X-API-Key."""

import secrets

from fastapi import Header, HTTPException, status

from maintai.config import get_settings


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """
    Vérifie la validité de la clé API envoyée par le client.

    La clé est transmise dans l'en-tête HTTP X-API-Key.

    Codes d'erreur :
        - 401 : clé API absente ou incorrecte.
        - 500 : clé API non configurée côté serveur.
    """

    # Étape 1 : récupérer les paramètres de configuration du serveur.
    settings = get_settings()

    # Récupérer la clé API attendue depuis la configuration.
    expected_api_key = settings.api_key

    # Étape 2 : vérifier que le serveur possède une clé API configurée.
    # Si aucune clé n'est définie, il s'agit d'une erreur serveur (500).
    if not expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="La clé API n'est pas configurée sur le serveur.",
        )

    # Étape 3 : vérifier que le client a envoyé une clé API.
    # Si l'en-tête X-API-Key est absent ou vide, retourner 401.
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API manquante.",
        )

    # Étape 4 : comparer la clé du client avec celle du serveur.
    # secrets.compare_digest effectue une comparaison sécurisée
    # afin de limiter les risques d'attaques par analyse temporelle.
    if not secrets.compare_digest(x_api_key, expected_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API invalide.",
        )

    # Étape 5 : si les deux clés correspondent, aucune erreur n'est levée.
    # FastAPI autorise alors l'exécution de la route demandée.
    return None
