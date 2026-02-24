import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Happy Store Kids", layout="wide", page_icon="🛍️")

# Initialisation critique des variables de session
if 'panier' not in st.session_state: st.session_state['panier'] = []
if 'acces_autorise' not in st.session_state: st.session_state['acces_autorise'] = False
if 'admin_connecte' not in st.session_state: st.session_state['admin_connecte'] = False

# --- GESTION DES FICHIERS ---
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
    u, p = st.text_input("Utilisateur"), st.text_input("Mot de passe", type="password")
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

# --- NAVIGATION (ONGLETS) ---
is_admin = st.session_state['admin_connecte']
if is_admin:
    t1, t2, t3 = st.tabs(["🛒 Caisse Directe", "📦 Gestion Stock", "✅ Validations"])
else:
    t1, t2 = st.tabs(["🛒 Caisse Directe", "📩 Envoyer Arrivage"])

# --- 1. ONGLET CAISSE (MULTI-ARTICLES) ---
with t1:
    st.subheader("🛒 Terminal de Vente")
    recherche = st.text_input("⌨️ Tapez le nom de l'article :", placeholder="Propositions automatiques...")
    
    if recherche:
        mask = df_stock["Article"].str.contains(recherche, case=False, na=False) & (df_stock["Quantite"] > 0)
        suggestions = df_stock[mask]
        if not suggestions.empty:
            for _, item in suggestions.iterrows():
                c1, c2 = st.columns([3, 1])
                c1.write(f"**{item['Article']}** | {item['PV']} DA")
                if c2.button(f"Choisir ➕", key=f"add_{item['Article']}"):
                    if not any(p['Article'] == item['Article'] for p in st.session_state['panier']):
                        st.session_state['panier'].append({
                            'Article': item['Article'], 'PV': float(item['PV']),
                            'Qte': 1, 'PA': float(item['PA']),
                            'Frais': float(item['Frais']), 'Max': int(item['Quantite'])
                        })
                        st.rerun()

    st.divider()

    if st.session_state['panier']:
        total_general = 0
        st.write("### 🛍️ Articles sélectionnés")
        for idx, p in enumerate(st.session_state['panier']):
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 0.5])
                col1.write(f"**{p['Article']}**")
                p['PV'] = col2.number_input("Prix", value=p['PV'], key=f"p_{idx}", step=50.0)
                p['Qte'] = col3.number_input("Qté", min_value=1, max_value=p['Max'], value=p['Qte'], key=f"q_{idx}")
                if col4.button("❌", key=f"del_{idx}"):
                    st.session_state['panier'].pop(idx)
                    st.rerun()
                total_general += p['PV'] * p['Qte']
        
        st.markdown(f"""
            <div style="background-color:#d4edda; padding:20px; border-radius:12px; border: 2px solid #28a745; text-align:center;">
                <h2 style="color:#155724; margin:0;">TOTAL GÉNÉRAL</h2>
                <h1 style="color:#28a745; margin:0; font-size: 55px; font-weight: bold;">{total_general:,.0f} DA</h1>
            </div>
        """, unsafe_content_html=True)

        if st.button("💰 ENCAISSER ET VIDER LA CAISSE", use_container_width=True, type="primary"):
            for p in st.session_state['panier']:
                benef = p['Qte'] * (p['PV'] - (p['PA'] + p['Frais']))
                new_v = pd.DataFrame([[datetime.now().date(), p['Article'], p['Qte'], p['PV']*p['Qte'], benef]], 
                                     columns=["Date", "Article", "Qte", "Vente_Total", "Benefice"])
                df_ventes = pd.concat([df_ventes, new_v], ignore_index=True)
                df_stock.loc[df_stock["Article"] == p['Article'], "Quantite"] -= p['Qte']
            save_data(df_ventes, "ventes.csv"); save_data(df_stock, "stock.csv")
            st.session_state['panier'] = []
            st.success("Vente réussie !")
            st.rerun()

# --- 2. ONGLET STOCK & ARRIVAGE ---
if is_admin:
    with t2:
        st.subheader("📦 Modification du Stock")
        recherche_edit = st.text_input("🔍 Rechercher article à modifier :")
        if recherche_edit:
            s_edit = df_stock[df_stock["Article"].str.contains(recherche_edit, case=False, na=False)]
            if not s_edit.empty:
                art_sel = st.selectbox("Article :", s_edit["Article"].tolist())
                idx = df_stock[df_stock["Article"] == art_sel].index[0]
                row = df_stock.loc[idx]
                with st.form("edit_f"):
                    n_n = st.text_input("Nom", value=row['Article'])
                    n_pa = st.number_input("Achat", value=float(row['PA']))
                    n_fr = st.number_input("Frais", value=float(row['Frais']))
                    n_pv = st.number_input("PV", value=float(row['PV']))
                    n_q = st.number_input("Quantité", value=int(row['Quantite']))
                    if st.form_submit_button("💾 Sauvegarder"):
                        df_stock.loc[idx] = [n_n, n_pa, n_fr, n_pv, n_q]
                        save_data(df_stock, "stock.csv"); st.rerun()

    with t3:
        st.subheader("✅ Valider Arrivages")
        if df_demandes.empty: st.info("Aucun arrivage en attente.")
        else:
            for i, d in df_demandes.iterrows():
                with st.expander(f"📦 {d['Article']} ({int(d['Qte'])} pcs)"):
                    with st.form(f"val_{i}"):
                        v_pa = st.number_input("Achat Unit.", min_value=0.0)
                        v_fr_tot = st.number_input("Frais Transport TOTAUX", min_value=0.0)
                        v_pv = st.number_input("PV Final", value=float(d['PV_Suggere']))
                        if st.form_submit_button("✅ Ajouter au Stock"):
                            f_u = v_fr_tot / d['Qte'] if d['Qte'] > 0 else 0
                            new_item = pd.DataFrame([[d['Article'], v_pa, f_u, v_pv, d['Qte']]], columns=df_stock.columns)
                            df_stock = pd.concat([df_stock, new_item], ignore_index=True)
                            df_demandes = df_demandes.drop(i)
                            save_data(df_stock, "stock.csv"); save_data(df_demandes, "demandes.csv")
                            st.rerun()
else:
    with t2:
        st.subheader("📩 Signaler un Arrivage")
        with st.form("arr_f"):
            a_n = st.text_input("Nom de l'article")
            a_q = st.number_input("Quantité", min_value=1)
            a_pv = st.number_input("PV suggéré", min_value=0.0)
            if st.form_submit_button("Envoyer à l'Admin"):
                new_d = pd.DataFrame([[datetime.now().date(), a_n, a_q, a_pv]], columns=df_demandes.columns)
                df_demandes = pd.concat([df_demandes, new_d], ignore_index=True)
                save_data(df_demandes, "demandes.csv"); st.success("Envoyé !"); st.rerun()
