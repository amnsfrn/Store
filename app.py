import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Happy Store Kids", layout="wide", page_icon="🛍️")

# Initialisation des sessions
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
    if st.button("🔴 DÉCONNEXION", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    if st.session_state['panier']:
        if st.button("🗑️ VIDER LA CAISSE"):
            st.session_state['panier'] = []
            st.rerun()

is_admin = st.session_state['admin_connecte']
tabs = st.tabs(["🛒 Caisse", "📦 Stock", "✅ Validations"]) if is_admin else st.tabs(["🛒 Caisse", "📩 Arrivage"])

# --- 1. CAISSE MULTI-ARTICLES ---
with tabs[0]:
    st.subheader("🛒 Caisse Directe")
    
    # Recherche
    recherche = st.text_input("⌨️ Tapez pour chercher un article :", placeholder="Ex: Jeans...")
    
    if recherche:
        # Filtrage sécurisé
        suggestions = df_stock[df_stock["Article"].str.contains(recherche, case=False, na=False) & (df_stock["Quantite"] > 0)]
        
        if not suggestions.empty:
            st.write("---")
            for _, item in suggestions.iterrows():
                col1, col2 = st.columns([3, 1])
                col1.write(f"**{item['Article']}** | {item['PV']} DA")
                if col2.button(f"Ajouter ➕", key=f"btn_{item['Article']}"):
                    # Ajout au panier avec vérification des doublons
                    if not any(p['Article'] == item['Article'] for p in st.session_state['panier']):
                        st.session_state['panier'].append({
                            'Article': item['Article'],
                            'PV': float(item['PV']),
                            'Qte': 1,
                            'PA': float(item['PA']),
                            'Frais': float(item['Frais']),
                            'Max': int(item['Quantite'])
                        })
                        st.rerun()
        else:
            st.warning("Article non trouvé.")

    st.write("---")

    # Affichage du Panier
    if st.session_state['panier']:
        total_final = 0
        st.write("### Articles en cours :")
        
        # On utilise une liste pour stocker les modifs car st.form ne gère pas bien le dynamique
        for idx, p in enumerate(st.session_state['panier']):
            with st.container():
                c1, c2, c3, c4 = st.columns([2, 1, 1, 0.5])
                c1.write(f"**{p['Article']}**")
                # Mise à jour directe des valeurs dans le dictionnaire
                p['PV'] = c2.number_input("Prix", value=p['PV'], key=f"pv_{idx}", step=50.0)
                p['Qte'] = c3.number_input("Qté", min_value=1, max_value=p['Max'], value=p['Qte'], key=f"q_{idx}")
                if c4.button("❌", key=f"del_{idx}"):
                    st.session_state['panier'].pop(idx)
                    st.rerun()
                
                total_ligne = p['PV'] * p['Qte']
                total_final += total_ligne
                st.write(f"Sous-total : **{total_ligne:,.0f} DA**")
                st.write("---")

        # Affichage du TOTAL GÉNÉRAL
        st.markdown(f"""
        <div style="background-color:#d4edda; padding:15px; border-radius:10px; text-align:center; border: 2px solid #28a745;">
            <h2 style="color:#155724; margin:0;">TOTAL À ENCAISSER</h2>
            <h1 style="color:#28a745; margin:0; font-size:45px;">{total_final:,.0f} DA</h1>
        </div>
        """, unsafe_content_html=True)

        st.write("")
        # LE BOUTON D'ENCAISSEMENT FINAL
        if st.button("💰 ENCAISSER ET VIDER LA CAISSE", use_container_width=True, type="primary"):
            for p in st.session_state['panier']:
                # Calcul bénéfice
                benef = p['Qte'] * (p['PV'] - (p['PA'] + p['Frais']))
                # Enregistrement vente
                new_v = pd.DataFrame([[datetime.now().date(), p['Article'], p['Qte'], p['PV']*p['Qte'], benef]], columns=df_ventes.columns)
                df_ventes = pd.concat([df_ventes, new_v], ignore_index=True)
                # Mise à jour stock
                df_stock.loc[df_stock["Article"] == p['Article'], "Quantite"] -= p['Qte']
            
            save_data(df_ventes, "ventes.csv")
            save_data(df_stock, "stock.csv")
            st.session_state['panier'] = [] # On vide tout
            st.success("Vente enregistrée ! Caisse prête pour le client suivant.")
            st.rerun()
    else:
        st.info("La caisse est vide. Cherchez un article ci-dessus.")

# --- RESTE DU CODE (ADMIN STOCK ET VALIDATION) ---
# Gardez votre code de validation et de gestion de stock tel quel en dessous
