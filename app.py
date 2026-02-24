import streamlit as st
import pandas as pd
from datetime import datetime
import os

# Configuration
st.set_page_config(page_title="Happy Store - Caisse", page_icon="🏪")

# Initialisation
if 'ventes_du_jour' not in st.session_state:
    st.session_state.ventes_du_jour = []

# Titre
st.title("🏪 Happy Store - Caisse")

# Entrée des ventes
with st.form("saisie_vente"):
    col1, col2, col3 = st.columns(3)
    with col1:
        article = st.text_input("Article", placeholder="Nom de l'article")
    with col2:
        prix = st.number_input("Prix de vente (DA)", min_value=0.0, step=10.0)
    with col3:
        st.write("")  # Espacement
        st.write("")
        ajouter = st.form_submit_button("➕ Ajouter la vente")

if ajouter and article and prix > 0:
    st.session_state.ventes_du_jour.append({
        "Heure": datetime.now().strftime("%H:%M"),
        "Article": article,
        "Prix": prix
    })
    st.success(f"✅ {article} ajouté - {prix} DA")
    st.rerun()

# Affichage des ventes du jour
if st.session_state.ventes_du_jour:
    st.divider()
    st.subheader("📋 Ventes du jour")
    
    # Tableau des ventes
    df = pd.DataFrame(st.session_state.ventes_du_jour)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Calcul du total
    total = df["Prix"].sum()
    
    # Total de fin de journée (TRÈS GROS)
    st.divider()
    st.markdown(f"# 🟢 TOTAL DU JOUR : **{total:,.0f} DA**")
    st.divider()
    
    # Bouton pour sauvegarder et réinitialiser
    col1, col2, col3 = st.columns(3)
    with col2:
        if st.button("📅 FIN DE JOURNÉE", type="primary", use_container_width=True):
            # Sauvegarde dans un fichier CSV
            fichier = f"ventes_{datetime.now().strftime('%Y%m%d')}.csv"
            df.to_csv(fichier, index=False)
            
            # Réinitialiser
            st.session_state.ventes_du_jour = []
            st.success(f"✅ Ventes sauvegardées dans {fichier}")
            st.rerun()
else:
    st.info("Aucune vente aujourd'hui. Commencez par ajouter des articles !")

# Pied de page
st.divider()
st.caption(f"Dernière mise à jour : {datetime.now().strftime('%d/%m/%Y %H:%M')}")