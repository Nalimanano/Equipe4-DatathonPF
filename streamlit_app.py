import streamlit as st
import Analyse_financière as fa  # Import your financial analysis module

# Main Function
def main():
    st.title("Financial Data Analysis")
    symbol = st.text_input("Enter Stock Symbol:")
    
    if symbol:
        # Get company data
        info, historique, bilan, compte_de_resultat, flux_de_tresorerie = fa.get_company_data(symbol)

        # Display company sector
        secteur = fa.display_sector_info(info)
        st.subheader("Company Sector")
        st.write(secteur)

        # Plot EBITDA
        dates = compte_de_resultat.columns
        fig_ebitda = fa.plot_financial_metric(dates, compte_de_resultat.loc['EBITDA'].values, "Évolution de l'EBITDA", "EBITDA (en milliards)")
        st.pyplot(fig_ebitda)

        # Plot Gross Profit Margin
        GPM = fa.calculate_gross_profit_margin(compte_de_resultat)
        fig_gpm = fa.plot_financial_metric(dates, GPM, "Évolution du Gross Profit Margin", "GPM %")
        st.pyplot(fig_gpm)

        # Plot market weights
        top_companies = fa.display_sector_info(info)
        fig_weights = fa.plot_market_weights(top_companies)
        if fig_weights is not None:
            st.pyplot(fig_weights)
        else:
            st.write("Error: No market weight data available.")

if __name__ == "__main__":
    main()
