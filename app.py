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

# --- 1. CAISSE (AVEC AFFICHAGE DU TOTAL) ---
with tabs[0]:
    st.subheader("🛒 Terminal de Vente")
    if df_stock.empty:
        st.info("Stock vide.")
    else:
        recherche = st.text_input("⌨️ Tapez le nom de l'article :", key="search_box")
        
        if recherche:
            mask = df_stock["Article"].str.contains(recherche, case=False, na=False)
            suggestions = df_stock[mask]["Article"].tolist()
            
            if suggestions:
                choix = st.radio("Sélectionnez l'article :", suggestions, label_visibility="collapsed")
                
                if choix:
                    info = df_stock[df_stock["Article"] == choix].iloc[0]
                    with st.form("vente_form", clear_on_submit=True):
                        st.info(f"Produit : **{choix}** | En stock : **{int(info['Quantite'])}**")
                        
                        col1, col2 = st.columns(2)
                        p_v = col1.number_input("Prix Unitaire (DA)", value=float(info['PV']), step=50.0)
                        q_v = col2.number_input("Quantité", min_value=1, max_value=int(info['Quantite']), step=1)
                        
                        # --- AFFICHAGE DU TOTAL EN TEMPS RÉEL ---
                        total_ticket = p_v * q_v
                        st.markdown(f"""
                        <div style="background-color:#2e3136; padding:20px; border-radius:10px; border-left: 8px solid #ff4b4b; margin-bottom:20px">
                            <h2 style="color:white; margin:0;">TOTAL À PAYER :</h2>
                            <h1 style="color:#ff4b4b; margin:0;">{total_ticket:,.2f} DA</h1>
                        </div>
                        """, unsafe_content_html=True)
                        
                        if st.form_submit_button("✅ ENREGISTRER LA VENTE"):
                            benef = q_v * (p_v - (info['PA'] + info['Frais']))
                            new_v = pd.DataFrame([[datetime.now().date(), choix, q_v, total_ticket, benef]], columns=df_ventes.columns)
                            df_ventes = pd.concat([df_ventes, new_v], ignore_index=True)
                            df_stock.loc[df_stock["Article"] == choix, "Quantite"] -= q_v
                            save_data(df_ventes, "ventes.csv"); save_data(df_stock, "stock.csv")
                            st.success(f"Vente validée : {total_ticket:,.2f} DA")
                            st.rerun()
            else:
                st.warning("Aucun article trouvé.")

# --- 2. GESTION STOCK & VALIDATION ---
if is_admin:
    with tabs[1]:
        st.subheader("📦 Modification")
        # (Le code de recherche/modification reste le même pour la rapidité)
        recherche_edit = st.text_input("🔍 Chercher article :", key="edit_search")
        if recherche_edit:
            mask_edit = df_stock["Article"].str.contains(recherche_edit, case=False, na=False)
            s_edit = df_stock[mask_edit]["Article"].tolist()
            if s_edit:
                art_edit = st.radio("Choisir :", s_edit, key="r_edit")
                idx = df_stock[df_stock["Article"] == art_edit].index[0]
                row = df_stock.loc[idx]
                with st.form("edit_stock"):
                    n_n = st.text_input("Nom", value=row['Article'])
                    n_pa = st.number_input("Achat Unit.", value=float(row['PA']))
                    n_fr = st.number_input("Frais Unit.", value=float(row['Frais']))
                    n_pv = st.number_input("PV", value=float(row['PV']))
                    n_q = st.number_input("Quantité", value=int(row['Quantite']))
                    if st.form_submit_button("💾 Sauvegarder"):
                        df_stock.loc[idx] = [n_n, n_pa, n_fr, n_pv, n_q]
                        save_data(df_stock, "stock.csv"); st.rerun()

    with tabs[2]:
        st.subheader("✅ Valider Arrivages (Calcul Frais)")
        if df_demandes.empty: st.write("Rien à valider.")
        else:
            for i, d in df_demandes.iterrows():
                with st.expander(f"📦 {d['Article']} ({int(d['Qte'])} pcs)"):
                    with st.form(f"val_{i}"):
                        v_pa = st.number_input("Prix d'Achat Unitaire", min_value=0.0)
                        v_fr_tot = st.number_input("Frais de TRANSPORT TOTAUX", min_value=0.0)
                        v_pv = st.number_input("Prix de Vente Final", value=float(d['PV_Suggere']))
                        
                        # --- AFFICHAGE TOTAL ACHAT POUR L'ADMIN ---
                        total_investissement = (v_pa * d['Qte']) + v_fr_tot
                        st.write(f"💰 Investissement total pour ce lot : **{total_investissement:,.2f} DA**")
                        
                        if st.form_submit_button("✅ Ajouter au Stock"):
                            f_u = v_fr_tot / d['Qte'] if d['Qte'] > 0 else 0
                            new_item = pd.DataFrame([[d['Article'], v_pa, f_u, v_pv, d['Qte']]], columns=df_stock.columns)
                            df_stock = pd.concat([df_stock, new_item], ignore_index=True)
                            df_demandes = df_demandes.drop(i)
                            save_data(df_stock, "stock.csv"); save_data(df_demandes, "demandes.csv")
                            st.rerun()
