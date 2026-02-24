import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Happy Store Kids", layout="wide", page_icon="🛍️")

if 'acces_autorise' not in st.session_state: st.session_state['acces_autorise'] = False
if 'admin_connecte' not in st.session_state: st.session_state['admin_connecte'] = False

# --- FONCTIONS DE DONNÉES ---
def load_data(file, columns):
    if os.path.exists(file):
        try:
            df = pd.read_csv(file)
            if not df.empty and 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], dayfirst=True).dt.date
            return df
        except: return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

def save_data(df, file):
    df.to_csv(file, index=False)

# Chargement
df_stock = load_data("stock.csv", ["Article", "PA", "Frais", "PV", "Quantite"])
df_ventes = load_data("ventes.csv", ["Date", "Article", "Qte", "Vente_Total", "Benefice"])
df_retours = load_data("retours.csv", ["Date", "Article", "Qte", "Montant_Rendu"])
df_demandes = load_data("demandes_stock.csv", ["Date", "Article", "Qte_Ajout", "PV_Suggere"])

# --- CONNEXION ---
if not st.session_state['acces_autorise'] and not st.session_state['admin_connecte']:
    st.title("🔐 Happy Store Kids")
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

if st.sidebar.button("🔴 Déconnexion"):
    st.session_state.clear()
    st.rerun()

is_admin = st.session_state['admin_connecte']

# --- INTERFACE ADMIN ---
if is_admin:
    st.title("📊 Direction - Happy Store Kids")
    tabs = st.tabs(["🛒 Caisse Directe", "📦 Gestion Stock", "💰 Bénéfices", "📜 Historiques"])
    
    with tabs[1]:
        st.subheader("➕ Ajouter un Article (Direct)")
        with st.form("admin_add_direct"):
            n = st.text_input("Nom de l'article")
            q = st.number_input("Quantité totale reçue", min_value=1)
            pa = st.number_input("Prix d'Achat unitaire (PA)", min_value=0.0)
            frais_globaux = st.number_input("Frais de transport pour TOUTE la quantité", min_value=0.0)
            pv = st.number_input("Prix de Vente (PV)", min_value=0.0)
            
            if st.form_submit_button("Ajouter au Stock"):
                if n:
                    # Calcul des frais par pièce automatique
                    frais_unitaire = frais_globaux / q
                    new_row = pd.DataFrame([[n, pa, frais_unitaire, pv, q]], columns=df_stock.columns)
                    df_stock = pd.concat([df_stock, new_row], ignore_index=True)
                    save_data(df_stock, "stock.csv")
                    st.success(f"Article ajouté ! Frais par pièce calculés : {frais_unitaire:.2f} DA")
                    st.rerun()

        st.divider()
        st.subheader("✅ Validation des arrivages User")
        if not df_demandes.empty:
            for i, row in df_demandes.iterrows():
                with st.expander(f"📦 {row['Article']} (+{row['Qte_Ajout']})"):
                    c1, c2, c3 = st.columns(3)
                    pa_v = c1.number_input("PA Unitaire", key=f"pa_{i}")
                    fr_g = c2.number_input("Frais Transport TOTAUX", key=f"frg_{i}")
                    pv_v = c3.number_input("PV Final", value=float(row['PV_Suggere']), key=f"pv_{i}")
                    
                    if st.button("Valider l'entrée", key=f"val_{i}"):
                        fr_u = fr_g / int(row['Qte_Ajout'])
                        # Mise à jour stock logic... (identique mais avec fr_u)
                        new_item = pd.DataFrame([[row['Article'], pa_v, fr_u, pv_v, int(row['Qte_Ajout'])]], columns=df_stock.columns)
                        df_stock = pd.concat([df_stock, new_item], ignore_index=True)
                        df_demandes = df_demandes.drop(i)
                        save_data(df_stock, "stock.csv"); save_data(df_demandes, "demandes_stock.csv")
                        st.rerun()

# --- RESTE DU CODE (CAISSE & USER) ---
# ... (La logique de vente et de retour reste la même)
