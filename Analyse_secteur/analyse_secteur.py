import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd

# Dictionnaire de départ : une seule entreprise par secteur
secteurs_acteurs = {
    "Technology": "AAPL",
    "Healthcare": "JNJ",
    "Financial Services": "MA",
    "Energy": "XOM",
    "Industrials": "BA",
    "Consumer Cyclical": "AMZN",
    "Communication Services": "GOOG",
    "Consumer Defensive": "WMT",
    "Basic Materials": "LIN",
    "Real Estate":"PLD",
    "Utilities":"NEE"
}

# Fonction pour obtenir les concurrents majeurs dans un secteur
def obtenir_acteurs_principaux(nom_secteur):
    # Récupérer le ticker d'une entreprise représentative pour ce secteur
    ticker_representatif = secteurs_acteurs.get(nom_secteur)
    if not ticker_representatif:
        print("Secteur non disponible.")
        return None, None
    
    try:
        # Initialiser le ticker de l'entreprise représentative
        entreprise = yf.Ticker(ticker_representatif)
        
        # Obtenir des concurrents clés dans le même secteur
        secteur = entreprise.info['sector'].lower()
        sector = yf.Sector(secteur)
        print(secteur)
        top_companies = sector.top_companies    

        # Convertir les poids de marché en DataFrame
        weights_df = pd.DataFrame({
            'Entreprise': top_companies.index,
            'Poids de Marché (%)': top_companies['market weight']
        })

        ## Regroupement des entreprises avec moins de 1%
        threshold = 0.012
        others_mask = weights_df['Poids de Marché (%)'] < threshold
        others_weight = weights_df.loc[others_mask, 'Poids de Marché (%)'].sum()

        # Créer un DataFrame pour les "Autres"
        others_table = weights_df[others_mask]
        if not others_table.empty:
            others_table = others_table[['Poids de Marché (%)']] * 100 

        # Filtrer les entreprises ayant plus de 1%
        filtered_df = weights_df[~others_mask].copy()
        filtered_df.loc[len(filtered_df)] = ['Autres', others_weight]  # Ajouter la ligne "Autres"

        return filtered_df, others_table
    
    except Exception as e:
        print(f"Erreur lors de la récupération des données pour {nom_secteur} : {e}")
        return None, None

# Fonction pour tracer le graphique des parts de marché
def tracer_pie_chart(filtered_df, secteur):
    if not filtered_df.empty:
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.pie(filtered_df['Poids de Marché (%)'], labels=filtered_df['Entreprise'], autopct='%1.1f%%', startangle=140)
        ax.set_title(f'Poids de Marché des Entreprises Clés dans le Secteur {secteur.capitalize()}')
        plt.axis('equal')
        return fig
    else:
        print("Erreur : Le DataFrame est vide.")
        return None

# Utiliser les fonctions pour le secteur "Technologie"
filtered_df, others_table = obtenir_acteurs_principaux('Technologie')
if filtered_df is not None:
    fig = tracer_pie_chart(filtered_df, 'Technologie')
    if fig:
        plt.show()  # Afficher le graphique si on est en local, sinon utiliser st.pyplot(fig) dans Streamlit
