import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Configuration
st.set_page_config(page_title="Gestion Magasin DZ", layout="wide")

# --- PARAMÈTRES FIXES ---
CODE_PATRON = "9696"

# --- CHARGEMENT DES DONNÉES ---
def load_data(file, columns):
    if os.path.exists(file):
        return pd.read_csv(file)
    return pd.DataFrame(columns=columns)

def save_data(df, file):
    df.to_csv(file, index=False)

df_stock = load_data("stock.csv", ["Article", "PA", "Frais", "PV", "Quantite"])
df_ventes = load_data("ventes.csv", ["Date", "Article", "Qte", "Vente_Total", "Benefice"])
# Fichier pour stocker Loyer/Salaire
df_config = load_data("config.csv", ["Type", "Valeur"])

# --- ACCÈS ---
st.sidebar.title("🔐 Administration")
pwd = st.sidebar.text_input("Code Patron", type="password")
is_admin = (pwd == CODE_PATRON)

if is_admin:
    st.title("📊 Tableau de Bord Direction")
    
    # --- SECTION CONFIGURATION INITIALE ---
    with st.sidebar.expander("⚙️ Paramètres Fixes (Mensuels)"):
        loyer_m = st.number_input("Loyer Mensuel (DA)", value=float(df_config[df_config['Type']=='Loyer']['Valeur'].values[0]) if not df_config[df_config['Type']=='Loyer'].empty else 0.0)
        salaire_m = st.number_input("Salaire Employé (DA)", value=float(df_config[df_config['Type']=='Salaire']['Valeur'].values[0]) if not df_config[df_config['Type']=='Salaire'].empty else 0.0)
        
        if st.button("Enregistrer Paramètres"):
            df_config = pd.DataFrame([["Loyer", loyer_m], ["Salaire", salaire_m]], columns=["Type", "Valeur"])
            save_data(df_config, "config.csv")
            st.success("Paramètres mis à jour !")

    # --- CALCULS FINANCIERS ---
    charges_mensuelles = loyer_m + salaire_m
    charge_journaliere = charges_mensuelles / 30
    
    brut_total = df_ventes['Benefice'].sum()
    # On calcule les charges cumulées depuis le début du mois (ou total)
    net_total = brut_total - charges_mensuelles # Ici on retire le mois complet par défaut

    col1, col2, col3 = st.columns(3)
    col1.metric("Bénéfice Brut", f"{brut_total:,.2f} DA")
    col2.metric("Charges Fixes", f"- {charges_mensuelles:,.2f} DA", help="Loyer + Salaire")
    col3.metric("Bénéfice NET", f"{net_total:,.2f} DA", delta_color="normal")

    tabs = st.tabs(["💰 Ventes", "📦 Stocks & Alertes", "📈 Historique & Calendrier"])

    # ONGLET STOCKS
    with tabs[1]:
        st.subheader("Gestion des Articles")
        low_stock = df_stock[df_stock['Quantite'] <= 5]
        if not low_stock.empty:
            st.error(f"⚠️ Alerte : {len(low_stock)} articles bientôt épuisés !")
        st.dataframe(df_stock, use_container_width=True)
        
        with st.expander("Ajouter un nouveau produit"):
            n = st.text_input("Nom")
            c1, c2 = st.columns(2)
            pa = c1.number_input("Prix d'Achat")
            fr = c1.number_input("Frais")
            pv = c2.number_input("Prix de Vente")
            qt = c2.number_input("Quantité")
            if st.button("Valider l'ajout"):
                new = pd.DataFrame([[n, pa, fr, pv, qt]], columns=df_stock.columns)
                df_stock = pd.concat([df_stock, new], ignore_index=True)
                save_data(df_stock, "stock.csv")
                st.rerun()

    # ONGLET HISTORIQUE
    with tabs[2]:
        st.subheader("Historique des Ventes")
        st.dataframe(df_ventes, use_container_width=True)
        st.write(f"**Analyse :** Le coût de fonctionnement de votre magasin est de **{charge_journaliere:,.2f} DA par jour**.")

# --- LOGIQUE EMPLOYÉ ---
else:
    st.title("🏪 Caisse Magasin")
    if not df_stock.empty:
        art = st.selectbox("Article", df_stock["Article"])
        prix_v = df_stock[df_stock["Article"] == art]["PV"].values[0]
        st.info(f"Prix : {prix_v:,.2f} DA")
        qte = st.number_input("Quantité", min_value=1)
        if st.button("Valider la Vente"):
            row = df_stock[df_stock["Article"] == art].iloc[0]
            if row["Quantite"] >= qte:
                benef_vente = qte * (row["PV"] - (row["PA"] + row["Frais"]))
                total_vente = qte * row["PV"]
                
                # Sauvegarde vente
                new_v = pd.DataFrame([[datetime.now().strftime("%d/%m/%Y"), art, qte, total_vente, benef_vente]], columns=df_ventes.columns)
                df_ventes = pd.concat([df_ventes, new_v], ignore_index=True)
                # Maj Stock
                df_stock.loc[df_stock["Article"] == art, "Quantite"] -= qte
                
                save_data(df_ventes, "ventes.csv")
                save_data(df_stock, "stock.csv")
                st.success("Vente réussie !")
                st.rerun()
            else:
                st.error("Stock insuffisant")
