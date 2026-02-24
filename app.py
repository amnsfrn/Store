import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Happy Store Kids", layout="wide", page_icon="🛍️")

# Initialisation du panier et de la session
if 'panier' not in st.session_state: st.session_state['panier'] = []
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

# --- CONNEXION ---
if not st.session_state['acces_autorise'] and not st.session_state['admin_connecte']:
    st.title("🔐 Happy Store")
    u, p = st.text_input("Utilisateur"), st.text_input("Pass", type="password")
    if st.button("OK"):
        if u.lower() == "admin" and p == "Thanksgod@99":
            st.session_state['admin_connecte'], st.session_state['acces_autorise'] = True, True
            st.rerun()
        elif u.lower() == "user" and p == "0699302032":
            st.session_state['acces_autorise'] = True
            st.rerun()
        else: st.error("Erreur")
    st.stop()

# --- NAVIGATION ---
is_admin = st.session_state['admin_connecte']
tabs = st.tabs(["🛒 Caisse", "📦 Stock", "✅ Validations"]) if is_admin else st.tabs(["🛒 Caisse", "📩 Arrivage"])

# --- 1. CAISSE AVEC SUGGESTIONS ---
with tabs[0]:
    st.subheader("🛒 Terminal de Vente")
    
    # Barre de recherche (ouvre le clavier direct)
    recherche = st.text_input("⌨️ Tapez le nom de l'article :", placeholder="Ex: Robe...")
    
    if recherche:
        # Filtrage instantané pour les propositions
        suggestions = df_stock[df_stock["Article"].str.contains(recherche, case=False, na=False) & (df_stock["Quantite"] > 0)]
        
        if not suggestions.empty:
            st.write("🔍 **Propositions :**")
            for _, item in suggestions.iterrows():
                col_name, col_btn = st.columns([3, 1])
                col_name.write(f"{item['Article']} | **{item['PV']} DA**")
                if col_btn.button(f"Choisir", key=f"add_{item['Article']}"):
                    # Ajouter au panier s'il n'y est pas déjà
                    if not any(p['Article'] == item['Article'] for p in st.session_state['panier']):
                        st.session_state['panier'].append({
                            'Article': item['Article'], 'PV': float(item['PV']),
                            'Qte': 1, 'Max': int(item['Quantite']),
                            'PA': float(item['PA']), 'Frais': float(item['Frais'])
                        })
                    st.rerun()

    st.divider()

    # Affichage du Panier (Articles sélectionnés)
    if st.session_state['panier']:
        st.write("### 🛍️ Articles en caisse")
        total_general = 0
        
        for idx, p in enumerate(st.session_state['panier']):
            with st.container():
                c1, c2, c3, c4 = st.columns([2, 1, 1, 0.5])
                c1.write(f"**{p['Article']}**")
                p['PV'] = c2.number_input("Prix", value=p['PV'], key=f"pv_{idx}")
                p['Qte'] = c3.number_input("Qté", min_value=1, max_value=p['Max'], value=p['Qte'], key=f"q_{idx}")
                if c4.button("❌", key=f"del_{idx}"):
                    st.session_state['panier'].pop(idx)
                    st.rerun()
                
                total_ligne = p['PV'] * p['Qte']
                total_general += total_ligne
                st.write(f"Prix : {p['PV']} DA x {p['Qte']} = **{total_ligne:,.0f} DA**")
                st.write("---")

        # AFFICHAGE DU TOTAL GÉNÉRAL EN GROS VERT
        st.markdown(f"""
        <div style="background-color:#d4edda; padding:20px; border-radius:10px; border: 2px solid #28a745; text-align:center; margin-bottom:20px">
            <h2 style="color:#155724; margin:0; font-family:sans-serif;">TOTAL GÉNÉRAL</h2>
            <h1 style="color:#28a745; margin:0; font-size: 55px; font-weight:bold;">{total_general:,.0f} DA</h1>
        </div>
        """, unsafe_content_html=True)

        # BOUTON ENCAISSER (NETTOIE TOUT)
        if st.button("💰 ENCAISSER ET VIDER LA CAISSE", use_container_width=True, type="primary"):
            for p in st.session_state['panier']:
                benef = p['Qte'] * (p['PV'] - (p['PA'] + p['Frais']))
                new_v = pd.DataFrame([[datetime.now().date(), p['Article'], p['Qte'], p['PV']*p['Qte'], benef]], columns=df_ventes.columns)
                df_ventes = pd.concat([df_ventes, new_v], ignore_index=True)
                df_stock.loc[df_stock["Article"] == p['Article'], "Quantite"] -= p['Qte']
            
            save_data(df_ventes, "ventes.csv")
            save_data(df_stock, "stock.csv")
            st.session_state['panier'] = [] # On nettoie les cases
            st.success("Vente enregistrée !")
            st.rerun()
    else:
        st.info("Caisse vide. Tapez un nom pour proposer des articles.")
