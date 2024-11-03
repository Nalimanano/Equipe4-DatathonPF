import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
import mplfinance as mpf
import numpy as np

# Téléchargement des données boursières d'Apple
data = yf.download('AAPL', interval='1wk', period='5y')
data.columns = data.columns.droplevel(1)  # Supprimer le niveau "Ticker"
data.index = pd.to_datetime(data.index)

# Calcul des indicateurs techniques
ema_12 = data['Close'].ewm(span=12, adjust=False).mean()
ema_26 = data['Close'].ewm(span=26, adjust=False).mean()
data['MACD'] = ema_12 - ema_26
data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
data['Hist'] = data['MACD'] - data['Signal']

# Calcul du RSI
delta = data['Close'].diff()
up = delta.clip(lower=0)
down = -1 * delta.clip(upper=0)
ema_up = up.ewm(com=13, adjust=False).mean()
ema_down = down.ewm(com=13, adjust=False).mean()
rs = ema_up / ema_down
data['RSI'] = 100 - (100 / (1 + rs))

# Listes pour stocker les niveaux de support et de résistance
supports = []
resistances = []

# Tolérance de 1 % pour la détection
tolerance_percentage = 0.01
min_retouch = 3

# Détection des niveaux de support et résistance où le prix est revenu au moins 3 fois
levels = []
for i in range(1, len(data) - 1):
    current_price = data['Close'].iloc[i]  # Utiliser iloc pour corriger l'avertissement
    lower_bound = current_price * (1 - tolerance_percentage)
    upper_bound = current_price * (1 + tolerance_percentage)
    
    within_range_count = ((data['Close'] >= lower_bound) & (data['Close'] <= upper_bound)).sum()
    if within_range_count >= min_retouch:
        levels.append(float(current_price))

# Déterminer le prix actuel (dernier prix de clôture)
current_price = data['Close'].iloc[-1]
resistances = [level for level in levels if level > current_price]
supports = [level for level in levels if level < current_price]

# Fonction pour trouver les intervalles contenant le plus de niveaux et calculer la moyenne des valeurs dans chaque intervalle
def find_most_frequent_interval(levels, interval_size=current_price*0.05, max_intervals=3):
    min_level, max_level = min(levels), max(levels)
    intervals = np.arange(min_level, max_level + interval_size, interval_size)

    interval_counts = {interval: [] for interval in intervals}
    for level in levels:
        for interval in intervals:
            if interval <= level < interval + interval_size:
                interval_counts[interval].append(level)
                break

    sorted_intervals = sorted(interval_counts.items(), key=lambda x: len(x[1]), reverse=True)[:max_intervals]
    relevant_levels = [np.mean(values) for _, values in sorted_intervals if values]

    return relevant_levels

# Obtenir les 3 supports et 3 résistances pertinents
top_resistances = find_most_frequent_interval(resistances)
top_supports = find_most_frequent_interval(supports)

# Conversion des niveaux pertinents en type float standard
top_resistances = [float(level) for level in top_resistances]
top_supports = [float(level) for level in top_supports]

# Calculer l'ATH
ath_price = data['Close'].max()

# Fusionner les supports, résistances et l'ATH pour hlines et définir les couleurs
hlines = top_supports + top_resistances + [ath_price]
hlines_colors = ['g'] * len(top_supports) + ['r'] * len(top_resistances) + ['b']

# Tracer le graphique des bougies avec la SMA 50, supports, résistances et ATH
mpf.plot(data, type='candle', volume=True, style='charles', title='Graphique en Chandeliers pour AAPL',
         ylabel='Prix', ylabel_lower='Volume', figratio=(12, 6), 
         hlines=dict(hlines=hlines, colors=hlines_colors, linestyle='-.', linewidths=2, alpha = 0.5,label =(1,2,3)),
         mav=(50))

# Tracer le MACD et le RSI
fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(12, 8), sharex=True)

# Tracer le MACD
ax1.set_title('MACD', fontsize=16)
ax1.plot(data.index, data['MACD'], color='blue', label='MACD', linewidth=2)
ax1.plot(data.index, data['Signal'], color='red', label='Signal', linewidth=2)
ax1.axhline(0, color='black', linestyle='--', linewidth=1)
ax1.fill_between(data.index, 0, data['Hist'], where=data['Hist'] >= 0, color='green', alpha=0.5, label='Histogram')
ax1.fill_between(data.index, 0, data['Hist'], where=data['Hist'] < 0, color='red', alpha=0.5)
ax1.legend()

# Tracer le RSI
ax2.set_title('RSI', fontsize=16)
ax2.plot(data.index, data['RSI'], color='green', label='RSI', linewidth=2)
ax2.axhline(30, color='black', linestyle='--', linewidth=1)
ax2.axhline(70, color='black', linestyle='--', linewidth=1)
ax2.fill_between(data.index, 30, 100, where=data['RSI'] >= 30, color='lightgray', alpha=0.5)
ax2.fill_between(data.index, 0, 30, where=data['RSI'] < 30, color='lightcoral', alpha=0.5, label='Oversold Area')
ax2.fill_between(data.index, 70, 100, where=data['RSI'] > 70, color='lightgreen', alpha=0.5, label='Overbought Area')
ax2.legend(loc='upper right')

# Ajuster les marges pour améliorer la lisibilité
plt.subplots_adjust(left=0.09, bottom=0.10, right=0.94, top=0.95, hspace=0.4)

# Afficher les graphiques
plt.show()





## ANALYSES

# Analyse du RSI
def analyse_RSI():
    rsi_current = data['RSI'].iloc[-1]
    last_overbought = data[data['RSI'] > 70].index.max()
    last_oversold = data[data['RSI'] < 30].index.max()

    if rsi_current > 70:
        rsi_analysis = "RSI est en surachat (>70). Un retournement baissier pourrait se produire."
    elif rsi_current < 30:
        rsi_analysis = "RSI est en survente (<30). Un retournement haussier pourrait se produire."
    else:
        rsi_analysis = "RSI est neutre, entre 30 et 70. Aucune conclusion ne peut être tirée"
    
    return rsi_analysis




# Analyse du MACD
def analyse_MACD():
    achat1 = None  # Initialisé à None pour gérer les cas neutres
    achat2 = None
    achat3 = None

    # Analyse détaillée du MACD
    macd_current = data['MACD'].iloc[-1]
    signal_current = data['Signal'].iloc[-1]

    # Analyse du momentum basé sur l'histogramme du MACD
    histogram_current = data['Hist'].iloc[-1]
    histogram_previous = data['Hist'].iloc[-2]

    # Analyser le changement entre l'histogramme actuel et le précédent
    if histogram_current > histogram_previous:
        momentum_shift = "Le momentum s'accélère (augmentation de l'histogramme)."
        achat1 = True
    elif histogram_current < histogram_previous:
        momentum_shift = "Le momentum ralentit (diminution de l'histogramme), ce qui pourrait indiquer une fin de mouvement."
        achat1 = False
    else:
        momentum_shift = "Pas de changement dans le momentum (l'histogramme est stable)."

    # Déterminer si le MACD est au-dessus ou en dessous de 0
    if macd_current > 0:
        macd_trend = "Les moyennes mobiles sous-jacentes sont en position haussière (MACD > 0), indiquant une tendance haussière."
        achat2 = True
    elif macd_current < 0:
        macd_trend = "Les moyennes mobiles sous-jacentes sont en position baissière (MACD < 0), indiquant une tendance baissière."
        achat2 = False
    else:
        macd_trend = "Le MACD est à 0, indiquant une position neutre."

    # Déterminer le croisement entre le MACD et la ligne de signal
    if macd_current > signal_current:
        macd_crossover = "Le MACD est au-dessus de la ligne de signal, suggérant un potentiel signal d'achat (momentum haussier)."
        achat3 = True
    elif macd_current < signal_current:
        macd_crossover = "Le MACD est en dessous de la ligne de signal, suggérant un potentiel signal de vente (momentum baissier)."
        achat3 = False
    else:
        macd_crossover = "Le MACD est égal à la ligne de signal, indiquant une absence de momentum net."

    # Résumé de l'analyse MACD
    macd_analysis = f"{macd_trend} {macd_crossover} {momentum_shift}"

    # Calculer le nombre de signaux positifs, négatifs et neutres
    achat_signals = sum([signal is True for signal in [achat1, achat2, achat3]])
    vente_signals = sum([signal is False for signal in [achat1, achat2, achat3]])

    # Recommandations en fonction des signaux
    if achat_signals == 3:
        macd_analysis += "\nIl est fortement recommandé d'acheter"
    elif achat_signals == 2:
        macd_analysis += "\nIl est recommandé d'acheter."
    elif vente_signals == 3:
        macd_analysis += "\nIl est fortement recommandé de vendre."
    elif vente_signals == 2:
        macd_analysis += "\nIl est recommandé de vendre."
    else:
        macd_analysis += "\nIl n'est pas recommandé d'acheter ni de vendre."

    return macd_analysis


# Analyse de la Tendance avec la SMA 50

# Calcul de la SMA 50
data['SMA_50'] = data['Close'].rolling(window=50).mean()

def analyse_sma():
    sma_50_current = data['SMA_50'].iloc[-1]
    if current_price > sma_50_current:
        trend_analysis = "La tendance est haussière (prix > SMA 50)."
    else:
        trend_analysis = "La tendance est baissière (prix < SMA 50)."
    return trend_analysis

def analyse_niveaux():
    current_price = data['Close'].iloc[-1]
    tolerance = current_price * 0.02  # 2% de tolérance

    # Trouver le niveau le plus proche du prix actuel dans les limites de tolérance
    levels_sorted = sorted(levels, key=lambda x: abs(x - current_price))
    closest_level = levels_sorted[0] if levels_sorted else None

    if closest_level is None:
        return "Aucun niveau de support ou de résistance identifié."

    # Vérifier si le niveau le plus proche est dans la fourchette de tolérance
    if abs(closest_level - current_price) > tolerance:
        return "Le prix actuel n'est pas suffisamment proche d'un niveau clé."

    # Déterminer si le niveau le plus proche est une résistance ou un support
    if closest_level > current_price:
        level_type = "résistance"
    else:
        level_type = "support"

    # Détection de rejet ou de dépassement
    level_analysis = ""
    recommandation = "Neutre"
    if level_type == "résistance":
        if current_price < closest_level and data['Close'].iloc[-2] >= closest_level:
            level_analysis = f"La résistance à {closest_level:.2f} a été rejetée récemment, ce qui suggère un potentiel signal de vente."
            recommandation = "Vendre"
        elif current_price > closest_level:
            level_analysis = f"La résistance à {closest_level:.2f} a été dépassée, indiquant un potentiel signal d'achat."
            recommandation = "Acheter"
        else:
            level_analysis = f"Le prix est proche de la résistance à {closest_level:.2f}."
    else:  # closest_level is a support
        if current_price > closest_level and data['Close'].iloc[-2] <= closest_level:
            level_analysis = f"Le support à {closest_level:.2f} a été rejeté récemment, ce qui suggère un potentiel signal d'achat."
            recommandation = "Acheter"
        elif current_price < closest_level:
            level_analysis = f"Le support à {closest_level:.2f} a été dépassé, indiquant un potentiel signal de vente."
            recommandation = "Vendre"
        else:
            level_analysis = f"Le prix est proche du support à {closest_level:.2f}."

    return f"{level_analysis} Recommandation : {recommandation}."

print(analyse_RSI())
print(analyse_MACD())
print(analyse_sma())
print(analyse_niveaux())