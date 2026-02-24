import streamlit as st
from datetime import datetime
import pandas as pd
import os

# Configuration
st.set_page_config(page_title="Happy Store - Caisse", page_icon="🏪", layout="wide")

# Initialisation de la session
if 'connecte' not in st.session_state:
    st.session_state.connecte = False
if 'ventes' not in st.session_state:
    st.session_state.ventes = []
if 'date_actuelle' not in st.session_state:
    st.session_state.date_actuelle = datetime.now().strftime("%Y-%m-%d")
if 'page' not in st.session_state:
    st.session_state.page = "caisse"

# PAGE DE CONNEXION
if not st.session_state.connecte:
    st.title("🔐 Happy Store - Connexion")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login"):
            username = st.text_input("Nom d'utilisateur")
            password = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Se connecter", use_container_width=True):
                if username == "user" and password == "0699302032":
                    st.session_state.connecte = True
                    st.rerun()
                else:
                    st.error("Identifiants incorrects")
    st.stop()

# BARRE LATÉRALE
with st.sidebar:
    st.title("🏪 Happy Store")
    st.divider()
    
    # Boutons de navigation
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧾 Caisse", use_container_width=True):
            st.session_state.page = "caisse"
            st.rerun()
    with col2:
        if st.button("📚 Historique", use_container_width=True):
            st.session_state.page = "historique"
            st.rerun()
    
    st.divider()
    
    # Déconnexion
    if st.button("🚪 Déconnexion", use_container_width=True, type="primary"):
        st.session_state.connecte = False
        st.rerun()

# Vérifier si on a changé de jour
date_du_jour = datetime.now().strftime("%Y-%m-%d")
if date_du_jour != st.session_state.date_actuelle:
    # Sauvegarder les ventes de la veille automatiquement
    if st.session_state.ventes:
        fichier_veille = f"ventes_{st.session_state.date_actuelle}.csv"
        pd.DataFrame(st.session_state.ventes).to_csv(fichier_veille, index=False)
    # Nouvelle journée
    st.session_state.ventes = []
    st.session_state.date_actuelle = date_du_jour

# PAGE CAISSE
if st.session_state.page == "caisse":
    st.title("🧾 Caisse enregistreuse")
    st.subheader(f"📅 {datetime.now().strftime('%d/%m/%Y')}")
    
    # Formulaire de saisie
    with st.form("saisie", clear_on_submit=True):
        col1, col2, col3 = st.columns([3, 2, 1])
        
        with col1:
            article = st.text_input("Article", placeholder="Nom de l'article", label_visibility="collapsed")
        with col2:
            prix = st.number_input("Prix", min_value=0.0, step=100.0, format="%.0f", label_visibility="collapsed")
        with col3:
            ajouter = st.form_submit_button("➕ Ajouter", use_container_width=True)
    
        if ajouter and article and prix > 0:
            st.session_state.ventes.append({
                "Heure": datetime.now().strftime("%H:%M"),
                "Article": article,
                "Prix (DA)": prix
            })
            st.rerun()
    
    # Affichage des ventes du jour
    if st.session_state.ventes:
        st.divider()
        
        # Tableau des ventes
        df = pd.DataFrame(st.session_state.ventes)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Calcul du total
        total = df["Prix (DA)"].sum()
        
        st.divider()
        # Afficher le total en GROS
        st.markdown(f"# 💰 TOTAL : **{total:,.0f} DA**")
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
        st.info("Saisissez un article et son prix pour commencer")

# PAGE HISTORIQUE
elif st.session_state.page == "historique":
    st.title("📚 Historique des ventes")
    
    # Récupérer tous les fichiers de ventes
    fichiers = [f for f in os.listdir(".") if f.startswith("ventes_") and f.endswith(".csv")]
    
    if fichiers:
        # Trier par date (plus récent d'abord)
        fichiers.sort(reverse=True)
        
        # Sélecteur de date
        dates = [f.replace("ventes_", "").replace(".csv", "") for f in fichiers]
        dates_format = [datetime.strptime(d, "%Y-%m-%d").strftime("%d/%m/%Y") for d in dates]
        
        selected_date = st.selectbox("Sélectionner une date", dates_format)
        
        # Trouver le fichier correspondant
        index = dates_format.index(selected_date)
        fichier = fichiers[index]
        
        # Lire et afficher les ventes
        df_historique = pd.read_csv(fichier)
        
        st.divider()
        st.subheader(f"📅 Ventes du {selected_date}")
        
        # Afficher le tableau
        st.dataframe(df_historique, use_container_width=True, hide_index=True)
        
        # Calculer et afficher le total
        total_historique = df_historique["Prix (DA)"].sum()
        st.markdown(f"## TOTAL : **{total_historique:,.0f} DA**")
        
        # Statistiques
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Nombre d'articles", len(df_historique))
        with col2:
            st.metric("Prix moyen", f"{df_historique['Prix (DA)'].mean():,.0f} DA")
        with col3:
            st.metric("Total", f"{total_historique:,.0f} DA")
        
        # Bouton pour supprimer (optionnel)
        with st.expander("⚙️ Options"):
            if st.button(f"🗑️ Supprimer les ventes du {selected_date}"):
                os.remove(fichier)
                st.success("Fichier supprimé")
                st.rerun()
    else:
        st.info("Aucun historique disponible")