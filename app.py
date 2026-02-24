import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Happy Store Kids", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #FF4B4B;
        text-align: center;
        margin-bottom: 2rem;
    }
    .total-display {
        font-size: 3rem;
        font-weight: bold;
        color: #00A36C;
        text-align: center;
        padding: 2rem;
        background: #f0f2f6;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .cart-item {
        background: white;
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
    }
    .success-button {
        background-color: #00A36C;
        color: white;
        font-weight: bold;
    }
    .stButton button {
        border-radius: 5px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialisation sécurisée
if 'panier' not in st.session_state:
    st.session_state['panier'] = []
if 'acces_autorise' not in st.session_state:
    st.session_state['acces_autorise'] = False
if 'admin_connecte' not in st.session_state:
    st.session_state['admin_connecte'] = False
if 'historique_ventes' not in st.session_state:
    st.session_state['historique_ventes'] = []
if 'vente_en_cours' not in st.session_state:
    st.session_state['vente_en_cours'] = False

# --- 2. GESTION DES DONNÉES ---
def load_data(file, columns):
    if os.path.exists(file):
        try:
            df = pd.read_csv(file)
            # Force les colonnes numériques pour éviter les TypeError
            numeric_cols = ["PA", "Frais", "PV", "Quantite", "Vente_Total", "Benefice"]
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            return df
        except Exception as e:
            st.error(f"Erreur de chargement de {file}: {e}")
            return pd.DataFrame(columns=columns)
    return pd.DataFrame(columns=columns)

def save_data(df, file):
    try:
        df.to_csv(file, index=False)
        return True
    except Exception as e:
        st.error(f"Erreur de sauvegarde: {e}")
        return False

def backup_data():
    """Crée une sauvegarde des données"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for file in ["stock.csv", "ventes.csv"]:
        if os.path.exists(file):
            df = pd.read_csv(file)
            df.to_csv(f"backup_{timestamp}_{file}", index=False)

# Chargement des données
df_stock = load_data("stock.csv", ["Article", "PA", "Frais", "PV", "Quantite"])
df_ventes = load_data("ventes.csv", ["Date", "Article", "Qte", "Vente_Total", "Benefice"])

# --- 3. BARRE LATÉRALE AMÉLIORÉE ---
with st.sidebar:
    st.image("https://via.placeholder.com/150x50/FF4B4B/FFFFFF?text=HAPPY+STORE", use_column_width=True)
    st.markdown("---")
    
    if st.session_state['acces_autorise'] or st.session_state['admin_connecte']:
        # Afficher l'utilisateur connecté
        user_type = "👑 Administrateur" if st.session_state['admin_connecte'] else "👤 Utilisateur"
        st.info(f"Connecté: {user_type}")
        
        # Statistiques rapides
        if st.session_state['panier']:
            nb_articles = sum(item['Qte'] for item in st.session_state['panier'])
            st.metric("Articles dans le panier", nb_articles)
        
        st.markdown("---")
        
        # Actions rapides
        st.subheader("⚡ Actions rapides")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Nouvelle vente", use_container_width=True):
                st.session_state['panier'] = []
                st.session_state['vente_en_cours'] = False
                st.rerun()
        with col2:
            if st.button("📊 Rapports", use_container_width=True):
                st.session_state['show_reports'] = True
        
        st.markdown("---")
        
        # Bouton de déconnexion
        if st.button("🔴 SE DÉCONNECTER", use_container_width=True, type="primary"):
            st.session_state.clear()
            st.rerun()

# --- 4. CONNEXION AMÉLIORÉE ---
if not st.session_state['acces_autorise'] and not st.session_state['admin_connecte']:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 class='main-header'>🔐 Happy Store Kids</h1>", unsafe_allow_html=True)
        st.markdown("---")
        
        with st.form("login_form"):
            u = st.text_input("👤 Nom d'utilisateur")
            p = st.text_input("🔑 Mot de passe", type="password")
            submitted = st.form_submit_button("Se connecter", use_container_width=True, type="primary")
            
            if submitted:
                if u.lower() == "admin" and p == "admin0699302032":
                    st.session_state['admin_connecte'] = True
                    st.session_state['acces_autorise'] = True
                    st.success("Connexion administrateur réussie!")
                    st.rerun()
                elif u.lower() == "user" and p == "0699302032":
                    st.session_state['acces_autorise'] = True
                    st.success("Connexion réussie!")
                    st.rerun()
                else:
                    st.error("❌ Identifiants incorrects")
        
        st.markdown("---")
        st.caption("💡 Conseil: Utilisez 'user' / '0699302032' pour la caisse")
    st.stop()

# --- 5. NAVIGATION AVANCÉE ---
is_admin = st.session_state['admin_connecte']

if is_admin:
    tabs = st.tabs(["🛒 Caisse", "📦 Gestion Stock", "📊 Statistiques", "⚙️ Paramètres"])
else:
    tabs = st.tabs(["🛒 Caisse"])

# --- 6. ONGLET CAISSE AMÉLIORÉ ---
with tabs[0]:
    st.markdown("<h1 class='main-header'>🛒 Terminal de Vente</h1>", unsafe_allow_html=True)
    
    # Barre de recherche avec suggestions
    col1, col2 = st.columns([3, 1])
    with col1:
        recherche = st.text_input("🔍 Rechercher un article...", placeholder="Tapez le nom de l'article...")
    with col2:
        if st.button("🔄 Réinitialiser", use_container_width=True):
            st.session_state.search_key = 0
            st.rerun()
    
    # Affichage des articles disponibles
    if recherche:
        mask = df_stock["Article"].astype(str).str.contains(recherche, case=False, na=False) & (df_stock["Quantite"] > 0)
        suggestions = df_stock[mask]
        
        if not suggestions.empty:
            st.subheader("📋 Résultats de recherche:")
            cols = st.columns(3)
            for idx, (_, item) in enumerate(suggestions.iterrows()):
                with cols[idx % 3]:
                    with st.container():
                        st.markdown(f"""
                        <div style='border:1px solid #ddd; padding:1rem; border-radius:5px; margin:0.5rem 0;'>
                            <h4>{item['Article']}</h4>
                            <p>💰 Prix: {item['PV']:,.0f} DA</p>
                            <p>📦 Stock: {item['Quantite']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button(f"➕ Ajouter {item['Article']}", key=f"add_{item['Article']}_{idx}"):
                            index_ex = next((i for i, p in enumerate(st.session_state['panier']) 
                                           if p['Article'] == item['Article']), None)
                            if index_ex is not None:
                                if st.session_state['panier'][index_ex]['Qte'] < item['Quantite']:
                                    st.session_state['panier'][index_ex]['Qte'] += 1
                                    st.success(f"Quantité augmentée pour {item['Article']}")
                            else:
                                st.session_state['panier'].append({
                                    'Article': str(item['Article']), 
                                    'PV': float(item['PV']),
                                    'Qte': 1, 
                                    'PA': float(item['PA']),
                                    'Frais': float(item['Frais']), 
                                    'Max': int(item['Quantite'])
                                })
                                st.success(f"{item['Article']} ajouté au panier!")
                            st.rerun()
        else:
            st.warning("Aucun article trouvé")
    
    st.markdown("---")
    
    # Panier d'achat
    if st.session_state['panier']:
        st.subheader("🛍️ Panier actuel")
        
        total_general = 0.0
        for idx, p in enumerate(st.session_state['panier']):
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 0.5])
                col1.markdown(f"**{p['Article']}**")
                col2.markdown(f"Prix unitaire: {p['PV']:,.0f} DA")
                
                new_qte = col3.number_input(
                    "Qté", 
                    min_value=1, 
                    max_value=int(p['Max']), 
                    value=int(p['Qte']),
                    key=f"qty_{idx}",
                    label_visibility="collapsed"
                )
                if new_qte != p['Qte']:
                    p['Qte'] = new_qte
                    st.rerun()
                
                sous_total = p['PV'] * p['Qte']
                col4.markdown(f"**{sous_total:,.0f} DA**")
                
                if col5.button("🗑️", key=f"del_{idx}"):
                    st.session_state['panier'].pop(idx)
                    st.rerun()
                
                total_general += sous_total
        
        # Affichage du total
        st.markdown(f"""
        <div class='total-display'>
            TOTAL: {total_general:,.0f} DA
        </div>
        """, unsafe_allow_html=True)
        
        # Options de paiement
        col1, col2, col3 = st.columns(3)
        with col2:
            if st.button("💰 VALIDER LA VENTE", use_container_width=True, type="primary"):
                # Backup avant validation
                backup_data()
                
                # Enregistrement de la vente
                for p in st.session_state['panier']:
                    benef = float(p['Qte']) * (float(p['PV']) - (float(p['PA']) + float(p['Frais'])))
                    new_v = pd.DataFrame([[
                        datetime.now().strftime("%Y-%m-%d %H:%M"), 
                        p['Article'], 
                        p['Qte'], 
                        p['PV'] * p['Qte'], 
                        benef
                    ]], columns=["Date", "Article", "Qte", "Vente_Total", "Benefice"])
                    df_ventes = pd.concat([df_ventes, new_v], ignore_index=True)
                    df_stock.loc[df_stock["Article"] == p['Article'], "Quantite"] -= p['Qte']
                
                if save_data(df_ventes, "ventes.csv") and save_data(df_stock, "stock.csv"):
                    st.balloons()
                    st.success("✅ Vente enregistrée avec succès!")
                    st.session_state['panier'] = []
                    st.session_state['vente_en_cours'] = False
                    st.rerun()
    else:
        st.info("🛒 Le panier est vide. Commencez par rechercher des articles!")

# --- 7. GESTION STOCK (ADMIN) ---
if is_admin:
    with tabs[1]:
        st.subheader("📦 Gestion de l'Inventaire")
        
        # Affichage du stock actuel
        st.dataframe(
            df_stock.style.format({
                'PA': '{:,.0f} DA',
                'Frais': '{:,.0f} DA',
                'PV': '{:,.0f} DA',
                'Quantite': '{:,.0f}'
            }),
            use_container_width=True,
            height=400
        )
        
        # Ajout d'article
        with st.expander("➕ Ajouter un nouvel article", expanded=False):
            with st.form("nouvel_article"):
                col1, col2 = st.columns(2)
                with col1:
                    nom = st.text_input("Nom de l'article")
                    pa = st.number_input("Prix d'achat (PA)", min_value=0.0)
                with col2:
                    frais = st.number_input("Frais", min_value=0.0)
                    pv = st.number_input("Prix de vente (PV)", min_value=0.0)
                
                quantite = st.number_input("Quantité initiale", min_value=0, value=0)
                
                submitted = st.form_submit_button("Ajouter au stock")
                if submitted and nom:
                    new_row = pd.DataFrame([{
                        "Article": nom,
                        "PA": pa,
                        "Frais": frais,
                        "PV": pv,
                        "Quantite": quantite
                    }])
                    df_stock = pd.concat([df_stock, new_row], ignore_index=True)
                    save_data(df_stock, "stock.csv")
                    st.success(f"{nom} ajouté au stock!")
                    st.rerun()

    with tabs[2]:
        st.subheader("📊 Statistiques")
        
        # Analyse des ventes
        if not df_ventes.empty:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_ventes = df_ventes['Vente_Total'].sum()
                st.metric("💰 Chiffre d'affaires", f"{total_ventes:,.0f} DA")
            
            with col2:
                total_benefice = df_ventes['Benefice'].sum()
                st.metric("📈 Bénéfice", f"{total_benefice:,.0f} DA")
            
            with col3:
                nb_ventes = len(df_ventes)
                st.metric("🛍️ Nombre de ventes", nb_ventes)
            
            with col4:
                marge_moy = (total_benefice / total_ventes * 100) if total_ventes > 0 else 0
                st.metric("📊 Marge moyenne", f"{marge_moy:.1f}%")
            
            # Graphiques
            col1, col2 = st.columns(2)
            
            with col1:
                # Ventes par article
                ventes_articles = df_ventes.groupby('Article')['Vente_Total'].sum().reset_index()
                fig = px.bar(ventes_articles, x='Article', y='Vente_Total', 
                           title="Ventes par article",
                           labels={'Vente_Total': 'Montant (DA)', 'Article': 'Article'})
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Évolution des ventes
                df_ventes['Date'] = pd.to_datetime(df_ventes['Date'])
                ventes_journalieres = df_ventes.groupby(df_ventes['Date'].dt.date)['Vente_Total'].sum().reset_index()
                fig2 = px.line(ventes_journalieres, x='Date', y='Vente_Total',
                             title="Évolution des ventes",
                             labels={'Vente_Total': 'Montant (DA)', 'Date': 'Date'})
                st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Aucune donnée de vente disponible")

    with tabs[3]:
        st.subheader("⚙️ Paramètres")
        
        # Sauvegarde
        if st.button("💾 Sauvegarder les données", use_container_width=True):
            backup_data()
            st.success("Sauvegarde effectuée!")
        
        # Réinitialisation
        with st.expander("⚠️ Zone dangereuse", expanded=False):
            st.warning("Ces actions sont irréversibles!")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🗑️ Vider les ventes", use_container_width=True):
                    df_ventes = pd.DataFrame(columns=["Date", "Article", "Qte", "Vente_Total", "Benefice"])
                    save_data(df_ventes, "ventes.csv")
                    st.success("Historique des ventes vidé!")
            with col2:
                if st.button("🔄 Réinitialiser le stock", use_container_width=True):
                    st.error("Fonction à implémenter avec précaution")