import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Happy Store Kids", layout="wide", page_icon="🛍️")

if 'acces_autorise' not in st.session_state: st.session_state['acces_autorise'] = False
if 'admin_connecte' not in st.session_state: st.session_state['admin_connecte'] = False

# --- CHARGEMENT ---
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

df_stock = load_data("stock.csv", ["Article", "PA", "Frais", "PV", "Quantite"])
df_ventes = load_data("ventes.csv", ["Date", "Article", "Qte", "Vente_Total", "Benefice"])
df_demandes = load_data("demandes.csv", ["Date", "Article", "Qte", "PV_Suggere"])

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

# --- BARRE LATÉRALE ---
with st.sidebar:
    if st.button("🔴 DÉCONNEXION", use_container_width=True):
        st.session_state.clear()
        st.rerun()

is_admin = st.session_state['admin_connecte']

# --- NAVIGATION ---
if is_admin:
    tabs = st.tabs(["🛒 Caisse Directe", "📦 Gestion Stock", "✅ Validations", "📊 Rapports"])
else:
    tabs = st.tabs(["🛒 Caisse Directe", "📩 Envoyer Arrivage"])

# --- 1. CAISSE (PROPOSITIONS INSTANTANÉES) ---
with tabs[0]:
    st.subheader("🛒 Terminal de Vente")
    if df_stock.empty:
        st.info("Stock vide.")
    else:
        # Champ de texte qui déclenche la recherche
        recherche = st.text_input("⌨️ Tapez le nom de l'article :", key="search_box")
        
        if recherche:
            # Filtrage en temps réel
            mask = df_stock["Article"].str.contains(recherche, case=False, na=False)
            suggestions = df_stock[mask]["Article"].tolist()
            
            if suggestions:
                st.write("🔍 **Suggestions trouvées :**")
                # Affichage des propositions sous forme de boutons pour sélection rapide
                choix = st.radio("Cliquez sur l'article voulu :", suggestions, label_visibility="collapsed")
                
                if choix:
                    info = df_stock[df_stock["Article"] == choix].iloc[0]
                    with st.form("vente_form", clear_on_submit=True):
                        st.info(f"Sélection : **{choix}** | Stock : **{int(info['Quantite'])}**")
                        c1, c2 = st.columns(2)
                        p_v = c1.number_input("Prix (DA)", value=float(info['PV']))
                        q_v = c2.number_input("Quantité", min_value=1, max_value=int(info['Quantite']), step=1)
                        
                        if st.form_submit_button("✅ VALIDER LA VENTE"):
                            benef = q_v * (p_v - (info['PA'] + info['Frais']))
                            new_v = pd.DataFrame([[datetime.now().date(), choix, q_v, q_v*p_v, benef]], columns=df_ventes.columns)
                            df_ventes = pd.concat([df_ventes, new_v], ignore_index=True)
                            df_stock.loc[df_stock["Article"] == choix, "Quantite"] -= q_v
                            save_data(df_ventes, "ventes.csv"); save_data(df_stock, "stock.csv")
                            st.success(f"Vendu : {choix}")
                            st.rerun()
            else:
                st.warning("Aucun article trouvé.")

# --- 2. GESTION STOCK (PROPOSITIONS ADMIN) ---
if is_admin:
    with tabs[1]:
        st.subheader("📦 Modifier un article")
        recherche_edit = st.text_input("🔍 Chercher pour modifier :", key="edit_search")
        if recherche_edit:
            mask_edit = df_stock["Article"].str.contains(recherche_edit, case=False, na=False)
            suggestions_edit = df_stock[mask_edit]["Article"].tolist()
            if suggestions_edit:
                art_edit = st.radio("Choisir l'article :", suggestions_edit, key="radio_edit")
                idx = df_stock[df_stock["Article"] == art_edit].index[0]
                row = df_stock.loc[idx]
                with st.form("edit_stock"):
                    n_n = st.text_input("Nom", value=row['Article'])
                    n_pa = st.number_input("Achat Unit.", value=float(row['PA']))
                    n_fr = st.number_input("Frais Unit.", value=float(row['Frais']))
                    n_pv = st.number_input("PV", value=float(row['PV']))
                    n_q = st.number_input("Quantité", value=int(row['Quantite']))
                    c1, c2 = st.columns(2)
                    if c1.form_submit_button("💾 Sauvegarder"):
                        df_stock.loc[idx] = [n_n, n_pa, n_fr, n_pv, n_q]
                        save_data(df_stock, "stock.csv"); st.rerun()
                    if c2.form_submit_button("🗑️ Supprimer"):
                        df_stock = df_stock.drop(idx); save_data(df_stock, "stock.csv"); st.rerun()

    # VALIDATIONS (Frais Totaux)
    with tabs[2]:
        st.subheader("✅ Valider Arrivages")
        if df_demandes.empty: st.write("Rien à valider.")
        else:
            for i, d in df_demandes.iterrows():
                with st.expander(f"📦 {d['Article']} ({int(d['Qte'])} pcs)"):
                    with st.form(f"val_form_{i}"):
                        v_pa = st.number_input("Achat Unit.", min_value=0.0)
                        v_fr_tot = st.number_input("Frais TRANSPORT TOTAUX", min_value=0.0)
                        v_pv = st.number_input("PV Final", value=float(d['PV_Suggere']))
                        if st.form_submit_button("Mettre en stock"):
                            f_u = v_fr_tot / d['Qte'] if d['Qte'] > 0 else 0
                            new_item = pd.DataFrame([[d['Article'], v_pa, f_u, v_pv, d['Qte']]], columns=df_stock.columns)
                            df_stock = pd.concat([df_stock, new_item], ignore_index=True)
                            df_demandes = df_demandes.drop(i)
                            save_data(df_stock, "stock.csv"); save_data(df_demandes, "demandes.csv")
                            st.rerun()
