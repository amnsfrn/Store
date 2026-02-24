import streamlit as st
from datetime import datetime
import pandas as pd

# Configuration
st.set_page_config(page_title="Happy Store - Caisse", page_icon="🏪")

# Initialisation
if 'ventes' not in st.session_state:
    st.session_state.ventes = []

# Titre
st.title("🏪 Happy Store - Caisse Simple")

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
            "Article": article,
            "Prix (DA)": prix
        })
        st.rerun()

# Affichage des ventes
if st.session_state.ventes:
    st.divider()
    
    # Tableau des ventes
    df = pd.DataFrame(st.session_state.ventes)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Total
    total = df["Prix (DA)"].sum()
    
    st.divider()
    # BOUTON TOTAL EN FIN DE JOURNÉE (très gros)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("💰 TOTAL FIN DE JOURNÉE", type="primary", use_container_width=True):
            st.markdown(f"# 🎯 TOTAL : **{total:,.0f} DA**")
            
            # Option pour réinitialiser
            if st.button("🔄 Nouvelle journée", use_container_width=True):
                # Sauvegarde dans un fichier
                df.to_csv(f"ventes_{datetime.now().strftime('%Y%m%d')}.csv", index=False)
                st.session_state.ventes = []
                st.rerun()
else:
    st.info("Saisissez un article et son prix")