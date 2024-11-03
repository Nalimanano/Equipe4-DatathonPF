import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
import mplfinance as mpf
import numpy as np

# Streamlit user input for stock ticker
ticker = st.text_input("Enter the stock ticker symbol:", "AAPL")

# Download stock data
data = yf.download(ticker, interval='1wk', period='5y')
data.columns = data.columns.droplevel(1)  # Remove the "Ticker" level
data.index = pd.to_datetime(data.index)

# Check if data is empty
if data.empty:
    st.error("No data found for the ticker: {}".format(ticker))
else:
    # Calculate technical indicators
    ema_12 = data['Close'].ewm(span=12, adjust=False).mean()
    ema_26 = data['Close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = ema_12 - ema_26
    data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
    data['Hist'] = data['MACD'] - data['Signal']

    # Calculate RSI
    delta = data['Close'].diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ema_up = up.ewm(com=13, adjust=False).mean()
    ema_down = down.ewm(com=13, adjust=False).mean()
    rs = ema_up / ema_down
    data['RSI'] = 100 - (100 / (1 + rs))

    # Lists to store support and resistance levels
    supports = []
    resistances = []

    # Tolerance and minimum retouch for detection
    tolerance_percentage = 0.01
    min_retouch = 3

    # Detect support and resistance levels
    levels = []
    for i in range(1, len(data) - 1):
        current_price = data['Close'].iloc[i]
        lower_bound = current_price * (1 - tolerance_percentage)
        upper_bound = current_price * (1 + tolerance_percentage)
        
        within_range_count = ((data['Close'] >= lower_bound) & (data['Close'] <= upper_bound)).sum()
        if within_range_count >= min_retouch:
            levels.append(float(current_price))

    # Determine current price and support/resistance
    current_price = data['Close'].iloc[-1]
    resistances = [level for level in levels if level > current_price]
    supports = [level for level in levels if level < current_price]

    # Function to find most frequent intervals
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

    # Get top support and resistance levels
    top_resistances = find_most_frequent_interval(resistances)
    top_supports = find_most_frequent_interval(supports)

    # Convert relevant levels to float
    top_resistances = [float(level) for level in top_resistances]
    top_supports = [float(level) for level in top_supports]

    # Calculate ATH
    ath_price = data['Close'].max()

    # Merge levels for hlines and set colors
    hlines = top_supports + top_resistances + [ath_price]
    hlines_colors = ['g'] * len(top_supports) + ['r'] * len(top_resistances) + ['b']

    # Plot candlestick chart
    mpf.plot(data, type='candle', volume=True, style='charles', title='Candlestick Chart for {}'.format(ticker),
             ylabel='Price', ylabel_lower='Volume', figratio=(12, 6), 
             hlines=dict(hlines=hlines, colors=hlines_colors, linestyle='-.', linewidths=2, alpha=0.5),
             mav=(50))

    # Plot MACD and RSI
    fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(12, 8), sharex=True)

    # Plot MACD
    ax1.set_title('MACD', fontsize=16)
    ax1.plot(data.index, data['MACD'], color='blue', label='MACD', linewidth=2)
    ax1.plot(data.index, data['Signal'], color='red', label='Signal', linewidth=2)
    ax1.axhline(0, color='black', linestyle='--', linewidth=1)
    ax1.fill_between(data.index, 0, data['Hist'], where=data['Hist'] >= 0, color='green', alpha=0.5, label='Histogram')
    ax1.fill_between(data.index, 0, data['Hist'], where=data['Hist'] < 0, color='red', alpha=0.5)
    ax1.legend()

    # Plot RSI
    ax2.set_title('RSI', fontsize=16)
    ax2.plot(data.index, data['RSI'], color='green', label='RSI', linewidth=2)
    ax2.axhline(30, color='black', linestyle='--', linewidth=1)
    ax2.axhline(70, color='black', linestyle='--', linewidth=1)
    ax2.fill_between(data.index, 30, 100, where=data['RSI'] >= 30, color='lightgray', alpha=0.5)
    ax2.fill_between(data.index, 0, 30, where=data['RSI'] < 30, color='lightcoral', alpha=0.5, label='Oversold Area')
    ax2.fill_between(data.index, 70, 100, where=data['RSI'] > 70, color='lightgreen', alpha=0.5, label='Overbought Area')
    ax2.legend(loc='upper right')

    # Adjust margins
    plt.subplots_adjust(left=0.09, bottom=0.10, right=0.94, top=0.95, hspace=0.4)

    # Display plots in Streamlit
    st.pyplot(fig)

    ## ANALYSES

    # Analyze RSI
    def analyse_RSI():
        rsi_current = data['RSI'].iloc[-1]
        last_overbought = data[data['RSI'] > 70].index.max()
        last_oversold = data[data['RSI'] < 30].index.max()

        if rsi_current > 70:
            rsi_analysis = "RSI is overbought (>70). A bearish reversal may occur."
        elif rsi_current < 30:
            rsi_analysis = "RSI is oversold (<30). A bullish reversal may occur."
        else:
            rsi_analysis = "RSI is neutral, between 30 and 70. No conclusion can be drawn."
        
        return rsi_analysis

    # Analyze MACD
    def analyse_MACD():
        achat1 = None
        achat2 = None
        achat3 = None

        macd_current = data['MACD'].iloc[-1]
        signal_current = data['Signal'].iloc[-1]

        histogram_current = data['Hist'].iloc[-1]
        histogram_previous = data['Hist'].iloc[-2]

        if histogram_current > histogram_previous:
            momentum_shift = "Momentum is accelerating (increasing histogram)."
            achat1 = True
        elif histogram_current < histogram_previous:
            momentum_shift = "Momentum is slowing down (decreasing histogram), which may indicate an end of the move."
            achat1 = False
        else:
            momentum_shift = "No change in momentum (histogram is stable)."

        if macd_current > 0:
            macd_trend = "Underlying moving averages are bullish (MACD > 0), indicating an upward trend."
            achat2 = True
        elif macd_current < 0:
            macd_trend = "Underlying moving averages are bearish (MACD < 0), indicating a downward trend."
            achat2 = False
        else:
            macd_trend = "MACD is at 0, indicating a neutral position."

        if macd_current > signal_current:
            macd_crossover = "MACD is above the signal line, suggesting a potential buy signal (bullish momentum)."
            achat3 = True
        elif macd_current < signal_current:
            macd_crossover = "MACD is below the signal line, suggesting a potential sell signal (bearish momentum)."
            achat3 = False
        else:
            macd_crossover = "MACD is equal to the signal line, indicating an absence of net momentum."

        macd_analysis = f"{macd_trend}\n{momentum_shift}\n{macd_crossover}"
        return macd_analysis, achat1, achat2, achat3

    # Display analysis
    st.subheader('RSI Analysis')
    st.write(analyse_RSI())

    st.subheader('MACD Analysis')
    macd_analysis, achat1, achat2, achat3 = analyse_MACD()
    st.write(macd_analysis)

    # Display Support and Resistance Levels
    st.subheader('Support and Resistance Levels')
    st.write('Support Levels: {}'.format(top_supports))
    st.write('Resistance Levels: {}'.format(top_resistances))
    st.write('All Time High (ATH): {}'.format(ath_price))

    # Add button to save the analysis report
    if st.button('Save Analysis Report'):
        report_content = f"Ticker: {ticker}\n\n" \
                         f"RSI Analysis: {analyse_RSI()}\n\n" \
                         f"MACD Analysis:\n{macd_analysis}\n\n" \
                         f"Support Levels: {top_supports}\n" \
                         f"Resistance Levels: {top_resistances}\n" \
                         f"All Time High (ATH): {ath_price}\n"

        with open(f"{ticker}_analysis_report.txt", "w") as file:
            file.write(report_content)

        st.success(f"Analysis report saved as {ticker}_analysis_report.txt")
