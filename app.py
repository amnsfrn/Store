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

# Chargement sécurisé
df_stock = load_data("stock.csv", ["Article", "PA", "Frais", "PV", "Quantite"])
df_ventes = load_data("ventes.csv", ["Date", "Article", "Qte", "Vente_Total", "Benefice"])
df_retours = load_data("retours.csv", ["Date", "Article", "Qte", "Montant_Rendu"])
df_demandes = load_data("demandes_stock.csv", ["Date", "Article", "Qte_Ajout", "PV_Suggere"])

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

if st.sidebar.button("🔴 Déconnexion"):
    st.session_state.clear()
    st.rerun()

is_admin = st.session_state['admin_connecte']

# --- INTERFACE ---
if is_admin:
    tabs = st.tabs(["🛒 Caisse Directe", "📦 Gestion Stock", "💰 Bénéfices", "📜 Historiques"])
    container = tabs[0]
else:
    t1, t2 = st.tabs(["🛒 Caisse Directe", "📦 Arrivage"])
    container = t1

# --- MODULE CAISSE ---
with container:
    st.subheader("🛒 Terminal de Vente")
    
    if df_stock.empty:
        st.warning("⚠️ Le stock est vide. Veuillez ajouter des articles dans l'onglet 'Stock' ou 'Arrivage' avant de vendre.")
    else:
        # 1. ZONE DE VENTE
        with st.expander("💳 ENREGISTRER UNE VENTE", expanded=True):
            col_v1, col_v2, col_v3, col_v4 = st.columns([3, 1, 1, 1])
            art_v = col_v1.selectbox("Article", sorted(df_stock["Article"].tolist()), key="v_art")
            
            # Sécurité pour trouver l'index
            matching_stock = df_stock[df_stock["Article"] == art_v]
            if not matching_stock.empty:
                idx_s = matching_stock.index[0]
                pv_defaut = float(df_stock.at[idx_s, "PV"])
                pv_final = col_v2.number_input("Prix (DA)", value=pv_defaut, step=10.0)
                qte_v = col_v3.number_input("Qte", min_value=1, step=1, key="qte_v")
                
                if col_v4.button("✅ Vendre", use_container_width=True):
                    if df_stock.at[idx_s, "Quantite"] >= qte_v:
                        pa, fr = df_stock.at[idx_s, "PA"], df_stock.at[idx_s, "Frais"]
                        benef = qte_v * (pv_final - (pa + fr))
                        new_v = pd.DataFrame([[datetime.now().date(), art_v, qte_v, qte_v*pv_final, benef]], columns=df_ventes.columns)
                        df_ventes = pd.concat([df_ventes, new_v], ignore_index=True)
                        df_stock.at[idx_s, "Quantite"] -= qte_v
                        save_data(df_ventes, "ventes.csv"); save_data(df_stock, "stock.csv")
                        st.success("Vente réussie !")
                        st.rerun()
                    else: st.error("Stock insuffisant !")

        # 2. ZONE DE RETOUR
        with st.expander("🔄 EFFECTUER UN RETOUR", expanded=False):
            art_r = st.selectbox("Article à retourner", sorted(df_stock["Article"].tolist()), key="r_art")
            
            # Recherche dans l'historique des ventes
            hist = df_ventes[df_ventes["Article"] == art_r].sort_values(by="Date", ascending=False)
            
            if not hist.empty:
                options = hist.apply(lambda x: f"{x['Date']} | Qté: {x['Qte']} | Prix: {x['Vente_Total']/x['Qte']} DA", axis=1).tolist()
                selection = st.selectbox("Choisir la vente d'origine", options)
                
                idx_h = options.index(selection)
                vente_ref = hist.iloc[idx_h]
                prix_u = vente_ref['Vente_Total'] / vente_ref['Qte']
                
                qte_r = st.number_input("Quantité retournée", min_value=1, max_value=int(vente_ref['Qte']), step=1)
                
                if st.button("⚠️ Valider le Retour"):
                    idx_stk = df_stock[df_stock["Article"] == art_r].index[0]
                    new_r = pd.DataFrame([[datetime.now().date(), art_r, qte_r, qte_r*prix_u]], columns=df_retours.columns)
                    df_retours = pd.concat([df_retours, new_r], ignore_index=True)
                    df_stock.at[idx_stk, "Quantite"] += qte_r
                    save_data(df_retours, "retours.csv"); save_data(df_stock, "stock.csv")
                    st.success("Retour effectué !")
                    st.rerun()
            else:
                st.info("Aucune vente enregistrée pour cet article. Impossible de faire un retour.")

# --- AJOUT DU STOCK (Pour corriger le problème du stock vide) ---
if is_admin:
    with tabs[1]:
        st.subheader("📦 Ajouter du Stock")
        with st.form("add_stock_admin"):
            n = st.text_input("Nom de l'article")
            q = st.number_input("Quantité", min_value=1)
            pa = st.number_input("Prix Achat", min_value=0.0)
            fr = st.number_input("Frais", min_value=0.0)
            pv = st.number_input("Prix Vente", min_value=0.0)
            if st.form_submit_button("Ajouter au Stock"):
                if n:
                    new_item = pd.DataFrame([[n, pa, fr, pv, q]], columns=df_stock.columns)
                    df_stock = pd.concat([df_stock, new_item], ignore_index=True)
                    save_data(df_stock, "stock.csv")
                    st.success("Article ajouté ! Vous pouvez maintenant le vendre.")
                    st.rerun()
