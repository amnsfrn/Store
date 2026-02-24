import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import calendar

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="Happy Store - Gestion Commerciale", 
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS personnalisé
st.markdown("""
<style>
    /* Style général */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* En-têtes */
    .main-header {
        font-size: 1.8rem;
        font-weight: 500;
        color: #2c3e50;
        padding: 1rem 0;
        border-bottom: 2px solid #e9ecef;
        margin-bottom: 2rem;
    }
    
    .section-header {
        font-size: 1.3rem;
        font-weight: 500;
        color: #495057;
        margin: 1.5rem 0 1rem 0;
    }
    
    /* Cartes métriques */
    .metric-card {
        background: white;
        padding: 1.2rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        border: 1px solid #e9ecef;
        text-align: center;
    }
    
    .metric-value {
        font-size: 1.8rem;
        font-weight: 600;
        color: #2c3e50;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #868e96;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Total caisse */
    .total-display {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        border: 2px solid #2c3e50;
        text-align: center;
        margin: 1rem 0;
    }
    
    .total-value {
        font-size: 2.5rem;
        font-weight: 600;
        color: #2c3e50;
    }
    
    /* Boutons */
    .stButton button {
        border-radius: 4px;
        font-weight: 400;
        transition: all 0.2s;
    }
    
    /* Alertes */
    .alert-low-stock {
        background-color: #fff3cd;
        border: 1px solid #ffecb5;
        color: #856404;
        padding: 0.5rem 1rem;
        border-radius: 4px;
    }
    
    /* Séparateurs */
    .divider {
        height: 1px;
        background-color: #e9ecef;
        margin: 2rem 0;
    }
    
    /* Cellules calendrier */
    .calendar-cell {
        border: 1px solid #e9ecef;
        border-radius: 4px;
        padding: 0.5rem;
        margin: 0.2rem;
        min-height: 80px;
    }
    
    .calendar-day {
        font-weight: 500;
        color: #2c3e50;
    }
    
    .calendar-amount {
        font-size: 0.8rem;
        color: #28a745;
    }
    
    .calendar-count {
        font-size: 0.7rem;
        color: #868e96;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. INITIALISATION SESSION ---
def init_session_state():
    """Initialise toutes les variables de session"""
    defaults = {
        'panier': [],
        'acces_autorise': False,
        'admin_connecte': False,
        'vente_en_cours': False,
        'search_key': 0,
        'notifications': [],
        'derniere_sync': datetime.now(),
        'preferences': {
            'seuil_alerte_stock': 5,
            'devise': 'DA',
            'format_date': '%d/%m/%Y'
        },
        'ventes_recherchees': [],
        'recherche_effectuee': False,
        'afficher_form_retour': False,
        'vente_selectionnee': None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# --- 3. GESTION DES DONNÉES ---
class DataManager:
    """Gestionnaire centralisé des données"""
    
    def __init__(self):
        self.files = {
            'stock': 'stock.csv',
            'ventes': 'ventes.csv',
            'clients': 'clients.csv',
            'fournisseurs': 'fournisseurs.csv',
            'depenses': 'depenses.csv',
            'clotures': 'clotures_caisse.csv'
        }
        self.init_data_files()
    
    def init_data_files(self):
        """Initialise les fichiers de données si nécessaire"""
        schemas = {
            'stock': ["ID", "Article", "PA", "Frais", "PV", "Quantite", "Categorie", "Fournisseur", "Date_ajout", "Seuil_alerte"],
            'ventes': ["ID", "Date", "Article", "Qte", "Vente_Total", "Benefice", "Client", "Mode_paiement", "Raison_retour", "Vente_originale"],
            'clients': ["ID", "Nom", "Prenom", "Email", "Telephone", "Adresse", "Date_inscription", "Total_achats", "Fidelite"],
            'fournisseurs': ["ID", "Nom", "Contact", "Telephone", "Email", "Adresse", "Categorie"],
            'depenses': ["ID", "Date", "Libelle", "Montant", "Categorie", "Mode_paiement", "Fournisseur"],
            'clotures': ["ID", "Date", "Caissier", "Montant_theorique", "Montant_compte", "Ecart", "Observations", "Statut"]
        }
        
        for key, columns in schemas.items():
            file = self.files[key]
            if not os.path.exists(file):
                pd.DataFrame(columns=columns).to_csv(file, index=False)
    
    def load_data(self, data_type):
        """Charge les données depuis le fichier CSV"""
        try:
            df = pd.read_csv(self.files[data_type])
            # Conversion des colonnes numériques
            numeric_cols = ["PA", "Frais", "PV", "Quantite", "Vente_Total", "Benefice", "Montant", "Total_achats", 
                           "Montant_theorique", "Montant_compte", "Ecart"]
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            return df
        except Exception as e:
            st.error(f"Erreur de chargement {data_type}: {e}")
            return pd.DataFrame()
    
    def save_data(self, df, data_type):
        """Sauvegarde les données dans le fichier CSV"""
        try:
            df.to_csv(self.files[data_type], index=False)
            return True
        except Exception as e:
            st.error(f"Erreur de sauvegarde {data_type}: {e}")
            return False
    
    def backup_all(self):
        """Crée une sauvegarde complète"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = f"backups/backup_{timestamp}"
        os.makedirs(backup_dir, exist_ok=True)
        
        for file in self.files.values():
            if os.path.exists(file):
                df = pd.read_csv(file)
                df.to_csv(f"{backup_dir}/{file}", index=False)
        
        return backup_dir

dm = DataManager()

# --- 4. CHARGEMENT DES DONNÉES ---
df_stock = dm.load_data('stock')
df_ventes = dm.load_data('ventes')
df_clients = dm.load_data('clients')
df_fournisseurs = dm.load_data('fournisseurs')
df_depenses = dm.load_data('depenses')
df_clotures = dm.load_data('clotures')

# --- 5. FONCTIONS UTILITAIRES ---
def generate_id(prefix="ID"):
    """Génère un ID unique"""
    return f"{prefix}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(df_stock)}"

def check_low_stock():
    """Vérifie les stocks bas et crée des notifications"""
    if not df_stock.empty:
        seuil = st.session_state.preferences['seuil_alerte_stock']
        low_stock = df_stock[df_stock['Quantite'] <= seuil]
        if not low_stock.empty:
            for _, item in low_stock.iterrows():
                msg = f"⚠️ Stock bas: {item['Article']} ({item['Quantite']} restants)"
                if msg not in st.session_state.notifications:
                    st.session_state.notifications.append(msg)

def format_currency(amount):
    """Formate le montant en devise"""
    return f"{amount:,.0f} {st.session_state.preferences['devise']}"

def get_daily_summary():
    """Résumé journalier des ventes"""
    if df_ventes.empty:
        return {'nb_ventes': 0, 'ca': 0, 'benefice': 0}
    
    df_ventes['Date'] = pd.to_datetime(df_ventes['Date'])
    today = datetime.now().date()
    ventes_aujourd = df_ventes[df_ventes['Date'].dt.date == today]
    
    return {
        'nb_ventes': len(ventes_aujourd),
        'ca': ventes_aujourd['Vente_Total'].sum() if not ventes_aujourd.empty else 0,
        'benefice': ventes_aujourd['Benefice'].sum() if not ventes_aujourd.empty else 0
    }

def enregistrer_cloture_caisse(montant_theorique, montant_compte, ecart, observations=""):
    """Enregistre une clôture de caisse dans l'historique"""
    fichier_clotures = "clotures_caisse.csv"
    
    if not os.path.exists(fichier_clotures):
        df_clotures = pd.DataFrame(columns=["ID", "Date", "Caissier", "Montant_theorique", 
                                           "Montant_compte", "Ecart", "Observations", "Statut"])
    else:
        df_clotures = pd.read_csv(fichier_clotures)
    
    nouvelle_cloture = pd.DataFrame([{
        'ID': generate_id('CLT'),
        'Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'Caissier': "Admin" if st.session_state.admin_connecte else "User",
        'Montant_theorique': montant_theorique,
        'Montant_compte': montant_compte,
        'Ecart': ecart,
        'Observations': observations,
        'Statut': "OK" if abs(ecart) < 100 else "À vérifier"
    }])
    
    df_clotures = pd.concat([df_clotures, nouvelle_cloture], ignore_index=True)
    df_clotures.to_csv(fichier_clotures, index=False)
    
    return True

def rechercher_ventes_client(date_recherche, article_recherche=""):
    """Recherche les ventes pour un retour éventuel"""
    if df_ventes.empty:
        return pd.DataFrame()
    
    df_ventes_copy = df_ventes.copy()
    df_ventes_copy['Date'] = pd.to_datetime(df_ventes_copy['Date'])
    
    # Filtrer par date
    mask = df_ventes_copy['Date'].dt.date == date_recherche
    
    # Filtrer par article si spécifié
    if article_recherche:
        mask &= df_ventes_copy['Article'].str.contains(article_recherche, case=False, na=False)
    
    # Exclure les retours déjà effectués
    mask &= df_ventes_copy['Qte'] > 0
    
    return df_ventes_copy[mask].copy()

def traiter_retour(id_vente, qte_retour, raison_retour):
    """Traite le retour d'une marchandise"""
    global df_ventes, df_stock
    
    # Trouver la vente originale
    vente_originale = df_ventes[df_ventes['ID'] == id_vente].iloc[0]
    
    if qte_retour > vente_originale['Qte']:
        return False, "Quantité retournée supérieure à la quantité vendue"
    
    # Créer une entrée de retour (vente négative)
    nouveau_retour = pd.DataFrame([{
        'ID': generate_id('RET'),
        'Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'Article': vente_originale['Article'],
        'Qte': -qte_retour,
        'Vente_Total': -(vente_originale['Vente_Total'] / vente_originale['Qte'] * qte_retour),
        'Benefice': -(vente_originale['Benefice'] / vente_originale['Qte'] * qte_retour),
        'Client': vente_originale['Client'] if 'Client' in vente_originale else 'Retour client',
        'Mode_paiement': 'Retour',
        'Raison_retour': raison_retour,
        'Vente_originale': id_vente
    }])
    
    df_ventes = pd.concat([df_ventes, nouveau_retour], ignore_index=True)
    
    # Remettre en stock
    df_stock.loc[df_stock['Article'] == vente_originale['Article'], 'Quantite'] += qte_retour
    
    # Sauvegarder
    dm.save_data(df_ventes, 'ventes')
    dm.save_data(df_stock, 'stock')
    
    return True, "Retour traité avec succès"

# --- 6. BARRE LATÉRALE ---
with st.sidebar:
    st.image("https://via.placeholder.com/200x60/2c3e50/ffffff?text=HAPPY+STORE", use_column_width=True)
    
    if st.session_state['acces_autorise'] or st.session_state['admin_connecte']:
        # Profil utilisateur
        user_status = "Administrateur" if st.session_state['admin_connecte'] else "Caissier"
        st.markdown(f"""
        <div style='padding:1rem 0;'>
            <div style='font-weight:500; color:#2c3e50;'>{user_status}</div>
            <div style='font-size:0.8rem; color:#868e96;'>{datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Notifications
        if st.session_state.notifications:
            with st.expander(f"🔔 Notifications ({len(st.session_state.notifications)})"):
                for notif in st.session_state.notifications:
                    st.warning(notif)
        
        # Menu de navigation
        menu_options = ["🏪 Caisse", "📊 Tableau de bord", "📅 Historique ventes"]
        if st.session_state['admin_connecte']:
            menu_options.extend(["📦 Stock", "👥 Clients", "🤝 Fournisseurs", "💰 Comptabilité", 
                                "📅 Calendrier ventes", "🔒 Clôture caisse", "↩️ Retours marchandise", "⚙️ Paramètres"])
        
        choix_menu = st.radio("Navigation", menu_options, label_visibility="collapsed")
        
        st.markdown("---")
        
        # Actions rapides
        with st.expander("⚡ Actions rapides"):
            if st.button("🆕 Nouvelle vente", use_container_width=True):
                st.session_state.panier = []
                st.rerun()
            
            if st.button("📊 Rapport journalier", use_container_width=True):
                st.session_state.show_daily_report = True
        
        # Déconnexion
        if st.button("🔴 Déconnexion", use_container_width=True, type="primary"):
            st.session_state.clear()
            st.rerun()

# --- 7. PAGE DE CONNEXION ---
if not st.session_state['acces_autorise'] and not st.session_state['admin_connecte']:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h1 class='main-header'>Happy Store</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#868e96;'>Système de gestion commerciale</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input("Nom d'utilisateur")
            password = st.text_input("Mot de passe", type="password")
            
            if st.form_submit_button("Se connecter", use_container_width=True, type="primary"):
                if username == "admin" and password == "admin0699":
                    st.session_state.admin_connecte = True
                    st.session_state.acces_autorise = True
                    st.rerun()
                elif username == "user" and password == "0699":
                    st.session_state.acces_autorise = True
                    st.rerun()
                else:
                    st.error("Identifiants incorrects")
        
        st.markdown("---")
        st.caption("© 2024 Happy Store - Tous droits réservés")
    st.stop()

# --- 8. CAISSE ---
if choix_menu == "🏪 Caisse":
    st.markdown("<h1 class='main-header'>Caisse enregistreuse</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        recherche = st.text_input("🔍 Rechercher un article", placeholder="Code barre ou nom...")
    with col2:
        if st.button("🆕 Nouvelle vente", use_container_width=True):
            st.session_state.panier = []
            st.rerun()
    with col3:
        st.metric("Stock total", df_stock['Quantite'].sum() if not df_stock.empty else 0)
    
    # Résultats de recherche
    if recherche and not df_stock.empty:
        mask = df_stock['Article'].str.contains(recherche, case=False, na=False) & (df_stock['Quantite'] > 0)
        results = df_stock[mask]
        
        if not results.empty:
            st.markdown("<div class='section-header'>Résultats</div>", unsafe_allow_html=True)
            cols = st.columns(3)
            for idx, (_, item) in enumerate(results.iterrows()):
                with cols[idx % 3]:
                    with st.container():
                        st.markdown(f"""
                        <div style='border:1px solid #e9ecef; padding:1rem; border-radius:4px; margin:0.5rem 0;'>
                            <div style='font-weight:500;'>{item['Article']}</div>
                            <div style='font-size:1.2rem; color:#2c3e50;'>{format_currency(item['PV'])}</div>
                            <div style='font-size:0.8rem; color:#868e96;'>Stock: {item['Quantite']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button("Ajouter", key=f"add_{item['ID']}_{idx}"):
                            existing = next((i for i, p in enumerate(st.session_state.panier) 
                                           if p['ID'] == item['ID']), None)
                            if existing is not None:
                                if st.session_state.panier[existing]['Qte'] < item['Quantite']:
                                    st.session_state.panier[existing]['Qte'] += 1
                            else:
                                st.session_state.panier.append({
                                    'ID': item['ID'],
                                    'Article': item['Article'],
                                    'PV': float(item['PV']),
                                    'Qte': 1,
                                    'Max': int(item['Quantite'])
                                })
                            st.rerun()
    
    # Panier
    if st.session_state.panier:
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        st.markdown("<div class='section-header'>Panier en cours</div>", unsafe_allow_html=True)
        
        total = 0
        for idx, item in enumerate(st.session_state.panier):
            col1, col2, col3, col4 = st.columns([4, 2, 2, 1])
            col1.write(f"**{item['Article']}**")
            col2.write(format_currency(item['PV']))
            
            new_qte = col3.number_input("Qté", min_value=1, max_value=item['Max'],
                                       value=item['Qte'], key=f"qte_{idx}", label_visibility="collapsed")
            if new_qte != item['Qte']:
                item['Qte'] = new_qte
                st.rerun()
            
            if col4.button("🗑️", key=f"del_{idx}"):
                st.session_state.panier.pop(idx)
                st.rerun()
            
            total += item['PV'] * item['Qte']
        
        # Total
        st.markdown(f"""
        <div class='total-display'>
            <div style='font-size:1rem; color:#868e96;'>Total TTC</div>
            <div class='total-value'>{format_currency(total)}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Paiement
        col1, col2, col3 = st.columns(3)
        with col2:
            mode_paiement = st.selectbox("Mode de paiement", ["Espèces", "Carte bancaire", "Chèque"])
            
            if st.button("✅ Valider la vente", use_container_width=True, type="primary"):
                for item in st.session_state.panier:
                    article_info = df_stock[df_stock['ID'] == item['ID']].iloc[0]
                    benef = item['Qte'] * (item['PV'] - (article_info['PA'] + article_info['Frais']))
                    
                    new_vente = pd.DataFrame([{
                        'ID': generate_id('V'),
                        'Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'Article': item['Article'],
                        'Qte': item['Qte'],
                        'Vente_Total': item['PV'] * item['Qte'],
                        'Benefice': benef,
                        'Client': 'Particulier',
                        'Mode_paiement': mode_paiement,
                        'Raison_retour': '',
                        'Vente_originale': ''
                    }])
                    
                    df_ventes = pd.concat([df_ventes, new_vente], ignore_index=True)
                    df_stock.loc[df_stock['ID'] == item['ID'], 'Quantite'] -= item['Qte']
                
                dm.save_data(df_ventes, 'ventes')
                dm.save_data(df_stock, 'stock')
                
                st.session_state.panier = []
                st.success("Vente enregistrée avec succès!")
                st.balloons()
                st.rerun()

# --- 9. TABLEAU DE BORD ---
elif choix_menu == "📊 Tableau de bord":
    st.markdown("<h1 class='main-header'>Tableau de bord</h1>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        ca_total = df_ventes['Vente_Total'].sum() if not df_ventes.empty else 0
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{format_currency(ca_total)}</div>
            <div class='metric-label'>Chiffre d'affaires total</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        benefice_total = df_ventes['Benefice'].sum() if not df_ventes.empty else 0
        marge = (benefice_total / ca_total * 100) if ca_total > 0 else 0
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{format_currency(benefice_total)}</div>
            <div class='metric-label'>Bénéfice total ({marge:.1f}%)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        stock_value = (df_stock['PA'] * df_stock['Quantite']).sum() if not df_stock.empty else 0
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{format_currency(stock_value)}</div>
            <div class='metric-label'>Valeur du stock</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        nb_clients = len(df_clients) if not df_clients.empty else 0
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{nb_clients}</div>
            <div class='metric-label'>Clients fidèles</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='section-header'>Évolution des ventes (30 jours)</div>", unsafe_allow_html=True)
        if not df_ventes.empty:
            df_ventes['Date'] = pd.to_datetime(df_ventes['Date'])
            dernier_30j = df_ventes[df_ventes['Date'] >= datetime.now() - timedelta(days=30)]
            if not dernier_30j.empty:
                ventes_jour = dernier_30j.groupby(dernier_30j['Date'].dt.date)['Vente_Total'].sum().reset_index()
                fig = px.line(ventes_jour, x='Date', y='Vente_Total', 
                             markers=True, line_shape='linear')
                fig.update_layout(
                    showlegend=False,
                    plot_bgcolor='white',
                    yaxis_title="Montant (DA)",
                    xaxis_title=""
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Aucune vente sur les 30 derniers jours")
        else:
            st.info("Aucune donnée de vente")
    
    with col2:
        st.markdown("<div class='section-header'>Top 5 articles</div>", unsafe_allow_html=True)
        if not df_ventes.empty:
            ventes_positives = df_ventes[df_ventes['Qte'] > 0]
            if not ventes_positives.empty:
                top_articles = ventes_positives.groupby('Article')['Qte'].sum().nlargest(5).reset_index()
                fig2 = px.bar(top_articles, x='Article', y='Qte',
                             color_discrete_sequence=['#2c3e50'])
                fig2.update_layout(
                    showlegend=False,
                    plot_bgcolor='white',
                    yaxis_title="Quantité vendue"
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("Aucune vente positive")
        else:
            st.info("Aucune donnée de vente")
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    summary = get_daily_summary()
    
    with col1:
        st.metric("Ventes aujourd'hui", summary['nb_ventes'])
    with col2:
        st.metric("Chiffre d'affaires", format_currency(summary['ca']))
    with col3:
        st.metric("Bénéfice", format_currency(summary['benefice']))

# --- 10. HISTORIQUE DES VENTES ---
elif choix_menu == "📅 Historique ventes":
    st.markdown("<h1 class='main-header'>Historique des ventes</h1>", unsafe_allow_html=True)
    
    if df_ventes.empty:
        st.info("Aucune vente enregistrée")
        st.stop()
    
    df_ventes['Date'] = pd.to_datetime(df_ventes['Date'])
    
    st.markdown("<div class='section-header'>Filtres</div>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
    
    with col1:
        vue_rapide = st.selectbox(
            "Vue rapide",
            ["Aujourd'hui", "Hier", "Cette semaine", "Ce mois", "Mois dernier", "Cette année", "Personnalisée"]
        )
    
    with col2:
        articles_list = ["Tous"] + sorted(df_ventes['Article'].unique().tolist())
        filtre_article = st.selectbox("Filtrer par article", articles_list)
    
    with col3:
        if 'Mode_paiement' in df_ventes.columns:
            paiements_list = ["Tous"] + sorted(df_ventes['Mode_paiement'].unique().tolist())
            filtre_paiement = st.selectbox("Mode de paiement", paiements_list)
        else:
            filtre_paiement = "Tous"
    
    with col4:
        st.write("")
        st.write("")
        if st.button("Réinitialiser", use_container_width=True):
            vue_rapide = "Aujourd'hui"
            filtre_article = "Tous"
            filtre_paiement = "Tous"
            st.rerun()
    
    aujourd_hui = datetime.now().date()
    
    if vue_rapide == "Aujourd'hui":
        date_debut = aujourd_hui
        date_fin = aujourd_hui
        libelle_periode = f"Ventes du {date_debut.strftime('%d/%m/%Y')}"
    
    elif vue_rapide == "Hier":
        date_debut = aujourd_hui - timedelta(days=1)
        date_fin = date_debut
        libelle_periode = f"Ventes du {date_debut.strftime('%d/%m/%Y')}"
    
    elif vue_rapide == "Cette semaine":
        date_debut = aujourd_hui - timedelta(days=aujourd_hui.weekday())
        date_fin = aujourd_hui
        libelle_periode = f"Ventes du {date_debut.strftime('%d/%m/%Y')} au {date_fin.strftime('%d/%m/%Y')}"
    
    elif vue_rapide == "Ce mois":
        date_debut = aujourd_hui.replace(day=1)
        date_fin = aujourd_hui
        libelle_periode = f"Ventes de {date_debut.strftime('%B %Y')}"
    
    elif vue_rapide == "Mois dernier":
        premier_du_mois = aujourd_hui.replace(day=1)
        date_debut = (premier_du_mois - timedelta(days=1)).replace(day=1)
        date_fin = premier_du_mois - timedelta(days=1)
        libelle_periode = f"Ventes de {date_debut.strftime('%B %Y')}"
    
    elif vue_rapide == "Cette année":
        date_debut = aujourd_hui.replace(month=1, day=1)
        date_fin = aujourd_hui
        libelle_periode = f"Ventes de l'année {aujourd_hui.year}"
    
    else:
        col1, col2 = st.columns(2)
        with col1:
            date_debut = st.date_input("Date début", value=aujourd_hui - timedelta(days=7))
        with col2:
            date_fin = st.date_input("Date fin", value=aujourd_hui)
        
        if date_debut > date_fin:
            st.error("La date de début doit être antérieure à la date de fin")
            st.stop()
        
        libelle_periode = f"Ventes du {date_debut.strftime('%d/%m/%Y')} au {date_fin.strftime('%d/%m/%Y')}"
    
    mask_date = (df_ventes['Date'].dt.date >= date_debut) & (df_ventes['Date'].dt.date <= date_fin)
    df_filtre = df_ventes[mask_date].copy()
    
    if filtre_article != "Tous":
        df_filtre = df_filtre[df_filtre['Article'] == filtre_article]
    
    if filtre_paiement != "Tous" and 'Mode_paiement' in df_filtre.columns:
        df_filtre = df_filtre[df_filtre['Mode_paiement'] == filtre_paiement]
    
    st.markdown(f"<div class='section-header'>{libelle_periode}</div>", unsafe_allow_html=True)
    
    if not df_filtre.empty:
        ventes_positives = df_filtre[df_filtre['Qte'] > 0]
        retours = df_filtre[df_filtre['Qte'] < 0]
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            nb_ventes = len(ventes_positives)
            st.metric("Nombre de ventes", nb_ventes)
        
        with col2:
            ca_periode = ventes_positives['Vente_Total'].sum()
            st.metric("Chiffre d'affaires", format_currency(ca_periode))
        
        with col3:
            benefice_periode = ventes_positives['Benefice'].sum()
            marge = (benefice_periode / ca_periode * 100) if ca_periode > 0 else 0
            st.metric("Bénéfice", format_currency(benefice_periode), f"{marge:.1f}%")
        
        with col4:
            qte_totale = ventes_positives['Qte'].sum()
            st.metric("Articles vendus", f"{qte_totale:.0f}")
        
        with col5:
            panier_moyen = ca_periode / nb_ventes if nb_ventes > 0 else 0
            st.metric("Panier moyen", format_currency(panier_moyen))
        
        if not retours.empty:
            st.warning(f"⚠️ {len(retours)} retour(s) sur cette période pour un montant de {format_currency(abs(retours['Vente_Total'].sum()))}")
        
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        st.markdown("<div class='section-header'>Détail des ventes</div>", unsafe_allow_html=True)
        
        df_display = df_filtre.sort_values('Date', ascending=False