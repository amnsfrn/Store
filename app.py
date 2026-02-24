# --- 1. ONGLET CAISSE ---
with tabs[0]:
    st.subheader("🛒 Terminal de Vente")
    if df_stock.empty:
        st.info("Le stock est vide. Ajoutez des articles pour commencer.")
    else:
        # La liste est triée. Vous pouvez cliquer et TAPER DIRECTEMENT le nom.
        liste_art = sorted(df_stock["Article"].unique().tolist())
        
        # Le label invite explicitement à taper au clavier
        choix = st.selectbox(
            "🔍 Cliquez ici et tapez le nom de l'article :", 
            [""] + liste_art,
            help="Tapez les premières lettres pour filtrer la liste"
        )
        
        if choix != "":
            info = df_stock[df_stock["Article"] == choix].iloc[0]
            with st.form("form_vente_final", clear_on_submit=True):
                st.markdown(f"### 📦 {choix}")
                st.write(f"Quantité disponible : **{int(info['Quantite'])}**")
                
                col1, col2 = st.columns(2)
                # Prix de vente par défaut affiché, mais modifiable au clavier
                p_v = col1.number_input("Prix de vente (DA)", value=float(info['PV']), step=50.0)
                # Quantité à vendre
                q_v = col2.number_input("Quantité", min_value=1, max_value=int(info['Quantite']), step=1)
                
                if st.form_submit_button("✅ VALIDER LA VENTE"):
                    # Calcul automatique du bénéfice
                    benef = q_v * (p_v - (info['PA'] + info['Frais']))
                    
                    # Enregistrement
                    new_v = pd.DataFrame([[datetime.now().date(), choix, q_v, q_v*p_v, benef]], columns=df_ventes.columns)
                    df_ventes = pd.concat([df_ventes, new_v], ignore_index=True)
                    
                    # Mise à jour du stock
                    df_stock.loc[df_stock["Article"] == choix, "Quantite"] -= q_v
                    
                    save_data(df_ventes, "ventes.csv")
                    save_data(df_stock, "stock.csv")
                    
                    st.success(f"Vendu : {q_v} x {choix}")
                    st.rerun()
