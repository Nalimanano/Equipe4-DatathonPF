import boto3
import json
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# Function to retrieve financial data
def get_financial_data_auto(ticker):
    company = yf.Ticker(ticker)
    income_statement = company.financials
    balance_sheet = company.balance_sheet

    revenue = income_statement.loc['Total Revenue'][:3] * 1e-6
    ebitda = income_statement.loc['EBITDA'][:3] * 1e-6
    net_income = income_statement.loc['Net Income'][:3] * 1e-6
    total_debt = balance_sheet.loc['Total Debt'][:3] * 1e-6
    cash = balance_sheet.loc['Cash And Cash Equivalents'][:3] * 1e-6
    net_debt = total_debt - cash
    liquidity_ratio = (balance_sheet.loc['Total Assets'][:3] / balance_sheet.loc['Total Liabilities Net Minority Interest'][:3]).values[::-1]
    debt_to_ebitda_ratio = (net_debt / ebitda).values[::-1]
    years = [str(date.year) for date in revenue.index][::-1]

    margins_df = pd.DataFrame({
        'Year': years,
        'Revenue (millions)': revenue.values[::-1],
        'EBITDA (millions)': ebitda.values[::-1],
        'Net Debt (millions)': net_debt.values[::-1],
        'Liquidity Ratio': liquidity_ratio,
        'Debt/EBITDA': debt_to_ebitda_ratio
    }).set_index('Year').T

    return margins_df, revenue, ebitda, net_income, net_debt, liquidity_ratio, debt_to_ebitda_ratio

# Call Claude model to interpret financial data and save to a text file
def interpret_financial_data_to_file(filename, revenue, ebitda, net_income, net_debt, liquidity_ratio, debt_to_ebitda_ratio):
    bedrock_runtime_client = boto3.client('bedrock-runtime', region_name='us-west-2')

    # Create a summary text for financial indicators
    data_summary = (
        f"**Financial Analysis Summary for the past 3 years:**\n\n"
        f"**Revenue (in millions):** {revenue.values}\n"
        f"**EBITDA (in millions):** {ebitda.values}\n"
        f"**Net Income (in millions):** {net_income.values}\n"
        f"**Net Debt (in millions):** {net_debt.values}\n"
        f"**Liquidity Ratio:** {liquidity_ratio}\n"
        f"**Debt/EBITDA Ratio:** {debt_to_ebitda_ratio}\n\n"
        "Please provide an interpretation of these financial indicators. Highlight strengths, weaknesses, and any potential risks or opportunities."
    )

    try:
        response = bedrock_runtime_client.invoke_model(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            contentType="application/json",
            accept="application/json",
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": data_summary
                            }
                        ]
                    }
                ]
            })
        )
        
        result = json.loads(response['body'].read())
        analysis_text = result["content"][0].get("text", "No analysis provided.")
        
        # Save the analysis to a text file
        with open(filename, "w") as file:
            file.write("Interpretation of Financial Data:\n")
            file.write(analysis_text)
        print(f"Analysis saved in {filename}")
        
    except Exception as e:
        print("Error accessing the Claude model:", e)

# Function to visualize data with Matplotlib
def plot_optimized_financial_data(margins_df):
    fig, axs = plt.subplots(2, 1, figsize=(12, 10))

    # Chart 1: Revenue, EBITDA, and Net Debt
    margins_df.T[['Revenue (millions)', 'EBITDA (millions)', 'Net Debt (millions)']].plot(
        kind='bar', ax=axs[0], color=['#4CAF50', '#2196F3', '#FF5722']
    )
    axs[0].set_title("Revenue, EBITDA, and Net Debt (in millions)", fontsize=14)
    axs[0].set_ylabel("Amounts (in millions)", fontsize=12)
    axs[0].legend(title="Indicators")
    for container in axs[0].containers:
        axs[0].bar_label(container, fmt="%.0f", label_type="edge")
    axs[0].grid(True, axis='y', linestyle='--', alpha=0.7)

    # Chart 2: Financial Ratios (Liquidity Ratio and Debt/EBITDA)
    margins_df.T[['Liquidity Ratio', 'Debt/EBITDA']].plot(
        kind='line', marker='o', ax=axs[1], color=['#673AB7', '#FF9800']
    )
    axs[1].set_title("Trends in Liquidity Ratio and Debt/EBITDA", fontsize=14)
    axs[1].set_ylabel("Ratio", fontsize=12)
    axs[1].set_xlabel("Year", fontsize=12)
    axs[1].legend(title="Ratios")
    for line in axs[1].lines:
        axs[1].annotate(f"{line.get_ydata()[-1]:.2f}", xy=(1, line.get_ydata()[-1]),
                        xytext=(5, 0), textcoords='offset points', color=line.get_color(),
                        fontsize=10, fontweight='bold', ha='left')
    axs[1].grid(True, linestyle='--', alpha=0.7)

    plt.tight_layout()
    plt.show()
    return fig

# Example usage
# ticker = 'AAPL'
# filename = "financial_analysis.txt"
# margins_df, revenue, ebitda, net_income, net_debt, liquidity_ratio, debt_to_ebitda_ratio = get_financial_data_auto(ticker)

# # Save the analysis to a text file
# interpret_financial_data_to_file(filename, margins_df, revenue, ebitda, net_income, net_debt, liquidity_ratio, debt_to_ebitda_ratio)

# # Display the charts
# plot_optimized_financial_data(margins_df)
