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
            if 'Date' in df.columns:
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

# Définition du container principal
if is_admin:
    tabs = st.tabs(["🛒 Caisse Directe", "📦 Gestion Stock", "💰 Bénéfices", "📜 Historiques"])
    container = tabs[0]
else:
    t1, t2 = st.tabs(["🛒 Caisse Directe", "📦 Arrivage"])
    container = t1

# --- MODULE CAISSE ---
with container:
    st.subheader("🛒 Terminal de Vente")
    
    # 1. ZONE DE VENTE (Prix modifiable)
    with st.expander("💳 ENREGISTRER UNE VENTE", expanded=True):
        col_v1, col_v2, col_v3, col_v4 = st.columns([3, 1, 1, 1])
        art_v = col_v1.selectbox("Article", sorted(df_stock["Article"].tolist()), key="v_art")
        idx_s = df_stock[df_stock["Article"] == art_v].index[0]
        
        # Le prix par défaut est celui du stock, mais il est modifiable
        pv_propose = float(df_stock.at[idx_s, "PV"])
        pv_final = col_v2.number_input("Prix de vente (DA)", value=pv_propose, step=50.0)
        qte_v = col_v3.number_input("Qte", min_value=1, step=1)
        
        if col_v4.button("✅ Valider", use_container_width=True):
            if df_stock.at[idx_s, "Quantite"] >= qte_v:
                pa, fr = df_stock.at[idx_s, "PA"], df_stock.at[idx_s, "Frais"]
                benef = qte_v * (pv_final - (pa + fr))
                new_v = pd.DataFrame([[datetime.now().date(), art_v, qte_v, qte_v*pv_final, benef]], columns=df_ventes.columns)
                df_ventes = pd.concat([df_ventes, new_v], ignore_index=True)
                df_stock.at[idx_s, "Quantite"] -= qte_v
                save_data(df_ventes, "ventes.csv"); save_data(df_stock, "stock.csv")
                st.success("Vente enregistrée !")
                st.rerun()
            else: st.error("Stock insuffisant !")

    # 2. ZONE DE RETOUR (Avec historique de prix)
    with st.expander("🔄 EFFECTUER UN RETOUR CLIENT"):
        st.info("Sélectionnez l'article pour voir les ventes passées et le prix appliqué.")
        col_r1, col_r2 = st.columns([2, 1])
        art_r = col_r1.selectbox("Article à retourner", sorted(df_stock["Article"].tolist()), key="r_art")
        
        # Rechercher dans l'historique des ventes pour cet article
        historique_art = df_ventes[df_ventes["Article"] == art_r].sort_values(by="Date", ascending=False)
        
        if not historique_art.empty:
            # Créer une liste de choix lisible : "Date - Qté - Prix Total"
            options_retour = historique_art.apply(lambda x: f"Vendu le {x['Date']} | Qté: {x['Qte']} | Total: {x['Vente_Total']} DA", axis=1).tolist()
            selection_retour = st.selectbox("Sélectionner la vente correspondante", options_retour)
            
            # Extraire l'index de la vente choisie pour récupérer le prix réel
            idx_hist = options_retour.index(selection_retour)
            vente_choisie = historique_art.iloc[idx_hist]
            prix_unitaire_vendu = vente_choisie['Vente_Total'] / vente_choisie['Qte']
            
            qte_r = st.number_input("Quantité à retourner", min_value=1, max_value=int(vente_choisie['Qte']), step=1)
            montant_rembourse = qte_r * prix_unitaire_vendu
            
            st.warning(f"Montant à rembourser : {montant_rembourse:,.2f} DA")
            
            if st.button("⚠️ Valider le Retour"):
                idx_s = df_stock[df_stock["Article"] == art_r].index[0]
                new_r = pd.DataFrame([[datetime.now().date(), art_r, qte_r, montant_rembourse]], columns=df_retours.columns)
                df_retours = pd.concat([df_retours, new_r], ignore_index=True)
                df_stock.at[idx_s, "Quantite"] += qte_r
                save_data(df_retours, "retours.csv"); save_data(df_stock, "stock.csv")
                st.success("Retour validé et stock mis à jour !")
                st.rerun()
        else:
            st.error("Aucune vente enregistrée pour cet article.")
