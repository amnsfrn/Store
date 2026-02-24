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
            return df
        except: return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

def save_data(df, file):
    df.to_csv(file, index=False)

# Chargement
df_stock = load_data("stock.csv", ["Article", "PA", "Frais", "PV", "Quantite"])
df_demandes = load_data("demandes.csv", ["Date", "Article", "Qte", "PV_Suggere"])

# --- CONNEXION ---
if not st.session_state['acces_autorise'] and not st.session_state['admin_connecte']:
    st.title("🔐 Connexion Happy Store Kids")
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

# --- BARRE LATÉRALE ---
if st.sidebar.button("🔴 Déconnexion"):
    st.session_state.clear()
    st.rerun()

# --- INTERFACE ---
if is_admin:
    tabs = st.tabs(["🛒 Caisse", "📦 Gestion Stock", "✅ Validations Arrivages", "💰 Rapports"])
else:
    tabs = st.tabs(["🛒 Caisse", "📩 Envoyer Arrivage"])

# --- MODULE STOCK (ADMIN SEULEMENT) ---
if is_admin:
    with tabs[1]:
        st.subheader("📦 Liste Complète du Stock")
        
        # Modification / Suppression
        for i, row in df_stock.iterrows():
            with st.expander(f"✏️ Modifier : {row['Article']} (Reste: {row['Quantite']})"):
                c1, c2, c3, c4, c5 = st.columns(5)
                new_n = c1.text_input("Nom", value=row['Article'], key=f"n_{i}")
                new_pa = c2.number_input("PA", value=float(row['PA']), key=f"pa_{i}")
                new_fr = c3.number_input("Frais", value=float(row['Frais']), key=f"fr_{i}")
                new_pv = c4.number_input("PV", value=float(row['PV']), key=f"pv_{i}")
                new_q = c5.number_input("Qte", value=int(row['Quantite']), key=f"q_{i}")
                
                col_btn1, col_btn2 = st.columns(2)
                if col_btn1.button("💾 Sauvegarder", key=f"save_{i}"):
                    df_stock.loc[i] = [new_n, new_pa, new_fr, new_pv, new_q]
                    save_data(df_stock, "stock.csv")
                    st.rerun()
                if col_btn2.button("🗑️ Supprimer", key=f"del_{i}"):
                    df_stock = df_stock.drop(i)
                    save_data(df_stock, "stock.csv")
                    st.rerun()

    # --- MODULE VALIDATION (ADMIN SEULEMENT) ---
    with tabs[2]:
        st.subheader("🔔 Demandes d'arrivages à valider")
        if df_demandes.empty:
            st.write("Aucune demande en attente.")
        else:
            for i, row in df_demandes.iterrows():
                with st.form(f"val_form_{i}"):
                    st.write(f"**Date:** {row['Date']}")
                    col_a1, col_a2, col_a3 = st.columns(3)
                    val_nom = col_a1.text_input("Nom Article", value=row['Article'])
                    val_qte = col_a2.number_input("Quantité", value=int(row['Qte']))
                    val_pv = col_a3.number_input("Prix de Vente", value=float(row['PV_Suggere']))
                    
                    st.write("---")
                    col_p1, col_p2 = st.columns(2)
                    val_pa = col_p1.number_input("Prix d'Achat (Admin)", min_value=0.0)
                    val_fr_t = col_p2.number_input("Frais Transport TOTAUX (Admin)", min_value=0.0)
                    
                    if st.form_submit_button("✅ Valider et Ajouter au Stock"):
                        fr_u = val_fr_t / val_qte if val_qte > 0 else 0
                        new_item = pd.DataFrame([[val_nom, val_pa, fr_u, val_pv, val_qte]], columns=df_stock.columns)
                        df_stock = pd.concat([df_stock, new_item], ignore_index=True)
                        df_demandes = df_demandes.drop(i)
                        save_data(df_stock, "stock.csv")
                        save_data(df_demandes, "demandes.csv")
                        st.rerun()

# --- MODULE ARRIVAGE (USER SEULEMENT) ---
if not is_admin:
    with tabs[1]:
        st.subheader("📩 Déclarer un nouvel arrivage")
        with st.form("user_arrivage", clear_on_submit=True):
            n = st.text_input("Nom de l'article")
            q = st.number_input("Quantité reçue", min_value=1)
            pv = st.number_input("Prix de vente souhaité", min_value=0.0)
            if st.form_submit_button("Envoyer pour Validation"):
                if n:
                    new_d = pd.DataFrame([[datetime.now().strftime("%d/%m/%Y"), n, q, pv]], columns=df_demandes.columns)
                    df_demandes = pd.concat([df_demandes, new_d], ignore_index=True)
                    save_data(df_demandes, "demandes.csv")
                    st.success("Demande envoyée à l'administrateur !")
