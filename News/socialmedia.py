import re
import json
import praw
import boto3
import pandas as pd
from datetime import datetime
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
import matplotlib.pyplot as plt
import plotly.graph_objects as go

nltk.download('vader_lexicon')

reddit = praw.Reddit(
    client_id='owWB16Ir3Z6_9odkKE85Qg',
    client_secret='LMrFbihEblbdRoboMmHHHW2z6xTM1A',
    user_agent='Datathon app (by u/me)'
)

# Initialisation du client Bedrock pour l'analyse de sujets
bedrock_runtime_client = boto3.client('bedrock-runtime', region_name='us-west-2')

# Fonction pour récupérer des posts Reddit en utilisant un mot-clé
def fetch_reddit_posts(keyword, subreddit="wallstreetbets", limit=10):
    posts = []
    subreddit_instance = reddit.subreddit(subreddit)

    for submission in subreddit_instance.search(keyword, limit=limit):
        posts.append({
            "date": datetime.fromtimestamp(submission.created_utc),
            "title": submission.title,
            "text": submission.selftext,
            "score": submission.score,
            "num_comments": submission.num_comments
        })
    
    df = pd.DataFrame(posts)
    # Combiner le titre et le texte dans une nouvelle colonne 'combined_text'
    df['combined_text'] = df['title'] + ' ' + df['text']
    return df

# 2. Analyse de Sujets avec Claude 3 Sonnet
def analyze_topics_all_posts(ticker, df):
    try:
        # Combine all posts' text into one string
        all_posts = " ".join(df['combined_text'].tolist())
        
        # Send a single request to analyze all posts at once
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
                                "text": f"""
                                            Analyze recent Reddit posts related to the stock ticker '{ticker}'.
                                            
                                            1. Calculate an overall average sentiment score for all posts combined, on a scale from 0 to 100 
                                            (where 0 is very negative, 50 is neutral, and 100 is very positive).
                                            
                                            2. Provide 1 to 3 key insights about sentiment trends or main topics discussed.
                                            
                                            Output format:
                                            - Average Sentiment Score: [average score]
                                            - Key Insights: [1 to 3 insights in bullet points]
                                            
                                            Reddit Posts:
                                            '{all_posts}'
                                            """
                            }
                        ]
                    }
                ]
            })
        )

        # Process the response
        result = json.loads(response['body'].read())
        if result and "content" in result:
            topics_analysis = result["content"][0].get("text")
            print(f"Topics and social Analysis for {ticker}: {topics_analysis}")
            social_file_name = f"{ticker}_social_analysis.txt"
            save_social_to_file(social_file_name, ticker, topics_analysis)
            
            return {"ticker": ticker, "analysis": topics_analysis}
        else:
            print(f"No analysis available for ticker {ticker}")
            return {}
    except Exception as e:
        print(f"Error accessing Bedrock model for ticker {ticker}:", e)
        return {}

def save_social_to_file(file_name, ticker, topics_analysis):
    with open(file_name, "a") as f:
        f.write(f"social for {ticker}:\n{topics_analysis}\n\n")
    print(f"social analysis saved to {file_name}")


def create_gauge2(score):
    fig = go.Figure()

    # Define limits
    min_val = 0
    max_val = 100

    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": "Sentiment Score", "font": {"color": "black"}},
        gauge={
            "axis": {"range": [min_val, max_val], "tickcolor": "darkgray"},
            "bar": {"color": "royalblue"},  # Stronger blue for the bar
            "bgcolor": "whitesmoke",  # Light background for contrast
            "steps": [
                {"range": [0, 50], "color": "#FF4500"},  # Dark orange for negative
                {"range": [50, 75], "color": "#FFD700"},  # Gold for neutral
                {"range": [75, 100], "color": "#32CD32"},  # Lime green for positive
            ],
            "threshold": {
                "line": {"color": "darkblue", "width": 4},  # Highlighting line for score
                "value": score, 
            },
        }
    ))

    fig.update_layout(paper_bgcolor="white")
    return fig