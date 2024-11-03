import pandas as pd
import yfinance as yf
import numpy as np
import mplfinance as mpf
import matplotlib.pyplot as plt

# Fonction pour télécharger les données et calculer les indicateurs techniques
def telecharger_donnees(ticker):
    data = yf.download(ticker, interval='1wk', period='5y')
    
    # Vérifier si les données sont vides
    if data.empty:
        raise ValueError(f"Aucune donnée disponible pour le ticker {ticker}. Veuillez vérifier le symbole ou réessayer plus tard.")
    
    data.columns = data.columns.droplevel(1)
    data.index = pd.to_datetime(data.index)
    return data

def calculer_indicateurs(data):
    # Calcul des indicateurs techniques (MACD, RSI)
    ema_12 = data['Close'].ewm(span=12, adjust=False).mean()
    ema_26 = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = ema_12 - ema_26
    data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
    data['Hist'] = data['MACD'] - data['Signal']
    
    delta = data['Close'].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=13, adjust=False).mean()
    ema_down = down.ewm(com=13, adjust=False).mean()
    rs = ema_up / ema_down
    data['RSI'] = 100 - (100 / (1 + rs))
    return data

def detecter_niveaux(data):
    tolerance_percentage = 0.01
    min_retouch = 3
    levels = []
    for i in range(1, len(data) - 1):
        current_price = data['Close'].iloc[i]
        lower_bound = current_price * (1 - tolerance_percentage)
        upper_bound = current_price * (1 + tolerance_percentage)
        within_range_count = ((data['Close'] >= lower_bound) & (data['Close'] <= upper_bound)).sum()
        if within_range_count >= min_retouch:
            levels.append(float(current_price))
    current_price = data['Close'].iloc[-1]
    resistances = [level for level in levels if level > current_price]
    supports = [level for level in levels if level < current_price]
    return supports, resistances

def trouver_intervalles_pertinents(levels, current_price, interval_size=None, max_intervals=3):
    interval_size = interval_size or current_price * 0.05
    min_level, max_level = min(levels), max(levels)
    intervals = np.arange(min_level, max_level + interval_size, interval_size)
    
    interval_counts = {interval: [] for interval in intervals}
    for level in levels:
        for interval in intervals:
            if interval <= level < interval + interval_size:
                interval_counts[interval].append(level)
                break

    sorted_intervals = sorted(interval_counts.items(), key=lambda x: len(x[1]), reverse=True)[:max_intervals]
    return [np.mean(values) for _, values in sorted_intervals if values]

def calculer_ath(data):
    return data['Close'].max()

# Fonction pour tracer le graphique des bougies
def tracer_graphique(data, supports, resistances, ath_price):
    hlines = supports + resistances + [ath_price]
    hlines_colors = ['g'] * len(supports) + ['r'] * len(resistances) + ['b']
    
    # Création de la figure et des axes pour les chandeliers et le volume
    fig, axlist = mpf.plot(data, type='candle', volume=True, style='charles',
                           title='Graphique en Chandeliers', ylabel='Prix',
                           ylabel_lower='Volume', figratio=(12, 6),
                           hlines=dict(hlines=hlines, colors=hlines_colors,
                                       linestyle='-.', linewidths=2, alpha=0.5),
                           mav=(50), returnfig=True)
    
    return fig

# Fonction pour tracer le MACD et le RSI
def tracer_macd_rsi(data):
    fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(12, 8), sharex=True)

    # Tracer le MACD
    ax1.set_title('MACD')
    ax1.plot(data.index, data['MACD'], color='blue', label='MACD', linewidth=2)
    ax1.plot(data.index, data['Signal'], color='red', label='Signal', linewidth=2)
    ax1.axhline(0, color='black', linestyle='--', linewidth=1)
    ax1.fill_between(data.index, 0, data['Hist'], where=data['Hist'] >= 0, color='green', alpha=0.5, label='Histogram')
    ax1.fill_between(data.index, 0, data['Hist'], where=data['Hist'] < 0, color='red', alpha=0.5)
    ax1.legend()

    # Tracer le RSI
    ax2.set_title('RSI')
    ax2.plot(data.index, data['RSI'], color='green', label='RSI', linewidth=2)
    ax2.axhline(30, color='black', linestyle='--', linewidth=1)
    ax2.axhline(70, color='black', linestyle='--', linewidth=1)
    ax2.fill_between(data.index, 30, 100, where=data['RSI'] >= 30, color='lightgray', alpha=0.5)
    ax2.fill_between(data.index, 0, 30, where=data['RSI'] < 30, color='lightcoral', alpha=0.5, label='Oversold Area')
    ax2.fill_between(data.index, 70, 100, where=data['RSI'] > 70, color='lightgreen', alpha=0.5, label='Overbought Area')
    ax2.legend(loc='upper right')

    plt.subplots_adjust(left=0.09, bottom=0.10, right=0.94, top=0.95, hspace=0.4)
    return fig
## ANALYSES

def analyse_rsi(data):
    """Analyse le RSI et retourne une interprétation."""
    rsi_current = data['RSI'].iloc[-1]
    if rsi_current > 70:
        return "RSI est en surachat (>70). Un retournement baissier pourrait se produire."
    elif rsi_current < 30:
        return "RSI est en survente (<30). Un retournement haussier pourrait se produire."
    return "RSI est neutre, entre 30 et 70. Aucune conclusion ne peut être tirée."


def analyse_macd(data):
    """Analyse le MACD et retourne une interprétation."""
    achat1 = achat2 = achat3 = None
    macd_current = data['MACD'].iloc[-1]
    signal_current = data['Signal'].iloc[-1]
    histogram_current = data['Hist'].iloc[-1]
    histogram_previous = data['Hist'].iloc[-2]

    # Analyse de l'histogramme pour le momentum
    if histogram_current > histogram_previous:
        momentum_shift = "Le momentum s'accélère (augmentation de l'histogramme)."
        achat1 = True
    elif histogram_current < histogram_previous:
        momentum_shift = "Le momentum ralentit (diminution de l'histogramme), ce qui pourrait indiquer une fin de mouvement."
        achat1 = False
    else:
        momentum_shift = "Pas de changement dans le momentum (l'histogramme est stable)."

    # Position du MACD par rapport à 0
    if macd_current > 0:
        macd_trend = "Les moyennes mobiles sous-jacentes sont en position haussière (MACD > 0), indiquant une tendance haussière."
        achat2 = True
    elif macd_current < 0:
        macd_trend = "Les moyennes mobiles sous-jacentes sont en position baissière (MACD < 0), indiquant une tendance baissière."
        achat2 = False
    else:
        macd_trend = "Le MACD est à 0, indiquant une position neutre."

    # Croisement MACD / Signal
    if macd_current > signal_current:
        macd_crossover = "Le MACD est au-dessus de la ligne de signal, suggérant un potentiel signal d'achat (momentum haussier)."
        achat3 = True
    elif macd_current < signal_current:
        macd_crossover = "Le MACD est en dessous de la ligne de signal, suggérant un potentiel signal de vente (momentum baissier)."
        achat3 = False
    else:
        macd_crossover = "Le MACD est égal à la ligne de signal, indiquant une absence de momentum net."

    # Synthèse de l'analyse MACD
    macd_analysis = f"{macd_trend} {macd_crossover} {momentum_shift}"
    achat_signals = sum([signal is True for signal in [achat1, achat2, achat3]])
    vente_signals = sum([signal is False for signal in [achat1, achat2, achat3]])

    # Recommandation
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


def analyse_sma(data):
    """Analyse la tendance basée sur la SMA 50."""
    data['SMA_50'] = data['Close'].rolling(window=50).mean()
    current_price = data['Close'].iloc[-1]
    sma_50_current = data['SMA_50'].iloc[-1]
    
    if current_price > sma_50_current:
        return "La tendance est haussière (prix > SMA 50)."
    return "La tendance est baissière (prix < SMA 50)."


def analyse_niveaux(data, levels):
    """Analyse les niveaux de support et de résistance proches du prix actuel."""
    current_price = data['Close'].iloc[-1]
    tolerance = current_price * 0.02

    # Niveau le plus proche dans les limites de tolérance
    levels_sorted = sorted(levels, key=lambda x: abs(x - current_price))
    closest_level = levels_sorted[0] if levels_sorted else None
    if closest_level is None:
        return "Aucun niveau de support ou de résistance identifié."
    if abs(closest_level - current_price) > tolerance:
        return "Le prix actuel n'est pas suffisamment proche d'un niveau clé."

    # Déterminer support ou résistance
    level_type = "résistance" if closest_level > current_price else "support"
    level_analysis, recommandation = "", "Neutre"

    # Rejet ou dépassement
    if level_type == "résistance":
        if current_price < closest_level and data['Close'].iloc[-2] >= closest_level:
            level_analysis = f"La résistance à {closest_level:.2f} a été rejetée récemment, ce qui suggère un potentiel signal de vente."
            recommandation = "Vendre"
        elif current_price > closest_level:
            level_analysis = f"La résistance à {closest_level:.2f} a été dépassée, indiquant un potentiel signal d'achat."
            recommandation = "Acheter"
        else:
            level_analysis = f"Le prix est proche de la résistance à {closest_level:.2f}."
    else:
        if current_price > closest_level and data['Close'].iloc[-2] <= closest_level:
            level_analysis = f"Le support à {closest_level:.2f} a été rejeté récemment, ce qui suggère un potentiel signal d'achat."
            recommandation = "Acheter"
        elif current_price < closest_level:
            level_analysis = f"Le support à {closest_level:.2f} a été dépassé, indiquant un potentiel signal de vente."
            recommandation = "Vendre"
        else:
            level_analysis = f"Le prix est proche du support à {closest_level:.2f}."

    return f"{level_analysis} Recommandation : {recommandation}."