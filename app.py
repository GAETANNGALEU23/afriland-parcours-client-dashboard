"""
Dashboard décisionnel — Parcours Client bancaire
Afriland First Bank

Mémoire de Master 2 — Business Intelligence / Data Analyse
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from auth import check_login, is_authenticated, login, logout
from data_loader import load_dimensions, load_fact_denormalized, apply_filters

# ----------------------------------------------------------------------
# Configuration générale
# ----------------------------------------------------------------------
APP_DIR = os.path.dirname(__file__)
LOGO_PATH = os.path.join(APP_DIR, "assets", "logo_afriland.png")
if not os.path.exists(LOGO_PATH):
    LOGO_PATH = os.path.join(APP_DIR, "assets", "logo_placeholder.png")

RED = "#C8102E"
BLACK = "#111111"
GRAY = "#6B6B6B"
PALETTE = [RED, BLACK, "#B4B2A9", "#8E0B20", "#D3D1C7", "#444441"]

st.set_page_config(
    page_title="Afriland First Bank — Parcours Client",
    page_icon=LOGO_PATH if os.path.exists(LOGO_PATH) else "🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Vérification défensive : si le dossier data/ n'a pas été poussé sur
# GitHub (ou est incomplet), on affiche un message clair plutôt qu'un
# traceback brut.
_REQUIRED_DATA_FILES = [
    "dim_client.csv", "dim_agence_operation.csv", "dim_canal.csv",
    "dim_compte_client.csv", "dim_produit.csv", "dim_gestionnaire.csv",
    "dim_statut_interaction.csv", "dim_type_transaction.csv",
    "dim_date_interaction.csv", "interaction.csv",
]
_DATA_DIR = os.path.join(APP_DIR, "data")
_missing = [f for f in _REQUIRED_DATA_FILES if not os.path.exists(os.path.join(_DATA_DIR, f))]
if _missing:
    st.error(
        "Fichiers de données manquants dans le dépôt : "
        + ", ".join(_missing)
        + ". Vérifiez que le dossier `data/` a bien été poussé sur GitHub "
        "(sur la page du dépôt, il doit apparaître au même niveau que `app.py`)."
    )
    st.stop()

CUSTOM_CSS = """
/* ===== Thème Afriland First Bank — Rouge / Noir / Blanc ===== */

:root {
    --afb-red: #C8102E;
    --afb-red-dark: #8E0B20;
    --afb-black: #111111;
    --afb-white: #FFFFFF;
    --afb-gray: #6B6B6B;
    --afb-bg: #F5F5F5;
}

/* Fond général */
.stApp {
    background-color: var(--afb-bg);
}

/* Barre latérale */
section[data-testid="stSidebar"] {
    background-color: var(--afb-black);
}
section[data-testid="stSidebar"] * {
    color: var(--afb-white) !important;
}
section[data-testid="stSidebar"] .stRadio label:hover {
    color: var(--afb-red) !important;
}
section[data-testid="stSidebar"] hr {
    border-color: #333333;
}

/* Boutons */
.stButton > button {
    background-color: var(--afb-red);
    color: var(--afb-white);
    border: none;
    border-radius: 6px;
    font-weight: 600;
    padding: 0.5rem 1.2rem;
    transition: background-color 0.15s ease;
}
.stButton > button:hover {
    background-color: var(--afb-red-dark);
    color: var(--afb-white);
}

/* Titres */
h1, h2, h3 {
    color: var(--afb-black);
    font-weight: 700;
}

/* Bandeau d'en-tête */
.afb-header {
    background: linear-gradient(90deg, var(--afb-black) 0%, var(--afb-red) 100%);
    padding: 1.1rem 1.6rem;
    border-radius: 10px;
    margin-bottom: 1.4rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.afb-header h1 {
    color: var(--afb-white) !important;
    font-size: 1.5rem;
    margin: 0;
}
.afb-header p {
    color: #EDEDED;
    margin: 0;
    font-size: 0.85rem;
}

/* Cartes KPI */
.afb-kpi-card {
    background-color: var(--afb-white);
    border-left: 5px solid var(--afb-red);
    border-radius: 8px;
    padding: 1rem 1.2rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    height: 100%;
}
.afb-kpi-label {
    color: var(--afb-gray);
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 0.3rem;
}
.afb-kpi-value {
    color: var(--afb-black);
    font-size: 1.7rem;
    font-weight: 700;
}
.afb-kpi-delta-up { color: #1E8E3E; font-size: 0.8rem; font-weight: 600; }
.afb-kpi-delta-down { color: var(--afb-red); font-size: 0.8rem; font-weight: 600; }

/* Cartes section */
.afb-card {
    background-color: var(--afb-white);
    border-radius: 10px;
    padding: 1.2rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    margin-bottom: 1rem;
}

/* Badge de rôle utilisateur */
.afb-badge {
    background-color: var(--afb-red);
    color: white;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
}

/* Masquer le menu et le footer par défaut de Streamlit */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Onglets */
.stTabs [data-baseweb="tab"] {
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    color: var(--afb-red) !important;
    border-bottom-color: var(--afb-red) !important;
}

"""

st.markdown(f"<style>{CUSTOM_CSS}</style>", unsafe_allow_html=True)

px.defaults.color_discrete_sequence = PALETTE
px.defaults.template = "plotly_white"


# ----------------------------------------------------------------------
# Composants réutilisables
# ----------------------------------------------------------------------
def kpi_card(label, value, help_text=None):
    st.markdown(
        f"""
        <div class="afb-kpi-card">
            <div class="afb-kpi-label">{label}</div>
            <div class="afb-kpi-value">{value}</div>
            {f'<div style="color:#888;font-size:0.75rem;margin-top:4px;">{help_text}</div>' if help_text else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_fcfa(x):
    if x >= 1_000_000_000:
        return f"{x/1_000_000_000:.2f} Md FCFA"
    if x >= 1_000_000:
        return f"{x/1_000_000:.1f} M FCFA"
    if x >= 1_000:
        return f"{x/1_000:.0f} K FCFA"
    return f"{x:.0f} FCFA"


def header(title, subtitle):
    logo_col, title_col = st.columns([1, 8])
    st.markdown(
        f"""
        <div class="afb-header">
            <div>
                <h1>{title}</h1>
                <p>{subtitle}</p>
            </div>
            <div style="text-align:right;">
                <span class="afb-badge">{st.session_state['user_info']['role']}</span>
                <p style="color:#EDEDED;font-size:0.8rem;margin-top:6px;">
                    {st.session_state['user_info']['nom_affiche']}
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------------------
# Page de connexion
# ----------------------------------------------------------------------
def login_page():
    left, mid, right = st.columns([1, 1.1, 1])
    with mid:
        st.write("")
        st.write("")
        if os.path.exists(LOGO_PATH):
            lcol1, lcol2, lcol3 = st.columns([1, 1, 1])
            with lcol2:
                st.image(LOGO_PATH, width=120)
        st.markdown(
            "<h2 style='text-align:center;margin-top:0.5rem;'>Système décisionnel — Parcours Client</h2>"
            "<p style='text-align:center;color:#6B6B6B;'>Connectez-vous pour accéder au tableau de bord</p>",
            unsafe_allow_html=True,
        )
        with st.form("login_form"):
            username = st.text_input("Identifiant")
            password = st.text_input("Mot de passe", type="password")
            submitted = st.form_submit_button("Se connecter", width='stretch')
            if submitted:
                user = check_login(username, password)
                if user:
                    login(username, user)
                    st.rerun()
                else:
                    st.error("Identifiant ou mot de passe incorrect.")
        st.markdown(
            "<p style='text-align:center;color:#AAAAAA;font-size:0.75rem;margin-top:1rem;'>"
            "Comptes de démonstration — admin / afriland2026 · direction / parcours2026</p>",
            unsafe_allow_html=True,
        )


# ----------------------------------------------------------------------
# Filtres latéraux
# ----------------------------------------------------------------------
def sidebar_filters(df):
    if os.path.exists(LOGO_PATH):
        st.sidebar.image(LOGO_PATH, width=90)
    st.sidebar.markdown("### Parcours Client")
    st.sidebar.caption(f"Connecté : {st.session_state['user_info']['nom_affiche']}")

    page = st.sidebar.radio(
        "Navigation",
        [
            "Vue d'ensemble", "Temporalité", "Canal", "Agence",
            "Produit", "Client", "Gestionnaires",
        ],
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("#### Filtres")

    min_date, max_date = df["date_interaction"].min(), df["date_interaction"].max()
    date_range = st.sidebar.date_input(
        "Période", value=(min_date.date(), max_date.date()),
        min_value=min_date.date(), max_value=max_date.date(),
    )
    if len(date_range) != 2:
        date_range = (min_date.date(), max_date.date())

    canaux = st.sidebar.multiselect("Canal", sorted(df["type_canal"].dropna().unique()))
    agences = st.sidebar.multiselect("Agence", sorted(df["nom_agence"].dropna().unique()))
    segments = st.sidebar.multiselect("Segment client", sorted(df["segment"].dropna().unique()))
    produits = st.sidebar.multiselect("Produit", sorted(df["nom_produit"].dropna().unique()))
    statuts = st.sidebar.multiselect("Statut", sorted(df["nom_status"].dropna().unique()))

    st.sidebar.markdown("---")
    if st.sidebar.button("Se déconnecter", width='stretch'):
        logout()
        st.rerun()

    filtered = apply_filters(
        df, date_range=date_range, canaux=canaux or None, agences=agences or None,
        segments=segments or None, produits=produits or None, statuts=statuts or None,
    )
    return page, filtered


# ----------------------------------------------------------------------
# Pages
# ----------------------------------------------------------------------
def page_overview(df):
    header("Vue d'ensemble", "Indicateurs clés du parcours client — toutes dimensions confondues")

    ok = df[df["nom_status"] == "Réussie"]
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        kpi_card("Clients actifs", f"{df['fk_client'].nunique():,}".replace(",", " "))
    with c2:
        kpi_card("Interactions", f"{len(df):,}".replace(",", " "))
    with c3:
        kpi_card("Montant total", format_fcfa(ok["montant_transaction"].sum()))
    with c4:
        taux = 100 * len(ok) / len(df) if len(df) else 0
        kpi_card("Taux de réussite", f"{taux:.1f}%")
    with c5:
        kpi_card("Solde moyen", format_fcfa(df["solde"].mean() if len(df) else 0))

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown('<div class="afb-card">', unsafe_allow_html=True)
        st.markdown("**Évolution mensuelle des interactions**")
        monthly = df.groupby("annee_mois").size().reset_index(name="nombre")
        fig = px.line(monthly, x="annee_mois", y="nombre", markers=True)
        fig.update_traces(line_color=RED)
        fig.update_layout(height=320, xaxis_title="", yaxis_title="Interactions", margin=dict(t=10))
        st.plotly_chart(fig, width='stretch')
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="afb-card">', unsafe_allow_html=True)
        st.markdown("**Répartition par statut**")
        stat = df["nom_status"].value_counts().reset_index()
        stat.columns = ["statut", "nombre"]
        fig = px.pie(stat, names="statut", values="nombre", hole=0.55)
        fig.update_layout(height=320, margin=dict(t=10), showlegend=True)
        st.plotly_chart(fig, width='stretch')
        st.markdown("</div>", unsafe_allow_html=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown('<div class="afb-card">', unsafe_allow_html=True)
        st.markdown("**Interactions par canal**")
        c = df["type_canal"].value_counts().reset_index()
        c.columns = ["canal", "nombre"]
        fig = px.bar(c, x="canal", y="nombre", text_auto=True)
        fig.update_layout(height=300, xaxis_title="", yaxis_title="", margin=dict(t=10))
        st.plotly_chart(fig, width='stretch')
        st.markdown("</div>", unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="afb-card">', unsafe_allow_html=True)
        st.markdown("**Top 5 produits utilisés**")
        p = df["nom_produit"].value_counts().head(5).reset_index()
        p.columns = ["produit", "nombre"]
        fig = px.bar(p, x="nombre", y="produit", orientation="h", text_auto=True)
        fig.update_layout(height=300, yaxis=dict(autorange="reversed"), xaxis_title="", yaxis_title="", margin=dict(t=10))
        st.plotly_chart(fig, width='stretch')
        st.markdown("</div>", unsafe_allow_html=True)


def page_temporalite(df):
    header("Temporalité", "Analyse de la dynamique temporelle du parcours client")

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("Jour le plus actif", df["jour_semaine"].value_counts().idxmax() if len(df) else "-")
    with c2:
        pic = df.groupby("annee_mois").size().idxmax() if len(df) else "-"
        kpi_card("Mois le plus actif", pic)
    with c3:
        kpi_card("Période couverte", f"{df['annee'].min()} – {df['annee'].max()}" if len(df) else "-")

    st.markdown('<div class="afb-card">', unsafe_allow_html=True)
    st.markdown("**Évolution quotidienne du volume et du montant des transactions**")
    daily = df.groupby(df["date_interaction"].dt.date).agg(
        nombre=("pk_interaction", "count"), montant=("montant_transaction", "sum")
    ).reset_index()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=daily["date_interaction"], y=daily["nombre"], name="Interactions",
                              line=dict(color=RED), yaxis="y1"))
    fig.add_trace(go.Scatter(x=daily["date_interaction"], y=daily["montant"], name="Montant (FCFA)",
                              line=dict(color=BLACK, dash="dot"), yaxis="y2"))
    fig.update_layout(
        height=360, margin=dict(t=10),
        yaxis=dict(title="Interactions"),
        yaxis2=dict(title="Montant", overlaying="y", side="right"),
        legend=dict(orientation="h", y=1.1),
    )
    st.plotly_chart(fig, width='stretch')
    st.markdown("</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="afb-card">', unsafe_allow_html=True)
        st.markdown("**Répartition par jour de la semaine**")
        order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        labels_fr = {"Monday": "Lundi", "Tuesday": "Mardi", "Wednesday": "Mercredi", "Thursday": "Jeudi",
                     "Friday": "Vendredi", "Saturday": "Samedi", "Sunday": "Dimanche"}
        dow = df["jour_semaine"].value_counts().reindex(order).reset_index()
        dow.columns = ["jour", "nombre"]
        dow["jour"] = dow["jour"].map(labels_fr)
        fig = px.bar(dow, x="jour", y="nombre", text_auto=True)
        fig.update_layout(height=320, xaxis_title="", yaxis_title="", margin=dict(t=10))
        st.plotly_chart(fig, width='stretch')
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="afb-card">', unsafe_allow_html=True)
        st.markdown("**Comparaison annuelle**")
        yr = df.groupby("annee").size().reset_index(name="nombre")
        fig = px.bar(yr, x="annee", y="nombre", text_auto=True)
        fig.update_layout(height=320, xaxis_title="", yaxis_title="", margin=dict(t=10))
        st.plotly_chart(fig, width='stretch')
        st.markdown("</div>", unsafe_allow_html=True)


def page_canal(df):
    header("Analyse par canal", "En ligne vs en agence — comportement multicanal du parcours client")

    c1, c2 = st.columns(2)
    with c1:
        online = df[df["type_canal"] == "En ligne"]
        part = 100 * len(online) / len(df) if len(df) else 0
        kpi_card("Part du digital", f"{part:.1f}%", "des interactions réalisées en ligne")
    with c2:
        ok = df[df["nom_status"] == "Réussie"]
        kpi_card("Montant traité", format_fcfa(ok["montant_transaction"].sum()))

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="afb-card">', unsafe_allow_html=True)
        st.markdown("**Évolution mensuelle par canal**")
        m = df.groupby(["annee_mois", "type_canal"]).size().reset_index(name="nombre")
        fig = px.area(m, x="annee_mois", y="nombre", color="type_canal")
        fig.update_layout(height=340, xaxis_title="", yaxis_title="", margin=dict(t=10), legend_title="")
        st.plotly_chart(fig, width='stretch')
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="afb-card">', unsafe_allow_html=True)
        st.markdown("**Type de transaction par canal**")
        ct = df.groupby(["type_canal", "type_transaction"]).size().reset_index(name="nombre")
        fig = px.bar(ct, x="nombre", y="type_transaction", color="type_canal", orientation="h", barmode="group")
        fig.update_layout(height=340, yaxis_title="", xaxis_title="", margin=dict(t=10), legend_title="")
        st.plotly_chart(fig, width='stretch')
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="afb-card">', unsafe_allow_html=True)
    st.markdown("**Taux de réussite par canal**")
    tx = df.groupby(["type_canal", "nom_status"]).size().reset_index(name="nombre")
    fig = px.bar(tx, x="type_canal", y="nombre", color="nom_status", barmode="stack")
    fig.update_layout(height=320, xaxis_title="", yaxis_title="", margin=dict(t=10), legend_title="Statut")
    st.plotly_chart(fig, width='stretch')
    st.markdown("</div>", unsafe_allow_html=True)


def page_agence(df):
    header("Analyse par agence", "Performance comparée du réseau d'agences")

    top_n = st.slider("Nombre d'agences à afficher", 5, 30, 15)
    ok = df[df["nom_status"] == "Réussie"]
    agg = ok.groupby(["nom_agence", "nom_ville", "lat", "lon"]).agg(
        montant=("montant_transaction", "sum"), nombre=("pk_interaction", "count")
    ).reset_index().sort_values("montant", ascending=False)

    col1, col2 = st.columns([3, 2])
    with col1:
        st.markdown('<div class="afb-card">', unsafe_allow_html=True)
        st.markdown(f"**Top {top_n} agences par montant traité**")
        top = agg.head(top_n)
        fig = px.bar(top, x="montant", y="nom_agence", orientation="h", text_auto=".2s")
        fig.update_layout(height=460, yaxis=dict(autorange="reversed"), yaxis_title="", xaxis_title="Montant (FCFA)", margin=dict(t=10))
        st.plotly_chart(fig, width='stretch')
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="afb-card">', unsafe_allow_html=True)
        st.markdown("**Répartition géographique**")
        geo = agg.dropna(subset=["lat", "lon"])
        fig = px.scatter_mapbox(
            geo, lat="lat", lon="lon", size="montant", color="montant",
            hover_name="nom_agence", hover_data={"nombre": True, "lat": False, "lon": False},
            color_continuous_scale=["#111111", "#C8102E"], zoom=4.7,
            center={"lat": 5.5, "lon": 12.5},
        )
        fig.update_layout(mapbox_style="carto-positron", height=460, margin=dict(t=10, l=0, r=0, b=0))
        st.plotly_chart(fig, width='stretch')
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="afb-card">', unsafe_allow_html=True)
    st.markdown("**Détail par agence**")
    st.dataframe(
        agg.rename(columns={"nom_agence": "Agence", "nom_ville": "Ville", "montant": "Montant (FCFA)", "nombre": "Nb interactions"})
           [["Agence", "Ville", "Nb interactions", "Montant (FCFA)"]],
        width='stretch', hide_index=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def page_produit(df):
    header("Analyse par produit", "Usage et pénétration des produits et services")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="afb-card">', unsafe_allow_html=True)
        st.markdown("**Répartition des interactions par produit**")
        p = df.groupby("nom_produit").size().reset_index(name="nombre").sort_values("nombre", ascending=False)
        fig = px.treemap(p, path=["nom_produit"], values="nombre",
                          color="nombre", color_continuous_scale=["#F5E4E7", RED])
        fig.update_layout(height=380, margin=dict(t=10))
        st.plotly_chart(fig, width='stretch')
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="afb-card">', unsafe_allow_html=True)
        st.markdown("**Sous-produits les plus utilisés**")
        sp = df.groupby("nom_sous_produit").size().reset_index(name="nombre").sort_values("nombre", ascending=False).head(10)
        fig = px.bar(sp, x="nombre", y="nom_sous_produit", orientation="h", text_auto=True)
        fig.update_layout(height=380, yaxis=dict(autorange="reversed"), yaxis_title="", xaxis_title="", margin=dict(t=10))
        st.plotly_chart(fig, width='stretch')
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="afb-card">', unsafe_allow_html=True)
    st.markdown("**Montant moyen par type de transaction**")
    ok = df[(df["nom_status"] == "Réussie") & (df["montant_transaction"] > 0)]
    tt = ok.groupby("type_transaction")["montant_transaction"].mean().reset_index().sort_values("montant_transaction", ascending=False)
    fig = px.bar(tt, x="type_transaction", y="montant_transaction", text_auto=".2s")
    fig.update_layout(height=340, xaxis_title="", yaxis_title="Montant moyen (FCFA)", margin=dict(t=10))
    fig.update_xaxes(tickangle=-30)
    st.plotly_chart(fig, width='stretch')
    st.markdown("</div>", unsafe_allow_html=True)


def page_client(df):
    header("Analyse client", "Profil et comportement des clients")

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("Clients dans le périmètre", f"{df['fk_client'].nunique():,}".replace(",", " "))
    with c2:
        part_part = 100 * (df["type_client"] == "Particulier").sum() / len(df) if len(df) else 0
        kpi_card("Part Particuliers", f"{part_part:.0f}%")
    with c3:
        top_seg = df["segment"].value_counts().idxmax() if len(df) else "-"
        kpi_card("Segment dominant", top_seg)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="afb-card">', unsafe_allow_html=True)
        st.markdown("**Répartition par segment**")
        seg = df["segment"].value_counts().reset_index()
        seg.columns = ["segment", "nombre"]
        fig = px.bar(seg, x="nombre", y="segment", orientation="h", text_auto=True)
        fig.update_layout(height=380, yaxis=dict(autorange="reversed"), yaxis_title="", xaxis_title="", margin=dict(t=10))
        st.plotly_chart(fig, width='stretch')
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="afb-card">', unsafe_allow_html=True)
        st.markdown("**Type de client & genre**")
        tc = df.drop_duplicates("fk_client")
        fig = px.sunburst(tc, path=["type_client", "genre_client"], color_discrete_sequence=PALETTE)
        fig.update_layout(height=380, margin=dict(t=10))
        st.plotly_chart(fig, width='stretch')
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="afb-card">', unsafe_allow_html=True)
    st.markdown("**Top 10 clients par montant transigé**")
    ok = df[df["nom_status"] == "Réussie"]
    top_c = ok.groupby(["fk_client", "nom_client", "segment"])["montant_transaction"].sum().reset_index()
    top_c = top_c.sort_values("montant_transaction", ascending=False).head(10)
    top_c["montant_transaction"] = top_c["montant_transaction"].map(format_fcfa)
    st.dataframe(
        top_c.rename(columns={"nom_client": "Client", "segment": "Segment", "montant_transaction": "Montant total"})
             [["Client", "Segment", "Montant total"]],
        width='stretch', hide_index=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def page_gestionnaire(df):
    header("Gestionnaires de comptes", "Portefeuille et performance des gestionnaires")

    ok = df[df["nom_status"] == "Réussie"]
    agg = ok.groupby("nom_gestionnaire").agg(
        clients=("fk_client", "nunique"), montant=("montant_transaction", "sum"),
        interactions=("pk_interaction", "count"),
    ).reset_index().sort_values("montant", ascending=False)

    c1, c2 = st.columns(2)
    with c1:
        kpi_card("Gestionnaires actifs", f"{df['fk_gestionnaire'].nunique()}")
    with c2:
        kpi_card("Portefeuille moyen", f"{agg['clients'].mean():.0f} clients" if len(agg) else "-")

    st.markdown('<div class="afb-card">', unsafe_allow_html=True)
    st.markdown("**Top 15 gestionnaires par montant géré**")
    top = agg.head(15)
    fig = px.bar(top, x="montant", y="nom_gestionnaire", orientation="h", text_auto=".2s",
                 hover_data=["clients", "interactions"])
    fig.update_layout(height=460, yaxis=dict(autorange="reversed"), yaxis_title="", xaxis_title="Montant (FCFA)", margin=dict(t=10))
    st.plotly_chart(fig, width='stretch')
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="afb-card">', unsafe_allow_html=True)
    st.markdown("**Détail des portefeuilles**")
    agg_display = agg.copy()
    agg_display["montant"] = agg_display["montant"].map(format_fcfa)
    st.dataframe(
        agg_display.rename(columns={"nom_gestionnaire": "Gestionnaire", "clients": "Nb clients",
                                     "montant": "Montant géré", "interactions": "Interactions"}),
        width='stretch', hide_index=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


# ----------------------------------------------------------------------
# Point d'entrée
# ----------------------------------------------------------------------
def main():
    if not is_authenticated():
        login_page()
        return

    df_all = load_fact_denormalized()
    page, df = sidebar_filters(df_all)

    if len(df) == 0:
        header(page, "Aucune donnée pour les filtres sélectionnés")
        st.warning("Aucune interaction ne correspond aux filtres sélectionnés. Élargissez la période ou les critères.")
        return

    if page == "Vue d'ensemble":
        page_overview(df)
    elif page == "Temporalité":
        page_temporalite(df)
    elif page == "Canal":
        page_canal(df)
    elif page == "Agence":
        page_agence(df)
    elif page == "Produit":
        page_produit(df)
    elif page == "Client":
        page_client(df)
    elif page == "Gestionnaires":
        page_gestionnaire(df)

    st.markdown(
        "<p style='text-align:center;color:#AAAAAA;font-size:0.75rem;margin-top:2rem;'>"
        "Afriland First Bank — Système décisionnel Parcours Client · Mémoire de Master 2 BI/Data Analyse"
        "</p>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
