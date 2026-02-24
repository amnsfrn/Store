import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="Happy Store Kids - Gestion", layout="wide", page_icon="🛍️")

if 'acces_autorise' not in st.session_state:
    st.session_state['acces_autorise'] = False
if 'admin_connecte' not in st.session_state:
    st.session_state['admin_connecte'] = False

# --- PROTECTION ENTREE ---
if not st.session_state['acces_autorise']:
    st.title("🔐 Accès Sécurisé")
    entree = st.text_input("Mot de passe d'accès", type="password")
    if st.button("Entrer"):
        if entree == "happystorekids":
            st.session_state['acces_autorise'] = True
            st.rerun()
        else:
            st.error("Incorrect")
    st.stop()

# --- FONCTIONS DONNÉES ---
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

df_stock = load_data("stock.csv", ["Article", "PA", "Frais", "PV", "Quantite"])
df_ventes = load_data("ventes.csv", ["Date", "Article", "Qte", "Vente_Total", "Benefice"])
df_config = load_data("config.csv", ["Type", "Valeur"])

# --- BARRE LATERALE ---
st.sidebar.title("🛂 Contrôle")
if not st.session_state['admin_connecte']:
    pwd = st.sidebar.text_input("Code Admin", type="password")
    if st.sidebar.button("Connexion Admin"):
        if pwd == "9696":
            st.session_state['admin_connecte'] = True
            st.rerun()
else:
    if st.sidebar.button("🔴 Déconnexion Admin"):
        st.session_state['admin_connecte'] = False
        st.rerun()

is_admin = st.session_state['admin_connecte']

# --- INTERFACE ---
if is_admin:
    st.title("📊 Direction - Happy Store Kids")
    tabs = st.tabs(["🛒 Caisse & Retours", "📦 Stock", "💰 Bénéfices", "📜 Historique"])

    with tabs[2]: # ONGLET BÉNÉFICES
        st.subheader("Analyse des Bénéfices")
        today = datetime.now().date()
        b_today = df_ventes[df_ventes['Date'] == today]['Benefice'].sum()
        b_7d = df_ventes[df_ventes['Date'] >= (today - timedelta(days=7))]['Benefice'].sum()
        b_30d = df_ventes[df_ventes['Date'] >= (today - timedelta(days=30))]['Benefice'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Aujourd'hui", f"{b_today:,.2f} DA")
        c2.metric("7 derniers jours", f"{b_7d:,.2f} DA")
        c3.metric("30 derniers jours", f"{b_30d:,.2f} DA")
        
        st.write("---")
        st.subheader("📅 Bénéfice par calendrier")
        choix_date = st.date_input("Choisir une date", today)
        b_precis = df_ventes[df_ventes['Date'] == choix_date]['Benefice'].sum()
        st.info(f"Bénéfice pour le {choix_date} : **{b_precis:,.2f} DA**")

    with tabs[3]: # ONGLET HISTORIQUE
        st.subheader("Historique Complet des Ventes")
        st.dataframe(df_ventes.sort_values(by='Date', ascending=False), use_container_width=True)

    with tabs[1]:
        st.subheader("Inventaire")
        with st.expander("➕ Ajouter un Produit"):
            n = st.text_input("Nom de l'article")
            col_a, col_b = st.columns(2)
            pa = col_a.number_input("Prix d'Achat")
            fr = col_a.number_input("Frais")
            pv = col_b.number_input("Prix de Vente")
            qt = col_b.number_input("Quantité")
            if st.button("Enregistrer"):
                new = pd.DataFrame([[n, pa, fr, pv, qt]], columns=df_stock.columns)
                df_stock = pd.concat([df_stock, new], ignore_index=True)
                save_data(df_stock, "stock.csv")
                st.rerun()
        st.dataframe(df_stock, use_container_width=True)

else:
    st.title("🏪 Caisse Magasin")

# --- MODULE CAISSE & RETOURS & END OF DAY ---
with (tabs[0] if is_admin else st.container()):
    choix_action = st.radio("Action", ["Vente", "Retour Article", "Fin de Journée (Clôture)"], horizontal=True)
    
    if choix_action == "Fin de Journée (Clôture)":
        st.subheader("🏁 Clôture de la Caisse")
        today = datetime.now().date()
        ventes_du_jour = df_ventes[df_ventes['Date'] == today]
        total_cash_theorique = ventes_du_jour['Vente_Total'].sum()
        
        st.info(f"Date : **{today.strftime('%d/%m/%Y')}**")
        st.metric("MONTANT TOTAL À RÉCUPÉRER", f"{total_cash_theorique:,.2f} DA")
        
        with st.expander("Voir le détail des ventes du jour"):
            st.table(ventes_du_jour[['Article', 'Qte', 'Vente_Total']])
            
        if st.button("Imprimer / Valider la journée"):
            st.success("Journée clôturée avec succès. L'employé doit vous remettre le montant affiché.")

    elif not df_stock.empty:
        art = st.selectbox("Article", df_stock["Article"])
        idx = df_stock[df_stock["Article"] == art].index[0]
        qte = st.number_input("Quantité", min_value=1, step=1)
        
        if choix_action == "Vente":
            st.info(f"Prix : {df_stock.at[idx, 'PV']} DA | Stock : {df_stock.at[idx, 'Quantite']}")
            if st.button("Valider la Vente"):
                if df_stock.at[idx, "Quantite"] >= qte:
                    benef = qte * (df_stock.at[idx, "PV"] - (df_stock.at[idx, "PA"] + df_stock.at[idx, "Frais"]))
                    new_v = pd.DataFrame([[datetime.now().date(), art, qte, qte*df_stock.at[idx, "PV"], benef]], columns=df_ventes.columns)
                    df_ventes = pd.concat([df_ventes, new_v], ignore_index=True)
                    df_stock.at[idx, "Quantite"] -= qte
                    save_data(df_ventes, "ventes.csv")
                    save_data(df_stock, "stock.csv")
                    st.success("Vendu !")
                    st.rerun()
        
        elif choix_action == "Retour Article":
            st.warning("Action : Remboursement client")
            if st.button("Confirmer le Retour"):
                benef_retour = qte * (df_stock.at[idx, "PV"] - (df_stock.at[idx, "PA"] + df_stock.at[idx, "Frais"]))
                new_r = pd.DataFrame([[datetime.now().date(), f"RETOUR: {art}", -qte, -(qte*df_stock.at[idx, "PV"]), -benef_retour]], columns=df_ventes.columns)
                df_ventes = pd.concat([df_ventes, new_r], ignore_index=True)
                df_stock.at[idx, "Quantite"] += qte
                save_data(df_ventes, "ventes.csv")
                save_data(df_stock, "stock.csv")
                st.success("Retour enregistré !")
                st.rerun()
