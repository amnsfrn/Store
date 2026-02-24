import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Happy Store Kids", layout="wide", page_icon="🛍️")

if 'acces_autorise' not in st.session_state: st.session_state['acces_autorise'] = False
if 'admin_connecte' not in st.session_state: st.session_state['admin_connecte'] = False

# --- CHARGEMENT DES DONNÉES ---
def load_data(file, columns):
    if os.path.exists(file):
        try:
            df = pd.read_csv(file)
            if not df.empty and 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce').dt.date
            return df
        except: return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

def save_data(df, file):
    df.to_csv(file, index=False)

# Chargement initial
df_stock = load_data("stock.csv", ["Article", "PA", "Frais", "PV", "Quantite"])
df_ventes = load_data("ventes.csv", ["Date", "Article", "Qte", "Vente_Total", "Benefice"])
df_retours = load_data("retours.csv", ["Date", "Article", "Qte", "Montant_Rendu"])

# --- CONNEXION ---
if not st.session_state['acces_autorise'] and not st.session_state['admin_connecte']:
    st.title("🔐 Connexion")
    u = st.text_input("Utilisateur")
    p = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter"):
        if u.lower() == "admin" and p == "Thanksgod@99":
            st.session_state['admin_connecte'], st.session_state['acces_autorise'] = True, True
            st.rerun()
        elif u.lower() == "user" and p == "0699302032":
            st.session_state['acces_autorise'] = True
            st.rerun()
        else: st.error("Identifiants incorrects")
    st.stop()

is_admin = st.session_state['admin_connecte']

# --- INTERFACE ---
if is_admin:
    tabs = st.tabs(["🛒 Caisse Directe", "📦 Gestion Stock", "💰 Bénéfices", "📜 Historiques"])
    caisse_tab, stock_tab = tabs[0], tabs[1]
else:
    tabs_u = st.tabs(["🛒 Caisse Directe", "📦 Arrivage"])
    caisse_tab, stock_tab = tabs_u[0], tabs_u[1]

# --- AJOUT D'ARTICLES (GESTION STOCK) ---
with stock_tab:
    st.subheader("➕ Ajouter un Article")
    # clear_on_submit=True permet de vider les cases automatiquement
    with st.form("add_stock_form", clear_on_submit=True):
        n = st.text_input("Nom de l'article")
        q = st.number_input("Quantité totale", min_value=1)
        pa = st.number_input("Prix d'Achat (Unitaire)", min_value=0.0)
        fr_t = st.number_input("Frais de transport (TOTAL pour tout le lot)", min_value=0.0)
        pv = st.number_input("Prix de Vente", min_value=0.0)
        
        if st.form_submit_button("✅ Valider l'Ajout"):
            if n:
                fr_u = fr_t / q if q > 0 else 0
                new_i = pd.DataFrame([[n, pa, fr_u, pv, q]], columns=df_stock.columns)
                df_stock = pd.concat([df_stock, new_i], ignore_index=True)
                save_data(df_stock, "stock.csv")
                st.success(f"L'article '{n}' a été ajouté. Les cases ont été vidées pour le suivant !")
                st.rerun()
            else:
                st.error("Veuillez entrer un nom d'article.")

# --- CAISSE DIRECTE ---
with caisse_tab:
    st.subheader("🛒 Terminal de Vente")
    if df_stock.empty:
        st.info("💡 Le stock est vide. Allez dans l'onglet **Gestion Stock** pour ajouter vos articles.")
    else:
        # Bloc Vente
        with st.expander("💳 ENREGISTRER UNE VENTE", expanded=True):
            with st.form("vente_form", clear_on_submit=True):
                art_v = st.selectbox("Article", sorted(df_stock["Article"].unique().tolist()))
                row = df_stock[df_stock["Article"] == art_v].iloc[0]
                col1, col2 = st.columns(2)
                p_final = col1.number_input("Prix de vente (modifiable)", value=float(row['PV']))
                q_v = col2.number_input("Qté", min_value=1, max_value=int(row['Quantite']))
                
                if st.form_submit_button("Valider Vente"):
                    benef = q_v * (p_final - (row['PA'] + row['Frais']))
                    new_v = pd.DataFrame([[datetime.now().date(), art_v, q_v, q_v*p_final, benef]], columns=df_ventes.columns)
                    df_ventes = pd.concat([df_ventes, new_v], ignore_index=True)
                    df_stock.loc[df_stock["Article"] == art_v, "Quantite"] -= q_v
                    save_data(df_ventes, "ventes.csv"); save_data(df_stock, "stock.csv")
                    st.success("Vente validée !")
                    st.rerun()
