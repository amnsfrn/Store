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

# Chargement
df_stock = load_data("stock.csv", ["Article", "PA", "Frais", "PV", "Quantite"])
df_ventes = load_data("ventes.csv", ["Date", "Article", "Qte", "Vente_Total", "Benefice"])
df_demandes = load_data("demandes_stock.csv", ["Date", "Article", "Qte_Ajout", "PV_Suggere"])
df_hist_stock = load_data("hist_stock.csv", ["Date", "Article", "Qte_Ajoutee", "Par"])

# --- CONNEXION ---
if not st.session_state['acces_autorise'] and not st.session_state['admin_connecte']:
    st.title("🔐 Happy Store Kids")
    u = st.text_input("Utilisateur")
    p = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter"):
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
    tabs = st.tabs(["🛒 Caisse", "📦 Stock & Validations", "💰 Bénéfices", "📜 Historiques"])
    
    with tabs[1]: # STOCK & VALIDATIONS
        # 1. VALEUR DU STOCK
        st.subheader("💰 Valeur de l'Inventaire")
        val_achat = ((df_stock['PA'] + df_stock['Frais']) * df_stock['Quantite']).sum()
        val_vente = (df_stock['PV'] * df_stock['Quantite']).sum()
        
        c_v1, c_v2, c_v3 = st.columns(3)
        c_v1.metric("Capital Investi (Achat)", f"{val_achat:,.2f} DA")
        c_v2.metric("Valeur Marchande (Vente)", f"{val_vente:,.2f} DA")
        c_v3.metric("Marge Potentielle", f"{(val_vente - val_achat):,.2f} DA")
        
        st.divider()

        # 2. VALIDATIONS EN ATTENTE
        st.subheader("✅ Demandes d'arrivage à valider")
        if not df_demandes.empty:
            for i, row in df_demandes.iterrows():
                with st.expander(f"Demande : {row['Article']} (+{row['Qte_Ajout']})"):
                    col_a, col_b, col_c, col_d = st.columns(4)
                    pa_val = col_a.number_input(f"PA Unitaire", min_value=0.0, key=f"pa_{i}")
                    fr_val = col_b.number_input(f"Frais Unitaire", min_value=0.0, key=f"fr_{i}")
                    pv_f = col_c.number_input(f"PV Final", min_value=0.0, value=float(row['PV_Suggere']), key=f"pv_{i}")
                    if col_d.button("Valider", key=f"btn_{i}"):
                        if row['Article'] in df_stock['Article'].values:
                            idx = df_stock[df_stock["Article"] == row['Article']].index[0]
                            df_stock.at[idx, "Quantite"] += int(row['Qte_Ajout'])
                            df_stock.at[idx, "PA"], df_stock.at[idx, "Frais"], df_stock.at[idx, "PV"] = pa_val, fr_val, pv_f
                        else:
                            new_item = pd.DataFrame([[row['Article'], pa_val, fr_val, pv_f, row['Qte_Ajout']]], columns=df_stock.columns)
                            df_stock = pd.concat([df_stock, new_item], ignore_index=True)
                        df_demandes = df_demandes.drop(i)
                        save_data(df_stock, "stock.csv"); save_data(df_demandes, "demandes_stock.csv")
                        st.rerun()
        else: st.write("Aucune demande.")

        st.divider()

        # 3. RECHERCHE ET LISTE
        st.subheader("📦 Inventaire & Recherche")
        search = st.text_input("🔍 Rechercher un produit par nom...", "")
        
        df_filtered = df_stock[df_stock['Article'].str.contains(search, case=False, na=False)]
        
        # Affichage avec bouton supprimer
        for idx, row in df_filtered.iterrows():
            c_nom, c_qte, c_pv, c_del = st.columns([3, 1, 1, 1])
            c_nom.write(f"**{row['Article']}**")
            c_qte.write(f"{row['Quantite']} en stock")
            c_pv.write(f"{row['PV']} DA")
            if c_del.button("🗑️ Supprimer", key=f"del_{idx}"):
                df_stock = df_stock.drop(idx)
                save_data(df_stock, "stock.csv")
                st.warning(f"{row['Article']} supprimé.")
                st.rerun()

else: # INTERFACE EMPLOYÉ
    st.title("🏪 Espace Employé")
    t1, t2 = st.tabs(["🛒 Caisse", "📦 Arrivage Stock"])
    with t2:
        st.subheader("Signaler une réception")
        liste_art = sorted(df_stock["Article"].tolist()) + ["--- NOUVEL ARTICLE ---"]
        choix = st.selectbox("Article reçu :", liste_art)
        nom_art = st.text_input("Nom de l'article") if choix == "--- NOUVEL ARTICLE ---" else choix
        qte_art = st.number_input("Quantité reçue", min_value=1)
        pv_sug = st.number_input("Prix de Vente (PV) suggéré", min_value=0.0)
        if st.button("Envoyer à l'Admin"):
            new_d = pd.DataFrame([[datetime.now().strftime("%d/%m/%Y"), nom_art, qte_art, pv_sug]], 
                                 columns=["Date", "Article", "Qte_Ajout", "PV_Suggere"])
            df_demandes = pd.concat([df_demandes, new_d], ignore_index=True)
            save_data(df_demandes, "demandes_stock.csv")
            st.info("Demande envoyée.")

# --- MODULE CAISSE (ADMIN & USER) ---
with (tabs[0] if is_admin else t1):
    # Logique de vente/retour/fin de journée habituelle
    st.write("Gestion des transactions...")
