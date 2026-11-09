import pytest

VALID = {
    "temperature_c": 60.0,
    "vibration_mm_s": 2.0,
    "load_pct": 50.0,
    "runtime_hours": 5000,
}

# VALID sans le champ load_pct
SANS_CHARGE = {k: v for k, v in VALID.items() if k != "load_pct"}

CAS_REFUSES = [
    # (description, url, corps, code attendu)
    ("champ manquant", "/v1/predict", SANS_CHARGE, 422),
    ("valeur absurde", "/v1/predict", {**VALID, "load_pct": 250}, 422),
    (
        "texte au lieu d'un nombre",
        "/v1/predict",
        {**VALID, "temperature_c": "abc"},
        422,
    ),
    ("champ en trop", "/v1/predict", {**VALID, "pressure": 10}, 422),
    ("mauvaise route", "/v1/predic", VALID, 404),
]


@pytest.mark.parametrize("description, url, corps, attendu", CAS_REFUSES)
def test_requete_refusee(client, description, url, corps, attendu):
    r = client.post(url, json=corps)

    assert r.status_code == attendu, (
        f"{description}: attendu {attendu}, obtenu {r.status_code}"
    )
