import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd

# Définir le symbole de l'entreprise
symbol = 'AIR'
entreprise = yf.Ticker(symbol)

# Récupérer les informations financières
info = entreprise.info
historique = entreprise.history(period='1y')
bilan = entreprise.balance_sheet
compte_de_resultat = entreprise.financials
flux_de_tresorerie = entreprise.cashflow

# Tracer l'EBITDA
def plot_financial_metric(dates, values, title, ylabel):
    plt.figure(figsize=(10, 6))
    plt.plot(dates, values, marker='o', linestyle='-', color='b')
    plt.title(title)
    plt.xlabel('Année')
    plt.ylabel(ylabel)
    plt.xticks(rotation=45)
    plt.grid()
    plt.tight_layout()
    plt.show()

dates = compte_de_resultat.columns
plot_financial_metric(dates, compte_de_resultat.loc['EBITDA'].values, "Évolution de l'EBITDA", "EBITDA (en milliards)")

# Tracer le Gross Profit Margin
GPM = (compte_de_resultat.loc['Gross Profit'] / compte_de_resultat.loc['Total Revenue']) * 100
plot_financial_metric(dates, GPM, "Évolution du Gross Profit Margin", "GPM %")

# Extraction du secteur et des entreprises clés
secteur = info['sector'].lower()
sector = yf.Sector(secteur)
top_companies = sector.top_companies
print(secteur)

# Convertir les poids de marché en DataFrame
weights_df = pd.DataFrame({
    'Entreprise': top_companies.index,
    'Poids de Marché (%)': top_companies['market weight']
})

# Regroupement des entreprises avec moins de 1%
threshold = 0.010
others_mask = weights_df['Poids de Marché (%)'] < threshold
others_weight = weights_df.loc[others_mask, 'Poids de Marché (%)'].sum()

# Créer un DataFrame pour les "Autres"
others_table = weights_df[others_mask]
if not others_table.empty:
    others_table = others_table[['Entreprise', 'Poids de Marché (%)']]
    print(others_table)

# Filtrer les entreprises ayant plus de 1%
filtered_df = weights_df[~others_mask].copy()
filtered_df.loc[len(filtered_df)] = ['Autres', others_weight]  # Ajouter la ligne "Autres"

# Vérification de la longueur des données et affichage du diagramme en secteurs
if not filtered_df.empty:
    plt.figure(figsize=(10, 8))
    plt.pie(filtered_df['Poids de Marché (%)'], labels=filtered_df['Entreprise'], autopct='%1.1f%%', startangle=140)
    plt.title(f'Poids de Marché des Entreprises Clés dans le Secteur {secteur.capitalize()}')
    plt.axis('equal')
    plt.show()
else:
    print("Erreur : Le DataFrame est vide.")