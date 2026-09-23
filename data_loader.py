"""
Chargement et préparation des données du datamart "Parcours Client".
Toutes les fonctions sont mises en cache par Streamlit pour éviter de
recharger les CSV à chaque interaction utilisateur.
"""

import os
import pandas as pd
import streamlit as st

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# Coordonnées approximatives des villes camerounaises (pour la carte)
VILLE_COORDS = {
    "Yaoundé": (3.8480, 11.5021), "Douala": (4.0511, 9.7679),
    "Bafoussam": (5.4737, 10.4176), "Bamenda": (5.9631, 10.1591),
    "Garoua": (9.3017, 13.3921), "Maroua": (10.5913, 14.3153),
    "Ngaoundéré": (7.3167, 13.5833), "Bertoua": (4.5771, 13.6845),
    "Ebolowa": (2.9167, 11.1500), "Kribi": (2.9500, 9.9167),
    "Buea": (4.1560, 9.2920), "Kumba": (4.6363, 9.4469),
    "Limbé": (4.0225, 9.2148), "Dschang": (5.4467, 10.0536),
    "Edéa": (3.8000, 10.1333), "Nkongsamba": (4.9547, 9.9401),
    "Bafang": (5.1500, 10.1833), "Bafia": (4.7500, 11.2333),
    "Baleng": (5.5000, 10.4333), "Batouri": (4.4333, 14.3667),
    "Foumbot": (5.5167, 10.6333), "Kousséri": (12.0833, 15.0333),
    "Loum": (4.7167, 9.7333), "Mbalmayo": (3.5167, 11.5000),
    "Mbouda": (5.6167, 10.2500), "Meiganga": (6.5167, 14.3000),
    "Obala": (4.1667, 11.5333), "Sangmélima": (2.9333, 11.9833),
    "Garoua-Boulaï": (5.8833, 14.5500), "Non défini": (4.05, 11.5),
}


@st.cache_data(show_spinner="Chargement des données du datamart…")
def load_dimensions():
    dims = {}
    for name in [
        "dim_client", "dim_agence_operation", "dim_canal", "dim_compte_client",
        "dim_produit", "dim_gestionnaire", "dim_statut_interaction",
        "dim_type_transaction", "dim_date_interaction",
    ]:
        dims[name] = pd.read_csv(os.path.join(DATA_DIR, f"{name}.csv"))
    dims["dim_date_interaction"]["date"] = pd.to_datetime(dims["dim_date_interaction"]["date"])
    return dims


@st.cache_data(show_spinner="Préparation du modèle analytique…")
def load_fact_denormalized():
    dims = load_dimensions()
    fact = pd.read_csv(os.path.join(DATA_DIR, "interaction.csv"))
    fact["date_interaction"] = pd.to_datetime(fact["date_interaction"])

    df = fact.merge(dims["dim_client"], left_on="fk_client", right_on="pk_client", how="left")
    df = df.merge(dims["dim_agence_operation"], left_on="fk_agence", right_on="pk_code_agence", how="left")
    df = df.merge(dims["dim_canal"], left_on="fk_canal", right_on="id_canal", how="left")
    df = df.merge(dims["dim_produit"], left_on="fk_produit", right_on="pk_produit", how="left")
    df = df.merge(dims["dim_gestionnaire"], left_on="fk_gestionnaire", right_on="code_gestionnaire", how="left")
    df = df.merge(dims["dim_statut_interaction"], left_on="fk_statut", right_on="pk_status", how="left")
    df = df.merge(dims["dim_type_transaction"], left_on="fk_type_transaction", right_on="id_type_transaction", how="left")

    df["lat"] = df["nom_ville"].map(lambda v: VILLE_COORDS.get(v, (None, None))[0])
    df["lon"] = df["nom_ville"].map(lambda v: VILLE_COORDS.get(v, (None, None))[1])

    df["annee_mois"] = df["date_interaction"].dt.to_period("M").astype(str)
    df["jour_semaine"] = df["date_interaction"].dt.day_name()
    df["annee"] = df["date_interaction"].dt.year

    return df


def apply_filters(df, date_range=None, canaux=None, agences=None, segments=None,
                   produits=None, statuts=None):
    out = df
    if date_range:
        out = out[(out["date_interaction"] >= pd.Timestamp(date_range[0])) &
                  (out["date_interaction"] <= pd.Timestamp(date_range[1]))]
    if canaux:
        out = out[out["type_canal"].isin(canaux)]
    if agences:
        out = out[out["nom_agence"].isin(agences)]
    if segments:
        out = out[out["segment"].isin(segments)]
    if produits:
        out = out[out["nom_produit"].isin(produits)]
    if statuts:
        out = out[out["nom_status"].isin(statuts)]
    return out
