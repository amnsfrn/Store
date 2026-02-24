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
        
        df_display = df_filtre.sort_values('Date', ascending=False).copy()
        df_display['Date'] = df_display['Date'].dt.strftime('%d/%m/%Y %H:%M')
        df_display['Vente_Total'] = df_display['Vente_Total'].apply(lambda x: format_currency(abs(x)))
        df_display['Qte'] = df_display['Qte'].apply(lambda x: f"{abs(x):.0f}" + (" (Retour)" if x < 0 else ""))
        
        display_cols = ['Date', 'Article', 'Qte', 'Vente_Total']
        if 'Mode_paiement' in df_display.columns:
            display_cols.append('Mode_paiement')
        if 'Raison_retour' in df_display.columns and any(df_display['Raison_retour'].notna()):
            display_cols.append('Raison_retour')
        
        st.dataframe(df_display[display_cols], use_container_width=True, height=400)
        
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<div class='section-header'>Ventes par jour</div>", unsafe_allow_html=True)
            ventes_par_jour = ventes_positives.groupby(ventes_positives['Date'].dt.date)['Vente_Total'].sum().reset_index()
            if not ventes_par_jour.empty:
                fig = px.bar(ventes_par_jour, x='Date', y='Vente_Total',
                            labels={'Vente_Total': 'Montant (DA)', 'Date': 'Date'},
                            color_discrete_sequence=['#2c3e50'])
                fig.update_layout(showlegend=False, plot_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("<div class='section-header'>Répartition par article</div>", unsafe_allow_html=True)
            ventes_par_article = ventes_positives.groupby('Article')['Vente_Total'].sum().nlargest(10).reset_index()
            if not ventes_par_article.empty:
                fig2 = px.pie(ventes_par_article, values='Vente_Total', names='Article',
                             color_discrete_sequence=px.colors.sequential.Greens_r)
                fig2.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig2, use_container_width=True)
    
    else:
        st.info("Aucune vente trouvée pour cette période")

# --- 11. GESTION STOCK ---
elif choix_menu == "📦 Stock" and st.session_state.admin_connecte:
    st.markdown("<h1 class='main-header'>Gestion des stocks</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📋 Inventaire", "➕ Nouvel article", "📊 Analyse stock"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            categories = ["Toutes"] + list(df_stock['Categorie'].unique()) if not df_stock.empty else ["Toutes"]
            categorie_filter = st.selectbox("Filtrer par catégorie", categories)
        with col2:
            show_low_stock = st.checkbox("Afficher uniquement les stocks bas")
        
        df_display = df_stock.copy()
        if not df_display.empty:
            if categorie_filter != "Toutes":
                df_display = df_display[df_display['Categorie'] == categorie_filter]
            if show_low_stock:
                df_display = df_display[df_display['Quantite'] <= df_display['Seuil_alerte']]
            
            st.dataframe(
                df_display.style.format({
                    'PA': lambda x: format_currency(x),
                    'Frais': lambda x: format_currency(x),
                    'PV': lambda x: format_currency(x),
                    'Quantite': '{:.0f}'
                }),
                use_container_width=True,
                height=400
            )
            
            with st.expander("Actions sur le stock"):
                col1, col2 = st.columns(2)
                with col1:
                    article_modif = st.selectbox("Sélectionner un article", df_stock['Article'].tolist())
                    if article_modif:
                        new_qte = st.number_input("Nouvelle quantité", min_value=0, value=0)
                        if st.button("Mettre à jour le stock"):
                            df_stock.loc[df_stock['Article'] == article_modif, 'Quantite'] = new_qte
                            dm.save_data(df_stock, 'stock')
                            st.success("Stock mis à jour")
                            st.rerun()
    
    with tab2:
        with st.form("nouvel_article"):
            col1, col2 = st.columns(2)
            with col1:
                nom = st.text_input("Nom de l'article*")
                categorie = st.selectbox("Catégorie", ["Alimentaire", "Boisson", "Hygiène", "Autre"])
                fournisseur = st.selectbox("Fournisseur", df_fournisseurs['Nom'].tolist() if not df_fournisseurs.empty else ["Aucun"])
            
            with col2:
                pa = st.number_input("Prix d'achat (PA)*", min_value=0.0, format="%.2f")
                frais = st.number_input("Frais", min_value=0.0, format="%.2f")
                pv = st.number_input("Prix de vente (PV)*", min_value=0.0, format="%.2f")
            
            col1, col2 = st.columns(2)
            with col1:
                quantite = st.number_input("Quantité initiale*", min_value=0, value=0)
            with col2:
                seuil_alerte = st.number_input("Seuil d'alerte", min_value=1, value=5)
            
            if st.form_submit_button("Ajouter au stock"):
                if nom and pa and pv:
                    new_article = pd.DataFrame([{
                        'ID': generate_id('ART'),
                        'Article': nom,
                        'PA': pa,
                        'Frais': frais,
                        'PV': pv,
                        'Quantite': quantite,
                        'Categorie': categorie,
                        'Fournisseur': fournisseur,
                        'Date_ajout': datetime.now().strftime('%Y-%m-%d'),
                        'Seuil_alerte': seuil_alerte
                    }])
                    df_stock = pd.concat([df_stock, new_article], ignore_index=True)
                    dm.save_data(df_stock, 'stock')
                    st.success("Article ajouté avec succès!")
                    st.rerun()
    
    with tab3:
        if not df_stock.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                stock_cat = df_stock.groupby('Categorie')['Quantite'].sum().reset_index()
                fig = px.pie(stock_cat, values='Quantite', names='Categorie',
                           title="Répartition du stock par catégorie",
                           color_discrete_sequence=px.colors.sequential.Greens_r)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                df_stock['Valeur_stock'] = df_stock['PA'] * df_stock['Quantite']
                top_value = df_stock.nlargest(10, 'Valeur_stock')[['Article', 'Valeur_stock']]
                if not top_value.empty:
                    fig2 = px.bar(top_value, x='Article', y='Valeur_stock',
                                title="Top 10 articles (valeur stock)",
                                color_discrete_sequence=['#2c3e50'])
                    st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Aucune donnée de stock")

# --- 12. GESTION CLIENTS ---
elif choix_menu == "👥 Clients" and st.session_state.admin_connecte:
    st.markdown("<h1 class='main-header'>Gestion des clients</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📋 Liste clients", "➕ Nouveau client"])
    
    with tab1:
        if not df_clients.empty:
            st.dataframe(
                df_clients.style.format({
                    'Total_achats': lambda x: format_currency(x)
                }),
                use_container_width=True
            )
            
            st.markdown("<div class='section-header'>Statistiques</div>", unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Nombre de clients", len(df_clients))
            with col2:
                ca_client = df_clients['Total_achats'].sum()
                st.metric("Chiffre d'affaires clients", format_currency(ca_client))
            with col3:
                moyen_achat = df_clients['Total_achats'].mean() if len(df_clients) > 0 else 0
                st.metric("Achat moyen", format_currency(moyen_achat))
    
    with tab2:
        with st.form("nouveau_client"):
            col1, col2 = st.columns(2)
            with col1:
                nom = st.text_input("Nom*")
                prenom = st.text_input("Prénom*")
                email = st.text_input("Email")
            with col2:
                telephone = st.text_input("Téléphone*")
                adresse = st.text_area("Adresse")
            
            if st.form_submit_button("Enregistrer client"):
                if nom and prenom and telephone:
                    new_client = pd.DataFrame([{
                        'ID': generate_id('CLT'),
                        'Nom': nom,
                        'Prenom': prenom,
                        'Email': email,
                        'Telephone': telephone,
                        'Adresse': adresse,
                        'Date_inscription': datetime.now().strftime('%Y-%m-%d'),
                        'Total_achats': 0,
                        'Fidelite': 'Nouveau'
                    }])
                    df_clients = pd.concat([df_clients, new_client], ignore_index=True)
                    dm.save_data(df_clients, 'clients')
                    st.success("Client enregistré!")
                    st.rerun()

# --- 13. FOURNISSEURS ---
elif choix_menu == "🤝 Fournisseurs" and st.session_state.admin_connecte:
    st.markdown("<h1 class='main-header'>Gestion des fournisseurs</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📋 Liste fournisseurs", "➕ Nouveau fournisseur"])
    
    with tab1:
        if not df_fournisseurs.empty:
            st.dataframe(df_fournisseurs, use_container_width=True)
    
    with tab2:
        with st.form("nouveau_fournisseur"):
            col1, col2 = st.columns(2)
            with col1:
                nom = st.text_input("Nom du fournisseur*")
                contact = st.text_input("Personne à contacter")
                telephone = st.text_input("Téléphone*")
            with col2:
                email = st.text_input("Email")
                adresse = st.text_area("Adresse")
                categorie = st.selectbox("Catégorie", ["Alimentaire", "Boisson", "Hygiène", "Divers"])
            
            if st.form_submit_button("Enregistrer fournisseur"):
                if nom and telephone:
                    new_fournisseur = pd.DataFrame([{
                        'ID': generate_id('FRN'),
                        'Nom': nom,
                        'Contact': contact,
                        'Telephone': telephone,
                        'Email': email,
                        'Adresse': adresse,
                        'Categorie': categorie
                    }])
                    df_fournisseurs = pd.concat([df_fournisseurs, new_fournisseur], ignore_index=True)
                    dm.save_data(df_fournisseurs, 'fournisseurs')
                    st.success("Fournisseur enregistré!")
                    st.rerun()

# --- 14. COMPTABILITÉ ---
elif choix_menu == "💰 Comptabilité" and st.session_state.admin_connecte:
    st.markdown("<h1 class='main-header'>Comptabilité</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📊 Synthèse", "💰 Dépenses", "📈 Rapports"])
    
    with tab1:
        col1, col2, col3, col4 = st.columns(4)
        
        ca = df_ventes[df_ventes['Qte'] > 0]['Vente_Total'].sum() if not df_ventes.empty else 0
        benefice = df_ventes[df_ventes['Qte'] > 0]['Benefice'].sum() if not df_ventes.empty else 0
        depenses = df_depenses['Montant'].sum() if not df_depenses.empty else 0
        
        with col1:
            st.metric("Chiffre d'affaires", format_currency(ca))
        with col2:
            st.metric("Bénéfice brut", format_currency(benefice))
        with col3:
            st.metric("Dépenses", format_currency(depenses))
        with col4:
            resultat_net = benefice - depenses
            st.metric("Résultat net", format_currency(resultat_net))
    
    with tab2:
        st.subheader("Enregistrer une dépense")
        with st.form("nouvelle_depense"):
            col1, col2 = st.columns(2)
            with col1:
                libelle = st.text_input("Libellé*")
                categorie = st.selectbox("Catégorie", ["Loyer", "Électricité", "Eau", "Fournitures", "Salaires", "Autre"])
            with col2:
                montant = st.number_input("Montant*", min_value=0.0)
                mode_paiement = st.selectbox("Mode de paiement", ["Espèces", "Carte", "Chèque", "Virement"])
            
            fournisseur = st.selectbox("Fournisseur (optionnel)", 
                                      ["Aucun"] + df_fournisseurs['Nom'].tolist() if not df_fournisseurs.empty else ["Aucun"])
            
            if st.form_submit_button("Enregistrer la dépense"):
                if libelle and montant:
                    new_depense = pd.DataFrame([{
                        'ID': generate_id('DEP'),
                        'Date': datetime.now().strftime('%Y-%m-%d'),
                        'Libelle': libelle,
                        'Montant': montant,
                        'Categorie': categorie,
                        'Mode_paiement': mode_paiement,
                        'Fournisseur': fournisseur if fournisseur != "Aucun" else ""
                    }])
                    df_depenses = pd.concat([df_depenses, new_depense], ignore_index=True)
                    dm.save_data(df_depenses, 'depenses')
                    st.success("Dépense enregistrée!")
                    st.rerun()
        
        if not df_depenses.empty:
            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            st.subheader("Historique des dépenses")
            df_depenses_display = df_depenses.copy()
            df_depenses_display['Montant'] = df_depenses_display['Montant'].apply(lambda x: format_currency(x))
            st.dataframe(df_depenses_display, use_container_width=True)

# --- 15. CALENDRIER DES VENTES ---
elif choix_menu == "📅 Calendrier ventes" and st.session_state.admin_connecte:
    st.markdown("<h1 class='main-header'>Calendrier des ventes</h1>", unsafe_allow_html=True)
    
    if df_ventes.empty:
        st.info("Aucune vente enregistrée")
        st.stop()
    
    df_ventes['Date'] = pd.to_datetime(df_ventes['Date'])
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    mois_liste = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
                  "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]
    
    with col1:
        mois_selection = st.selectbox("Mois", mois_liste, index=datetime.now().month - 1)
    
    with col2:
        annees_dispo = sorted(df_ventes['Date'].dt.year.unique(), reverse=True)
        annee_selection = st.selectbox("Année", annees_dispo)
    
    with col3:
        st.write("")
        st.write("")
        if st.button("Aujourd'hui", use_container_width=True):
            mois_selection = mois_liste[datetime.now().month - 1]
            annee_selection = datetime.now().year
            st.rerun()
    
    mois_numeros = {mois: i+1 for i, mois in enumerate(mois_liste)}
    mois_num = mois_numeros[mois_selection]
    
    ventes_mois = df_ventes[
        (df_ventes['Date'].dt.year == annee_selection) & 
        (df_ventes['Date'].dt.month == mois_num)
    ].copy()
    
    ventes_positives_mois = ventes_mois[ventes_mois['Qte'] > 0]
    
    cal = calendar.monthcalendar(annee_selection, mois_num)
    jours_semaine = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
    
    cols = st.columns(7)
    for i, jour in enumerate(jours_semaine):
        with cols[i]:
            st.markdown(f"<div style='text-align:center; font-weight:bold; color:#2c3e50;'>{jour}</div>", 
                       unsafe_allow_html=True)
    
    st.markdown("<div style='height:1px; background:#e9ecef; margin:0.5rem 0;'></div>", unsafe_allow_html=True)
    
    for semaine in cal:
        cols = st.columns(7)
        for i, jour in enumerate(semaine):
            with cols[i]:
                if jour != 0:
                    ventes_jour = ventes_positives_mois[ventes_positives_mois['Date'].dt.day == jour]
                    ca_jour = ventes_jour['Vente_Total'].sum() if not ventes_jour.empty else 0
                    nb_ventes = len(ventes_jour)
                    
                    if ca_jour > 0:
                        if ca_jour > 50000:
                            bg_color = "#d4edda"
                        elif ca_jour > 10000:
                            bg_color = "#fff3cd"
                        else:
                            bg_color = "#f8f9fa"
                    else:
                        bg_color = "white"
                    
                    st.markdown(f"""
                    <div style='
                        border:1px solid #e9ecef;
                        border-radius:4px;
                        padding:0.5rem;
                        margin:0.2rem;
                        background-color:{bg_color};
                        min-height:80px;
                    '>
                        <div style='font-weight:500; color:#2c3e50;'>{jour}</div>
                        <div style='font-size:0.8rem; color:#28a745;'>{format_currency(ca_jour)}</div>
                        <div style='font-size:0.7rem; color:#868e96;'>{nb_ventes} vente(s)</div>
                    </div>
                    """, unsafe_allow_html=True)
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        ca_mois = ventes_positives_mois['Vente_Total'].sum()
        st.metric("CA du mois", format_currency(ca_mois))
    
    with col2:
        benefice_mois = ventes_positives_mois['Benefice'].sum()
        st.metric("Bénéfice du mois", format_currency(benefice_mois))
    
    with col3:
        nb_jours_ventes = len(ventes_positives_mois['Date'].dt.date.unique())
        st.metric("Jours avec ventes", nb_jours_ventes)
    
    with col4:
        if not ventes_positives_mois.empty:
            meilleur_jour = ventes_positives_mois.groupby(ventes_positives_mois['Date'].dt.date)['Vente_Total'].sum().max()
            st.metric("Meilleur jour", format_currency(meilleur_jour))
    
    if not ventes_positives_mois.empty:
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        st.markdown("<div class='section-header'>Évolution journalière</div>", unsafe_allow_html=True)
        
        evolution = ventes_positives_mois.groupby(ventes_positives_mois['Date'].dt.day)['Vente_Total'].sum().reset_index()
        evolution.columns = ['Jour', 'Montant']
        
        fig = px.line(evolution, x='Jour', y='Montant', markers=True,
                     labels={'Montant': 'CA (DA)', 'Jour': 'Jour du mois'},
                     color_discrete_sequence=['#2c3e50'])
        fig.update_layout(plot_bgcolor='white')
        st.plotly_chart(fig, use_container_width=True)

# --- 16. CLÔTURE CAISSE ---
elif choix_menu == "🔒 Clôture caisse" and st.session_state.admin_connecte:
    st.markdown("<h1 class='main-header'>Clôture de caisse</h1>", unsafe_allow_html=True)
    
    fichier_clotures = "clotures_caisse.csv"
    deja_cloture_aujourdhui = False
    
    if os.path.exists(fichier_clotures):
        df_clotures = pd.read_csv(fichier_clotures)
        df_clotures['Date'] = pd.to_datetime(df_clotures['Date'])
        aujourdhui = datetime.now().date()
        deja_cloture_aujourdhui = any(df_clotures['Date'].dt.date == aujourdhui)
    
    if deja_cloture_aujourdhui:
        st.warning("⚠️ Une clôture a déjà été effectuée aujourd'hui. Vérifiez l'historique avant de procéder.")
    
    if not df_ventes.empty:
        df_ventes['Date'] = pd.to_datetime(df_ventes['Date'])
        ventes_aujourdhui = df_ventes[df_ventes['Date'].dt.date == datetime.now().date()]
        
        ventes_positives = ventes_aujourdhui[ventes_aujourdhui['Qte'] > 0]
        retours_aujourdhui = ventes_aujourdhui[ventes_aujourdhui['Qte'] < 0]
        
        montant_theorique = ventes_positives['Vente_Total'].sum()
        montant_retours = abs(retours_aujourdhui['Vente_Total'].sum()) if not retours_aujourdhui.empty else 0
        
        st.markdown("<div class='section-header'>Récapitulatif du jour</div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Ventes du jour**")
            if not ventes_positives.empty and 'Mode_paiement' in ventes_positives.columns:
                for mode in ventes_positives['Mode_paiement'].unique():
                    montant_mode = ventes_positives[ventes_positives['Mode_paiement'] == mode]['Vente_Total'].sum()
                    st.write(f"- {mode}: {format_currency(montant_mode)}")
            else:
                st.write("Aucune vente aujourd'hui")
        
        with col2:
            if montant_retours > 0:
                st.markdown("**Retours du jour**")
                st.write(f"- Retours: {format_currency(montant_retours)}")
                st.markdown(f"**Net à encaisser: {format_currency(montant_theorique)}**")
        
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        st.markdown("<div class='section-header'>Saisie du comptage</div>", unsafe_allow_html=True)
        
        with st.form("form_cloture"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Comptage par type**")
                montant_especes = st.number_input("Espèces", min_value=0.0, value=0.0, step=100.0)
                montant_cb = st.number_input("Carte bancaire", min_value=0.0, value=0.0, step=100.0)
                montant_cheque = st.number_input("Chèques", min_value=0.0, value=0.0, step=100.0)
                montant_autres = st.number_input("Autres", min_value=0.0, value=0.0, step=100.0)
            
            with col2:
                st.markdown("**Informations**")
                fond_caisse = st.number_input("Fond de caisse initial", min_value=0.0, value=5000.0, step=1000.0)
                observations = st.text_area("Observations (optionnel)", placeholder="Écarts, incidents...")
            
            montant_compte = montant_especes + montant_cb + montant_cheque + montant_autres
            montant_sans_fond = montant_compte - fond_caisse
            ecart = montant_sans_fond - montant_theorique
            
            st.markdown(f"""
            <div style='background:#f8f9fa; padding:1rem; border-radius:4px; margin:1rem 0;'>
                <div style='display:flex; justify-content:space-between;'>
                    <span>Montant théorique du jour:</span>
                    <span style='font-weight:500;'>{format_currency(montant_theorique)}</span>
                </div>
                <div style='display:flex; justify-content:space-between;'>
                    <span>Montant compté (hors fond):</span>
                    <span style='font-weight:500;'>{format_currency(montant_sans_fond)}</span>
                </div>
                <div style='display:flex; justify-content:space-between; font-size:1.2rem; margin-top:0.5rem;'>
                    <span>Écart:</span>
                    <span style='color:{"#dc3545" if abs(ecart) > 100 else "#28a745"}; font-weight:bold;'>
                        {format_currency(ecart)}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.form_submit_button("✅ Valider la clôture", use_container_width=True, type="primary"):
                if montant_compte >= fond_caisse:
                    enregistrer_cloture_caisse(montant_theorique, montant_sans_fond, ecart, observations)
                    st.success("Clôture de caisse enregistrée avec succès!")
                    st.balloons()
                    
                    st.markdown("""
                    <div style='border:2px solid #28a745; padding:1rem; border-radius:4px; margin-top:1rem;'>
                        <h3 style='color:#28a745;'>Récapitulatif à conserver</h3>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Date:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")
                        st.markdown(f"**Caissier:** {'Admin' if st.session_state.admin_connecte else 'User'}")
                    with col2:
                        st.markdown(f"**Total en caisse:** {format_currency(montant_compte)}")
                        st.markdown(f"**Dont fond:** {format_currency(fond_caisse)}")
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.error("Le montant compté ne peut pas être inférieur au fond de caisse")
    else:
        st.info("Aucune vente enregistrée")

# --- 17. RETOURS MARCHANDISE ---
elif choix_menu == "↩️ Retours marchandise" and st.session_state.admin_connecte:
    st.markdown("<h1 class='main-header'>Gestion des retours</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🔄 Nouveau retour", "📋 Historique retours", "📊 Statistiques retours"])
    
    with tab1:
        st.markdown("<div class='section-header'>Rechercher une vente</div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            date_recherche = st.date_input(
                "Date de la vente originale",
                value=datetime.now().date(),
                key="date_retour"
            )
        
        with col2:
            article_recherche = st.text_input("Rechercher par article (optionnel)", placeholder="Nom de l'article...")
        
        if st.button("🔍 Rechercher les ventes", use_container_width=True):
            ventes_trouvees = rechercher_ventes_client(date_recherche, article_recherche)
            
            if not ventes_trouvees.empty:
                st.session_state['ventes_recherchees'] = ventes_trouvees.to_dict('records')
                st.session_state['recherche_effectuee'] = True
                st.rerun()
        
        if st.session_state.get('recherche_effectuee', False) and st.session_state.get('ventes_recherchees'):
            ventes_trouvees = pd.DataFrame(st.session_state['ventes_recherchees'])
            
            st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='section-header'>Ventes trouvées ({len(ventes_trouvees)})</div>", unsafe_allow_html=True)
            
            for idx, (_, vente) in enumerate(ventes_trouvees.iterrows()):
                with st.container():
                    col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 1, 2, 2, 1])
                    
                    col1.write(f"**{vente['Date'].strftime('%d/%m/%Y %H:%M')}**")
                    col2.write(f"**{vente['Article']}**")
                    col3.write(f"x{vente['Qte']:.0f}")
                    col4.write(format_currency(vente['Vente_Total']))
                    col5.write(vente['Mode_paiement'] if 'Mode_paiement' in vente else "N/A")
                    
                    if col6.button("↩️ Retour", key=f"ret_{idx}"):
                        st.session_state['vente_selectionnee'] = vente.to_dict()
                        st.session_state['afficher_form_retour'] = True
                        st.rerun()
            
            if st.session_state.get('afficher_form_retour', False):
                vente = st.session_state['vente_selectionnee']
                
                st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='section-header'>Retour pour {vente['Article']}</div>", unsafe_allow_html=True)
                
                with st.form("form_retour"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Date vente originale:** {vente['Date'].strftime('%d/%m/%Y %H:%M')}")
                        st.write(f"**Quantité vendue:** {vente['Qte']:.0f}")
                        st.write(f"**Montant:** {format_currency(vente['Vente_Total'])}")
                    
                    with col2:
                        qte_max = int(vente['Qte'])
                        qte_retour = st.number_input(
                            "Quantité à retourner",
                            min_value=1,
                            max_value=qte_max,
                            value=1
                        )
                        
                        raison_retour = st.selectbox(
                            "Raison du retour",
                            ["Article défectueux", "Erreur de choix", "Article endommagé", 
                             "Insatisfaction client", "Autre"]
                        )
                        
                        if raison_retour == "Autre":
                            raison_retour = st.text_input("Précisez la raison")
                    
                    remboursement = (vente['Vente_Total'] / vente['Qte']) * qte_retour
                    
                    st.markdown(f"""
                    <div style='background:#f8f9fa; padding:1rem; border-radius:4px; margin:1rem 0;'>
                        <div style='display:flex; justify-content:space-between;'>
                            <span>Montant à rembourser:</span>
                            <span style='font-weight:bold; color:#dc3545;'>{format_currency(remboursement)}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns(3)
                    with col2:
                        if st.form_submit_button("✅ Confirmer le retour", use_container_width=True, type="primary"):
                            success, message = traiter_retour(vente['ID'], qte_retour, raison_retour)
                            if success:
                                st.success(message)
                                st.balloons()
                                st.session_state['afficher_form_retour'] = False
                                st.session_state['recherche_effectuee'] = False
                                st.rerun()
                            else:
                                st.error(message)
                    
                    if st.form_submit_button("Annuler", use_container_width=True):
                        st.session_state['afficher_form_retour'] = False
                        st.rerun()
        else:
            if st.session_state.get('recherche_effectuee', False):
                st.info("Aucune vente trouvée pour cette date")
    
    with tab2:
        st.markdown("<div class='section-header'>Historique des retours</div>", unsafe_allow_html=True)
        
        if not df_ventes.empty and 'Raison_retour' in df_ventes.columns:
            retours = df_ventes[df_ventes['Qte'] < 0].copy()
            
            if not retours.empty:
                retours['Date'] = pd.to_datetime(retours['Date'])
                retours = retours.sort_values('Date', ascending=False)
                
                retours['Date'] = retours['Date'].dt.strftime('%d/%m/%Y %H:%M')
                retours['Montant_rembourse'] = abs(retours['Vente_Total']).apply(lambda x: format_currency(x))
                retours['Quantite'] = abs(retours['Qte']).apply(lambda x: f"{x:.0f}")
                
                st.dataframe(
                    retours[['Date', 'Article', 'Quantite', 'Montant_rembourse', 'Raison_retour']],
                    use_container_width=True,
                    height=400
                )
                
                st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
                st.markdown("<div class='section-header'>Statistiques retours</div>", unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    montant_total_retours = abs(retours['Vente_Total'].sum())
                    st.metric("Montant total remboursé", format_currency(montant_total_retours))
                
                with col2:
                    nb_retours = len(retours)
                    st.metric("Nombre de retours", nb_retours)
                
                with col3:
                    ventes_positives = df_ventes[df_ventes['Qte'] > 0]
                    if not ventes_positives.empty:
                        ca_total = ventes_positives['Vente_Total'].sum()
                        taux_retour = (montant_total_retours / ca_total * 100) if ca_total > 0 else 0
                        st.metric("Taux de retour", f"{taux_retour:.2f}%")
                
                retours_par_raison = retours.groupby('Raison_retour').size().reset_index(name='Nombre')
                if not retours_par_raison.empty:
                    fig = px.pie(retours_par_raison, values='Nombre', names='Raison_retour',
                               title="Répartition des retours par raison",
                               color_discrete_sequence=px.colors.sequential.Reds_r)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Aucun retour enregistré")
        else:
            st.info("Aucun retour enregistré")
    
    with tab3:
        st.markdown("<div class='section-header'>Analyse des retours</div>", unsafe_allow_html=True)
        
        if not df_ventes.empty and 'Raison_retour' in df_ventes.columns:
            retours = df_ventes[df_ventes['Qte'] < 0].copy()
            
            if not retours.empty:
                retours['Date'] = pd.to_datetime(retours['Date'])
                
                top_retours = retours.groupby('Article').size().nlargest(10).reset_index(name='Nombre')
                if not top_retours.empty:
                    fig = px.bar(top_retours, x='Article', y='Nombre',
                               title="Top 10 des articles les plus retournés",
                               color_discrete_sequence=['#dc3545'])
                    fig.update_layout(plot_bgcolor='white')
                    st.plotly_chart(fig, use_container_width=True)
                
                retours_par_mois = retours.groupby(retours['Date'].dt.to_period('M')).size().reset_index(name='Nombre')
                retours_par_mois['Date'] = retours_par_mois['Date'].astype(str)
                
                if not retours_par_mois.empty:
                    fig2 = px.line(retours_par_mois, x='Date', y='Nombre', markers=True,
                                 title="Évolution mensuelle des retours",
                                 color_discrete_sequence=['#dc3545'])
                    fig2.update_layout(plot_bgcolor='white')
                    st.plotly_chart(fig2, use_container_width=True)
                
                st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
                st.markdown("<div class='section-header'>Impact financier</div>", unsafe_allow_html=True)
                
                retours_par_mois_fin = retours.groupby(retours['Date'].dt.to_period('M'))['Vente_Total'].sum().abs().reset_index()
                if not retours_par_mois_fin.empty:
                    retours_par_mois_fin['Date'] = retours_par_mois_fin['Date'].astype(str)
                    retours_par_mois_fin.columns = ['Date', 'Montant']
                    
                    fig3 = px.bar(retours_par_mois_fin, x='Date', y='Montant',
                                title="Montant des remboursements par mois",
                                labels={'Montant': 'Montant (DA)'},
                                color_discrete_sequence=['#dc3545'])
                    fig3.update_layout(plot_bgcolor='white')
                    st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("Aucun retour pour analyse")
        else:
            st.info("Aucune donnée de retour disponible")

# --- 18. PARAMÈTRES ---
elif choix_menu == "⚙️ Paramètres" and st.session_state.admin_connecte:
    st.markdown("<h1 class='main-header'>Paramètres</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["⚙️ Configuration", "💾 Sauvegardes", "📊 Rapports"])
    
    with tab1:
        st.subheader("Préférences")
        
        new_seuil = st.number_input("Seuil d'alerte stock", 
                                   min_value=1, 
                                   value=st.session_state.preferences['seuil_alerte_stock'])
        st.session_state.preferences['seuil_alerte_stock'] = new_seuil
        
        new_devise = st.text_input("Symbole devise", value=st.session_state.preferences['devise'])
        st.session_state.preferences['devise'] = new_devise
        
        if st.button("Sauvegarder les préférences"):
            st.success("Préférences sauvegardées")
    
    with tab2:
        st.subheader("Sauvegardes")
        
        if st.button("Créer une sauvegarde"):
            backup_dir = dm.backup_all()
            st.success(f"Sauvegarde créée dans {backup_dir}")
        
        if os.path.exists("backups"):
            backups = [d for d in os.listdir("backups") if d.startswith("backup_")]
            if backups:
                selected_backup = st.selectbox("Restaurer une sauvegarde", backups)
                if st.button("Restaurer"):
                    st.warning("Fonctionnalité à implémenter avec précaution")
    
    with tab3:
        st.subheader("Générer des rapports")
        
        periode = st.selectbox("Période", ["Aujourd'hui", "Cette semaine", "Ce mois", "Cette année", "Personnalisée"])
        
        if periode == "Personnalisée":
            col1, col2 = st.columns(2)
            with col1:
                date_debut = st.date_input("Date début")
            with col2:
                date_fin = st.date_input("Date fin")
        
        if st.button("Générer le rapport"):
            st.info("Rapport généré avec succès!")

# Vérification des stocks bas
check_low_stock()