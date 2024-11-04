import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd

# Dictionnaire de départ : une seule entreprise par secteur
secteurs_acteurs = {
    "Technology": "AAPL",
    "Healthcare": "JNJ",
    "Financial services": "JPM",
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
        secteur = entreprise.info['sectorKey']
        sector = yf.Sector(secteur)
        top_companies = sector.top_companies    

        # Convertir les poids de marché en DataFrame
        weights_df = pd.DataFrame({
            'Company': top_companies.index,
            'Market weight (%)': top_companies['market weight']
        })

        ## Regroupement des entreprises avec moins de 1%
        threshold = 0.012
        others_mask = weights_df['Market weight (%)'] < threshold
        others_weight = weights_df.loc[others_mask, 'Market weight (%)'].sum()

        # Créer un DataFrame pour les "Autres"
        others_table = weights_df[others_mask]
        if not others_table.empty:
            others_table = others_table[['Market weight (%)']] * 100 

        # Filtrer les entreprises ayant plus de 1%
        filtered_df = weights_df[~others_mask].copy()
        filtered_df.loc[len(filtered_df)] = ['Others', others_weight]  # Ajouter la ligne "Autres"

        return filtered_df, others_table
    
    except Exception as e:
        print(f"Erreur lors de la récupération des données pour {nom_secteur} : {e}")
        return None, None

# Fonction pour tracer le graphique des parts de marché
def tracer_pie_chart(filtered_df, secteur):
    if not filtered_df.empty:
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.pie(filtered_df['Market weight (%)'], labels=filtered_df['Company'], autopct='%1.1f%%', startangle=140)
        ax.set_title(f'Market Weight of Key Companies in the Sector{secteur.capitalize()}')
        plt.axis('equal')
        return fig
    else:
        print("Erreur : Le DataFrame est vide.")
        return None

# Utiliser les fonctions pour le secteur "Technologie"
filtered_df, others_table = obtenir_acteurs_principaux('Technology')
if filtered_df is not None:
    fig = tracer_pie_chart(filtered_df, "Technology")
    if fig:
        plt.show()  # Afficher le graphique si on est en local, sinon utiliser st.pyplot(fig) dans Streamlit

# Sélection des 5 plus grandes entreprises par poids de marché

def comp_5(nom_secteur):
    ticker_representatif = secteurs_acteurs.get(nom_secteur)

    entreprise = yf.Ticker(ticker_representatif)

    secteur = entreprise.info['sectorKey']
    sector = yf.Sector(secteur)
    top_companies = sector.top_companies

    top_5_companies = top_companies.head(5)
    top_5_symbols = top_5_companies.index.tolist()

    # Télécharger les données boursières pour les tickers sélectionnés
    data = yf.download(top_5_symbols, start="2020-01-01", end="2023-01-01")['Adj Close']

    # Calcul des rendements quotidiens et cumulés en pourcentage
    daily_returns = data.pct_change()
    cumulative_returns = (1 + daily_returns).cumprod() - 1
    cumulative_returns_percentage = cumulative_returns * 100

    return top_5_symbols,cumulative_returns_percentage, secteur

# Affichage
def tracer_comp_5(top_5_symbols, cumulative_returns_percentage, secteur):
    fig, ax = plt.subplots(figsize=(14, 7))  # Création de la figure et des axes
    for ticker in top_5_symbols:
        ax.plot(cumulative_returns_percentage[ticker], label=ticker)  # Tracé sur l'axe spécifié
    ax.set_xlabel('Date')
    ax.set_ylabel('Cumulative return (%)')
    ax.legend()
    return fig  # Retourne la figure pour un affichage sécurisé avec Streamlit


def calcul_indice_synthetique_et_sp500(nom_secteur):
    # Obtenir le ticker représentatif du secteur
    ticker_representatif = secteurs_acteurs.get(nom_secteur)
    if not ticker_representatif:
        print("Sector not available.")
        return None, None

    try:
        # Récupérer les informations de l'entreprise représentative
        entreprise = yf.Ticker(ticker_representatif)
        secteur = entreprise.info['sectorKey']
        sector = yf.Sector(secteur)
        top_companies = sector.top_companies

        # Sélectionner les 20 plus grandes entreprises par poids de marché
        top_20_companies = top_companies.sort_values(by='market weight', ascending=False).head(20)
        top_20_symbols = top_20_companies.index.tolist()  # Symboles des entreprises

        # Télécharger les données boursières ajustées pour ces entreprises et le S&P 500
        all_symbols = top_20_symbols + ["^GSPC"]  # Inclure le S&P 500
        data = yf.download(all_symbols, start="2020-01-01", end="2023-01-01")['Adj Close']
        
        # Calcul des rendements quotidiens
        daily_returns = data.pct_change()

        # Normalisation des poids de marché (somme = 1)
        market_weights = top_20_companies['market weight']
        market_weights_normalized = market_weights / market_weights.sum()

        # Calcul des rendements quotidiens de l'indice synthétique pondéré
        synthetic_index_daily_returns = (daily_returns[top_20_symbols] * market_weights_normalized.values).sum(axis=1)

        # Calcul des rendements cumulés pour l'indice synthétique et le S&P 500
        synthetic_index_cumulative_returns = (1 + synthetic_index_daily_returns).cumprod() - 1
        sp500_cumulative_returns = (1 + daily_returns["^GSPC"]).cumprod() - 1

        # Conversion en pourcentage pour interprétation plus claire
        synthetic_index_cumulative_returns_percentage = synthetic_index_cumulative_returns * 100
        sp500_cumulative_returns_percentage = sp500_cumulative_returns * 100

        return synthetic_index_cumulative_returns_percentage, sp500_cumulative_returns_percentage, secteur
    
    except Exception as e:
        print(f"Error retrieving data for {nom_secteur} : {e}")
        return None, None

# Affichage

def tracer_indice_synthetique_vs_sp500(synthetic_index, sp500_index, secteur):
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.plot(synthetic_index, label=f'Synthetic Sector Index{secteur.capitalize()}')
    ax.plot(sp500_index, label='S&P 500')
    ax.set_xlabel('Date')
    ax.set_ylabel('Cumulative return (%)')
    ax.legend()
    return fig  # Retourne la figure pour pouvoir l'utiliser dans st.pyplot()

def description_marche(nom_secteur):

    tech = yf.Sector(nom_secteur)
    overview = tech.overview
    # Création du tableau avec les données
    data = {
        'Description': [overview['description']],
        'Market capitalization (in €M)': [overview['market_cap'] * 1e-6],
        "Number of companies": [overview['companies_count']],
        'Market weight (%)': [overview['market_weight'] * 100]
    }
    
    # Conversion en DataFrame
    df = pd.DataFrame(data)
    return df
    
print(description_marche('technology'))