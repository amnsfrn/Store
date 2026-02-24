import streamlit as st
from datetime import datetime
import pandas as pd
import os

# Configuration
st.set_page_config(page_title="Happy Store - Caisse", page_icon="🏪")

# Initialisation de la session
if 'connecte' not in st.session_state:
    st.session_state.connecte = False
if 'ventes' not in st.session_state:
    st.session_state.ventes = []
if 'date_actuelle' not in st.session_state:
    st.session_state.date_actuelle = datetime.now().strftime("%Y-%m-%d")

# PAGE DE CONNEXION
if not st.session_state.connecte:
    st.title("🔐 Happy Store - Connexion")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login"):
            password = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Se connecter", use_container_width=True):
                if password == "0699302032":
                    st.session_state.connecte = True
                    st.rerun()
                else:
                    st.error("Mot de passe incorrect")
    st.stop()

# APPLICATION PRINCIPALE
st.title("🏪 Happy Store - Caisse")

# Vérifier si on a changé de jour
date_du_jour = datetime.now().strftime("%Y-%m-%d")
if date_du_jour != st.session_state.date_actuelle:
    # Sauvegarder les ventes de la veille
    if st.session_state.ventes:
        fichier_veille = f"ventes_{st.session_state.date_actuelle}.csv"
        pd.DataFrame(st.session_state.ventes).to_csv(fichier_veille, index=False)
    # Nouvelle journée
    st.session_state.ventes = []
    st.session_state.date_actuelle = date_du_jour

# Formulaire de saisie
with st.form("saisie", clear_on_submit=True):
    col1, col2, col3 = st.columns([3, 2, 1])
    
    with col1:
        article = st.text_input("Article", placeholder="Nom de l'article", label_visibility="collapsed")
    with col2:
        prix = st.number_input("Prix", min_value=0.0, step=100.0, format="%.0f", label_visibility="collapsed")
    with col3:
        ajouter = st.form_submit_button("➕ Ajouter")

    if ajouter and article and prix > 0:
        st.session_state.ventes.append({
            "Heure": datetime.now().strftime("%H:%M"),
            "Article": article,
            "Prix (DA)": prix
        })
        st.rerun()

# Affichage des ventes du jour
st.subheader(f"📋 Ventes du {datetime.now().strftime('%d/%m/%Y')}")

if st.session_state.ventes:
    # Tableau des ventes
    df = pd.DataFrame(st.session_state.ventes)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Calcul du total
    total = df["Prix (DA)"].sum()
    
    st.divider()
    # Afficher le total
    st.markdown(f"## TOTAL : **{total:,.0f} DA**")
    st.divider()
    
    # Bouton FIN DE JOURNÉE
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔚 FIN DE JOURNÉE", type="primary", use_container_width=True):
            # Sauvegarde
            fichier = f"ventes_{date_du_jour}.csv"
            df.to_csv(fichier, index=False)
            st.success(f"✅ Ventes sauvegardées dans {fichier}")
            
            # Réinitialiser
            st.session_state.ventes = []
            st.rerun()
else:
    st.info("Saisissez un article et son prix")

# Bouton déconnexion dans la barre latérale
with st.sidebar:
    st.title("Menu")
    if st.button("🚪 Déconnexion"):
        st.session_state.connecte = False
        st.rerun()
    
    # Afficher les fichiers de ventes précédentes
    st.divider()
    st.subheader("📂 Archives")
    fichiers = [f for f in os.listdir(".") if f.startswith("ventes_") and f.endswith(".csv")]
    if fichiers:
        fichiers.sort(reverse=True)
        for f in fichiers[:5]:  # Afficher les 5 derniers
            date = f.replace("ventes_", "").replace(".csv", "")
            st.caption(f"📁 {date}")
    else:
        st.caption("Aucune archive")