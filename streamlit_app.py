import streamlit as st
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
import re
import yfinance as yf
import time

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
    analyse_finale,
    description_action,
)

from Analyse_Technique.Analyse_technique import (
    telecharger_donnees, calculer_indicateurs, detecter_niveaux,
    trouver_intervalles_pertinents, calculer_ath, tracer_graphique,
    tracer_macd_rsi, analyse_macd, analyse_rsi, analyse_sma, analyse_niveaux
)

from Analyse_secteur.analyse_secteur import (
    secteurs_acteurs, obtenir_acteurs_principaux, tracer_pie_chart, comp_5, tracer_comp_5,
      calcul_indice_synthetique_et_sp500, tracer_indice_synthetique_vs_sp500, description_marche
)

from Rapport.sentiment import (create_bucket_if_not_exists, get_latest_10k_report, s3_upload, analyze_sentiment, 
                               save_sentiment_to_file, create_gauge)

from News.socialmedia import (fetch_reddit_posts, analyze_topics_all_posts, create_gauge2)

from Analyse_Financiere.auto_analyse_financiere import (get_financial_data_auto, interpret_financial_data_to_file, plot_optimized_financial_data)

st.set_page_config(layout="wide")

st.title("Equipe4 - Dashbaord for Financial Analysis")
# Choix entre action et secteur
analyse_choix = st.radio("What would you like to analyse ?", ("Action", "Sector"))

if analyse_choix == "Action":
    # Si l'utilisateur choisit "Action", afficher une boîte de texte pour entrer le ticker
    ticker = st.text_input("Enter the ticker of the company (ex : AAPL) :")
    
    if st.button("Generate Analysis", key="generate_analysis_action"):
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
                st.table(description_action(ticker))
                st.subheader("Margin Table and Financial Data")
                st.table(marges_df)


                st.write(analyse_finale(marge_brute, marge_ope, marge_benef, ebitda, benefice_net, dette_nette, bfr, ratio_liquidite, ratio_dette_ebitda))

                # Afficher les graphiques en Chandeliers avec Supports et Résistances
                col1, col2 = st.columns([3, 2], vertical_alignment = "top")  # Create two columns

                # Graphique en Chandeliers dans la première colonne
                with col1:
                    st.subheader("Candlestick Chart with Supports and Resistances")
                    fig_candle = tracer_graphique(data, top_supports, top_resistances, ath_price)
                    st.pyplot(fig_candle)

                    st.subheader("MACD and RSI indicators")
                    fig_macd_rsi = tracer_macd_rsi(data)
                    st.pyplot(fig_macd_rsi)

                    # Plot fig_auto here in col1 if it is generated
                    try:
                        filename = f"{ticker}_financial_auto_analysis.txt"
                        marges_df, chiffre_affaires, ebitda, benefice_net, dette_nette, ratio_liquidite, ratio_dette_ebitda = get_financial_data_auto(ticker)
                        
                        # Enregistrer l'analyse dans un fichier texte
                        interpret_financial_data_to_file(filename, chiffre_affaires, ebitda, benefice_net, dette_nette, ratio_liquidite, ratio_dette_ebitda)
                        fig_auto = plot_optimized_financial_data(marges_df)
                        
                        st.pyplot(fig_auto)
                    except Exception as e:
                        st.error(f"Error generating financial data plot: {str(e)}")

                # Afficher les indicateurs MACD et RSI dans la deuxième colonne
                with col2:
                    # Lire le contenu du fichier
                    try:
                        with open(filename, "r", encoding="utf-8") as file:
                            content3 = file.read()

                        # Afficher le contenu dans une zone de texte
                        st.subheader("Analysis")
                        st.markdown(content3, unsafe_allow_html=True)
                    except FileNotFoundError:
                        st.warning("Financial analysis file not found.")

                data = yf.Ticker(ticker).info
                # Extract governance information

                data = yf.Ticker(ticker).info
                governance_list = [
                            {
                                "Name": officer.get("name"),
                                "Position": officer.get("title"),
                                "Age": officer.get("age"),
                                "Total Compensation per year": f"${officer.get('totalPay', 0):,.2f}" if officer.get("totalPay") else "N/A",
                            }
                            for officer in data.get("companyOfficers", [])
                ]

                # Display the list of executives in a table format
                st.subheader("Executive Team")
                if governance_list: 
                    governance_df = pd.DataFrame(governance_list)
                    st.dataframe(governance_df)
                else:
                    st.write("No executive information available.")

                get_latest_10k_report(ticker)

                file_path = f"{ticker}_sentiment_analysis.txt" 

                # Lire le contenu du fichier
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                    match = re.search(r"3\. Sentiment Score: (\d+)", content)
                if match:
                    score = int(match.group(1))  # Convertir le nombre en float

                # Afficher le contenu dans une zone de texte
                st.subheader("Sentiments in 10K:")
                st.markdown(content, unsafe_allow_html=True)
                gauge_fig = create_gauge(score)
                st.plotly_chart(gauge_fig, use_container_width=True)

                reddit_posts_df = fetch_reddit_posts(ticker)

                topics_results = analyze_topics_all_posts(ticker, reddit_posts_df)

                file_path_2 = f"{ticker}_social_analysis.txt" 

                # Lire le contenu du fichier
                with open(file_path_2, "r", encoding="utf-8") as file:
                    content2 = file.read()
                    match = re.search(r"\ Average Sentiment Score: (\d+)", content2)
                if match:
                    score2 = int(match.group(1))

                # Afficher le contenu dans une zone de texte
                st.subheader("Sentiments In Social Media:")
                st.markdown(content2, unsafe_allow_html=True)

                gauge_fig2 = create_gauge2(score2)
                st.plotly_chart(gauge_fig2, use_container_width=True)
  
            
            except ValueError as e:
                st.error(f"Erreur lors de la récupération des données : {str(e)}")

elif analyse_choix == "Sector":
    # Afficher une liste déroulante pour sélectionner le secteur
    secteur_choisi = st.selectbox("Choose a financial sector :", list(secteurs_acteurs.keys()))
    
    if st.button("Analyze Sector", key="generate_analysis_secteur"):
        filtered_df, others_table = obtenir_acteurs_principaux(secteur_choisi)
        
        if isinstance(filtered_df, pd.DataFrame) and not filtered_df.empty:
            st.write(f"### Sector analysis {secteur_choisi.capitalize()}")
            ticker_representatif = secteurs_acteurs.get(secteur_choisi)
            entreprise = yf.Ticker(ticker_representatif)
            sec = entreprise.info['sectorKey']
            overview = description_marche(sec)
            st.table(overview)

            # Disposition des éléments en deux colonnes avec une proportion 3/4 pour le graphique et 1/4 pour le tableau
            left_space, col1, col2, right_space = st.columns([1, 3, 2, 0.5], vertical_alignment = "top", gap="small")  # Colonne 1 pour le graphique et colonne 2 pour le tableau
            
            # Graphique en camembert dans la première colonne
            with col1:
                st.write(f'### Market Weight of Key Companies in the Sector {secteur_choisi.capitalize()}')
                # Calcul de la hauteur en fonction de la longueur du tableau
                height = max(5, 0.5 * len(filtered_df))  
                fig, ax = plt.subplots(figsize=(10, height))
                ax.pie(filtered_df['Market weight (%)'], labels=filtered_df['Company'], autopct='%1.1f%%', startangle=140)
                
                # Affichage dans Streamlit
                st.pyplot(fig, use_container_width=True)

            # Tableau "Autres" dans la deuxième colonne
            with col2:
                # Réduire la taille du tableau en utilisant le style de Streamlit
                st.markdown("### Others")
                st.dataframe(others_table, height=int(height * 130))

            col3, col4, col5 = st.columns([1, 3, 1], vertical_alignment = "top", gap="small")
            # Graphique comparaison 5 plus grandes companies
            with col4:

                st.write(f'#### Comparison of cumulative returns (%) of the synthetic sector index {sec} and the S&P 500')
                synthetic_index_cumulative_returns_percentage, sp500_cumulative_returns_percentage, secteur = calcul_indice_synthetique_et_sp500(secteur_choisi)
                fig_comp_tot = tracer_indice_synthetique_vs_sp500(synthetic_index_cumulative_returns_percentage, sp500_cumulative_returns_percentage, secteur)
                st.pyplot(fig_comp_tot)

                st.write(f'#### Comparison of cumulative returns (%) of the main company and the 5 largest players in the sector {secteur}')
                top_5_symbols,cumulative_returns_percentage, secteur = comp_5(secteur_choisi)
                fig_comp_5 = tracer_comp_5(top_5_symbols,cumulative_returns_percentage, secteur)
                st.pyplot(fig_comp_5)


        else:
            st.warning(f"No data available for this sector : {secteur_choisi}.")