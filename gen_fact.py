import pandas as pd
import numpy as np

rng = np.random.default_rng(42)

base = "/home/claude/datamart/fichiers_excel/"
client = pd.read_excel(base+"dim_client.xlsx")
aide = pd.read_excel(base+"aide_client_compte.xlsx")
compte = pd.read_excel(base+"dim_compte_client.xlsx")
produit = pd.read_excel(base+"dim_produit.xlsx")
canal = pd.read_excel(base+"dim_canal.xlsx")
statut = pd.read_excel(base+"dim_statut_interaction.xlsx")
typetx = pd.read_excel(base+"dim_type_transaction.xlsx")
gestionnaire = pd.read_excel(base+"dim_gestionnaire.xlsx")
dates = pd.read_excel(base+"dim_date_interaction.xlsx")
agence = pd.read_excel(base+"dim_agence_operation.xlsx")

TODAY = pd.Timestamp("2026-09-23")
dates = dates[dates["date"] <= TODAY].reset_index(drop=True)

# maps
canal_id = dict(zip(canal["type_canal"], canal["id_canal"]))
statut_id = dict(zip(statut["nom_status"], statut["pk_status"]))
type_id = dict(zip(typetx["type_transaction"], typetx["id_type_transaction"]))

# assign each client a fixed gestionnaire (stable portfolio)
gest_codes = gestionnaire["code_gestionnaire"].tolist()
client = client.copy()
client["fk_gestionnaire"] = client["pk_client"].apply(lambda x: gest_codes[x % len(gest_codes)])

# client -> list of comptes
client_comptes = aide.groupby("pk_client")["pk_numero_compte_client"].apply(list).to_dict()
compte_solde = dict(zip(compte["pk_numero_compte_client"], compte["solde_compte"]))

PRODUCT_CFG = {
    "Compte bancaire": {"canal": {"En agence": 0.75, "En ligne": 0.25},
        "types": ["Dépôt espèces","Retrait espèces","Virement émis","Virement reçu","Souscription / ouverture","Consultation de solde"]},
    "Carte bancaire": {"canal": {"En agence": 0.3, "En ligne": 0.7},
        "types": ["Paiement marchand","Retrait espèces","Consultation de solde"]},
    "eFirst": {"canal": {"En ligne": 0.95, "En agence": 0.05},
        "types": ["Consultation de solde","Virement émis","Paiement de facture","Demande de relevé"]},
    "SARA Money": {"canal": {"En ligne": 0.9, "En agence": 0.1},
        "types": ["Envoi d'argent","Réception d'argent","Paiement marchand","Recharge crédit téléphonique","Retrait espèces","Dépôt espèces"]},
    "SARA Banking": {"canal": {"En ligne": 0.85, "En agence": 0.15},
        "types": ["Consultation de solde","Virement émis","Recharge crédit téléphonique","Paiement de facture"]},
    "SMS First": {"canal": {"En ligne": 1.0},
        "types": ["Consultation de solde","Demande de relevé"]},
    "Crédit": {"canal": {"En agence": 0.8, "En ligne": 0.2},
        "types": ["Remboursement de crédit","Souscription / ouverture","Virement reçu"]},
    "Épargne et placement": {"canal": {"En agence": 0.7, "En ligne": 0.3},
        "types": ["Dépôt espèces","Virement émis","Souscription / ouverture"]},
    "Transfert international": {"canal": {"En agence": 0.6, "En ligne": 0.4},
        "types": ["Envoi d'argent","Réception d'argent","Virement émis"]},
}

AMOUNT_RANGES = {
    "Dépôt espèces": (5000, 2_000_000),
    "Retrait espèces": (5000, 1_000_000),
    "Virement émis": (10000, 5_000_000),
    "Virement reçu": (10000, 5_000_000),
    "Paiement de facture": (2000, 300_000),
    "Recharge crédit téléphonique": (500, 20_000),
    "Paiement marchand": (1000, 500_000),
    "Envoi d'argent": (1000, 1_000_000),
    "Réception d'argent": (1000, 1_000_000),
    "Consultation de solde": (0, 0),
    "Demande de relevé": (0, 0),
    "Souscription / ouverture": (0, 100_000),
    "Remboursement de crédit": (10000, 2_000_000),
}

STATUT_WEIGHTS = {"Réussie": 0.90, "Échouée": 0.04, "En attente": 0.03, "Annulée": 0.02, "Rejetée": 0.01}
statut_names = list(STATUT_WEIGHTS.keys())
statut_w = np.array(list(STATUT_WEIGHTS.values()))

produit_by_cat = produit.groupby("nom_produit")["pk_produit"].apply(list).to_dict()

# number of interactions per client: skewed (lognormal), target ~ total N
N_TARGET = 60000
n_clients = len(client)
weights = rng.lognormal(mean=0.0, sigma=0.9, size=n_clients)
weights = weights / weights.sum()
n_per_client = rng.multinomial(N_TARGET, weights)

# date weighting: mild upward trend + slight weekday effect (lower on Sunday) + Dec/June bump
dates = dates.copy()
dates["dow"] = pd.to_datetime(dates["date"]).dt.dayofweek  # 0=Mon .. 6=Sun
dates["month"] = pd.to_datetime(dates["date"]).dt.month
t_index = np.arange(len(dates))
trend = 0.6 + 0.8 * (t_index / max(t_index.max(),1))  # growth over time
weekday_factor = np.where(dates["dow"].values == 6, 0.5, 1.0)  # Sunday lower
season_factor = np.where(dates["month"].isin([6,7,12]).values, 1.25, 1.0)
date_w = trend * weekday_factor * season_factor
date_w = date_w / date_w.sum()
date_choices_idx = dates.index.values

rows = []
pk = 1
prod_cats = list(PRODUCT_CFG.keys())
prod_cat_weights = np.array([5,4,3,4,4,3,4,2,3], dtype=float)  # rough popularity, matches product counts
prod_cat_weights = prod_cat_weights / prod_cat_weights.sum()

for i, row in client.reset_index(drop=True).iterrows():
    n = n_per_client[i]
    if n == 0:
        continue
    pkc = row["pk_client"]
    comptes = client_comptes.get(pkc, [])
    if not comptes:
        continue
    fk_gest = row["fk_gestionnaire"]

    cat_idx = rng.choice(len(prod_cats), size=n, p=prod_cat_weights)
    date_idx = rng.choice(date_choices_idx, size=n, p=date_w)
    compte_idx = rng.choice(len(comptes), size=n)

    for k in range(n):
        cat = prod_cats[cat_idx[k]]
        cfg = PRODUCT_CFG[cat]
        canal_names = list(cfg["canal"].keys())
        canal_p = np.array(list(cfg["canal"].values()))
        canal_p = canal_p / canal_p.sum()
        canal_name = rng.choice(canal_names, p=canal_p)
        type_name = rng.choice(cfg["types"])
        fk_produit = int(rng.choice(produit_by_cat[cat]))

        lo, hi = AMOUNT_RANGES[type_name]
        montant = 0 if hi == 0 else int(rng.uniform(lo, hi))
        if type_name in ("Consultation de solde", "Demande de relevé"):
            frais = 0
        elif montant > 0:
            frais = int(montant * rng.uniform(0.0, 0.02))
        else:
            frais = 0

        statut_name = rng.choice(statut_names, p=statut_w)
        d = dates.loc[date_idx[k], "date"]

        fk_compte = comptes[compte_idx[k]]
        solde = compte_solde.get(fk_compte, 0)
        nb_ops = 1 if rng.random() > 0.05 else int(rng.integers(2, 4))

        rows.append((
            pk, pkc, fk_produit, canal_id[canal_name], type_id[type_name],
            fk_gest, fk_compte, statut_id[statut_name], d, montant, frais, solde, nb_ops
        ))
        pk += 1

fact = pd.DataFrame(rows, columns=[
    "pk_interaction","fk_client","fk_produit","fk_canal","fk_type_transaction",
    "fk_gestionnaire","fk_compte","fk_statut","fk_date","montant_transaction",
    "frais_transaction","solde","nombre_operations"
])
fact["date_interaction"] = fact["fk_date"]
print(fact.shape)
print(fact.head())
fact.to_csv("/home/claude/streamlit_app/data/interaction.csv", index=False)
print("saved")
