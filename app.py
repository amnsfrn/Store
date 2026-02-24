import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Happy Store Kids", layout="wide", page_icon="🛍️")

# Initialisation des variables de session
if 'acces_autorise' not in st.session_state: st.session_state['acces_autorise'] = False
if 'admin_connecte' not in st.session_state: st.session_state['admin_connecte'] = False
if 'panier' not in st.session_state: st.session_state['panier'] = []

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
    st.title("⚙️ Menu")
    if st.button("🔴 DÉCONNEXION", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    if st.session_state['panier']:
        if st.button("🗑️ VIDER LE PANIER", color="red"):
            st.session_state['panier'] = []
            st.rerun()

is_admin = st.session_state['admin_connecte']

# --- NAVIGATION ---
if is_admin:
    tabs = st.tabs(["🛒 Caisse Multi-Articles", "📦 Gestion Stock", "✅ Validations", "📊 Rapports"])
else:
    tabs = st.tabs(["🛒 Caisse Multi-Articles", "📩 Envoyer Arrivage"])

# --- 1. CAISSE MULTI-ARTICLES ---
with tabs[0]:
    st.subheader("🛒 Terminal de Vente")
    
    # ÉTAPE 1 : RECHERCHE ET SÉLECTION
    recherche = st.text_input("⌨️ Tapez le nom pour ajouter au panier :", placeholder="Rechercher...")
    
    if recherche:
        mask = df_stock["Article"].str.contains(recherche, case=False, na=False)
        suggestions = df_stock[mask & (df_stock["Quantite"] > 0)]
        
        if not suggestions.empty:
            for _, item in suggestions.iterrows():
                col_name, col_btn = st.columns([3, 1])
                col_name.write(f"**{item['Article']}** ({int(item['Quantite'])} dispo) - {item['PV']} DA")
                if col_btn.button(f"➕ Ajouter", key=f"add_{item['Article']}"):
                    # Ajouter au panier (session_state)
                    deja_present = False
                    for p in st.session_state['panier']:
                        if p['Article'] == item['Article']:
                            deja_present = True
                    if not deja_present:
                        st.session_state['panier'].append({
                            'Article': item['Article'],
                            'PV': float(item['PV']),
                            'Qte': 1,
                            'Max': int(item['Quantite']),
                            'PA': float(item['PA']),
                            'Frais': float(item['Frais'])
                        })
                        st.rerun()
        else:
            st.warning("Aucun article trouvé ou rupture de stock.")

    st.divider()

    # ÉTAPE 2 : LE PANIER (VUE PAR BLOCS)
    if st.session_state['panier']:
        st.write("### 🛍️ Articles sélectionnés")
        total_general = 0
        
        for idx, p in enumerate(st.session_state['panier']):
            with st.container():
                c1, c2, c3, c4 = st.columns([2, 1, 1, 0.5])
                c1.markdown(f"**{p['Article']}**")
                p['PV'] = c2.number_input("Prix (DA)", value=p['PV'], key=f"pv_{idx}")
                p['Qte'] = c3.number_input("Qté", min_value=1, max_value=p['Max'], value=p['Qte'], key=f"qte_{idx}")
                if c4.button("❌", key=f"del_{idx}"):
                    st.session_state['panier'].pop(idx)
                    st.rerun()
                
                total_ligne = p['PV'] * p['Qte']
                total_general += total_ligne
                st.write(f"Sous-total : **{total_ligne:,.2f} DA**")
                st.divider()

        # ÉTAPE 3 : TOTAL GÉNÉRAL EN VERT ET GROS
        st.markdown(f"""
        <div style="background-color:#d4edda; padding:20px; border-radius:10px; border: 2px solid #28a745; text-align:center; margin-bottom:20px">
            <h2 style="color:#155724; margin:0;">TOTAL GÉNÉRAL</h2>
            <h1 style="color:#28a745; margin:0; font-size: 50px;">{total_general:,.2f} DA</h1>
        </div>
        """, unsafe_content_html=True)

        if st.button("✅ VALIDER ET ENREGISTRER LA VENTE", use_container_width=True, type="primary"):
            for p in st.session_state['panier']:
                # Calcul bénéfice pour chaque ligne
                benef = p['Qte'] * (p['PV'] - (p['PA'] + p['Frais']))
                new_v = pd.DataFrame([[datetime.now().date(), p['Article'], p['Qte'], p['PV']*p['Qte'], benef]], columns=df_ventes.columns)
                df_ventes = pd.concat([df_ventes, new_v], ignore_index=True)
                
                # Mise à jour du stock
                df_stock.loc[df_stock["Article"] == p['Article'], "Quantite"] -= p['Qte']
            
            save_data(df_ventes, "ventes.csv")
            save_data(df_stock, "stock.csv")
            st.session_state['panier'] = [] # Vider le panier
            st.success("Toute la vente a été enregistrée avec succès !")
            st.rerun()
    else:
        st.info("Votre panier est vide. Cherchez un article ci-dessus pour commencer.")

# --- RESTE DU CODE (GESTION STOCK / VALIDATION) ---
# (Gardez la même logique que précédemment pour les autres onglets)
