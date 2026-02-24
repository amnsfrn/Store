import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="Happy Store Kids - Gestion", layout="wide", page_icon="🛍️")

# --- INITIALISATION DES SESSIONS ---
if 'acces_autorise' not in st.session_state:
    st.session_state['acces_autorise'] = False
if 'admin_connecte' not in st.session_state:
    st.session_state['admin_connecte'] = False

# --- FONCTIONS DE DONNÉES ---
def load_data(file, columns):
    if os.path.exists(file):
        try:
            df = pd.read_csv(file)
            if 'Date' in df.columns and file != "sessions.csv":
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

# Chargement des fichiers
df_stock = load_data("stock.csv", ["Article", "PA", "Frais", "PV", "Quantite"])
df_ventes = load_data("ventes.csv", ["Date", "Article", "Qte", "Vente_Total", "Benefice"])
df_sessions = load_data("sessions.csv", ["Horodatage", "Profil"])

# --- ÉCRAN DE VERROUILLAGE (LOGIN) ---
if not st.session_state['acces_autorise']:
    st.title("🔐 Happy Store Kids - Connexion")
    col_log1, col_log2 = st.columns(2)
    user_input = col_log1.text_input("Nom d'utilisateur")
    pass_input = col_log2.text_input("Mot de passe", type="password")
    
    if st.button("Se connecter au magasin"):
        if user_input == "user" and pass_input == "0699302032":
            st.session_state['acces_autorise'] = True
            log_session("User (Caisse)")
            st.rerun()
        else:
            st.error("Identifiants incorrects")
    st.stop()

# --- BARRE LATÉRALE ---
st.sidebar.title("🛂 Contrôle")
if not st.session_state['admin_connecte']:
    pwd_admin = st.sidebar.text_input("Code Secret Admin", type="password")
    if st.sidebar.button("Débloquer Admin"):
        if pwd_admin == "9696":
            st.session_state['admin_connecte'] = True
            log_session("Admin (Accès Totale)")
            st.rerun()
else:
    if st.sidebar.button("🔴 Déconnexion Admin"):
        st.session_state['admin_connecte'] = False
        st.rerun()

is_admin = st.session_state['admin_connecte']

# --- INTERFACE ---
if is_admin:
    st.title("📊 Direction - Happy Store Kids")
    tabs = st.tabs(["🛒 Caisse", "📦 Stock", "💰 Bénéfices", "📜 Historiques"])

    with tabs[2]: # ONGLET BÉNÉFICES
        st.subheader("Analyse des Gains")
        # (Calculs de périodes identiques à votre version précédente)
        # ...

    with tabs[3]: # ONGLET HISTORIQUES (NOUVEAU)
        sub_tab1, sub_tab2 = st.tabs(["📈 Ventes", "🔑 Sessions de Connexion"])
        with sub_tab1:
            st.dataframe(df_ventes.sort_values(by='Date', ascending=False), use_container_width=True)
        with sub_tab2:
            st.subheader("Journal des connexions")
            st.write("Voici qui s'est connecté et à quelle heure :")
            st.dataframe(df_sessions.sort_values(by='Horodatage', ascending=False), use_container_width=True)

    with tabs[1]: # STOCK
        # (Interface de gestion de stock identique)
        st.subheader("Inventaire")
        st.dataframe(df_stock, use_container_width=True)

else:
    st.title("🏪 Caisse Magasin")
    st.write(f"Bienvenue. Session ouverte à : {datetime.now().strftime('%H:%M')}")

# --- MODULE CAISSE (COMMUN) ---
with (tabs[0] if is_admin else st.container()):
    choix = st.radio("Action", ["Vente", "Retour Article", "Fin de Journée"], horizontal=True)
    
    # (Logique de vente et de retour identique)
    if not df_stock.empty and choix != "Fin de Journée":
        art = st.selectbox("Article", df_stock["Article"])
        qte = st.number_input("Quantité", min_value=1, step=1)
        if st.button("Valider"):
            # ... (Traitement de la vente)
            st.success("Enregistré !")
            st.rerun()
    elif choix == "Fin de Journée":
        # ... (Calcul clôture)
        st.info("Clôture de caisse disponible")
