import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURATION DE PAGE ---
st.set_page_config(page_title="Gestion Magasin Pro DZ", layout="wide", page_icon="🇩🇿")

# --- INITIALISATION DE LA SESSION ---
if 'admin_connecte' not in st.session_state:
    st.session_state['admin_connecte'] = False

# --- FONCTIONS DE DONNÉES ---
def load_data(file, columns):
    if os.path.exists(file):
        try:
            return pd.read_csv(file)
        except:
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

def save_data(df, file):
    df.to_csv(file, index=False)

# Chargement initial des fichiers
df_stock = load_data("stock.csv", ["Article", "PA", "Frais", "PV", "Quantite"])
df_ventes = load_data("ventes.csv", ["Date", "Article", "Qte", "Vente_Total", "Benefice"])
df_config = load_data("config.csv", ["Type", "Valeur"])

# --- FONCTION DE RÉCUPÉRATION DES FRAIS (DÉFINIE AVANT UTILISATION) ---
def get_val(t, df):
    if not df.empty and t in df['Type'].values:
        return float(df[df['Type']==t]['Valeur'].values[0])
    return 0.0

# --- BARRE LATÉRALE : ESPACE ADMIN ---
st.sidebar.title("🔐 Espace Admin")

if not st.session_state['admin_connecte']:
    pwd = st.sidebar.text_input("Mot de passe Admin", type="password")
    if st.sidebar.button("Se connecter"):
        if pwd == "9696":
            st.session_state['admin_connecte'] = True
            st.rerun()
        else:
            st.sidebar.error("Mot de passe incorrect")
else:
    st.sidebar.success("✅ Connecté en tant qu'Admin")
    if st.sidebar.button("🔴 Déconnexion"):
        st.session_state['admin_connecte'] = False
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Configuration des Frais")
    
    # Formulaire de saisie avec valeurs actuelles
    loyer_in = st.sidebar.number_input("Loyer Mensuel (DA)", value=get_val("Loyer", df_config))
    salaire_in = st.sidebar.number_input("Salaire Mensuel (DA)", value=get_val("Salaire", df_config))
    fact_trim_in = st.sidebar.number_input("Factures (Trimestrielles) (DA)", value=get_val("Factures_Trim", df_config))
    casnos_in = st.sidebar.number_input("CASNOS (Annuelle) (DA)", value=get_val("Casnos_Annuel", df_config))
    impots_in = st.sidebar.number_input("Impôts (Annuels) (DA)", value=get_val("Impots_Annuel", df_config))
    
    if st.sidebar.button("💾 Enregistrer tous les frais"):
        data = [
            ["Loyer", loyer_in],
            ["Salaire", salaire_in],
            ["Factures_Trim", fact_trim_in],
            ["Casnos_Annuel", casnos_in],
            ["Impots_Annuel", impots_in]
        ]
        df_new_config = pd.DataFrame(data, columns=["Type", "Valeur"])
        save_data(df_new_config, "config.csv")
        st.sidebar.info("Frais mis à jour !")
        st.rerun()

is_admin = st.session_state['admin_connecte']

# --- CALCUL DES CHARGES MENSUELLES ---
frais_mensuels = (
    get_val("Loyer", df_config) + 
    get_val("Salaire", df_config) + 
    (get_val("Factures_Trim", df_config) / 3) + 
    (get_val("Casnos_Annuel", df_config) / 12) + 
    (get_val("Impots_Annuel", df_config) / 12)
)

# --- INTERFACE PRINCIPALE ---
if is_admin:
    st.title("📊 Tableau de Bord Direction")
    
    brut = df_ventes['Benefice'].sum()
    net = brut - frais_mensuels
    val_stock = ((df_stock['PA'] + df_stock['Frais']) * df_stock['Quantite']).sum()

    c1, c2, c3 = st.columns(3)
    c1.metric("Bénéfice Brut Total", f"{brut:,.2f} DA")
    c2.metric("Bénéfice NET Mensuel", f"{net:,.2f} DA", delta=f"-{frais_mensuels:,.2f} DA charges")
    c3.metric("Valeur du Stock", f"{val_stock:,.2f} DA")

    tabs = st.tabs(["🛒 Caisse", "📦 Stock", "📈 Historique & Frais"])

    with tabs[1]:
        st.subheader("Gestion du Stock")
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

    with tabs[2]:
        st.subheader("Détail des Charges Mensuelles")
        st.write(f"- Loyer : {get_val('Loyer', df_config):,.2f} DA")
        st.write(f"- Salaire : {get_val('Salaire', df_config):,.2f} DA")
        st.write(f"- Part Factures (Trim/3) : {get_val('Factures_Trim', df_config)/3:,.2f} DA")
        st.write(f"- Part CASNOS (Annuel/12) : {get_val('Casnos_Annuel', df_config)/12:,.2f} DA")
        st.write(f"- Part Impôts (Annuel/12) : {get_val('Impots_Annuel', df_config)/12:,.2f} DA")
        st.markdown("---")
        st.subheader("Historique des Ventes")
        st.dataframe(df_ventes, use_container_width=True)
else:
    st.title("🏪 Caisse Magasin")

# --- MODULE DE VENTE ---
with (tabs[0] if is_admin else st.container()):
    if not df_stock.empty:
        art_sel = st.selectbox("Article", df_stock["Article"])
        info = df_stock[df_stock["Article"] == art_sel].iloc[0]
        st.info(f"Prix : {info['PV']:,.2f} DA | Stock : {info['Quantite']}")
        qte_v = st.number_input("Quantité", min_value=1, step=1)
        
        if st.button("Valider la Vente"):
            if info["Quantite"] >= qte_v:
                total_v = qte_v * info["PV"]
                benef_v = qte_v * (info["PV"] - (info["PA"] + info["Frais"]))
                new_v = pd.DataFrame([[datetime.now().strftime("%d/%m/%Y"), art_sel, qte_v, total_v, benef_v]], columns=df_ventes.columns)
                df_ventes = pd.concat([df_ventes, new_v], ignore_index=True)
                df_stock.loc[df_stock["Article"] == art_sel, "Quantite"] -= qte_v
                save_data(df_ventes, "ventes.csv")
                save_data(df_stock, "stock.csv")
                st.success(f"Vendu ! {total_v:,.2f} DA")
                st.balloons()
                st.rerun()
