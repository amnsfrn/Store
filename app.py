import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Happy Store Kids", layout="wide")

# Initialisation ultra-sécurisée
if 'panier' not in st.session_state:
    st.session_state['panier'] = []
if 'acces_autorise' not in st.session_state:
    st.session_state['acces_autorise'] = False
if 'admin_connecte' not in st.session_state:
    st.session_state['admin_connecte'] = False

# --- 2. GESTION DES DONNÉES ---
def load_data(file, columns):
    if os.path.exists(file):
        try:
            df = pd.read_csv(file)
            # Force les colonnes numériques pour éviter les TypeError
            for col in ["PA", "Frais", "PV", "Quantite", "Vente_Total", "Benefice"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            return df
        except:
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

def save_data(df, file):
    df.to_csv(file, index=False)

df_stock = load_data("stock.csv", ["Article", "PA", "Frais", "PV", "Quantite"])
df_ventes = load_data("ventes.csv", ["Date", "Article", "Qte", "Vente_Total", "Benefice"])

# --- 3. BARRE LATÉRALE ---
with st.sidebar:
    st.title("⚙️ Menu")
    if st.session_state['acces_autorise'] or st.session_state['admin_connecte']:
        if st.button("🔴 DÉCONNECTER", use_container_width=True):
            st.session_state.clear()
            st.rerun()

# --- 4. CONNEXION ---
if not st.session_state['acces_autorise'] and not st.session_state['admin_connecte']:
    st.title("🔐 Accès Happy Store")
    u = st.text_input("Utilisateur")
    p = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter"):
        if u.lower() == "admin" and p == "admin0699302032":
            st.session_state['admin_connecte'], st.session_state['acces_autorise'] = True, True
            st.rerun()
        elif u.lower() == "user" and p == "0699302032":
            st.session_state['acces_autorise'] = True
            st.rerun()
        else:
            st.error("Identifiants incorrects")
    st.stop()

# --- 5. NAVIGATION ---
is_admin = st.session_state['admin_connecte']
tabs = st.tabs(["🛒 Caisse", "📦 Stock"]) if is_admin else st.tabs(["🛒 Caisse"])

# --- 6. ONGLET CAISSE ---
with tabs[0]:
    st.subheader("🛒 Terminal de Vente")
    
    if 'search_key' not in st.session_state:
        st.session_state.search_key = 0
    
    recherche = st.text_input("⌨️ Chercher un article :", key=f"search_{st.session_state.search_key}")
    
    if recherche:
        mask = df_stock["Article"].astype(str).str.contains(recherche, case=False, na=False) & (df_stock["Quantite"] > 0)
        suggestions = df_stock[mask]
        
        if not suggestions.empty:
            for _, item in suggestions.iterrows():
                c1, c2 = st.columns([4, 1])
                c1.write(f"**{item['Article']}** | {item['PV']} DA")
                if c2.button("➕ Ajouter", key=f"add_{item['Article']}"):
                    index_ex = next((i for i, p in enumerate(st.session_state['panier']) if p['Article'] == item['Article']), None)
                    if index_ex is not None:
                        if st.session_state['panier'][index_ex]['Qte'] < item['Quantite']:
                            st.session_state['panier'][index_ex]['Qte'] += 1
                    else:
                        st.session_state['panier'].append({
                            'Article': str(item['Article']), 
                            'PV': float(item['PV']),
                            'Qte': 1, 
                            'PA': float(item['PA']),
                            'Frais': float(item['Frais']), 
                            'Max': int(item['Quantite'])
                        })
                    st.session_state.search_key += 1
                    st.rerun()

    st.divider()

    if st.session_state['panier']:
        total_general = 0.0
        st.write("### 🛍️ Panier")
        
        for idx, p in enumerate(st.session_state['panier']):
            col1, col2, col3, col4 = st.columns([2, 1, 1, 0.5])
            col1.write(f"**{p['Article']}**")
            p['PV'] = col2.number_input("Prix", value=float(p['PV']), key=f"pv_{idx}")
            p['Qte'] = col3.number_input("Qté", min_value=1, max_value=int(p['Max']), value=int(p['Qte']), key=f"q_{idx}")
            if col4.button("❌", key=f"del_{idx}"):
                st.session_state['panier'].pop(idx)
                st.rerun()
            total_general += float(p['PV'] * p['Qte'])

        # --- TOTAL AFFICHÉ TRÈS GROS ---
        st.write("")
        st.write(f"## TOTAL : **{total_general:,.0f} DA**")
        st.write("")

        if st.button("💰 VALIDER ET ENCAISSER", use_container_width=True, type="primary"):
            for p in st.session_state['panier']:
                # Calcul profit
                benef = float(p['Qte']) * (float(p['PV']) - (float(p['PA']) + float(p['Frais'])))
                new_v = pd.DataFrame([[datetime.now().date(), p['Article'], p['Qte'], p['PV']*p['Qte'], benef]], 
                                     columns=["Date", "Article", "Qte", "Vente_Total", "Benefice"])
                df_ventes = pd.concat([df_ventes, new_v], ignore_index=True)
                # Mise à jour stock
                df_stock.loc[df_stock["Article"] == p['Article'], "Quantite"] -= p['Qte']
            
            save_data(df_ventes, "ventes.csv")
            save_data(df_stock, "stock.csv")
            st.session_state['panier'] = []
            st.success("Vente enregistrée !")
            st.rerun()
    else:
        st.info("Caisse vide.")

# --- 7. STOCK (ADMIN) ---
if is_admin:
    with tabs[1]:
        st.subheader("📦 Inventaire")
        st.dataframe(df_stock, use_container_width=True)
