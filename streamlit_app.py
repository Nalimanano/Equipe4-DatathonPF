# app.py

import streamlit as st
import matplotlib.pyplot as plt
import mplfinance as mpf
import plotly.graph_objects as go


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

st.title("Tableau de Bord d'Analyse Financière et Technique")

ticker = st.text_input("Entrez le symbole boursier de l'entreprise :")

if st.button("Générer l'Analyse"):
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

data = get_data(ticker)
data = calculate_indicators(data)

# Indicateurs et niveaux
levels = detect_support_resistance(data)
current_price = data['Close'].iloc[-1]
top_resistances = find_most_frequent_intervals([lvl for lvl in levels if lvl > current_price], current_price)
top_supports = find_most_frequent_intervals([lvl for lvl in levels if lvl < current_price], current_price)

# Analyse
st.subheader("Analyse RSI")
st.write(analyse_rsi(data))

st.subheader("Analyse MACD")
st.write(analyse_macd(data))

st.subheader("Analyse de la tendance (SMA 50)")
st.write(analyse_trend(data))

st.subheader("Analyse des niveaux de support et résistance")
closest_level, level_type = analyse_levels(data, levels)
st.write(f"Niveau le plus proche: {closest_level:.2f} ({level_type})")

# Graphique en chandeliers avec Plotly
st.subheader("Graphique en Chandeliers avec SMA 50 et niveaux")
fig = go.Figure()

# Ajouter les bougies
fig.add_trace(go.Candlestick(
    x=data.index,
    open=data['Open'],
    high=data['High'],
    low=data['Low'],
    close=data['Close'],
    name='Candlesticks'
))

# Ajouter la SMA 50
fig.add_trace(go.Scatter(
    x=data.index,
    y=data['Close'].rolling(window=50).mean(),
    mode='lines',
    name='SMA 50',
    line=dict(color='orange', width=1)
))

# Graphique MACD et RSI
st.subheader("Graphique MACD et RSI")
fig_macd_rsi = go.Figure()

# Tracer le MACD
fig_macd_rsi.add_trace(go.Scatter(
    x=data.index,
    y=data['MACD'],
    mode='lines',
    name='MACD',
    line=dict(color='blue')
))

fig_macd_rsi.add_trace(go.Scatter(
    x=data.index,
    y=data['Signal'],
    mode='lines',
    name='Signal',
    line=dict(color='red')
))

# Tracer l'histogramme du MACD avec des couleurs basées sur les valeurs
fig_macd_rsi.add_trace(go.Bar(
    x=data.index,
    y=data['Hist'],
    name='Histogram',
    marker=dict(color=['green' if val >= 0 else 'red' for val in data['Hist']])
))

fig_macd_rsi.update_layout(title='Graphique MACD',
                            xaxis_title='Date',
                            yaxis_title='MACD',
                            yaxis=dict(range=[min(data['MACD'].min(), data['Signal'].min()) - 1, 
                                              max(data['MACD'].max(), data['Signal'].max()) + 1]))

# Tracer le RSI
fig_macd_rsi.add_trace(go.Scatter(
    x=data.index,
    y=data['RSI'],
    mode='lines',
    name='RSI',
    line=dict(color='purple')
))

# Ajouter les lignes de surachat et de survente
fig_macd_rsi.add_shape(type='line', x0=data.index[0], y0=70, x1=data.index[-1], y1=70,
                        line=dict(color='red', width=2, dash='dash'))

fig_macd_rsi.add_shape(type='line', x0=data.index[0], y0=30, x1=data.index[-1], y1=30,
                        line=dict(color='green', width=2, dash='dash'))

fig_macd_rsi.update_layout(title='Graphique MACD et RSI',
                            xaxis_title='Date',
                            yaxis_title='Valeurs')

st.plotly_chart(fig_macd_rsi)
