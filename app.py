import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Happy Store Kids", layout="wide", page_icon="🛍️")

# Initialisation critique des variables de session (évite les erreurs TypeError)
if 'panier' not in st.session_state: st.session_state['panier'] = []
if 'acces_autorise' not in st.session_state: st.session_state['acces_autorise'] = False
if 'admin_connecte' not in st.session_state: st.session_state['admin_connecte'] = False

# --- CHARGEMENT DES DONNÉES ---
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
    if st.button("🔴 DÉCONNEXION"):
        st.session_state.clear()
        st.rerun()
    if st.session_state['panier']:
        if st.button("🗑️ VIDER LA CAISSE"):
            st.session_state['panier'] = []
            st.rerun()

# --- NAVIGATION ---
is_admin = st.session_state['admin_connecte']
tabs = st.tabs(["🛒 Caisse", "📦 Stock", "✅ Validations"]) if is_admin else st.tabs(["🛒 Caisse", "📩 Arrivage"])

# --- 1. ONGLET CAISSE (MULTI-ARTICLES) ---
with tabs[0]:
    st.subheader("🛒 Terminal de Vente")
    
    # Recherche avec propositions automatiques
    recherche = st.text_input("⌨️ Chercher un article :", placeholder="Tapez les premières lettres...")
    
    if recherche:
        suggestions = df_stock[df_stock["Article"].str.contains(recherche, case=False, na=False) & (df_stock["Quantite"] > 0)]
        if not suggestions.empty:
            for _, item in suggestions.iterrows():
                col1, col2 = st.columns([3, 1])
                col1.write(f"**{item['Article']}** | {item['PV']} DA")
                if col2.button(f"Ajouter ➕", key=f"btn_{item['Article']}"):
                    if not any(p['Article'] == item['Article'] for p in st.session_state['panier']):
                        st.session_state['panier'].append({
                            'Article': item['Article'], 'PV': float(item['PV']),
                            'Qte': 1, 'PA': float(item['PA']),
                            'Frais': float(item['Frais']), 'Max': int(item['Quantite'])
                        })
                        st.rerun()

    st.divider()

    # Affichage du Panier et Calcul du Total
    if st.session_state['panier']:
        total_general = 0
        st.write("### 🛍️ Liste des articles")
        
        for idx, p in enumerate(st.session_state['panier']):
            with st.expander(f"📦 {p['Article']}", expanded=True):
                c1, c2, c3 = st.columns([2, 2, 1])
                p['PV'] = c1.number_input("Prix (DA)", value=p['PV'], key=f"pv_{idx}", step=50.0)
                p['Qte'] = c2.number_input("Quantité", min_value=1, max_value=p['Max'], value=p['Qte'], key=f"q_{idx}")
                if c3.button("🗑️", key=f"del_{idx}"):
                    st.session_state['panier'].pop(idx)
                    st.rerun()
                
                st.write(f"Total article : **{p['PV'] * p['Qte']:,.0f} DA**")
                total_general += p['PV'] * p['Qte']

        # --- AFFICHAGE DU TOTAL GÉNÉRAL EN GROS VERT ---
        st.markdown(f"""
            <div style="background-color:#d4edda; padding:20px; border-radius:10px; border: 2px solid #28a745; text-align:center; margin: 20px 0;">
                <h2 style="color:#155724; margin:0;">TOTAL À ENCAISSER</h2>
                <h1 style="color:#28a745; margin:0; font-size: 50px; font-weight: bold;">{total_general:,.0f} DA</h1>
            </div>
        """, unsafe_content_html=True)

        # BOUTON D'ENCAISSEMENT FINAL
        if st.button("💰 VALIDER ET ENCAISSER TOUT", use_container_width=True, type="primary"):
            for p in st.session_state['panier']:
                # Enregistrement de chaque article
                benef = p['Qte'] * (p['PV'] - (p['PA'] + p['Frais']))
                new_v = pd.DataFrame([[datetime.now().date(), p['Article'], p['Qte'], p['PV']*p['Qte'], benef]], columns=df_ventes.columns)
                df_ventes = pd.concat([df_ventes, new_v], ignore_index=True)
                # Mise à jour du stock
                df_stock.loc[df_stock["Article"] == p['Article'], "Quantite"] -= p['Qte']
            
            save_data(df_ventes, "ventes.csv")
            save_data(df_stock, "stock.csv")
            st.session_state['panier'] = [] # Nettoyage de la caisse
            st.success("Vente enregistrée avec succès !")
            st.rerun()
    else:
        st.info("La caisse est vide. Ajoutez des articles pour voir le total.")
