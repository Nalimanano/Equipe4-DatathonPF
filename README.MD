# Financial Analysis Project

This project provides tools for financial analysis using various Python libraries, enabling data retrieval, sentiment analysis, and data visualization. The project leverages multiple APIs and includes AWS configuration for accessing financial data sources and performing analyses.

## Table of Contents

- [Technologies Used](#technologies-used)
- [Installation](#installation)
- [AWS Configuration](#aws-configuration)
- [Usage](#usage)
- [License](#license)
- [Contributing](#contributing)
- [Acknowledgments](#acknowledgments)

## Technologies Used

This project utilizes the following libraries:

- `boto3`: AWS SDK for Python, used to interact with AWS services.
- `sec-api`: Client for accessing the SEC API for financial report extraction.
- `praw`: Python Reddit API Wrapper, used for sentiment analysis on Reddit posts.
- `pandas`: Data manipulation and analysis library.
- `nltk`: Natural Language Toolkit for text processing and sentiment analysis.
- `plotly`: Interactive graphing and data visualization library.
- `matplotlib`: Static and animated plotting library for visualizations.
- `yfinance`: Library for fetching historical market data from Yahoo Finance.
- `mplfinance`: Visualization library specialized for financial data.
- `numpy`: Library for numerical operations and matrix calculations.

## Installation

To set up the project, follow these steps:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Nalimanano/Equipe4-DatathonPF.git
   cd Equipe4-DatathonPF

2. **Install the requirements**:
   pip install boto3
   pip install sec-api
   pip install praw
   pip install pandas
   pip install nltk
   pip install plotly
   pip install matplotlib
   pip install yfinance
   pip install mplfinance
   pip install numpy
   pip install streamlit

3. **Configure AWS**:
   You will be prompted to enter the following information:
     - **AWS Access Key ID**: AKIAQCER2INJ7W3E5J7B
     - **AWS Secret Access Key**: 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
     - **Default region name**: us-west-2
     - **Default output format**: text