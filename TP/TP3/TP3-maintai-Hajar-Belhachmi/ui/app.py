
"""Interface Streamlit de MaintAI : explorer les données, puis demander une prédiction à l'API.

Lancement (depuis la racine du projet) : python -m streamlit run ui/app.py
"""

import httpx
import pandas as pd
import streamlit as st

from maintai.client import APIError, MaintaiClient
from maintai.config import FEATURES, get_settings


st.set_page_config(page_title="MaintAI", page_icon="🔧")
st.title("MaintAI · prédiction de panne")


@st.cache_data
def charger(path) -> pd.DataFrame:
    """Charge les données depuis le fichier CSV."""
    return pd.read_csv(path)


# Configuration de l'API
with st.sidebar:
    url = st.text_input("URL de l'API", "http://localhost:8000")
    cle = st.text_input("Clé API", type="password")


# Création des deux onglets
onglet_donnees, onglet_prediction = st.tabs(["Données", "Prédiction"])


# --------------------------------------------------
# SPRINT 1 : Explorer les données
# --------------------------------------------------

with onglet_donnees:
    df = charger(get_settings().data_path)

    # Trois indicateurs
    col1, col2, col3 = st.columns(3)

    col1.metric("Nombre de relevés", len(df))

    col2.metric(
        "Taux de panne",
        f"{df['failure'].mean():.1%}"
    )

    col3.metric(
        "Température moyenne",
        f"{df['temperature_c'].mean():.1f} °C"
    )

    # Choisir une variable à analyser
    variable = st.selectbox(
        "Choisir une variable à analyser",
        FEATURES
    )

    # Calculer le taux de panne par tranche
    tranches = pd.cut(df[variable], bins=10)

    taux_par_tranche = (
        df.groupby(tranches, observed=True)["failure"]
        .mean()
    )

    graphique = pd.DataFrame({
        "Tranche": [round(i.mid, 2) for i in taux_par_tranche.index],
        "Taux de panne": taux_par_tranche.values
    })

    st.subheader(f"Taux de panne selon {variable}")

    st.bar_chart(
        graphique,
        x="Tranche",
        y="Taux de panne"
    )

    # Nuage de points température / vibration
    df_nuage = df.copy()

    df_nuage["Panne"] = df_nuage["failure"].map({
        0: "Non",
        1: "Oui"
    })

    st.subheader("Température et vibration selon la panne")

    st.scatter_chart(
        df_nuage,
        x="temperature_c",
        y="vibration_mm_s",
        color="Panne"
    )


# --------------------------------------------------
# SPRINT 2 : Demander une prédiction à l'API
# --------------------------------------------------

with onglet_prediction:

    with st.form("releve"):

        releve = {
            "temperature_c": st.slider(
                "Température (°C)", -40.0, 150.0, 72.0
            ),
            "vibration_mm_s": st.slider(
                "Vibration (mm/s)", 0.0, 50.0, 6.0
            ),
            "load_pct": st.slider(
                "Charge (%)", 0.0, 100.0, 85.0
            ),
            "runtime_hours": st.number_input(
                "Heures de fonctionnement", 0, 100_000, 15000
            ),
        }

        envoye = st.form_submit_button("Prédire")

    if envoye:
        try:
            client = MaintaiClient(url, api_key=cle)
            resultat = client.predict(releve)

        except APIError as e:
            st.warning(
                f"Erreur API {e.status_code} : {e.detail}"
            )

        except httpx.HTTPError:
            st.error(
                "API injoignable. Vérifiez que le serveur est démarré."
            )

        else:
            # Récupérer la probabilité de panne
            pct = round(resultat["failure_probability"] * 100)

            st.metric(
                "Probabilité de panne",
                f"{pct} %"
            )

            # Afficher le résultat
            if resultat["alert"]:
                st.error("ALERTE : risque de panne détecté !")
            else:
                st.success(
                    "Fonctionnement normal : aucune panne détectée."
                )
