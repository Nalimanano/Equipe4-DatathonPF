import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
import mplfinance as mpf
import numpy as np

def download_data(ticker='AAPL', interval='1wk', period='5y'):
    data = yf.download(ticker, interval=interval, period=period)
    data.columns = data.columns.droplevel(1)
    data.index = pd.to_datetime(data.index)
    return data

def calculate_technical_indicators(data):
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

def detect_levels(data, tolerance_percentage=0.01, min_retouch=3):
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

def find_most_frequent_interval(levels, interval_size, max_intervals=3):
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

def plot_stock_data(data, supports, resistances, ath_price):
    hlines = supports + resistances + [ath_price]
    hlines_colors = ['g'] * len(supports) + ['r'] * len(resistances) + ['b']

    mpf.plot(data, type='candle', volume=True, style='charles', title='Graphique en Chandeliers pour AAPL',
             ylabel='Prix', ylabel_lower='Volume', figratio=(12, 6),
             hlines=dict(hlines=hlines, colors=hlines_colors, linestyle='-.', linewidths=2, alpha=0.5),
             mav=(50))

def plot_macd_rsi(data):
    fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(12, 8), sharex=True)

    ax1.set_title('MACD', fontsize=16)
    ax1.plot(data.index, data['MACD'], color='blue', label='MACD', linewidth=2)
    ax1.plot(data.index, data['Signal'], color='red', label='Signal', linewidth=2)
    ax1.axhline(0, color='black', linestyle='--', linewidth=1)
    ax1.fill_between(data.index, 0, data['Hist'], where=data['Hist'] >= 0, color='green', alpha=0.5, label='Histogram')
    ax1.fill_between(data.index, 0, data['Hist'], where=data['Hist'] < 0, color='red', alpha=0.5)
    ax1.legend()

    ax2.set_title('RSI', fontsize=16)
    ax2.plot(data.index, data['RSI'], color='green', label='RSI', linewidth=2)
    ax2.axhline(30, color='black', linestyle='--', linewidth=1)
    ax2.axhline(70, color='black', linestyle='--', linewidth=1)
    ax2.fill_between(data.index, 30, 100, where=data['RSI'] >= 30, color='lightgray', alpha=0.5)
    ax2.fill_between(data.index, 0, 30, where=data['RSI'] < 30, color='lightcoral', alpha=0.5, label='Oversold Area')
    ax2.fill_between(data.index, 70, 100, where=data['RSI'] > 70, color='lightgreen', alpha=0.5, label='Overbought Area')
    ax2.legend(loc='upper right')

    plt.subplots_adjust(left=0.09, bottom=0.10, right=0.94, top=0.95, hspace=0.4)
    plt.show()

# Main execution
def main():
    data = download_data()
    data = calculate_technical_indicators(data)
    supports, resistances = detect_levels(data)
    top_supports = find_most_frequent_interval(supports, interval_size=data['Close'].iloc[-1] * 0.05)
    top_resistances = find_most_frequent_interval(resistances, interval_size=data['Close'].iloc[-1] * 0.05)
    ath_price = data['Close'].max()

    plot_stock_data(data, top_supports, top_resistances, ath_price)
    plot_macd_rsi(data)

if __name__ == "__main__":
    main()
