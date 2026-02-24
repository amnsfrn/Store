import streamlit as st
import pandas as pd
import os

# Configuration de l'app
st.set_page_config(page_title="Mon Magasin", page_icon="🏢")

# --- FONCTION DE SAUVEGARDE (Auto-suffisante) ---
# On utilise un fichier CSV local qui reste sur le serveur gratuitement
def load_data(file):
    if os.path.exists(file):
        return pd.read_csv(file)
    else:
        if file == "stock.csv":
            return pd.DataFrame(columns=["Article", "PA", "Frais", "PV", "Quantite"])
        return pd.DataFrame(columns=["Date", "Article", "Qte", "Vente_Total", "Benefice"])

def save_data(df, file):
    df.to_csv(file, index=False)

# Chargement automatique
df_stock = load_data("stock.csv")
df_ventes = load_data("ventes.csv")

# --- INTERFACE UNIQUE ---
st.title("📱 Gestion Magasin")

# Calcul du Capital en haut (toujours visible)
valeur_stock = ((df_stock['PA'] + df_stock['Frais']) * df_stock['Quantite']).sum()
profit_total = df_ventes['Benefice'].sum()
capital = valeur_stock + profit_total

col1, col2 = st.columns(2)
col1.metric("Capital Global", f"{capital} €")
col2.metric("Bénéfice Réalisé", f"{profit_total} €", delta=f"{profit_total} €")

st.write("---")

# Menu par onglets (Pas besoin de changer d'application)
tab_vente, tab_stock, tab_bilan = st.tabs(["💰 Ventes", "📦 Stock", "📊 Analyse"])

with tab_vente:
    st.subheader("Nouvelle Vente")
    article = st.selectbox("Choisir l'article", df_stock["Article"])
    qte = st.number_input("Quantité vendue", min_value=1)
    
    if st.button("Valider la vente"):
        # Calcul
        item = df_stock[df_stock["Article"] == article].iloc[0]
        b_unit = item["PV"] - (item["PA"] + item["Frais"])
        total_v = qte * item["PV"]
        total_b = qte * b_unit
        
        # Enregistrement
        nouvelle_ligne = pd.DataFrame([[pd.Timestamp.now().strftime("%d/%m/%Y"), article, qte, total_v, total_b]], 
                                     columns=df_ventes.columns)
        df_ventes = pd.concat([df_ventes, nouvelle_ligne], ignore_index=True)
        
        # Soustraction du stock
        df_stock.loc[df_stock["Article"] == article, "Quantite"] -= qte
        
        save_data(df_ventes, "ventes.csv")
        save_data(df_stock, "stock.csv")
        st.success("Vente enregistrée et stock mis à jour !")
        st.rerun()

with tab_stock:
    st.subheader("Inventaire")
    # Formulaire d'ajout
    with st.expander("➕ Ajouter un nouveau produit"):
        n = st.text_input("Nom")
        pa = st.number_input("Prix d'Achat")
        fr = st.number_input("Frais (transport...)")
        pv = st.number_input("Prix de Vente")
        qt = st.number_input("Quantité initiale", min_value=1)
        if st.button("Ajouter au stock"):
            nouveau_p = pd.DataFrame([[n, pa, fr, pv, qt]], columns=df_stock.columns)
            df_stock = pd.concat([df_stock, nouveau_p], ignore_index=True)
            save_data(df_stock, "stock.csv")
            st.rerun()
    
    st.dataframe(df_stock, use_container_width=True)

with tab_bilan:
    st.subheader("Quel article se vend le plus ?")
    if not df_ventes.empty:
        top = df_ventes.groupby("Article")["Qte"].sum().sort_values(ascending=False)
        st.bar_chart(top)
        st.write("Historique des ventes :")
        st.table(df_ventes.tail(10))
