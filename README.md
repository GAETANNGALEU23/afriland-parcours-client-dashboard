# Dashboard Parcours Client — Afriland First Bank

Application Streamlit de restitution du système décisionnel « Parcours
Client », réalisée dans le cadre d'un mémoire de Master 2 (Business
Intelligence — Data Analyse).

## Fonctionnalités

- Page d'authentification (comptes de démonstration inclus)
- 7 vues d'analyse : Vue d'ensemble, Temporalité, Canal, Agence,
  Produit, Client, Gestionnaires
- Filtres globaux : période, canal, agence, segment, produit, statut
- Thème visuel Afriland First Bank (rouge / noir / blanc)
- Modèle de données fidèle au datamart en étoile du mémoire (table de
  faits `interaction` + 9 dimensions)

## Structure du projet

```
streamlit_app/
├── app.py                  # Application principale
├── auth.py                 # Authentification
├── data_loader.py          # Chargement et préparation des données
├── requirements.txt
├── .streamlit/config.toml  # Thème natif Streamlit
├── assets/
│   ├── logo_placeholder.png   # Logo temporaire — à remplacer
│   └── style.css
└── data/
    ├── dim_*.csv            # Tables de dimension (données réelles fournies)
    └── interaction.csv      # Table de faits (voir note ci-dessous)
```

## ⚠️ À faire avant publication / soutenance

1. **Logo** : `assets/logo_placeholder.png` est un logo générique de
   substitution. Remplacez-le par le logo officiel d'Afriland First
   Bank (fichier `assets/logo_afriland.png`, format PNG avec fond
   transparent recommandé) — l'application le détecte automatiquement.
2. **Comptes de connexion** : les identifiants de démonstration
   (`admin` / `direction`) sont codés dans `auth.py` à titre d'exemple.
   Avant tout déploiement public, déplacez-les vers
   `.streamlit/secrets.toml` (fichier à ne **jamais** committer sur
   GitHub) :
   ```toml
   [credentials]
   admin = "<hash_sha256>"
   ```
3. **Table de faits `interaction`** : voir note méthodologique
   ci-dessous — à documenter explicitement dans le Chapitre 4.

## Note méthodologique — génération de la table de faits

Les 9 tables de dimension utilisées sont vos données réelles
(`fichiers_excel_par_table.zip`). La table de faits `interaction`
n'était pas fournie (chargement manuel, comme indiqué dans
`02_insert_dimensions.sql`) : elle a donc été **simulée** de façon
contrôlée à partir des dimensions réelles, afin que l'application soit
démontrable de bout en bout :

- 60 000 interactions réparties sur les 5 000 clients réels (loi
  log-normale : quelques clients très actifs, beaucoup de clients
  occasionnels — plus réaliste qu'une répartition uniforme) ;
- chaque interaction utilise un couple client/compte réellement
  existant (`aide_client_compte.xlsx`), un canal, un produit et un
  type de transaction cohérents entre eux (ex. : SARA Money est
  majoritairement utilisé en ligne, un dépôt espèces majoritairement
  en agence) ;
- les montants respectent des fourchettes réalistes par type de
  transaction (ex. : recharge crédit téléphonique de quelques
  centaines à 20 000 FCFA, virement émis jusqu'à 5 000 000 FCFA) ;
- le statut est très majoritairement « Réussie » (90 %), avec une
  fraction d'échecs/rejets/annulations réaliste ;
- la répartition dans le temps suit une tendance croissante (adoption
  digitale progressive) avec un léger creux le dimanche.

**Pour la soutenance**, il est recommandé de préciser clairement que
la table de faits est une simulation contrôlée reproduisant la
structure et la logique métier réelles, en l'absence d'un extrait de
production. Le script de génération (`gen_fact.py`, fourni à part)
peut être ré-exécuté pour produire un nouveau jeu de données ou
remplacé par un véritable export une fois disponible — la structure
des colonnes attendue par l'application resterait identique.

## Installation locale

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Déploiement sur Streamlit Community Cloud

1. Poussez ce dossier sur un dépôt GitHub (public ou privé).
2. Sur [share.streamlit.io](https://share.streamlit.io), créez une
   nouvelle application en pointant vers `app.py`.
3. Ajoutez vos secrets (identifiants) dans les paramètres de
   l'application si vous avez suivi l'étape 2 ci-dessus.
4. Déployez — l'URL générée peut être intégrée telle quelle au
   Chapitre 4 du mémoire (captures d'écran + lien).
