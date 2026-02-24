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

# --- BARRE LATÉRALE (DÉCONNEXION) ---
with st.sidebar:
    st.title("⚙️ Menu")
    if st.button("🔴 SE DÉCONNECTER", use_container_width=True):
        st.session_state.clear()
        st.rerun()

is_admin = st.session_state['admin_connecte']

# --- NAVIGATION ---
if is_admin:
    tabs = st.tabs(["🛒 Caisse Directe", "📦 Gestion Stock", "✅ Validations", "📊 Rapports"])
else:
    tabs = st.tabs(["🛒 Caisse Directe", "📩 Envoyer Arrivage"])

# --- 1. ONGLET CAISSE ---
with tabs[0]:
    st.subheader("🛒 Terminal de Vente")
    if df_stock.empty:
        st.info("Le stock est vide. Ajoutez des articles pour commencer.")
    else:
        liste_art = sorted(df_stock["Article"].unique().tolist())
        choix = st.selectbox("🔍 Chercher un article", [""] + liste_art)
        
        if choix != "":
            info = df_stock[df_stock["Article"] == choix].iloc[0]
            # Correction : Le bouton de validation est maintenant BIEN à l'intérieur du form
            with st.form("form_vente_final", clear_on_submit=True):
                st.write(f"En stock : **{int(info['Quantite'])}**")
                c1, c2 = st.columns(2)
                p_v = c1.number_input("Prix de vente (DA)", value=float(info['PV']))
                q_v = c2.number_input("Quantité", min_value=1, max_value=int(info['Quantite']), step=1)
                
                if st.form_submit_button("✅ VALIDER LA VENTE"):
                    benef = q_v * (p_v - (info['PA'] + info['Frais']))
                    new_v = pd.DataFrame([[datetime.now().date(), choix, q_v, q_v*p_v, benef]], columns=df_ventes.columns)
                    df_ventes = pd.concat([df_ventes, new_v], ignore_index=True)
                    df_stock.loc[df_stock["Article"] == choix, "Quantite"] -= q_v
                    save_data(df_ventes, "ventes.csv"); save_data(df_stock, "stock.csv")
                    st.success("Vente réussie !")
                    st.rerun()

# --- 2. ONGLET GESTION / VALIDATION ---
if is_admin:
    # MODIFICATION STOCK
    with tabs[1]:
        st.subheader("📦 Modification du Stock existant")
        art_edit = st.selectbox("Sélectionner un article", [""] + sorted(df_stock["Article"].tolist()))
        if art_edit != "":
            idx = df_stock[df_stock["Article"] == art_edit].index[0]
            row = df_stock.loc[idx]
            with st.form("edit_form"):
                n_n = st.text_input("Nom", value=row['Article'])
                n_pa = st.number_input("Prix d'Achat (Unitaire)", value=float(row['PA']))
                n_fr = st.number_input("Frais (Unitaire)", value=float(row['Frais']))
                n_pv = st.number_input("Prix de Vente", value=float(row['PV']))
                n_q = st.number_input("Quantité", value=int(row['Quantite']))
                
                colb1, colb2 = st.columns(2)
                if colb1.form_submit_button("💾 Sauvegarder"):
                    df_stock.loc[idx] = [n_n, n_pa, n_fr, n_pv, n_q]
                    save_data(df_stock, "stock.csv"); st.rerun()
                if colb2.form_submit_button("🗑️ Supprimer"):
                    df_stock = df_stock.drop(idx); save_data(df_stock, "stock.csv"); st.rerun()

    # VALIDATION DES ARRIVAGES (FRAIS TOTAUX)
    with tabs[2]:
        st.subheader("✅ Valider les nouveaux arrivages")
        if df_demandes.empty:
            st.write("Rien à valider.")
        else:
            for i, d in df_demandes.iterrows():
                with st.expander(f"📦 {d['Article']} (Quantité: {d['Qte']})"):
                    with st.form(f"val_batch_{i}"):
                        v_pa = st.number_input("Prix d'Achat Unitaire", min_value=0.0)
                        # MODIFICATION ICI : FRAIS POUR TOUTE LA QUANTITÉ
                        v_fr_total = st.number_input(f"Frais de transport TOTAUX pour les {int(d['Qte'])} pièces", min_value=0.0)
                        v_pv = st.number_input("Prix de vente final", value=float(d['PV_Suggere']))
                        
                        if st.form_submit_button("Valider l'entrée en stock"):
                            # Calcul automatique par pièce
                            frais_par_piece = v_fr_total / d['Qte'] if d['Qte'] > 0 else 0
                            new_item = pd.DataFrame([[d['Article'], v_pa, frais_par_piece, v_pv, d['Qte']]], columns=df_stock.columns)
                            df_stock = pd.concat([df_stock, new_item], ignore_index=True)
                            df_demandes = df_demandes.drop(i)
                            save_data(df_stock, "stock.csv"); save_data(df_demandes, "demandes.csv")
                            st.rerun()
else:
    # VUE USER : ENVOI ARRIVAGE
    with tabs[1]:
        st.subheader("📩 Déclarer un arrivage")
        with st.form("user_form", clear_on_submit=True):
            n = st.text_input("Nom article")
            q = st.number_input("Quantité", min_value=1)
            p = st.number_input("Prix de vente suggéré", min_value=0.0)
            if st.form_submit_button("Envoyer au Patron"):
                new_d = pd.DataFrame([[datetime.now().date(), n, q, p]], columns=df_demandes.columns)
                df_demandes = pd.concat([df_demandes, new_d], ignore_index=True)
                save_data(df_demandes, "demandes.csv")
                st.success("Transmis !")
