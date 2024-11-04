import re
import json
import praw
import boto3
import pandas as pd
from datetime import datetime
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import nltk
import matplotlib.pyplot as plt

# Télécharger le lexique pour VADER
nltk.download('vader_lexicon')

# Authentification avec l'API de Reddit
reddit = praw.Reddit(
    client_id='owWB16Ir3Z6_9odkKE85Qg',
    client_secret='LMrFbihEblbdRoboMmHHHW2z6xTM1A',
    user_agent='Datathon app (by u/me)'
)

# Initialisation du client Bedrock pour l'analyse de sujets
bedrock_runtime_client = boto3.client('bedrock-runtime', region_name='us-west-2')

# Fonction pour récupérer des posts Reddit en utilisant un mot-clé
def fetch_reddit_posts(keyword, subreddit="wallstreetbets", limit=50):
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
def analyze_topics_per_post(ticker, df):
    try:
        topics_results = []
        
        for i, row in df.iterrows():
            post = row['combined_text']
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
                                                1. Calculate an overall average sentiment score for all posts combined, on a scale from -100 to 100 
                                                (where -100 is very negative, 0 is neutral, and 100 is very positive). Briefly interpret this average score 
                                                (e.g., "A high average score indicates a positive outlook among users").
                                                
                                                2. For each individual post, provide:
                                                   - A brief summary of the main sentiment and topics discussed.
                                                   - The sentiment score of the post (from -100 to 100), with a short explanation of what the score indicates.
                                                   
                                                Output in the following format:
                                                
                                                1. **Overall Sentiment Score: [average sentiment score] - [interpretation of the score]**
                                                
                                                2. **Detailed Analysis for Each Post:**
                                                   - Post [Index]:
                                                     - Sentiment Score: [sentiment score for the post] - [brief explanation of the score]
                                                     - Key Points: [Very brief summary of main sentiment and topics]
                                                
                                                Reddit Posts:
                                                '{post}'
                                                """



                                }
                            ]
                        }
                    ]
                })
            )

            # Extraction de l'analyse de sujets pour chaque post
            result = json.loads(response['body'].read())
            if result and "content" in result:
                topics_analysis = result["content"][0].get("text")
                topics_results.append({"post_index": i, "topics": topics_analysis})
                print(f"Main Topics for post #{i+1} of {ticker}: {topics_analysis}")
            else:
                print(f"No topic analysis available for post #{i+1} of ticker {ticker}")
        
        return topics_results
    except Exception as e:
        print(f"Error accessing Bedrock model for ticker {ticker}:", e)
        return []

# Exemple d'utilisation
ticker = "TSLA"
reddit_posts_df = fetch_reddit_posts(ticker)

# Effectuer l'analyse des sujets
topics_results = analyze_topics_per_post(ticker, reddit_posts_df)