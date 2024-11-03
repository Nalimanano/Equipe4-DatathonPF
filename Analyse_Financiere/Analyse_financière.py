import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# Function to get company data from yfinance
def get_company_data(symbol):
    entreprise = yf.Ticker(symbol)
    info = entreprise.info
    historique = entreprise.history(period='1y')
    bilan = entreprise.balance_sheet
    compte_de_resultat = entreprise.financials
    flux_de_tresorerie = entreprise.cashflow
    return info, historique, bilan, compte_de_resultat, flux_de_tresorerie

# Plotting function for financial metrics
def plot_financial_metric(dates, values, title, ylabel):
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(dates, values, marker='o', linestyle='-', color='b')
    ax.set_title(title)
    ax.set_xlabel('Année')
    ax.set_ylabel(ylabel)
    ax.tick_params(axis='x', rotation=45)
    ax.grid()
    return fig  # Return the figure instead of using st.pyplot here

# Function to get Gross Profit Margin
def calculate_gross_profit_margin(compte_de_resultat):
    GPM = (compte_de_resultat.loc['Gross Profit'] / compte_de_resultat.loc['Total Revenue']) * 100
    return GPM

# Function to display sector data
def display_sector_info(info):
    secteur = info['sector'].lower()
    return secteur  # Return the sector instead of printing it

# Function to plot market weights
def plot_market_weights(top_companies):
    weights_df = pd.DataFrame({
        'Entreprise': top_companies.index,
        'Poids de Marché (%)': top_companies['market weight']
    })

    threshold = 0.010
    others_mask = weights_df['Poids de Marché (%)'] < threshold
    others_weight = weights_df.loc[others_mask, 'Poids de Marché (%)'].sum()

    filtered_df = weights_df[~others_mask].copy()
    filtered_df.loc[len(filtered_df)] = ['Autres', others_weight]

    if not filtered_df.empty:
        fig, ax = plt.subplots(figsize=(10, 8))
        ax.pie(filtered_df['Poids de Marché (%)'], labels=filtered_df['Entreprise'], autopct='%1.1f%%', startangle=140)
        ax.set_title('Poids de Marché des Entreprises Clés')
        ax.axis('equal')
        return fig  # Return the figure instead of using st.pyplot here
    else:
        return None  # Return None if DataFrame is empty
