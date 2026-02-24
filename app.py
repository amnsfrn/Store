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

# Chargement des fichiers
df_stock = load_data("stock.csv", ["Article", "PA", "Frais", "PV", "Quantite"])
df_ventes = load_data("ventes.csv", ["Date", "Article", "Qte", "Vente_Total", "Benefice"])
df_config = load_data("config.csv", ["Type", "Valeur"])

# --- BARRE LATÉRALE : ESPACE ADMIN ---
st.sidebar.title("🔐 Espace Admin")

if not st.session_state['admin_connecte']:
    # Mode Déconnecté
    pwd = st.sidebar.text_input("Mot de passe Admin", type="password")
    if st.sidebar.button("Se connecter"):
        if pwd == "9696":
            st.session_state['admin_connecte'] = True
            st.rerun()
        else:
            st.sidebar.error("Mot de passe incorrect")
else:
    # Mode Connecté
    st.sidebar.success("✅ Connecté en tant qu'Admin")
    if st.sidebar.button("🔴 Déconnexion"):
        st.session_state['admin_connecte'] = False
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Paramètres Frais Fixes")
    
    # Récupération loyer/salaire
    l_actuel = float(df_config[df_config['Type']=='Loyer']['Valeur'].values[0]) if not df_config[df_config['Type']=='Loyer'].empty else 0.0
    s_actuel = float(df_config[df_config['Type']=='Salaire']['Valeur'].values[0]) if not df_config[df_config['Type']=='Salaire'].empty else 0.0

    loyer_in = st.sidebar.number_input("Loyer Mensuel (DA)", value=l_actuel)
    salaire_in = st.sidebar.number_input("Salaire Employé (DA)", value=s_actuel)
    
    if st.sidebar.button("💾 Enregistrer Frais"):
        df_new_config = pd.DataFrame([["Loyer", loyer_in], ["Salaire", salaire_in]], columns=["Type", "Valeur"])
        save_data(df_new_config, "config.csv")
        st.sidebar.info("Paramètres sauvegardés !")
        st.rerun()

is_admin = st.session_state['admin_connecte']

# --- CALCULS FINANCIERS (PATRON) ---
loyer_val = float(df_config[df_config['Type']=='Loyer']['Valeur'].values[0]) if not df_config[df_config['Type']=='Loyer'].empty else 0.0
salaire_val = float(df_config[df_config['Type']=='Salaire']['Valeur'].values[0]) if not df_config[df_config['Type']=='Salaire'].empty else 0.0
total_frais_fixes = loyer_val + salaire_val

# --- INTERFACE PRINCIPALE ---
if is_admin:
    st.title("📊 Tableau de Bord Direction")
    
    # Métriques
    brut = df_ventes['Benefice'].sum()
    net = brut - total_frais_fixes
    val_stock = ((df_stock['PA'] + df_stock['Frais']) * df_stock['Quantite']).sum()

    c1, c2, c3 = st.columns(3)
    c1.metric("Bénéfice Brut", f"{brut:,.2f} DA")
    c2.metric("Bénéfice NET", f"{net:,.2f} DA", delta=f"-{total_frais_fixes} DA Frais")
    c3.metric("Valeur Stock", f"{val_stock:,.2f} DA")

    tabs = st.tabs(["🛒 Ventes", "📦 Stock & Alertes", "📈 Historique"])

    with tabs[0]:
        st.subheader("Caisse (Admin)")
        # La caisse est définie plus bas pour éviter la répétition

    with tabs[1]:
        st.subheader("État des Stocks")
        # Alerte stock bas
        alerte = df_stock[df_stock['Quantite'] <= 5]
        if not alerte.empty:
            st.warning(f"⚠️ {len(alerte)} articles sont presque épuisés !")
            st.dataframe(alerte[['Article', 'Quantite']])

        with st.expander("➕ Ajouter un Produit"):
            n = st.text_input("Nom de l'article")
            col_a, col_b = st.columns(2)
            pa = col_a.number_input("Prix d'Achat (DA)")
            fr = col_a.number_input("Frais (DA)")
            pv = col_b.number_input("Prix de Vente (DA)")
            qt = col_b.number_input("Quantité Initiale")
            if st.button("Enregistrer le produit"):
                new_art = pd.DataFrame([[n, pa, fr, pv, qt]], columns=df_stock.columns)
                df_stock = pd.concat([df_stock, new_art], ignore_index=True)
                save_data(df_stock, "stock.csv")
                st.rerun()
        st.dataframe(df_stock, use_container_width=True)

    with tabs[2]:
        st.subheader("Historique Complet")
        st.dataframe(df_ventes, use_container_width=True)

else:
    st.title("🏪 Caisse Magasin")
    st.info("Mode Employé actif. Prix d'achat et bénéfices masqués.")

# --- MODULE DE VENTE (COMMUN) ---
# Si Admin, on affiche dans l'onglet 0, sinon en direct
with (tabs[0] if is_admin else st.container()):
    if not df_stock.empty:
        art_sel = st.selectbox("Choisir l'article", df_stock["Article"], key="vente_art")
        info_art = df_stock[df_stock["Article"] == art_sel].iloc[0]
        st.info(f"Prix de vente : {info_art['PV']:,.2f} DA | Stock : {info_art['Quantite']}")
        
        qte_v = st.number_input("Quantité vendue", min_value=1, step=1)
        
        if st.button("Valider la Vente"):
            if info_art["Quantite"] >= qte_v:
                total_v = qte_v * info_art["PV"]
                benef_v = qte_v * (info_art["PV"] - (info_art["PA"] + info_art["Frais"]))
                
                # Mise à jour
                new_v = pd.DataFrame([[datetime.now().strftime("%d/%m/%Y"), art_sel, qte_v, total_v, benef_v]], columns=df_ventes.columns)
                df_ventes = pd.concat([df_ventes, new_v], ignore_index=True)
                df_stock.loc[df_stock["Article"] == art_sel, "Quantite"] -= qte_v
                
                save_data(df_ventes, "ventes.csv")
                save_data(df_stock, "stock.csv")
                st.success(f"Vente effectuée ! Total : {total_v:,.2f} DA")
                st.balloons()
                st.rerun()
            else:
                st.error("Stock insuffisant !")
    else:
        st.error("Le stock est vide. L'Admin doit ajouter des produits.")
