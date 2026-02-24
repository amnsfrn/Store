import streamlit as st
import pandas as pd
import os

# Configuration de l'application
st.set_page_config(page_title="Gestion Magasin DZ", page_icon="🇩🇿")

# --- MOT DE PASSE PATRON ---
CODE_PATRON = "9696" 

# --- FONCTIONS DE SAUVEGARDE ---
def load_data(file):
    if os.path.exists(file):
        return pd.read_csv(file)
    if "stock" in file:
        return pd.DataFrame(columns=["Article", "PA", "Frais", "PV", "Quantite"])
    return pd.DataFrame(columns=["Date", "Article", "Qte", "Vente_Total", "Benefice"])

def save_data(df, file):
    df.to_csv(file, index=False)

# Chargement des données
df_stock = load_data("stock.csv")
df_ventes = load_data("ventes.csv")

# --- BARRE LATÉRALE (ZONE SÉCURISÉE) ---
st.sidebar.title("🔐 Accès Administration")
password = st.sidebar.text_input("Code Patron", type="password")
is_admin = (password == CODE_PATRON)

if is_admin:
    st.sidebar.success("Mode Patron Activé")
else:
    st.sidebar.info("Mode Employé : Prix d'achat masqués")

# --- AFFICHAGE DU CAPITAL (UNIQUEMENT POUR LE PATRON) ---
if is_admin:
    st.title("📊 Tableau de Bord Patron")
    valeur_stock = ((df_stock['PA'] + df_stock['Frais']) * df_stock['Quantite']).sum()
    profit_total = df_ventes['Benefice'].sum()
    capital = valeur_stock + profit_total

    c1, c2 = st.columns(2)
    c1.metric("Capital Global (Stock + Profit)", f"{capital:,.2f} DA")
    c2.metric("Bénéfice Total Réalisé", f"{profit_total:,.2f} DA")
    st.write("---")

# --- INTERFACE PRINCIPALE ---
if is_admin:
    tabs = st.tabs(["💰 Enregistrer Vente", "📦 Gérer Stock & Prix", "📈 Analyses & Historique"])
else:
    tabs = st.tabs(["💰 Caisse (Ventes)"])
    st.title("🏪 Caisse Magasin")

# --- ONGLET VENTES (ACCESSIBLE À TOUS) ---
with tabs[0]:
    st.subheader("Nouvelle Vente")
    if not df_stock.empty:
        article = st.selectbox("Sélectionner l'article", df_stock["Article"])
        
        # On affiche seulement le prix de vente à l'employé
        prix_v_actuel = df_stock[df_stock["Article"] == article]["PV"].values[0]
        st.info(f"Prix de vente : {prix_v_actuel:,.2f} DA")
        
        qte = st.number_input("Quantité vendue", min_value=1, step=1)
        
        if st.button("Valider la Vente"):
            item = df_stock[df_stock["Article"] == article].iloc[0]
            
            if item["Quantite"] >= qte:
                total_v = qte * item["PV"]
                # Le calcul du bénéfice se fait en arrière-plan (invisible pour l'employé)
                total_b = qte * (item["PV"] - (item["PA"] + item["Frais"]))
                
                # Mise à jour des ventes
                nouveau = pd.DataFrame([[pd.Timestamp.now().strftime("%d/%m/%Y"), article, qte, total_v, total_b]], columns=df_ventes.columns)
                df_ventes = pd.concat([df_ventes, nouveau], ignore_index=True)
                
                # Mise à jour du stock
                df_stock.loc[df_stock["Article"] == article, "Quantite"] -= qte
                
                save_data(df_ventes, "ventes.csv")
                save_data(df_stock, "stock.csv")
                st.success(f"Vente enregistrée : {total_v:,.2f} DA")
                st.balloons()
                st.rerun()
            else:
                st.error("Stock insuffisant pour cette vente !")
    else:
        st.warning("Le stock est vide. Veuillez demander au patron d'ajouter des articles.")

# --- ONGLETS RÉSERVÉS AU PATRON ---
if is_admin:
    with tabs[1]:
        st.subheader("Configuration du Stock et des Coûts")
        with st.expander("➕ Ajouter un nouveau produit"):
            n = st.text_input("Nom de l'article")
            col_a, col_b = st.columns(2)
            pa = col_a.number_input("Prix d'Achat (DA)", min_value=0.0)
            fr = col_a.number_input("Frais (Transport, Douane...) (DA)", min_value=0.0)
            pv = col_b.number_input("Prix de Vente au Client (DA)", min_value=0.0)
            qt = col_b.number_input("Quantité en stock", min_value=0)
            
            if st.button("Ajouter à l'inventaire"):
                if n:
                    nouvel_art = pd.DataFrame([[n, pa, fr, pv, qt]], columns=df_stock.columns)
                    df_stock = pd.concat([df_stock, nouvel_art], ignore_index=True)
                    save_data(df_stock, "stock.csv")
                    st.success(f"{n} ajouté au stock.")
                    st.rerun()
                else:
                    st.error("Veuillez donner un nom à l'article.")
        
        st.write("### Inventaire Complet")
        st.dataframe(df_stock, use_container_width=True)

    with tabs[2]:
        st.subheader("Analyses du Magasin")
        if not df_ventes.empty:
            col_an1, col_an2 = st.columns(2)
            
            with col_an1:
                st.write("**Top des ventes (Quantité)**")
                top = df_ventes.groupby("Article")["Qte"].sum().sort_values(ascending=False)
                st.bar_chart(top)
            
            with col_an2:
                st.write("**Bénéfice par article**")
                benef_art = df_ventes.groupby("Article")["Benefice"].sum().sort_values(ascending=False)
                st.bar_chart(benef_art)

            st.write("### Historique détaillé des transactions")
            st.dataframe(df_ventes, use_container_width=True)
        else:
            st.info("Aucune donnée de vente disponible pour l'analyse.")
