import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="Happy Store Kids - Gestion", layout="wide", page_icon="🛍️")

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

def log_session(profil):
    df_logs = load_data("sessions.csv", ["Horodatage", "Profil"])
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    new_log = pd.DataFrame([[now, profil]], columns=["Horodatage", "Profil"])
    df_logs = pd.concat([df_logs, new_log], ignore_index=True)
    save_data(df_logs, "sessions.csv")

# Chargement
df_stock = load_data("stock.csv", ["Article", "PA", "Frais", "PV", "Quantite"])
df_ventes = load_data("ventes.csv", ["Date", "Article", "Qte", "Vente_Total", "Benefice"])
df_sessions = load_data("sessions.csv", ["Horodatage", "Profil"])
df_demandes = load_data("demandes_stock.csv", ["Date", "Article", "Qte_Ajout", "Statut"])
df_hist_stock = load_data("hist_stock.csv", ["Date", "Article", "Qte_Ajoutee", "Par"])

# --- ÉCRAN DE CONNEXION UNIQUE ---
if not st.session_state['acces_autorise'] and not st.session_state['admin_connecte']:
    st.title("🔐 Happy Store Kids")
    
    col1, col2 = st.columns(2)
    u = col1.text_input("Utilisateur")
    p = col2.text_input("Mot de passe", type="password")
    
    if st.button("Se connecter"):
        # Verification ADMIN
        if u.lower() == "admin" and p == "Thanksgod@99":
            st.session_state['admin_connecte'] = True
            st.session_state['acces_autorise'] = True
            log_session("Admin")
            st.rerun()
        # Verification USER
        elif u.lower() == "user" and p == "0699302032":
            st.session_state['acces_autorise'] = True
            st.session_state['admin_connecte'] = False
            log_session("User")
            st.rerun()
        else:
            st.error("Identifiants incorrects")
    st.stop()

# --- BARRE LATÉRALE ---
st.sidebar.title("🛂 Session")
if st.session_state['admin_connecte']:
    st.sidebar.success("Mode: Propriétaire")
else:
    st.sidebar.info("Mode: Employé")

if st.sidebar.button("🔴 Déconnexion"):
    st.session_state['acces_autorise'] = False
    st.session_state['admin_connecte'] = False
    st.rerun()

is_admin = st.session_state['admin_connecte']

# --- INTERFACE ---
if is_admin:
    st.title("📊 Tableau de Bord Direction")
    tabs = st.tabs(["🛒 Caisse", "📦 Stock & Validations", "💰 Bénéfices", "📜 Historiques"])
    
    with tabs[1]: # STOCK ADMIN
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("✅ Demandes de l'employé")
            if not df_demandes.empty:
                for i, row in df_demandes.iterrows():
                    c_art, c_qte, c_btn = st.columns([2, 1, 1])
                    c_art.write(f"**{row['Article']}**")
                    c_qte.write(f"+{row['Qte_Ajout']}")
                    if c_btn.button("Valider", key=f"val_{i}"):
                        idx = df_stock[df_stock["Article"] == row['Article']].index[0]
                        df_stock.at[idx, "Quantite"] += int(row['Qte_Ajout'])
                        new_h = pd.DataFrame([[datetime.now().strftime("%d/%m/%Y"), row['Article'], row['Qte_Ajout'], "User (Validé)"]], columns=df_hist_stock.columns)
                        df_hist_stock = pd.concat([df_hist_stock, new_h], ignore_index=True)
                        df_demandes = df_demandes.drop(i)
                        save_data(df_stock, "stock.csv"); save_data(df_hist_stock, "hist_stock.csv"); save_data(df_demandes, "demandes_stock.csv")
                        st.rerun()
        with col2:
            st.subheader("⚡ Ajout Direct")
            art_a = st.selectbox("Article", df_stock["Article"], key="adm_add")
            qte_a = st.number_input("Quantité", min_value=1)
            if st.button("Alimenter Stock"):
                idx = df_stock[df_stock["Article"] == art_a].index[0]
                df_stock.at[idx, "Quantite"] += qte_a
                new_h = pd.DataFrame([[datetime.now().strftime("%d/%m/%Y"), art_a, qte_a, "Admin"]], columns=df_hist_stock.columns)
                df_hist_stock = pd.concat([df_hist_stock, new_h], ignore_index=True)
                save_data(df_stock, "stock.csv"); save_data(df_hist_stock, "hist_stock.csv")
                st.success("Stock mis à jour !")
                st.rerun()
        st.divider()
        st.dataframe(df_stock, use_container_width=True)

    with tabs[2]: # BÉNÉFICES
        st.subheader("💰 Analyse")
        today = datetime.now().date()
        col_d1, col_d2 = st.columns(2)
        d_deb = col_d1.date_input("Du", today - timedelta(days=7))
        d_fin = col_d2.date_input("Au", today)
        mask = (df_ventes['Date'] >= d_deb) & (df_ventes['Date'] <= d_fin)
        res = df_ventes.loc[mask]
        st.metric("Bénéfice Net", f"{res['Benefice'].sum():,.2f} DA")
        st.dataframe(res, use_container_width=True)

    with tabs[3]: # HISTORIQUES
        h1, h2, h3 = st.tabs(["Ventes", "Entrées Stock", "Connexions"])
        with h1: st.dataframe(df_ventes.sort_values(by="Date", ascending=False))
        with h2: st.dataframe(df_hist_stock.sort_values(by="Date", ascending=False))
        with h3: st.dataframe(df_sessions.sort_values(by="Horodatage", ascending=False))

else: # INTERFACE EMPLOYÉ
    st.title("🏪 Espace Employé")
    t1, t2 = st.tabs(["🛒 Caisse", "📦 Arrivage Stock"])
    with t2:
        st.subheader("Réception de marchandise")
        art_d = st.selectbox("Article reçu", df_stock["Article"])
        qte_d = st.number_input("Quantité", min_value=1)
        if st.button("Envoyer pour validation"):
            new_d = pd.DataFrame([[datetime.now().strftime("%d/%m/%Y"), art_d, qte_d, "En attente"]], columns=df_demandes.columns)
            df_demandes = pd.concat([df_demandes, new_d], ignore_index=True)
            save_data(df_demandes, "demandes_stock.csv")
            st.info("Demande envoyée.")

# --- MODULE CAISSE (LOGIQUE VENTE/RETOUR) ---
with (tabs[0] if is_admin else t1):
    mode = st.radio("Action", ["Vente", "Retour Article", "Fin de Journée"], horizontal=True)
    if mode == "Fin de Journée":
        total = df_ventes[df_ventes['Date'] == datetime.now().date()]['Vente_Total'].sum()
        st.metric("TOTAL CAISSE DU JOUR", f"{total:,.2f} DA")
    elif not df_stock.empty:
        art_s = st.selectbox("Article", df_stock["Article"], key="c_art")
        idx_s = df_stock[df_stock["Article"] == art_s].index[0]
        qte_s = st.number_input("Quantité", min_value=1, step=1, key="c_qte")
        if st.button("Confirmer"):
            p_v = df_stock.at[idx_s, "PV"]; p_a = df_stock.at[idx_s, "PA"]; p_f = df_stock.at[idx_s, "Frais"]
            if mode == "Vente":
                if df_stock.at[idx_s, "Quantite"] >= qte_s:
                    new_v = pd.DataFrame([[datetime.now().date(), art_s, qte_s, qte_s*p_v, qte_s*(p_v-(p_a+p_f))]], columns=df_ventes.columns)
                    df_ventes = pd.concat([df_ventes, new_v], ignore_index=True)
                    df_stock.at[idx_s, "Quantite"] -= qte_s
                    st.success("Vente effectuée !")
                else: st.error("Stock insuffisant")
            else: # Retour
                new_v = pd.DataFrame([[datetime.now().date(), f"RETOUR: {art_s}", -qte_s, -(qte_s*p_v), -(qte_s*(p_v-(p_a+p_f)))]], columns=df_ventes.columns)
                df_ventes = pd.concat([df_ventes, new_v], ignore_index=True)
                df_stock.at[idx_s, "Quantite"] += qte_s
                st.success("Retour effectué !")
            save_data(df_ventes, "ventes.csv"); save_data(df_stock, "stock.csv")
            st.rerun()
