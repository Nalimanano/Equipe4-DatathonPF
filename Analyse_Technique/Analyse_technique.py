import pandas as pd
import yfinance as yf
import numpy as np
import mplfinance as mpf

def get_data(ticker):
    data = yf.download(ticker, interval='1wk', period='5y')
    data.index = pd.to_datetime(data.index)
    print(data)
    return data
def calculate_indicators(data):
    # MACD
    ema_12 = data['Close'].ewm(span=12, adjust=False).mean()
    ema_26 = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = ema_12 - ema_26
    data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
    data['Hist'] = data['MACD'] - data['Signal']

    # RSI
    delta = data['Close'].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=13, adjust=False).mean()
    ema_down = down.ewm(com=13, adjust=False).mean()
    rs = ema_up / ema_down
    data['RSI'] = 100 - (100 / (1 + rs))

    # SMA 50
    data['SMA_50'] = data['Close'].rolling(window=50).mean()
    return data

def detect_support_resistance(data, tolerance=0.01, min_retouch=3):
    levels = []
    for i in range(1, len(data) - 1):
        current_price = data['Close'].iloc[i]
        lower_bound = current_price * (1 - tolerance)
        upper_bound = current_price * (1 + tolerance)
        within_range_count = ((data['Close'] >= lower_bound) & (data['Close'] <= upper_bound)).sum()
        if within_range_count >= min_retouch:
            levels.append(float(current_price))
    return levels

def find_most_frequent_intervals(levels, current_price, interval_size=None, max_intervals=3):
    if interval_size is None:
        interval_size = current_price * 0.05
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

def analyse_rsi(data):
    rsi_current = data['RSI'].iloc[-1]
    if rsi_current > 70:
        return "RSI est en surachat (>70). Un retournement baissier pourrait se produire."
    elif rsi_current < 30:
        return "RSI est en survente (<30). Un retournement haussier pourrait se produire."
    else:
        return "RSI est neutre, entre 30 et 70."

def analyse_macd(data):
    macd_current = data['MACD'].iloc[-1]
    signal_current = data['Signal'].iloc[-1]
    histogram_current = data['Hist'].iloc[-1]
    histogram_previous = data['Hist'].iloc[-2]

    momentum_shift = ("Le momentum s'accélère." if histogram_current > histogram_previous else 
                      "Le momentum ralentit." if histogram_current < histogram_previous else
                      "Pas de changement dans le momentum.")

    macd_trend = ("Tendance haussière." if macd_current > 0 else 
                  "Tendance baissière." if macd_current < 0 else 
                  "Position neutre.")

    macd_crossover = ("Potentiel signal d'achat." if macd_current > signal_current else 
                      "Potentiel signal de vente." if macd_current < signal_current else 
                      "Pas de signal net.")

    return f"{macd_trend} {macd_crossover} {momentum_shift}"

def analyse_trend(data):
    current_price = data['Close'].iloc[-1]
    sma_50 = data['SMA_50'].iloc[-1]
    return ("Tendance haussière." if current_price > sma_50 else "Tendance baissière.")

def analyse_levels(data, levels):
    current_price = data['Close'].iloc[-1]
    levels_sorted = sorted(levels, key=lambda x: abs(x - current_price))
    closest_level = levels_sorted[0] if levels_sorted else None
    return closest_level, ("Support" if closest_level < current_price else "Résistance")
