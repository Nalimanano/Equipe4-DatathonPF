# Analyse_Technique/analyse_technique.py

import yfinance as yf
import pandas as pd

# Fonction pour récupérer les données financières
def get_financial_data(ticker):
    entreprise = yf.Ticker(ticker)
    compte_de_resultat = entreprise.financials
    bilan = entreprise.balance_sheet

    chiffre_affaires = compte_de_resultat.loc['Total Revenue'][:3] * 1e-6
    ebitda = compte_de_resultat.loc['EBITDA'][:3] * 1e-6
    benefice_brut = compte_de_resultat.loc['Gross Profit'][:3] * 1e-6
    benefice_operationnel = compte_de_resultat.loc['Operating Income'][:3] * 1e-6
    benefice_net = compte_de_resultat.loc['Net Income'][:3] * 1e-6

    dette_totale = bilan.loc['Total Debt'][:3] * 1e-6
    tresorerie = bilan.loc['Cash And Cash Equivalents'][:3] * 1e-6
    dette_nette = dette_totale - tresorerie

    # Calcul du Besoin en Fonds de Roulement (BFR)
    stocks = bilan.loc['Inventory'][:3] * 1e-6  # Conversion en millions
    creances_clients = bilan.loc['Accounts Receivable'][:3] * 1e-6
    dettes_fournisseurs = bilan.loc['Accounts Payable'][:3] * 1e-6
    bfr = stocks + creances_clients - dettes_fournisseurs

    # Calcul des ratios de liquidité et dette/EBITDA
    actifs_circulants = bilan.loc['Total Assets'][:3] * 1e-6
    passifs_circulants = bilan.loc['Total Liabilities Net Minority Interest'][:3] * 1e-6
    ratio_liquidite = actifs_circulants / passifs_circulants
    ratio_dette_ebitda = dette_nette / ebitda

    annees = [str(date.year) for date in chiffre_affaires.index][::-1]

    marge_brute = [(benefice_brut[annee] / chiffre_affaires[annee]) * 100 for annee in chiffre_affaires.index][::-1]
    marge_ope = [(benefice_operationnel[annee] / chiffre_affaires[annee]) * 100 for annee in chiffre_affaires.index][::-1]
    marge_benef = [(benefice_net[annee] / chiffre_affaires[annee]) * 100 for annee in chiffre_affaires.index][::-1]

    marges_df = pd.DataFrame({
        'Année': annees,
        'Chiffre d\'Affaires (millions)': chiffre_affaires.values[::-1],
        'EBITDA (millions)': ebitda.values[::-1],
        'Dette Nette (millions)': dette_nette.values[::-1],
        'BFR (millions)': bfr.values[::-1],
        'Marge Brute (%)': marge_brute,
        'Marge Opérationnelle (%)': marge_ope,
        'Marge Bénéficiaire (%)': marge_benef,
        'Résultat Net (millions)': benefice_net.values[::-1],
        'Ratio de Liquidité': ratio_liquidite.values[::-1],
        'Dette/EBITDA': ratio_dette_ebitda.values[::-1]
    }).set_index('Année').T

    return marges_df, marge_brute, marge_ope, marge_benef, ebitda, benefice_net, dette_nette, bfr, ratio_liquidite, ratio_dette_ebitda

def analyse_marge_brute(marge_brute):
    if marge_brute[2] > marge_brute[1] > marge_brute[0]:
        return "La marge brute a augmenté chaque année, indiquant une gestion de production efficace.", "bon"
    elif marge_brute[2] < marge_brute[1] < marge_brute[0]:
        return "La marge brute a baissé chaque année, ce qui peut indiquer une augmentation des coûts de production.", "mauvais"
    elif marge_brute[2] > marge_brute[1] < marge_brute[0]:
        return "La marge brute a d'abord baissé, puis s'est redressée, ce qui peut indiquer une tentative d'optimisation des coûts de production.", "bon"
    elif marge_brute[2] < marge_brute[1] > marge_brute[0]:
        return "La marge brute a augmenté, puis diminué, ce qui peut suggérer des difficultés à maintenir les gains de rentabilité.", "mauvais"
    else:
        return "La marge brute est restée relativement stable, montrant une constance dans les coûts de production.", "neutre"
 
def analyse_marge_operationnelle(marge_ope):
    if marge_ope[2] > marge_ope[1] > marge_ope[0]:
        return "La marge opérationnelle a augmenté continuellement, suggérant une gestion efficace des coûts opérationnels.", "bon"
    elif marge_ope[2] < marge_ope[1] < marge_ope[0]:
        return "La marge opérationnelle a baissé chaque année, ce qui peut indiquer une augmentation des frais d'exploitation.", "mauvais"
    elif marge_ope[2] > marge_ope[1] < marge_ope[0]:
        return "La marge opérationnelle a d'abord baissé puis s'est redressée, ce qui peut suggérer une reprise d'efficacité dans la gestion des coûts.", "bon"
    elif marge_ope[2] < marge_ope[1] > marge_ope[0]:
        return "La marge opérationnelle a augmenté puis diminué, suggérant une instabilité dans la gestion des coûts opérationnels.", "mauvais"
    else:
        return "La marge opérationnelle est stable, montrant une constance dans la gestion des coûts d'exploitation.", "neutre"
 
def analyse_marge_beneficiaire(marge_benef):
    if marge_benef[2] > marge_benef[1] > marge_benef[0]:
        return "La marge bénéficiaire a augmenté chaque année, indiquant une rentabilité croissante après toutes les dépenses.", "bon"
    elif marge_benef[2] < marge_benef[1] < marge_benef[0]:
        return "La marge bénéficiaire a baissé chaque année, ce qui peut signaler une augmentation des coûts totaux ou des taxes.", "mauvais"
    elif marge_benef[2] > marge_benef[1] < marge_benef[0]:
        return "La marge bénéficiaire a d'abord baissé puis s'est redressée, ce qui pourrait indiquer un contrôle accru des dépenses.", "bon"
    elif marge_benef[2] < marge_benef[1] > marge_benef[0]:
        return "La marge bénéficiaire a augmenté puis diminué, ce qui pourrait indiquer une instabilité dans la gestion des coûts ou des taxes.", "mauvais"
    else:
        return "La marge bénéficiaire est stable, montrant une bonne maîtrise des coûts globaux et des impôts.", "neutre"
 
# Fonctions pour l'analyse de l'EBITDA, du Résultat Net et de la Dette Nette
 
def analyse_ebitda(ebitda):
    if ebitda.iloc[2] > ebitda.iloc[1] > ebitda.iloc[0]:
        return "L'EBITDA a augmenté chaque année, montrant une performance opérationnelle solide.", "bon"
    elif ebitda.iloc[2] < ebitda.iloc[1] < ebitda.iloc[0]:
        return "L'EBITDA a diminué chaque année, ce qui pourrait indiquer une baisse d'efficacité opérationnelle.", "mauvais"
    elif ebitda.iloc[2] > ebitda.iloc[1] < ebitda.iloc[0]:
        return "L'EBITDA a d'abord baissé puis augmenté, ce qui pourrait indiquer un retour à l'amélioration opérationnelle.", "bon"
    elif ebitda.iloc[2] < ebitda.iloc[1] > ebitda.iloc[0]:
        return "L'EBITDA a augmenté puis diminué, ce qui pourrait indiquer une instabilité dans l'efficacité opérationnelle.", "mauvais"
    else:
        return "L'EBITDA est stable, suggérant une constance dans les performances opérationnelles.", "neutre"
 
def analyse_resultat_net(benefice_net):
    if benefice_net.iloc[2] > benefice_net.iloc[1] > benefice_net.iloc[0]:
        return "Le résultat net a augmenté chaque année, montrant une amélioration de la rentabilité nette.", "bon"
    elif benefice_net.iloc[2] < benefice_net.iloc[1] < benefice_net.iloc[0]:
        return "Le résultat net a baissé chaque année, ce qui pourrait être préoccupant pour la rentabilité.", "mauvais"
    elif benefice_net.iloc[2] > benefice_net.iloc[1] < benefice_net.iloc[0]:
        return "Le résultat net a d'abord baissé puis augmenté, ce qui pourrait suggérer un retour à la croissance des profits.", "bon"
    elif benefice_net.iloc[2] < benefice_net.iloc[1] > benefice_net.iloc[0]:
        return "Le résultat net a augmenté puis diminué, ce qui pourrait indiquer une instabilité dans la rentabilité.", "mauvais"
    else:
        return "Le résultat net est resté stable, suggérant une constance dans les performances financières.", "neutre"
 
def analyse_dette_nette(dette_nette):
    if dette_nette.iloc[2] < dette_nette.iloc[1] < dette_nette.iloc[0]:
        return "La dette nette a diminué chaque année, indiquant une réduction de l'endettement.", "bon"
    elif dette_nette.iloc[2] > dette_nette.iloc[1] > dette_nette.iloc[0]:
        return "La dette nette a augmenté chaque année, ce qui peut indiquer un accroissement de l'endettement.", "mauvais"
    elif dette_nette.iloc[2] < dette_nette.iloc[1] > dette_nette.iloc[0]:
        return "La dette nette a d'abord augmenté puis diminué, indiquant une gestion de la dette plus rigoureuse.", "bon"
    elif dette_nette.iloc[2] > dette_nette.iloc[1] < dette_nette.iloc[0]:
        return "La dette nette a diminué puis augmenté, ce qui pourrait signaler des fluctuations dans les financements.", "mauvais"
    else:
        return "La dette nette est stable, montrant une constance dans la gestion de la dette.", "neutre"

# Fonction pour analyser l'évolution du BFR
def analyse_bfr(bfr):
    if bfr.iloc[2] < bfr.iloc[1] < bfr.iloc[0]:
        return "Le BFR a diminué chaque année, indiquant une meilleure gestion des stocks et créances, ou une réduction des dettes fournisseurs.", "bon"
    elif bfr.iloc[2] > bfr.iloc[1] > bfr.iloc[0]:
        return "Le BFR a augmenté chaque année, ce qui peut signaler une hausse des stocks ou un allongement des délais de paiement clients.", "mauvais"
    elif bfr.iloc[2] > bfr.iloc[1] < bfr.iloc[0]:
        return "Le BFR a d'abord augmenté puis diminué, ce qui pourrait indiquer une amélioration récente dans la gestion des liquidités.", "bon"
    elif bfr.iloc[2] < bfr.iloc[1] > bfr.iloc[0]:
        return "Le BFR a diminué puis augmenté, ce qui peut signaler une instabilité dans la gestion des stocks et créances.", "mauvais"
    else:
        return "Le BFR est stable, montrant une gestion constante des liquidités pour les opérations.", "neutre"

# Fonctions pour l'analyse des ratios de liquidité et dette/EBITDA
def analyse_ratio_liquidite(ratio_liquidite):
    if ratio_liquidite.iloc[2] > ratio_liquidite.iloc[1] > ratio_liquidite.iloc[0]:
        return "Le ratio de liquidité a augmenté chaque année, indiquant une meilleure capacité à couvrir les dettes court terme.", "bon"
    elif ratio_liquidite.iloc[2] < ratio_liquidite.iloc[1] < ratio_liquidite.iloc[0]:
        return "Le ratio de liquidité a baissé chaque année, ce qui peut signaler une réduction de la capacité à couvrir les passifs courants.", "mauvais"
    else:
        return "Le ratio de liquidité est relativement stable.", "neutre"

def analyse_dette_ebitda(ratio_dette_ebitda):
    if ratio_dette_ebitda.iloc[2] < ratio_dette_ebitda.iloc[1] < ratio_dette_ebitda.iloc[0]:
        return "Le ratio Dette/EBITDA a diminué chaque année, indiquant une meilleure capacité à rembourser la dette.", "bon"
    elif ratio_dette_ebitda.iloc[2] > ratio_dette_ebitda.iloc[1] > ratio_dette_ebitda.iloc[0]:
        return "Le ratio Dette/EBITDA a augmenté chaque année, ce qui peut signaler une capacité réduite à rembourser la dette.", "mauvais"
    else:
        return "Le ratio Dette/EBITDA est stable.", "neutre"
    
# Analyse finale basée sur les conclusions des fonctions individuelles
def analyse_finale(marge_brute, marge_ope, marge_benef, ebitda, benefice_net, dette_nette, bfr, ratio_liquidite, ratio_dette_ebitda):
    analyses = [
        analyse_marge_brute(marge_brute)[1],
        analyse_marge_operationnelle(marge_ope)[1],
        analyse_marge_beneficiaire(marge_benef)[1],
        analyse_ebitda(ebitda)[1],
        analyse_resultat_net(benefice_net)[1],
        analyse_dette_nette(dette_nette)[1],
        analyse_bfr(bfr)[1],
        analyse_ratio_liquidite(ratio_liquidite)[1],
        analyse_dette_ebitda(ratio_dette_ebitda)[1]
    ]
    
    evaluation_counts = {"bon": analyses.count("bon"), "mauvais": analyses.count("mauvais"), "neutre": analyses.count("neutre")}
    
    # Établir la conclusion
    if evaluation_counts["bon"] >= 6:
        return "Conclusion : Très bons chiffres."
    elif evaluation_counts["bon"] >= 4:
        return "Conclusion : Bons chiffres."
    elif evaluation_counts["mauvais"] >= 6:
        return "Conclusion : Très mauvais chiffres."
    else:
        return "Conclusion : Mauvais chiffres."

 # Afficher les analyses
ticker = 'AAPL'
marges_df, marge_brute, marge_ope, marge_benef, ebitda, benefice_net, dette_nette, bfr, ratio_liquidite, ratio_dette_ebitda = get_financial_data(ticker)
print("\nAnalyse de l'évolution des marges et impact :\n")
print("Marge Brute (%) :", analyse_marge_brute(marge_brute)[0])
print("Marge Opérationnelle (%) :", analyse_marge_operationnelle(marge_ope)[0])
print("Marge Bénéficiaire (%) :", analyse_marge_beneficiaire(marge_benef)[0])
print("EBITDA :", analyse_ebitda(ebitda)[0])
print("Résultat Net :", analyse_resultat_net(benefice_net)[0])
print("Dette Nette :", analyse_dette_nette(dette_nette)[0])
print("BFR :", analyse_bfr(bfr)[0])
print("Ratio de Liquidité :", analyse_ratio_liquidite(ratio_liquidite)[0])
print("Dette/EBITDA :", analyse_dette_ebitda(ratio_dette_ebitda)[0])

# Afficher la conclusion finale
print("\n", analyse_finale(marge_brute, marge_ope, marge_benef, ebitda, benefice_net, dette_nette, bfr, ratio_liquidite, ratio_dette_ebitda))