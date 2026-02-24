import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="Happy Store Kids", layout="wide", page_icon="🛍️")

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

# Chargement
df_stock = load_data("stock.csv", ["Article", "PA", "Frais", "PV", "Quantite"])
df_ventes = load_data("ventes.csv", ["Date", "Article", "Qte", "Vente_Total", "Benefice"])
df_demandes = load_data("demandes_stock.csv", ["Date", "Article", "Qte_Ajout", "PV_Suggere"])
df_hist_stock = load_data("hist_stock.csv", ["Date", "Article", "Qte_Ajoutee", "Par"])

# --- CONNEXION ---
if not st.session_state['acces_autorise'] and not st.session_state['admin_connecte']:
    st.title("🔐 Happy Store Kids")
    u = st.text_input("Utilisateur")
    p = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter"):
        if u.lower() == "admin" and p == "Thanksgod@99":
            st.session_state['admin_connecte'] = True
            st.session_state['acces_autorise'] = True
            st.rerun()
        elif u.lower() == "user" and p == "0699302032":
            st.session_state['acces_autorise'] = True
            st.rerun()
        else: st.error("Identifiants incorrects")
    st.stop()

if st.sidebar.button("🔴 Déconnexion"):
    st.session_state.clear()
    st.rerun()

is_admin = st.session_state['admin_connecte']

# --- INTERFACE ---
if is_admin:
    st.title("📊 Direction - Happy Store Kids")
    tabs = st.tabs(["🛒 Caisse", "📦 Stock & Validations", "💰 Bénéfices", "📜 Historiques"])
    
    with tabs[1]: # STOCK & VALIDATIONS
        st.subheader("✅ Demandes d'arrivage à valider")
        if not df_demandes.empty:
            for i, row in df_demandes.iterrows():
                with st.expander(f"Demande : {row['Article']} (+{row['Qte_Ajout']})", expanded=True):
                    c1, c2, c3, c4 = st.columns(4)
                    pa_val = c1.number_input(f"Prix d'Achat (Unitaire)", min_value=0.0, key=f"pa_{i}")
                    frais_val = c2.number_input(f"Frais (Unitaire)", min_value=0.0, key=f"fr_{i}")
                    pv_final = c3.number_input(f"Prix de Vente (PV)", min_value=0.0, value=float(row['PV_Suggere']), key=f"pv_{i}")
                    
                    if c4.button("Confirmer l'Entrée", key=f"btn_{i}"):
                        # Mise à jour du stock
                        if row['Article'] in df_stock['Article'].values:
                            idx = df_stock[df_stock["Article"] == row['Article']].index[0]
                            df_stock.at[idx, "Quantite"] += int(row['Qte_Ajout'])
                            df_stock.at[idx, "PA"] = pa_val
                            df_stock.at[idx, "Frais"] = frais_val
                            df_stock.at[idx, "PV"] = pv_final
                        else:
                            new_item = pd.DataFrame([[row['Article'], pa_val, frais_val, pv_final, row['Qte_Ajout']]], columns=df_stock.columns)
                            df_stock = pd.concat([df_stock, new_item], ignore_index=True)
                        
                        # Historique
                        new_h = pd.DataFrame([[datetime.now().strftime("%d/%m/%Y"), row['Article'], row['Qte_Ajout'], "User (Validé Admin)"]], columns=df_hist_stock.columns)
                        df_hist_stock = pd.concat([df_hist_stock, new_h], ignore_index=True)
                        
                        # Nettoyage
                        df_demandes = df_demandes.drop(i)
                        save_data(df_stock, "stock.csv")
                        save_data(df_hist_stock, "hist_stock.csv")
                        save_data(df_demandes, "demandes_stock.csv")
                        st.success(f"{row['Article']} ajouté au stock !")
                        st.rerun()
        else:
            st.info("Aucune demande en attente.")

        st.divider()
        st.subheader("📦 Inventaire Actuel")
        # Tri
        tri = st.selectbox("Trier par :", ["Nom (A-Z)", "Quantité (Croissant)"])
        df_display = df_stock.sort_values("Article") if tri == "Nom (A-Z)" else df_stock.sort_values("Quantite")
        st.dataframe(df_display, use_container_width=True)

    # ... (Tabs Caisse, Bénéfices, Historiques identiques)

else: # INTERFACE EMPLOYÉ
    st.title("🏪 Espace Employé")
    t1, t2 = st.tabs(["🛒 Caisse", "📦 Arrivage Marchandise"])
    
    with t2:
        st.subheader("Signaler une réception")
        # Recherche intelligente
        liste_art = sorted(df_stock["Article"].tolist()) + ["--- NOUVEL ARTICLE ---"]
        choix = st.selectbox("Article reçu :", liste_art)
        
        nom_art = st.text_input("Nom de l'article") if choix == "--- NOUVEL ARTICLE ---" else choix
        qte_art = st.number_input("Quantité reçue", min_value=1)
        pv_sug = st.number_input("Prix de Vente (PV) étiqueté", min_value=0.0)
        
        if st.button("Envoyer pour Validation Admin"):
            if nom_art:
                new_d = pd.DataFrame([[datetime.now().strftime("%d/%m/%Y"), nom_art, qte_art, pv_sug]], 
                                     columns=["Date", "Article", "Qte_Ajout", "PV_Suggere"])
                df_demandes = pd.concat([df_demandes, new_d], ignore_index=True)
                save_data(df_demandes, "demandes_stock.csv")
                st.success("Demande envoyée ! Le stock sera mis à jour après validation du patron.")

# --- MODULE CAISSE ---
# (Reprendre ici le code de vente/retour/fin de journée précédemment fourni)
