import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURATION & DONNÉES ---
st.set_page_config(page_title="Happy Store Kids", layout="wide", page_icon="🛍️")

if 'acces_autorise' not in st.session_state: st.session_state['acces_autorise'] = False
if 'admin_connecte' not in st.session_state: st.session_state['admin_connecte'] = False

def load_data(file, columns):
    if os.path.exists(file):
        try:
            df = pd.read_csv(file)
            return df
        except: return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

def save_data(df, file):
    df.to_csv(file, index=False)

df_stock = load_data("stock.csv", ["Article", "PA", "Frais", "PV", "Quantite"])
df_ventes = load_data("ventes.csv", ["Date", "Article", "Qte", "Vente_Total", "Benefice"])
df_demandes = load_data("demandes.csv", ["Date", "Article", "Qte", "PV_Suggere"])

# --- CONNEXION (Simplifiée pour l'exemple) ---
# ... (Gardez votre bloc de connexion habituel ici)

is_admin = st.session_state['admin_connecte']

# --- INTERFACE ---
if is_admin:
    tabs = st.tabs(["🛒 Caisse Directe", "📦 Gestion Stock", "✅ Validations", "📊 Rapports"])
else:
    tabs = st.tabs(["🛒 Caisse Directe", "📩 Envoyer Arrivage"])

# --- MODULE CAISSE (USER & ADMIN) ---
with tabs[0]:
    st.subheader("🛒 Terminal de Vente")
    if not df_stock.empty:
        # Liste triée pour la recherche
        liste_articles = sorted(df_stock["Article"].unique().tolist())
        
        with st.expander("💳 ENREGISTRER UNE VENTE", expanded=True):
            with st.form("vente_form", clear_on_submit=True):
                # La recherche s'active dès que vous tapez dans cette case
                art_v = st.selectbox("Tapez les premières lettres de l'article", [""] + liste_articles)
                
                if art_v != "":
                    row = df_stock[df_stock["Article"] == art_v].iloc[0]
                    c1, c2 = st.columns(2)
                    pv_v = c1.number_input("Prix (DA)", value=float(row['PV']))
                    qte_v = col2.number_input("Qté", min_value=1, max_value=int(row['Quantite']))
                    
                    if st.form_submit_button("✅ Valider"):
                        # Logique de vente...
                        st.success("Vendu !")
                        st.rerun()
    else:
        st.info("Le stock est vide.")

# --- MODULE GESTION STOCK (ADMIN : RECHERCHE POUR MODIFIER) ---
if is_admin:
    with tabs[1]:
        st.subheader("🔍 Rechercher un article pour modifier/supprimer")
        if not df_stock.empty:
            art_a_modifier = st.selectbox("Chercher l'article à gérer", [""] + sorted(df_stock["Article"].tolist()), key="search_admin")
            
            if art_a_modifier != "":
                idx = df_stock[df_stock["Article"] == art_a_modifier].index[0]
                row = df_stock.loc[idx]
                
                with st.container(border=True):
                    col1, col2, col3, col4, col5 = st.columns(5)
                    new_n = col1.text_input("Nom", value=row['Article'])
                    new_pa = col2.number_input("PA", value=float(row['PA']))
                    new_fr = col3.number_input("Frais", value=float(row['Frais']))
                    new_pv = col4.number_input("PV", value=float(row['PV']))
                    new_q = col5.number_input("Stock", value=int(row['Quantite']))
                    
                    btn1, btn2 = st.columns(2)
                    if btn1.button("💾 Sauvegarder les modifications"):
                        df_stock.loc[idx] = [new_n, new_pa, new_fr, new_pv, new_q]
                        save_data(df_stock, "stock.csv")
                        st.success("Modifié !")
                        st.rerun()
                    if btn2.button("🗑️ Supprimer l'article"):
                        df_stock = df_stock.drop(idx)
                        save_data(df_stock, "stock.csv")
                        st.rerun()
