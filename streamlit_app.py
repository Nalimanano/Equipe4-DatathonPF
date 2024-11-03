import streamlit as st
import matplotlib.pyplot as plt
import mplfinance as mpf

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

st.title("Tableau de Bord d'Analyse Financière et Technique")

# Entrée de texte pour le ticker de l'entreprise
ticker = st.text_input("Entrez le symbole boursier de l'entreprise :")

if st.button("Générer l'Analyse", key="generate_analysis"):

    # Vérifier que le ticker n'est pas vide
    if not ticker:
        st.error("Veuillez entrer un symbole boursier valide.")
    else:
        # Essayer de télécharger les données pour le ticker
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

        except ValueError as e:
            st.error(f"Erreur lors de la récupération des données : {str(e)}")
