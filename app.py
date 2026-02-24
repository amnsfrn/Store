import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Happy Store Kids", layout="wide", page_icon="🛍️")

# Initialisation des sessions
if 'acces_autorise' not in st.session_state: st.session_state['acces_autorise'] = False
if 'admin_connecte' not in st.session_state: st.session_state['admin_connecte'] = False

# --- FONCTIONS DE DONNÉES ---
def load_data(file, columns):
    if os.path.exists(file):
        try:
            df = pd.read_csv(file)
            if not df.empty and 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce').dt.date
            return df
        except: return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

def save_data(df, file):
    df.to_csv(file, index=False)

# Chargement des fichiers
df_stock = load_data("stock.csv", ["Article", "PA", "Frais", "PV", "Quantite"])
df_ventes = load_data("ventes.csv", ["Date", "Article", "Qte", "Vente_Total", "Benefice"])
df_retours = load_data("retours.csv", ["Date", "Article", "Qte", "Montant_Rendu"])
df_demandes = load_data("demandes_stock.csv", ["Date", "Article", "Qte_Ajout", "PV_Suggere"])

# --- CONNEXION ---
if not st.session_state['acces_autorise'] and not st.session_state['admin_connecte']:
    st.title("🔐 Happy Store Kids")
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

# --- BARRE LATÉRALE (SIDEBAR) ---
st.sidebar.title("⚙️ Options")
if st.sidebar.button("🔴 Déconnexion"):
    st.session_state.clear()
    st.rerun()

# Bouton de sauvegarde manuelle (Téléchargement)
st.sidebar.markdown("---")
st.sidebar.subheader("💾 Sauvegarde locale")
csv_stock = df_stock.to_csv(index=False).encode('utf-8')
st.sidebar.download_button("📥 Télécharger Stock (CSV)", data=csv_stock, file_name=f"stock_{datetime.now().strftime('%d_%m')}.csv")

is_admin = st.session_state['admin_connecte']

# --- INTERFACE ---
if is_admin:
    tabs = st.tabs(["🛒 Caisse Directe", "📦 Gestion Stock", "💰 Bénéfices", "📜 Historiques"])
    caisse_tab, stock_tab = tabs[0], tabs[1]
else:
    tabs_u = st.tabs(["🛒 Caisse Directe", "📦 Arrivage"])
    caisse_tab, stock_tab = tabs_u[0], tabs_u[1]

# --- ONGLE : GESTION STOCK ---
with stock_tab:
    if is_admin:
        st.subheader("➕ Ajouter un Article")
        with st.form("add_form", clear_on_submit=True):
            n = st.text_input("Nom de l'article")
            q = st.number_input("Quantité totale", min_value=1)
            pa = st.number_input("Prix d'Achat (Unitaire)", min_value=0.0)
            fr_t = st.number_input("Frais de transport (TOTAL du lot)", min_value=0.0)
            pv = st.number_input("Prix de Vente", min_value=0.0)
            if st.form_submit_button("Ajouter au Stock"):
                if n:
                    fr_u = fr_t / q if q > 0 else 0
                    new_i = pd.DataFrame([[n, pa, fr_u, pv, q]], columns=df_stock.columns)
                    df_stock = pd.concat([df_stock, new_i], ignore_index=True)
                    save_data(df_stock, "stock.csv")
                    st.success(f"✅ {n} ajouté avec {fr_u:.2f} DA de frais/pièce")
                    st.rerun()
    else:
        # Interface employé pour les demandes (Arrivage)
        with st.form("user_form", clear_on_submit=True):
            n = st.text_input("Nom article reçu")
            q = st.number_input("Quantité", min_value=1)
            pv_s = st.number_input("PV Suggéré", min_value=0.0)
            if st.form_submit_button("Envoyer au Patron"):
                new_d = pd.DataFrame([[datetime.now().date(), n, q, pv_s]], columns=df_demandes.columns)
                save_data(pd.concat([df_demandes, new_d]), "demandes_stock.csv")
                st.info("Demande envoyée.")

# --- ONGLE : CAISSE DIRECTE ---
with caisse_tab:
    st.subheader("🛒 Terminal")
    if df_stock.empty:
        st.warning("Ajoutez des articles dans l'onglet Stock.")
    else:
        # VENTE
        with st.expander("💳 VENTE", expanded=True):
            with st.form("v_form", clear_on_submit=True):
                art = st.selectbox("Article", sorted(df_stock["Article"].unique().tolist()))
                row = df_stock[df_stock["Article"] == art].iloc[0]
                c1, c2 = st.columns(2)
                p_final = c1.number_input("Prix de vente", value=float(row['PV']))
                q_v = c2.number_input("Qté", min_value=1, max_value=int(row['Quantite']))
                if st.form_submit_button("Valider Vente"):
                    benef = q_v * (p_final - (row['PA'] + row['Frais']))
                    new_v = pd.DataFrame([[datetime.now().date(), art, q_v, q_v*p_final, benef]], columns=df_ventes.columns)
                    df_ventes = pd.concat([df_ventes, new_v], ignore_index=True)
                    df_stock.loc[df_stock["Article"] == art, "Quantite"] -= q_v
                    save_data(df_ventes, "ventes.csv"); save_data(df_stock, "stock.csv")
                    st.success("Vente enregistrée")
                    st.rerun()

        # RETOUR
        with st.expander("🔄 RETOUR CLIENT"):
            with st.form("r_form", clear_on_submit=True):
                art_r = st.selectbox("Article retourné", sorted(df_stock["Article"].unique().tolist()), key="sel_r")
                hist = df_ventes[df_ventes["Article"] == art_r]
                if not hist.empty:
                    opts = hist.apply(lambda x: f"{x['Date']} | Qté: {x['Qte']} | Prix: {x['Vente_Total']/x['Qte']} DA", axis=1).tolist()
                    sel = st.selectbox("Vente d'origine", opts)
                    q_r = st.number_input("Qté retournée", min_value=1)
                    if st.form_submit_button("Confirmer Retour"):
                        p_u = hist.iloc[opts.index(sel)]['Vente_Total'] / hist.iloc[opts.index(sel)]['Qte']
                        new_r = pd.DataFrame([[datetime.now().date(), art_r, q_r, q_r*p_u]], columns=df_retours.columns)
                        df_retours = pd.concat([df_retours, new_r], ignore_index=True)
                        df_stock.loc[df_stock["Article"] == art_r, "Quantite"] += q_r
                        save_data(df_retours, "retours.csv"); save_data(df_stock, "stock.csv")
                        st.success("Stock mis à jour !")
                        st.rerun()
                else: st.write("Aucun historique pour cet article.")
