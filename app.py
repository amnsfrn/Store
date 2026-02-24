import streamlit as st

st.set_page_config(page_title="Gestion Magasin", layout="centered")

# =========================
# INITIALISATION
# =========================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "role" not in st.session_state:
    st.session_state.role = None

if "panier" not in st.session_state:
    st.session_state.panier = []

# Articles simples
ARTICLES = [
    {"nom": "Ensemble Benic’s", "prix": 3500},
    {"nom": "Robe Fille Rose", "prix": 2800},
    {"nom": "T-shirt Garçon Nike", "prix": 2200},
    {"nom": "Pantalon Jeans Junior", "prix": 3000},
    {"nom": "Pyjama Enfant", "prix": 1800},
]

# =========================
# LOGIN
# =========================

if not st.session_state.logged_in:
    st.title("Connexion")

    username = st.text_input("Utilisateur")
    password = st.text_input("Mot de passe", type="password")

    if st.button("Se connecter"):
        if username == "admin" and password == "1234":
            st.session_state.logged_in = True
            st.session_state.role = "admin"
            st.rerun()
        elif username == "user" and password == "1234":
            st.session_state.logged_in = True
            st.session_state.role = "user"
            st.rerun()
        else:
            st.error("Identifiants incorrects")

# =========================
# APPLICATION PRINCIPALE
# =========================

else:

    st.title("Gestion de Magasin")
    st.write(f"Connecté en tant que : {st.session_state.role}")

    # Bouton déconnexion
    if st.button("Se déconnecter"):
        st.session_state.logged_in = False
        st.session_state.role = None
        st.session_state.panier = []
        st.rerun()

    st.divider()

    # =========================
    # RECHERCHE INTELLIGENTE
    # =========================

    recherche = st.text_input("Rechercher un article")

    if recherche:
        resultats = [
            article for article in ARTICLES
            if recherche.lower() in article["nom"].lower()
        ]
    else:
        resultats = ARTICLES

    st.subheader("Articles disponibles")

    for article in resultats:
        col1, col2 = st.columns([3, 1])

        with col1:
            if st.button(article["nom"], key=article["nom"]):
                st.session_state.panier.append(article)

        with col2:
            st.write(f'{article["prix"]} DA')

    # =========================
    # PANIER
    # =========================

    st.divider()
    st.subheader("Panier")

    if st.session_state.panier:
        total = 0
        for i, item in enumerate(st.session_state.panier):
            col1, col2 = st.columns([3,1])
            with col1:
                st.write(f"- {item['nom']}")
            with col2:
                if st.button("❌", key=f"remove_{i}"):
                    st.session_state.panier.pop(i)
                    st.rerun()
            total += item["prix"]

        st.write(f"### Total : {total} DA")

        if st.button("Vider panier"):
            st.session_state.panier = []
            st.rerun()

    else:
        st.write("Panier vide")