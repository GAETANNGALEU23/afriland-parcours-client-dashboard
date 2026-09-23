"""
Authentification de l'application.

Pour la démonstration, les comptes sont définis ci-dessous (mots de
passe stockés hachés en SHA-256, jamais en clair). Pour un déploiement
réel, remplacer ce dictionnaire par une lecture depuis st.secrets
(fichier .streamlit/secrets.toml, non versionné sur GitHub) :

    [credentials]
    admin = "hash_sha256_ici"

et charger via st.secrets["credentials"].
"""

import hashlib
import streamlit as st


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# Comptes de démonstration : admin / afriland2026  —  direction / parcours2026
USERS = {
    "admin": {
        "hash": _hash("afriland2026"),
        "nom_affiche": "Administrateur",
        "role": "Administrateur",
    },
    "direction": {
        "hash": _hash("parcours2026"),
        "nom_affiche": "Direction Data & IA",
        "role": "Consultation",
    },
}


def check_login(username: str, password: str):
    user = USERS.get(username.strip().lower())
    if user and user["hash"] == _hash(password):
        return user
    return None


def is_authenticated() -> bool:
    return st.session_state.get("authenticated", False)


def login(username: str, user_info: dict):
    st.session_state["authenticated"] = True
    st.session_state["username"] = username
    st.session_state["user_info"] = user_info


def logout():
    for key in ("authenticated", "username", "user_info"):
        st.session_state.pop(key, None)
