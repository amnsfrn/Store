import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Happy Store Kids", layout="wide", page_icon="🛍️")

# Initialisation des sessions si elles n'existent pas
if 'acces_autorise' not in st.session_state: st.session_state['acces_autorise'] = False
if 'admin_connecte' not in st.session_state: st.session_state['admin_connecte'] = False

# --- FONCTIONS DE DONNÉES ---
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

# Chargement des bases
df_stock = load_data("stock.csv", ["Article", "PA", "Frais", "PV", "Quantite"])
df_ventes = load_data("ventes.csv", ["Date", "Article", "Qte", "Vente_Total", "Benefice"])
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

# --- NAVIGATION ---
if is_admin:
    tabs = st.tabs(["🛒 Caisse Directe", "📦 Gestion Stock", "✅ Validations", "📊 Rapports"])
else:
    tabs = st.tabs(["🛒 Caisse Directe", "📩 Envoyer Arrivage"])

# --- MODULE CAISSE (POUR TOUS) ---
with tabs[0]:
    st.subheader("🛒 Terminal de Vente")
    if df_stock.empty:
        st.info("Le stock est vide. Ajoutez des articles pour commencer.")
    else:
        # 1. Sélection de l'article avec recherche
        liste_art = sorted(df_stock["Article"].unique().tolist())
        choix_art = st.selectbox("Tapez les premières lettres de l'article", [""] + liste_art)

        if choix_art != "":
            # On récupère les infos de l'article choisi
            info = df_stock[df_stock["Article"] == choix_art].iloc[0]
            
            with st.form("form_vente", clear_on_submit=True):
                st.write(f"**Article sélectionné :** {choix_art}")
                col1, col2 = st.columns(2)
                p_vente = col1.number_input("Prix de vente (DA)", value=float(info['PV']))
                q_vendu = col2.number_input("Quantité", min_value=1, max_value=int(info['Quantite']), step=1)
                
                # LE BOUTON DE VALIDATION (Important pour éviter l'erreur de votre image)
                submit_v = st.form_submit_button("✅ VALIDER LA VENTE")
                
                if submit_v:
                    benef = q_vendu * (p_vente - (info['PA'] + info['Frais']))
                    new_v = pd.DataFrame([[datetime.now().date(), choix_art, q_vendu, q_vendu*p_vente, benef]], columns=df_ventes.columns)
                    df_ventes = pd.concat([df_ventes, new_v], ignore_index=True)
                    df_stock.loc[df_stock["Article"] == choix_art, "Quantite"] -= q_vendu
                    save_data(df_ventes, "ventes.csv"); save_data(df_stock, "stock.csv")
                    st.success("Vente enregistrée !")
                    st.rerun()

# --- GESTION STOCK (ADMIN UNIQUEMENT) ---
if is_admin:
    with tabs[1]:
        st.subheader("📦 Modification / Suppression")
        if not df_stock.empty:
            art_edit = st.selectbox("Chercher un article à modifier", [""] + sorted(df_stock["Article"].tolist()))
            if art_edit != "":
                idx = df_stock[df_stock["Article"] == art_edit].index[0]
                row = df_stock.loc[idx]
                with st.form("edit_form"):
                    c1, c2, c3, c4, c5 = st.columns(5)
                    n_n = c1.text_input("Nom", value=row['Article'])
                    n_pa = c2.number_input("PA", value=float(row['PA']))
                    n_fr = c3.number_input("Frais", value=float(row['Frais']))
                    n_pv = c4.number_input("PV", value=float(row['PV']))
                    n_q = c5.number_input("Quantité", value=int(row['Quantite']))
                    
                    col_b1, col_b2 = st.columns(2)
                    if col_b1.form_submit_button("💾 Sauvegarder"):
                        df_stock.loc[idx] = [n_n, n_pa, n_fr, n_pv, n_q]
                        save_data(df_stock, "stock.csv"); st.rerun()
                    if col_b2.form_submit_button("🗑️ Supprimer l'article"):
                        df_stock = df_stock.drop(idx); save_data(df_stock, "stock.csv"); st.rerun()

# --- ARRIVAGE (USER) ---
else:
    with tabs[1]:
        st.subheader("📩 Déclarer un arrivage")
        with st.form("form_user", clear_on_submit=True):
            nom_a = st.text_input("Nom de l'article")
            qte_a = st.number_input("Quantité", min_value=1)
            pv_s = st.number_input("Prix de vente suggéré", min_value=0.0)
            if st.form_submit_button("Envoyer pour validation"):
                new_d = pd.DataFrame([[datetime.now().date(), nom_a, qte_a, pv_s]], columns=df_demandes.columns)
                df_demandes = pd.concat([df_demandes, new_d], ignore_index=True)
                save_data(df_demandes, "demandes.csv")
                st.success("Envoyé au patron !")
