import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Happy Store Kids", layout="wide", page_icon="🛍️")

# Initialisation des variables de session
if 'acces_autorise' not in st.session_state: st.session_state['acces_autorise'] = False
if 'admin_connecte' not in st.session_state: st.session_state['admin_connecte'] = False

# --- FONCTIONS DE GESTION DES DONNÉES ---
def load_data(file, columns):
    if os.path.exists(file):
        try:
            df = pd.read_csv(file)
            # Correction automatique des dates pour l'affichage
            if not df.empty and 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce').dt.date
            return df
        except: return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

def save_data(df, file):
    df.to_csv(file, index=False)

# Chargement des bases de données
df_stock = load_data("stock.csv", ["Article", "PA", "Frais", "PV", "Quantite"])
df_ventes = load_data("ventes.csv", ["Date", "Article", "Qte", "Vente_Total", "Benefice"])
df_demandes = load_data("demandes.csv", ["Date", "Article", "Qte", "PV_Suggere"])

# --- SYSTÈME DE CONNEXION ---
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
    st.write(f"Session : **{'Admin' if st.session_state['admin_connecte'] else 'User'}**")
    if st.button("🔴 SE DÉCONNECTER", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    st.divider()
    # Option de sauvegarde locale
    csv_stk = df_stock.to_csv(index=False).encode('utf-8')
    st.download_button("💾 Télécharger Copie Stock", data=csv_stk, file_name="sauvegarde_stock.csv")

is_admin = st.session_state['admin_connecte']

# --- NAVIGATION PAR ONGLETS ---
if is_admin:
    tabs = st.tabs(["🛒 Caisse Directe", "📦 Gestion Stock", "✅ Validations", "📊 Rapports"])
else:
    tabs = st.tabs(["🛒 Caisse Directe", "📩 Envoyer Arrivage"])

# --- 1. ONGLET CAISSE (ADMIN & USER) ---
with tabs[0]:
    st.subheader("🛒 Terminal de Vente")
    if df_stock.empty:
        st.info("Le stock est vide. Allez dans l'onglet Stock pour commencer.")
    else:
        # Recherche prédictive
        liste_art = sorted(df_stock["Article"].unique().tolist())
        choix = st.selectbox("🔍 Chercher un article (tapez les premières lettres)", [""] + liste_art)
        
        if choix != "":
            info = df_stock[df_stock["Article"] == choix].iloc[0]
            with st.form("vente_rapide", clear_on_submit=True):
                st.write(f"Article : **{choix}** | En stock : **{int(info['Quantite'])}**")
                c1, c2 = st.columns(2)
                p_v = c1.number_input("Prix de vente (DA)", value=float(info['PV']))
                q_v = c2.number_input("Quantité à vendre", min_value=1, max_value=int(info['Quantite']), step=1)
                
                if st.form_submit_button("✅ VALIDER LA VENTE"):
                    # Calcul bénéfice : PV - (PA + Frais unitaires)
                    benef = q_v * (p_v - (info['PA'] + info['Frais']))
                    new_v = pd.DataFrame([[datetime.now().date(), choix, q_v, q_v*p_v, benef]], columns=df_ventes.columns)
                    
                    df_ventes = pd.concat([df_ventes, new_v], ignore_index=True)
                    df_stock.loc[df_stock["Article"] == choix, "Quantite"] -= q_v
                    
                    save_data(df_ventes, "ventes.csv")
                    save_data(df_stock, "stock.csv")
                    st.success("Vente réussie !")
                    st.rerun()

# --- 2. ONGLET GESTION / ARRIVAGE ---
if is_admin:
    # --- VUE ADMIN : MODIFIER & SUPPRIMER ---
    with tabs[1]:
        st.subheader("📦 Liste et Modification du Stock")
        if not df_stock.empty:
            art_edit = st.selectbox("Sélectionner pour modifier/supprimer", [""] + sorted(df_stock["Article"].tolist()))
            if art_edit != "":
                idx = df_stock[df_stock["Article"] == art_edit].index[0]
                row = df_stock.loc[idx]
                with st.form("edit_stock"):
                    col_e1, col_e2, col_e3, col_e4, col_e5 = st.columns(5)
                    n_n = col_e1.text_input("Nom", value=row['Article'])
                    n_pa = col_e2.number_input("PA Unit.", value=float(row['PA']))
                    n_fr = col_e3.number_input("Frais Unit.", value=float(row['Frais']))
                    n_pv = col_e4.number_input("PV", value=float(row['PV']))
                    n_q = col_e5.number_input("Quantité", value=int(row['Quantite']))
                    
                    b1, b2 = st.columns(2)
                    if b1.form_submit_button("💾 Sauvegarder"):
                        df_stock.loc[idx] = [n_n, n_pa, n_fr, n_pv, n_q]
                        save_data(df_stock, "stock.csv")
                        st.success("Modifié !")
                        st.rerun()
                    if b2.form_submit_button("🗑️ Supprimer l'article"):
                        df_stock = df_stock.drop(idx)
                        save_data(df_stock, "stock.csv")
                        st.rerun()

    # --- VUE ADMIN : VALIDATION DES ARRIVAGES USER ---
    with tabs[2]:
        st.subheader("🔔 Arrivages envoyés par l'équipe")
        if df_demandes.empty:
            st.write("Aucune demande en attente.")
        else:
            for i, d in df_demandes.iterrows():
                with st.expander(f"📦 {d['Article']} (Quantité: {d['Qte']})"):
                    with st.form(f"val_{i}"):
                        v_n = st.text_input("Nom final", value=d['Article'])
                        v_q = st.number_input("Quantité réelle", value=int(d['Qte']))
                        v_pv = st.number_input("Prix de vente final", value=float(d['PV_Suggere']))
                        st.divider()
                        v_pa = st.number_input("Prix d'Achat Unitaire", min_value=0.0)
                        v_fr_t = st.number_input("Frais de transport TOTAUX pour ce lot", min_value=0.0)
                        
                        if st.form_submit_button("✅ Valider et mettre en Stock"):
                            f_u = v_fr_t / v_q if v_q > 0 else 0 # Calcul auto frais/pièce
                            new_item = pd.DataFrame([[v_n, v_pa, f_u, v_pv, v_q]], columns=df_stock.columns)
                            df_stock = pd.concat([df_stock, new_item], ignore_index=True)
                            df_demandes = df_demandes.drop(i)
                            save_data(df_stock, "stock.csv")
                            save_data(df_demandes, "demandes.csv")
                            st.rerun()
else:
    # --- VUE USER : ENVOYER ARRIVAGE ---
    with tabs[1]:
        st.subheader("📩 Déclarer un nouvel arrivage")
        with st.form("user_arrivage", clear_on_submit=True):
            n_art = st.text_input("Nom de l'article")
            q_art = st.number_input("Quantité reçue", min_value=1)
            p_sugg = st.number_input("Prix de vente souhaité", min_value=0.0)
            if st.form_submit_button("Envoyer pour Validation"):
                if n_art:
                    new_d = pd.DataFrame([[datetime.now().date(), n_art, q_art, p_sugg]], columns=df_demandes.columns)
                    df_demandes = pd.concat([df_demandes, new_d], ignore_index=True)
                    save_data(df_demandes, "demandes.csv")
                    st.success("Demande transmise au patron !")
                else: st.error("Le nom est obligatoire.")
