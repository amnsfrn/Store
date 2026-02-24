import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- 1. CONFIGURATION & INITIALISATION ---
# On prépare les variables AVANT de lancer l'affichage pour éviter les erreurs "NameError"
st.set_page_config(page_title="Happy Store Kids", layout="wide")

if 'panier' not in st.session_state: st.session_state['panier'] = []
if 'acces_autorise' not in st.session_state: st.session_state['acces_autorise'] = False
if 'admin_connecte' not in st.session_state: st.session_state['admin_connecte'] = False

# --- 2. FONCTIONS DE DONNÉES ---
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

# --- 3. CONNEXION ---
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

# --- 4. CRÉATION DES ONGLETS (Résout l'erreur NameError) ---
is_admin = st.session_state['admin_connecte']
if is_admin:
    t_caisse, t_stock = st.tabs(["🛒 Caisse Directe", "📦 Gestion Stock"])
else:
    t_caisse = st.tabs(["🛒 Caisse Directe"])[0]

# --- 5. L'ONGLET CAISSE (MULTI-ARTICLES) ---
with t_caisse:
    st.subheader("🛒 Terminal de Vente")
    
    # Barre de recherche avec propositions
    recherche = st.text_input("🔍 Tapez le nom pour ajouter :", key="search_input")
    
    if recherche:
        # On filtre le stock en temps réel
        mask = df_stock["Article"].str.contains(recherche, case=False, na=False) & (df_stock["Quantite"] > 0)
        suggestions = df_stock[mask]
        
        if not suggestions.empty:
            for _, item in suggestions.iterrows():
                col_n, col_b = st.columns([3, 1])
                col_n.write(f"**{item['Article']}** | {item['PV']} DA")
                # Bouton de sélection immédiate
                if col_b.button(f"Choisir", key=f"btn_{item['Article']}"):
                    if not any(p['Article'] == item['Article'] for p in st.session_state['panier']):
                        st.session_state['panier'].append({
                            'Article': item['Article'], 'PV': float(item['PV']),
                            'Qte': 1, 'PA': float(item['PA']),
                            'Frais': float(item['Frais']), 'Max': int(item['Quantite'])
                        })
                        st.rerun()

    st.divider()

    # Affichage du Panier (Les cases d'articles)
    if st.session_state['panier']:
        total_general = 0
        st.write("### 🛍️ Articles en attente")
        
        for idx, p in enumerate(st.session_state['panier']):
            with st.container():
                c1, c2, c3, c4 = st.columns([2, 1, 1, 0.5])
                c1.write(f"**{p['Article']}**")
                # Mise à jour des prix/quantités sans formulaire pour éviter les bugs
                p['PV'] = c2.number_input("Prix", value=p['PV'], key=f"pv_{idx}", step=50.0)
                p['Qte'] = c3.number_input("Qté", min_value=1, max_value=p['Max'], value=p['Qte'], key=f"q_{idx}")
                if c4.button("❌", key=f"del_{idx}"):
                    st.session_state['panier'].pop(idx)
                    st.rerun()
                
                total_general += (p['PV'] * p['Qte'])
                st.write("---")

        # --- TOTAL GÉNÉRAL EN GROS VERT ---
        st.markdown(f"""
            <div style="background-color:#d4edda; padding:20px; border-radius:10px; border: 2px solid #28a745; text-align:center;">
                <h2 style="color:#155724; margin:0;">TOTAL À PAYER</h2>
                <h1 style="color:#28a745; margin:0; font-size: 50px;">{total_general:,.0f} DA</h1>
            </div>
        """, unsafe_content_html=True)

        st.write("")
        # --- BOUTON ENCAISSER (NETTOYAGE) ---
        if st.button("💰 ENCAISSER ET VIDER LA PAGE", use_container_width=True, type="primary"):
            for p in st.session_state['panier']:
                # Enregistrement
                benef = p['Qte'] * (p['PV'] - (p['PA'] + p['Frais']))
                new_v = pd.DataFrame([[datetime.now().date(), p['Article'], p['Qte'], p['PV']*p['Qte'], benef]], 
                                     columns=["Date", "Article", "Qte", "Vente_Total", "Benefice"])
                df_ventes = pd.concat([df_ventes, new_v], ignore_index=True)
                # Déduction stock
                df_stock.loc[df_stock["Article"] == p['Article'], "Quantite"] -= p['Qte']
            
            save_data(df_ventes, "ventes.csv")
            save_data(df_stock, "stock.csv")
            st.session_state['panier'] = [] # Nettoie les cases
            st.success("Vente enregistrée !")
            st.rerun()
    else:
        st.info("Aucun article sélectionné.")

# --- 6. GESTION STOCK (ADMIN UNIQUEMENT) ---
if is_admin:
    with t_stock:
        st.write("### Liste du Stock")
        st.dataframe(df_stock, use_container_width=True)
