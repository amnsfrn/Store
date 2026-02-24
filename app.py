import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Happy Store Kids - Gestion", layout="wide", page_icon="🛍️")

# --- INITIALISATION DES SESSIONS ---
if 'acces_autorise' not in st.session_state:
    st.session_state['acces_autorise'] = False
if 'admin_connecte' not in st.session_state:
    st.session_state['admin_connecte'] = False

# --- PROTECTION À L'ENTRÉE (MOT DE PASSE GÉNÉRAL) ---
if not st.session_state['acces_autorise']:
    st.title("🔐 Accès Sécurisé - Happy Store Kids")
    entree = st.text_input("Entrez le mot de passe d'accès au magasin", type="password")
    if st.button("Entrer"):
        if entree == "happystorekids":
            st.session_state['acces_autorise'] = True
            st.rerun()
        else:
            st.error("Mot de passe incorrect")
    st.stop() # Arrête le code ici tant que le mot de passe n'est pas bon

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
st.sidebar.title("🛂 Contrôle")

if not st.session_state['admin_connecte']:
    st.sidebar.subheader("Connexion Admin")
    pwd = st.sidebar.text_input("Code Secret Admin", type="password")
    if st.sidebar.button("Se connecter"):
        if pwd == "9696":
            st.session_state['admin_connecte'] = True
            st.rerun()
        else:
            st.sidebar.error("Code incorrect")
else:
    st.sidebar.success("✅ Mode ADMIN actif")
    if st.sidebar.button("🔴 Déconnexion Admin"):
        st.session_state['admin_connecte'] = False
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Configuration des Frais")
    
    # Saisie des frais
    n_loyer = st.sidebar.number_input("Loyer Mensuel", value=0.0)
    n_salaire = st.sidebar.number_input("Salaire Mensuel", value=0.0)
    n_trim = st.sidebar.number_input("Factures (Trimestre)", value=0.0)
    n_casnos = st.sidebar.number_input("CASNOS (Annuel)", value=0.0)
    n_impots = st.sidebar.number_input("Impôts (Annuel)", value=0.0)
    
    if st.sidebar.button("💾 Enregistrer Frais"):
        d = [["Loyer", n_loyer], ["Salaire", n_salaire], ["Factures_Trim", n_trim], ["Casnos", n_casnos], ["Impots", n_impots]]
        save_data(pd.DataFrame(d, columns=["Type", "Valeur"]), "config.csv")
        st.sidebar.success("Frais sauvegardés !")
        st.rerun()

# --- CALCUL DES CHARGES ---
frais_mensuels = 0.0
if not df_config.empty:
    for t, v in zip(df_config['Type'], df_config['Valeur']):
        if t == "Loyer" or t == "Salaire": frais_mensuels += float(v)
        if t == "Factures_Trim": frais_mensuels += float(v) / 3
        if t in ["Casnos", "Impots"]: frais_mensuels += float(v) / 12

# --- INTERFACE ---
is_admin = st.session_state['admin_connecte']

if is_admin:
    st.title("📊 Direction - Happy Store Kids")
    brut = df_ventes['Benefice'].sum()
    net = brut - frais_mensuels
    
    c1, c2 = st.columns(2)
    c1.metric("Bénéfice Brut Total", f"{brut:,.2f} DA")
    c2.metric("Bénéfice NET Mensuel", f"{net:,.2f} DA")

    tabs = st.tabs(["🛒 Caisse", "📦 Stock & Achats", "📈 Historique & Frais"])
    
    with tabs[1]:
        st.subheader("Gestion des Articles")
        with st.expander("Ajouter un nouveau produit"):
            name = st.text_input("Nom de l'article")
            col_a, col_b = st.columns(2)
            p_a = col_a.number_input("Prix d'Achat")
            p_f = col_a.number_input("Frais (Transport/Douane)")
            p_v = col_b.number_input("Prix de Vente")
            q_i = col_b.number_input("Quantité en stock", min_value=1)
            if st.button("Ajouter au stock"):
                new_item = pd.DataFrame([[name, p_a, p_f, p_v, q_i]], columns=df_stock.columns)
                df_stock = pd.concat([df_stock, new_item], ignore_index=True)
                save_data(df_stock, "stock.csv")
                st.success("Produit ajouté !")
                st.rerun()
        st.dataframe(df_stock, use_container_width=True)
        
    with tabs[2]:
        st.subheader("Historique des ventes")
        st.dataframe(df_ventes, use_container_width=True)
else:
    st.title("🏪 Caisse Magasin")

# --- CAISSE ---
with (tabs[0] if is_admin else st.container()):
    if not df_stock.empty:
        art = st.selectbox("Sélectionner l'article", df_stock["Article"])
        idx = df_stock[df_stock["Article"] == art].index[0]
        st.info(f"Prix : {df_stock.at[idx, 'PV']:,.2f} DA | En stock : {df_stock.at[idx, 'Quantite']}")
        qte = st.number_input("Quantité à vendre", min_value=1, step=1)
        
        if st.button("Valider la Vente"):
            if df_stock.at[idx, "Quantite"] >= qte:
                p_v = df_stock.at[idx, "PV"]
                p_a = df_stock.at[idx, "PA"]
                p_f = df_stock.at[idx, "Frais"]
                benef = qte * (p_v - (p_a + p_f))
                
                # Sauvegarde
                new_v = pd.DataFrame([[datetime.now().strftime("%d/%m/%Y"), art, qte, qte*p_v, benef]], columns=df_ventes.columns)
                df_ventes = pd.concat([df_ventes, new_v], ignore_index=True)
                df_stock.at[idx, "Quantite"] -= qte
                save_data(df_ventes, "ventes.csv")
                save_data(df_stock, "stock.csv")
                st.success("Vente enregistrée avec succès !")
                st.rerun()
            else:
                st.error("Stock insuffisant !")
    else:
        st.warning("Le stock est vide.")
