# app.py

import streamlit as st
import matplotlib.pyplot as plt
import mplfinance as mpf
import plotly.graph_objects as go
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
    analyse_finale
)
from Analyse_Technique.Analyse_technique import (get_data, calculate_indicators, detect_support_resistance,
                      find_most_frequent_intervals, analyse_rsi, analyse_macd,
                      analyse_trend, analyse_levels)

from Rapport.sentiment import (create_bucket_if_not_exists, get_latest_10k_report, s3_upload, analyze_sentiment, save_sentiment_to_file, create_gauge)

st.title("Tableau de Bord d'Analyse Financière et Technique")

ticker = st.text_input("Entrez le symbole boursier de l'entreprise :")

if st.button("Générer l'Analyse"):
    data = yf.Ticker(ticker).info

    # Extraire la liste des responsables de gouvernance
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


    # Récupérer les données financières
    marges_df, marge_brute, marge_ope, marge_benef, ebitda, benefice_net, dette_nette = get_financial_data(ticker)

    st.subheader("Tableau des Marges et Données Financières")
    st.table(marges_df)

    st.subheader("Analyse des Marges et Performance Financière")
    st.write("**Marge Brute (%) :**", analyse_marge_brute(marge_brute)[0])
    st.write("**Marge Opérationnelle (%) :**", analyse_marge_operationnelle(marge_ope)[0])
    st.write("**Marge Bénéficiaire (%) :**", analyse_marge_beneficiaire(marge_benef)[0])
    st.write("**EBITDA :**", analyse_ebitda(ebitda)[0])
    st.write("**Résultat Net :**", analyse_resultat_net(benefice_net)[0])
    st.write("**Dette Nette :**", analyse_dette_nette(dette_nette)[0])

    # Conclusion finale
    st.subheader("Conclusion")
    analyses = [
        analyse_marge_brute(marge_brute)[1],
        analyse_marge_operationnelle(marge_ope)[1],
        analyse_marge_beneficiaire(marge_benef)[1],
        analyse_ebitda(ebitda)[1],
        analyse_resultat_net(benefice_net)[1],
        analyse_dette_nette(dette_nette)[1]
    ]
    st.write(analyse_finale(marge_brute, marge_ope, marge_benef, ebitda, benefice_net, dette_nette))

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


