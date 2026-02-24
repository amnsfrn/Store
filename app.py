import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Happy Store Kids", layout="wide", page_icon="🛍️")

# Initialisation obligatoire pour éviter les plantages (TypeError/NameError)
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

# Chargement initial
df_stock = load_data("stock.csv", ["Article", "PA", "Frais", "PV", "Quantite"])
df_ventes = load_data("ventes.csv", ["Date", "Article", "Qte", "Vente_Total", "Benefice"])

# --- SYSTÈME DE CONNEXION ---
if not st.session_state['acces_autorise'] and not st.session_state['admin_connecte']:
    st.title("🔐 Accès Happy Store")
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

# --- NAVIGATION ---
is_admin = st.session_state['admin_connecte']
tabs = st.tabs(["🛒 Caisse Directe", "📦 Gestion Stock"]) if is_admin else st.tabs(["🛒 Caisse Directe", "📩 Arrivage"])

# --- 1. CAISSE (MULTI-ARTICLES & SUGGESTIONS) ---
with tabs[0]:
    st.header("🛒 Terminal de Vente")
    
    # Barre de recherche avec propositions
    recherche = st.text_input("🔍 Tapez le nom de l'article :", placeholder="Recherche instantanée...")
    
    if recherche:
        # Filtrage en temps réel
        mask = df_stock["Article"].str.contains(recherche, case=False, na=False) & (df_stock["Quantite"] > 0)
        suggestions = df_stock[mask]
        
        if not suggestions.empty:
            for _, item in suggestions.iterrows():
                c1, c2 = st.columns([4, 1])
                c1.write(f"📦 **{item['Article']}** | {item['PV']} DA (Stock: {int(item['Quantite'])})")
                if c2.button("➕ Ajouter", key=f"add_{item['Article']}"):
                    if not any(p['Article'] == item['Article'] for p in st.session_state['panier']):
                        st.session_state['panier'].append({
                            'Article': item['Article'], 'PV': float(item['PV']),
                            'Qte': 1, 'PA': float(item['PA']),
                            'Frais': float(item['Frais']), 'Max': int(item['Quantite'])
                        })
                        st.rerun()
    
    st.divider()

    # Affichage du Panier
    if st.session_state['panier']:
        total_general = 0
        st.subheader("🛍️ Articles sélectionnés")
        
        for idx, p in enumerate(st.session_state['panier']):
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 0.5])
                col1.write(f"**{p['Article']}**")
                p['PV'] = col2.number_input("Prix", value=p['PV'], key=f"p_{idx}", step=50.0)
                p['Qte'] = col3.number_input("Qté", min_value=1, max_value=p['Max'], value=p['Qte'], key=f"q_{idx}")
                if col4.button("❌", key=f"d_{idx}"):
                    st.session_state['panier'].pop(idx)
                    st.rerun()
                
                total_ligne = p['PV'] * p['Qte']
                total_general += total_ligne
                st.write(f"Sous-total : **{total_ligne:,.0f} DA**")
                st.write("---")

        # --- TOTAL GÉNÉRAL EN GROS VERT ---
        st.markdown(f"""
            <div style="background-color:#d4edda; padding:20px; border-radius:12px; border: 3px solid #28a745; text-align:center;">
                <h2 style="color:#155724; margin:0;">TOTAL GÉNÉRAL</h2>
                <h1 style="color:#28a745; margin:0; font-size: 55px; font-weight: bold;">{total_general:,.0f} DA</h1>
            </div>
        """, unsafe_content_html=True)

        st.write("")
        # --- BOUTON ENCAISSER (NETTOYAGE CAISSE) ---
        if st.button("💰 ENCAISSER ET VALIDER LA VENTE", use_container_width=True, type="primary"):
            for p in st.session_state['panier']:
                # Enregistrement
                benef = p['Qte'] * (p['PV'] - (p['PA'] + p['Frais']))
                new_v = pd.DataFrame([[datetime.now().date(), p['Article'], p['Qte'], p['PV']*p['Qte'], benef]], 
                                     columns=["Date", "Article", "Qte", "Vente_Total", "Benefice"])
                df_ventes = pd.concat([df_ventes, new_v], ignore_index=True)
                # Déduction Stock
                df_stock.loc[df_stock["Article"] == p['Article'], "Quantite"] -= p['Qte']
            
            save_data(df_ventes, "ventes.csv")
            save_data(df_stock, "stock.csv")
            st.session_state['panier'] = [] # Nettoie la caisse
            st.success("Vente réussie ! Caisse vidée.")
            st.rerun()
    else:
        st.info("La caisse est vide. Cherchez un article ci-dessus.")

# --- 2. GESTION STOCK (ADMIN) ---
if is_admin:
    with tabs[1]:
        st.header("📦 Gestion du Stock")
        st.dataframe(df_stock, use_container_width=True)
