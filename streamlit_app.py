import streamlit as st
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
import re
import yfinance as yf

from Analyse_Financiere.Analyse_financiere import (
    get_financial_data,
    analyse_marge_brute,
    analyse_marge_operationnelle,
    analyse_marge_beneficiaire,
    analyse_ebitda,
    analyse_resultat_net,
    analyse_dette_nette,
    analyse_bfr,
    analyse_ratio_liquidite,
    analyse_dette_ebitda,
    analyse_finale
)

from Analyse_Technique.Analyse_technique import (
    telecharger_donnees, calculer_indicateurs, detecter_niveaux,
    trouver_intervalles_pertinents, calculer_ath, tracer_graphique,
    tracer_macd_rsi, analyse_macd, analyse_rsi, analyse_sma, analyse_niveaux
)

from Analyse_secteur.analyse_secteur import (
    secteurs_acteurs, obtenir_acteurs_principaux, tracer_pie_chart
)

from Rapport.sentiment import (create_bucket_if_not_exists, get_latest_10k_report, s3_upload, analyze_sentiment, 
                               save_sentiment_to_file, create_gauge)

st.title("Tableau de Bord d'Analyse Financière et Technique")
# Choix entre action et secteur
analyse_choix = st.radio("Que souhaitez-vous analyser ?", ("Action", "Secteur"))

if analyse_choix == "Action":
    # Si l'utilisateur choisit "Action", afficher une boîte de texte pour entrer le ticker
    ticker = st.text_input("Entrez le symbole boursier de l'entreprise :")
    
    if st.button("Générer l'Analyse pour l'Action", key="generate_analysis_action"):
        if not ticker:
            st.error("Veuillez entrer un symbole boursier valide.")
        else:
            # Analyse financière et technique pour le ticker
            try:
                data = telecharger_donnees(ticker)

                # Calcul des indicateurs techniques
                data = calculer_indicateurs(data)
                supports, resistances = detecter_niveaux(data)
                top_supports = trouver_intervalles_pertinents(supports, data['Close'].iloc[-1])
                top_resistances = trouver_intervalles_pertinents(resistances, data['Close'].iloc[-1])
                ath_price = calculer_ath(data)

                # Récupérer les données financières
                marges_df, marge_brute, marge_ope, marge_benef, ebitda, benefice_net, dette_nette, bfr, ratio_liquidite, ratio_dette_ebitda = get_financial_data(ticker)

                # Afficher le tableau financier
                st.subheader("Tableau des Marges et Données Financières")
                st.table(marges_df)

                # Afficher l'analyse des marges et performance financière
                st.subheader("Analyse des Marges et Performance Financière")
                st.write("**Marge Brute (%) :**", analyse_marge_brute(marge_brute)[0])
                st.write("**Marge Opérationnelle (%) :**", analyse_marge_operationnelle(marge_ope)[0])
                st.write("**Marge Bénéficiaire (%) :**", analyse_marge_beneficiaire(marge_benef)[0])
                st.write("**EBITDA :**", analyse_ebitda(ebitda)[0])
                st.write("**Résultat Net :**", analyse_resultat_net(benefice_net)[0])
                st.write("**Dette Nette :**", analyse_dette_nette(dette_nette)[0])
                st.write("**Besoin en Fonds de Roulement :**", analyse_bfr(bfr)[0])
                st.write("**Ratio Dette/EBITDA :**", analyse_dette_ebitda(ratio_dette_ebitda)[0])
                st.write("**Ratio de liquidité :**", analyse_ratio_liquidite(ratio_liquidite)[0])

                # Conclusion finale
                st.subheader("Conclusion")
                st.write(analyse_finale(marge_brute, marge_ope, marge_benef, ebitda, benefice_net, dette_nette, bfr, ratio_liquidite, ratio_dette_ebitda))

                # Afficher les graphiques en Chandeliers avec Supports et Résistances
                st.subheader("Graphique en Chandeliers avec Supports et Résistances")
                fig_candle = tracer_graphique(data, top_supports, top_resistances, ath_price)
                st.pyplot(fig_candle)

                # Afficher les indicateurs MACD et RSI
                st.subheader("Indicateurs MACD et RSI")
                fig_macd_rsi = tracer_macd_rsi(data)
                st.pyplot(fig_macd_rsi)

                # Afficher les analyses techniques
                st.subheader("Analyse Technique")
                st.write("**RSI :**", analyse_rsi(data))
                st.write("**MACD :**", analyse_macd(data))
                st.write("**Tendance SMA 50 :**", analyse_sma(data))
                st.write("**Niveaux de Support et Résistance :**", analyse_niveaux(data, supports + resistances))

                # Extraire la liste des responsables de gouvernance
                data = yf.Ticker(ticker).info
                # Extract governance information
                governance_list = [
                    {
                        "Name": officer.get("name"),
                        "Position": officer.get("title"),
                        "Age": officer.get("age"),
                        "Total Compensation per year": f"${officer.get('totalPay', 0):,.2f}" if officer.get("totalPay") else "N/A",
                    }
                    for officer in data.get("companyOfficers", [])
                ]

                # Display the list of executives
                st.subheader("Executive Team")
                for officer in governance_list:
                    st.write(f"**Name**: {officer['Name']}")
                    st.write(f"**Position**: {officer['Position']}")
                    st.write(f"**Age**: {officer['Age']}")
                    st.write(f"**Total Compensation**: {officer['Total Compensation per year']}")
                    st.write("---")  # Separator between executives

                get_latest_10k_report(ticker)

                file_path = f"{ticker}_sentiment_analysis.txt" 

                # Lire le contenu du fichier
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    match = re.search(r"3\. Sentiment Score: (\d+\.\d+)", content)
                if match:
                    score = float(match.group(1))  # Convertir le nombre en float

                # Afficher le contenu dans une zone de texte
                st.text_area("Contenu du fichier :", content, height=300)
                gauge_fig = create_gauge(score)
                st.plotly_chart(gauge_fig, use_container_width=True)

            except ValueError as e:
                st.error(f"Erreur lors de la récupération des données : {str(e)}")

elif analyse_choix == "Secteur":
    # Afficher une liste déroulante pour sélectionner le secteur
    secteur_choisi = st.selectbox("Choisissez un secteur financier :", list(secteurs_acteurs.keys()))
    
    if st.button("Analyser le Secteur", key="generate_analysis_secteur"):
        filtered_df, others_table = obtenir_acteurs_principaux(secteur_choisi)
        
        if isinstance(filtered_df, pd.DataFrame) and not filtered_df.empty:
            st.write(f"### Analyse du secteur {secteur_choisi.capitalize()}")

            # Disposition des éléments en deux colonnes avec une proportion 3/4 pour le graphique et 1/4 pour le tableau
            col1, col2 = st.columns([3, 1])  # Colonne 1 pour le graphique et colonne 2 pour le tableau
            
            # Graphique en camembert dans la première colonne
            with col1:
                # Calcul de la hauteur en fonction de la longueur du tableau
                height = max(5, 0.5 * len(filtered_df))  
                fig, ax = plt.subplots(figsize=(10, height))
                ax.pie(filtered_df['Poids de Marché (%)'], labels=filtered_df['Entreprise'], autopct='%1.1f%%', startangle=140)
                ax.set_title(f'Poids de Marché des Entreprises Clés dans le Secteur {secteur_choisi.capitalize()}')
                
                # Affichage dans Streamlit
                st.pyplot(fig, use_container_width=True)

            # Tableau "Autres" dans la deuxième colonne
            with col2:
                # Réduire la taille du tableau en utilisant le style de Streamlit
                st.markdown("### Autres")
                st.dataframe(others_table.style.set_table_attributes("style='font-size:80%'"))
        else:
            st.warning(f"Aucune donnée disponible pour le secteur {secteur_choisi}.")