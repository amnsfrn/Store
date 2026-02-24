import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Gestion Magasin Pro DZ", layout="wide", page_icon="🇩🇿")

if 'admin_connecte' not in st.session_state:
    st.session_state['admin_connecte'] = False

# --- FONCTIONS DE DONNÉES ---
def load_data(file, columns):
    if os.path.exists(file):
        try: return pd.read_csv(file)
        except: return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

def save_data(df, file):
    df.to_csv(file, index=False)

# Chargement
df_stock = load_data("stock.csv", ["Article", "PA", "Frais", "PV", "Quantite"])
df_ventes = load_data("ventes.csv", ["Date", "Article", "Qte", "Vente_Total", "Benefice"])
df_config = load_data("config.csv", ["Type", "Valeur"])

# --- BARRE LATÉRALE ---
st.sidebar.title("🔐 Espace Admin")

if not st.session_state['admin_connecte']:
    pwd = st.sidebar.text_input("Mot de passe Admin", type="password")
    if st.sidebar.button("Se connecter"):
        if pwd == "9696":
            st.session_state['admin_connecte'] = True
            st.rerun()
        else:
            st.sidebar.error("Incorrect")
else:
    if st.sidebar.button("🔴 Déconnexion"):
        st.session_state['admin_connecte'] = False
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Paramètres des Frais")
    
    # Saisie des frais
    n_loyer = st.sidebar.number_input("Loyer Mensuel", value=0.0)
    n_salaire = st.sidebar.number_input("Salaire Mensuel", value=0.0)
    n_trim = st.sidebar.number_input("Factures (Trimestre)", value=0.0)
    n_casnos = st.sidebar.number_input("CASNOS (Annuel)", value=0.0)
    n_impots = st.sidebar.number_input("Impôts (Annuel)", value=0.0)
    
    if st.sidebar.button("💾 Enregistrer Frais"):
        d = [["Loyer", n_loyer], ["Salaire", n_salaire], ["Factures_Trim", n_trim], ["Casnos", n_casnos], ["Impots", n_impots]]
        save_data(pd.DataFrame(d, columns=["Type", "Valeur"]), "config.csv")
        st.sidebar.success("OK !")
        st.rerun()

# --- CALCUL DES CHARGES (Version simplifiée sans erreur) ---
frais_mensuels = 0.0
if not df_config.empty:
    for t, v in zip(df_config['Type'], df_config['Valeur']):
        if t == "Loyer" or t == "Salaire": frais_mensuels += float(v)
        if t == "Factures_Trim": frais_mensuels += float(v) / 3
        if t == "Casnos" or t == "Impots": frais_mensuels += float(v) / 12

# --- INTERFACE ---
is_admin = st.session_state['admin_connecte']

if is_admin:
    st.title("📊 Tableau de Bord Admin")
    brut = df_ventes['Benefice'].sum()
    net = brut - frais_mensuels
    
    c1, c2 = st.columns(2)
    c1.metric("Bénéfice Brut Total", f"{brut:,.2f} DA")
    c2.metric("Bénéfice NET Mensuel Estime", f"{net:,.2f} DA")

    tabs = st.tabs(["🛒 Caisse", "📦 Stock", "📈 Historique"])
    
    with tabs[1]:
        st.subheader("Inventaire")
        with st.expander("Ajouter Produit"):
            name = st.text_input("Nom")
            p_a = st.number_input("Achat")
            p_v = st.number_input("Vente")
            q_i = st.number_input("Quantité", min_value=1)
            if st.button("Ajouter"):
                new_item = pd.DataFrame([[name, p_a, 0, p_v, q_i]], columns=df_stock.columns)
                df_stock = pd.concat([df_stock, new_item], ignore_index=True)
                save_data(df_stock, "stock.csv")
                st.rerun()
        st.dataframe(df_stock)
        
    with tabs[2]:
        st.subheader("Ventes")
        st.dataframe(df_ventes)
else:
    st.title("🏪 Caisse Employé")

# --- CAISSE (ACCESSIBLE SELON MODE) ---
with (tabs[0] if is_admin else st.container()):
    if not df_stock.empty:
        art = st.selectbox("Article", df_stock["Article"])
        qte = st.number_input("Quantité", min_value=1, step=1)
        if st.button("Valider"):
            idx = df_stock[df_stock["Article"] == art].index[0]
            if df_stock.at[idx, "Quantite"] >= qte:
                # Calcul
                p_v = df_stock.at[idx, "PV"]
                p_a = df_stock.at[idx, "PA"]
                benef = qte * (p_v - p_a)
                # Save
                new_v = pd.DataFrame([[datetime.now().strftime("%d/%m/%Y"), art, qte, qte*p_v, benef]], columns=df_ventes.columns)
                df_ventes = pd.concat([df_ventes, new_v], ignore_index=True)
                df_stock.at[idx, "Quantite"] -= qte
                save_data(df_ventes, "ventes.csv")
                save_data(df_stock, "stock.csv")
                st.success("Vendu !")
                st.rerun()
