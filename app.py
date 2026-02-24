import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ================= CONFIGURATION =================
st.set_page_config(page_title="Happy Store Kids", layout="wide")

if 'panier' not in st.session_state:
    st.session_state['panier'] = []
if 'acces_autorise' not in st.session_state:
    st.session_state['acces_autorise'] = False
if 'admin_connecte' not in st.session_state:
    st.session_state['admin_connecte'] = False

# ================= FONCTIONS =================
def load_data(file, columns):
    if os.path.exists(file):
        try:
            df = pd.read_csv(file)
            if not df.empty and 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce').dt.date
            return df
        except:
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

def save_data(df, file):
    df.to_csv(file, index=False)

df_stock = load_data("stock.csv", ["Article", "PA", "Frais", "PV", "Quantite"])
df_ventes = load_data("ventes.csv", ["Date", "Article", "Qte", "Vente_Total", "Benefice"])

# ================= CONNEXION =================
if not st.session_state['acces_autorise'] and not st.session_state['admin_connecte']:
    st.title("🔐 Happy Store Kids")

    u = st.text_input("Utilisateur")
    p = st.text_input("Mot de passe", type="password")

    if st.button("Se connecter"):
        if u.lower() == "admin" and p == "admin0699302032":
            st.session_state['admin_connecte'] = True
            st.session_state['acces_autorise'] = True
            st.rerun()
        elif u.lower() == "user" and p == "0699302032":
            st.session_state['acces_autorise'] = True
            st.rerun()
        else:
            st.error("Identifiants incorrects")

    st.stop()

# ================= BOUTON DECONNEXION =================
col1, col2 = st.columns([6,1])
with col2:
    if st.button("🚪 Se déconnecter"):
        st.session_state['acces_autorise'] = False
        st.session_state['admin_connecte'] = False
        st.session_state['panier'] = []
        st.rerun()

# ================= ONGLETS =================
is_admin = st.session_state['admin_connecte']

if is_admin:
    t_caisse, t_stock = st.tabs(["🛒 Caisse Directe", "📦 Gestion Stock"])
else:
    t_caisse = st.tabs(["🛒 Caisse Directe"])[0]

# ================= CAISSE =================
with t_caisse:

    st.subheader("🛒 Terminal de Vente")

    # ===== RECHERCHE INTELLIGENTE SIMPLE =====
    st.write("### 🔍 Ajouter un article")

    recherche = st.text_input(
        "Tapez le nom de l'article :",
        key="recherche"
    )

    # Suggestions automatiques dès première lettre
    suggestions = df_stock[
        df_stock["Article"].str.contains(recherche, case=False, na=False) &
        (df_stock["Quantite"] > 0)
    ] if recherche else pd.DataFrame()

    if not suggestions.empty:

        for _, item in suggestions.iterrows():

            if st.button(
                f"{item['Article']} - {item['PV']} DA",
                key=f"add_{item['Article']}"
            ):

                # Vérifier si déjà dans panier
                existing = next(
                    (p for p in st.session_state['panier'] if p['Article'] == item['Article']),
                    None
                )

                if existing:
                    if existing['Qte'] < existing['Max']:
                        existing['Qte'] += 1
                else:
                    st.session_state['panier'].append({
                        'Article': item['Article'],
                        'PV': float(item['PV']),
                        'Qte': 1,
                        'PA': float(item['PA']),
                        'Frais': float(item['Frais']),
                        'Max': int(item['Quantite'])
                    })

                # Vider barre recherche proprement
                st.session_state['recherche'] = ""
                st.rerun()

    st.divider()

    # ===== PANIER =====
    if st.session_state['panier']:

        total_general = 0
        st.write("### 🛍️ Articles en attente")

        for idx, item in enumerate(st.session_state['panier']):

            with st.container():
                c1, c2, c3, c4 = st.columns([2,1,1,0.5])

                c1.write(f"**{item['Article']}**")

                prix = c2.number_input(
                    "Prix",
                    value=float(item['PV']),
                    step=50.0,
                    key=f"pv_{idx}"
                )

                qte = c3.number_input(
                    "Qté",
                    min_value=1,
                    max_value=int(item['Max']),
                    value=int(item['Qte']),
                    key=f"q_{idx}"
                )

                if c4.button("❌", key=f"del_{idx}"):
                    st.session_state['panier'].pop(idx)
                    st.rerun()

                # Mise à jour panier proprement
                st.session_state['panier'][idx]['PV'] = float(prix)
                st.session_state['panier'][idx]['Qte'] = int(qte)

                total_general += float(prix) * int(qte)

                st.write("---")

        # ===== TOTAL VERT =====
        st.markdown(f"""
            <div style="background-color:#d4edda; padding:20px; border-radius:10px; border:2px solid #28a745; text-align:center;">
                <h2 style="color:#155724; margin:0;">TOTAL À PAYER</h2>
                <h1 style="color:#28a745; margin:0; font-size:50px;">{total_general:,.0f} DA</h1>
            </div>
        """, unsafe_allow_html=True)

        if st.button("💰 ENCAISSER", use_container_width=True, type="primary"):

            for p in st.session_state['panier']:

                benef = p['Qte'] * (p['PV'] - (p['PA'] + p['Frais']))

                new_v = pd.DataFrame(
                    [[datetime.now().date(), p['Article'], p['Qte'], p['PV'] * p['Qte'], benef]],
                    columns=["Date", "Article", "Qte", "Vente_Total", "Benefice"]
                )

                df_ventes = pd.concat([df_ventes, new_v], ignore_index=True)
                df_stock.loc[df_stock["Article"] == p['Article'], "Quantite"] -= p['Qte']

            save_data(df_ventes, "ventes.csv")
            save_data(df_stock, "stock.csv")

            st.session_state['panier'] = []
            st.success("Vente enregistrée !")
            st.rerun()

    else:
        st.info("Aucun article sélectionné.")

# ================= STOCK ADMIN =================
if is_admin:
    with t_stock:
        st.write("### 📦 Liste du Stock")
        st.dataframe(df_stock, use_container_width=True)