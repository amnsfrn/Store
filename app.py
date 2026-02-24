import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="Happy Store Kids", layout="wide", page_icon="🛍️")

if 'acces_autorise' not in st.session_state: st.session_state['acces_autorise'] = False
if 'admin_connecte' not in st.session_state: st.session_state['admin_connecte'] = False

# --- FONCTIONS DE DONNÉES ---
def load_data(file, columns):
    if os.path.exists(file):
        try:
            df = pd.read_csv(file)
            if 'Date' in df.columns and file not in ["sessions.csv", "demandes_stock.csv"]:
                df['Date'] = pd.to_datetime(df['Date'], dayfirst=True).dt.date
            return df
        except: return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

def save_data(df, file):
    df.to_csv(file, index=False)

# Chargement des fichiers
df_stock = load_data("stock.csv", ["Article", "PA", "Frais", "PV", "Quantite"])
df_ventes = load_data("ventes.csv", ["Date", "Article", "Qte", "Vente_Total", "Benefice"])
df_demandes = load_data("demandes_stock.csv", ["Date", "Article", "Qte_Ajout", "PV_Suggere"])

# --- CONNEXION ---
if not st.session_state['acces_autorise'] and not st.session_state['admin_connecte']:
    st.title("🔐 Connexion Magasin")
    u = st.text_input("Utilisateur")
    p = st.text_input("Mot de passe", type="password")
    if st.button("Entrer"):
        if u.lower() == "admin" and p == "Thanksgod@99":
            st.session_state['admin_connecte'] = True
            st.session_state['acces_autorise'] = True
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

# --- INTERFACE ---
if is_admin:
    st.title("📊 Direction - Happy Store Kids")
    tabs = st.tabs(["🛒 Caisse", "📦 Gestion Stock", "💰 Bénéfices", "📜 Historiques"])
    
    with tabs[1]: # GESTION STOCK (ADMIN)
        st.subheader("➕ Ajouter un Article (Direct)")
        with st.form("admin_add_form"):
            col1, col2 = st.columns(2)
            # Recherche intelligente ou nouveau nom
            liste_existante = ["--- NOUVEL ARTICLE ---"] + sorted(df_stock["Article"].tolist())
            choix = col1.selectbox("Sélectionner ou Nouveau", liste_existante)
            nom_art = col1.text_input("Nom de l'article (si nouveau)")
            qte_art = col2.number_input("Quantité à ajouter", min_value=1)
            pa_art = col1.number_input("Prix d'Achat (PA)", min_value=0.0)
            fr_art = col2.number_input("Frais de transport", min_value=0.0)
            pv_art = col2.number_input("Prix de Vente (PV)", min_value=0.0)
            
            if st.form_submit_button("Ajouter directement au stock"):
                final_name = nom_art if choix == "--- NOUVEL ARTICLE ---" else choix
                if final_name:
                    if final_name in df_stock['Article'].values:
                        idx = df_stock[df_stock["Article"] == final_name].index[0]
                        df_stock.at[idx, "Quantite"] += qte_art
                        df_stock.at[idx, "PA"], df_stock.at[idx, "Frais"], df_stock.at[idx, "PV"] = pa_art, fr_art, pv_art
                    else:
                        new_row = pd.DataFrame([[final_name, pa_art, fr_art, pv_art, qte_art]], columns=df_stock.columns)
                        df_stock = pd.concat([df_stock, new_row], ignore_index=True)
                    save_data(df_stock, "stock.csv")
                    st.success(f"{final_name} ajouté !")
                    st.rerun()

        st.divider()
        st.subheader("✅ Demandes de l'user à valider")
        if not df_demandes.empty:
            for i, row in df_demandes.iterrows():
                with st.expander(f"Demande : {row['Article']} (+{row['Qte_Ajout']})"):
                    c_pa = st.number_input("Entrer PA", key=f"pa_{i}")
                    c_fr = st.number_input("Entrer Frais", key=f"fr_{i}")
                    c_pv = st.number_input("Confirmer PV", value=float(row['PV_Suggere']), key=f"pv_{i}")
                    if st.button("Valider cette entrée", key=f"btn_{i}"):
                        # (Code de validation identique au précédent pour mettre à jour stock.csv)
                        st.rerun()

else: # INTERFACE USER
    st.title("🏪 Espace Employé")
    t1, t2 = st.tabs(["🛒 Caisse", "📦 Arrivage Marchandise"])
    
    with t2:
        st.subheader("Ajouter un article reçu")
        with st.form("user_add_form"):
            liste_existante = ["--- NOUVEL ARTICLE ---"] + sorted(df_stock["Article"].tolist())
            choix = st.selectbox("Article", liste_existante)
            nom_art = st.text_input("Nom de l'article (si nouveau)")
            qte_art = st.number_input("Quantité reçue", min_value=1)
            pv_sug = st.number_input("Prix de Vente (PV)", min_value=0.0)
            
            if st.form_submit_button("Envoyer pour validation"):
                final_name = nom_art if choix == "--- NOUVEL ARTICLE ---" else choix
                if final_name:
                    new_d = pd.DataFrame([[datetime.now().strftime("%d/%m/%Y"), final_name, qte_art, pv_sug]], 
                                         columns=["Date", "Article", "Qte_Ajout", "PV_Suggere"])
                    df_demandes = pd.concat([df_demandes, new_d], ignore_index=True)
                    save_data(df_demandes, "demandes_stock.csv")
                    st.success("Transmis au patron !")
