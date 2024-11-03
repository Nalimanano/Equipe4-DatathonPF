from sec_api import QueryApi, ExtractorApi
import boto3
import json
import os
import time

# Initialisation des APIs
api_key = "92b5d37f639c36b7bdd4f83b8210cfb76706934bf25a2883bd1f3da6f2c28113"
queryApi = QueryApi(api_key=api_key)
extractorApi = ExtractorApi(api_key=api_key)

# Configurer le client Bedrock Runtime
bedrock_runtime_client = boto3.client('bedrock-runtime', region_name='us-west-2')  # Modify region if necessary

# Configuration S3
s3_bucket_name = "10kreportspf"  # Replace with your S3 bucket name
s3_folder = "10k_reports/"  # Folder in the S3 bucket where files will be saved

# Create S3 client
s3_client = boto3.client('s3', region_name='us-west-2')  # Modify region if necessary

# Function to create the S3 bucket if it doesn't exist
def create_bucket_if_not_exists(bucket_name):
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"Bucket '{bucket_name}' already exists.")
    except Exception as e:
        try:
            s3_client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={
                'LocationConstraint': 'us-west-2' 
            })
            print(f"Bucket '{bucket_name}' created successfully.")
        except Exception as e:
            print(f"Error creating bucket: {e}")

create_bucket_if_not_exists(s3_bucket_name)

def get_latest_10k_report(ticker):
    sections = ["1", "1A", "7"]    
    existing_sections_text = {}

    for section in sections:
        s3_file_name = f"{s3_folder}{ticker}_section_{section}.txt"
        try:
            s3_client.head_object(Bucket=s3_bucket_name, Key=s3_file_name)
            print(f"Le fichier '{s3_file_name}' existe déjà dans S3.")
            
            response = s3_client.get_object(Bucket=s3_bucket_name, Key=s3_file_name)
            section_text = response['Body'].read().decode('utf-8')
            existing_sections_text[section] = section_text
        except Exception:
            pass

    if existing_sections_text:
        print(f"Tous les fichiers pour le ticker '{ticker}' existent déjà. Effectuer l'analyse de sentiment.")
        combined_text = "\n".join(existing_sections_text.values())
        analyze_sentiment("Combined Sections", combined_text, ticker)
        return

    query = {
        "query": f"ticker:{ticker} AND formType:\"10-K\"",
        "from": "0",
        "size": "1",
        "sort": [{"filedAt": {"order": "desc"}}]
    }

    filings = queryApi.get_filings(query)
    if not filings.get("filings"):
        print("Aucun rapport 10-K trouvé pour ce ticker.")
        return None
    filing_url = filings["filings"][0].get("linkToFilingDetails")
    if not filing_url:
        print("Aucun lien valide pour le rapport 10-K.")
        return None

    combined_text = ""
    
    for section in sections:
        try:
            section_text = extractorApi.get_section(filing_url, str(section), "text")
            if section_text:
                combined_text += section_text + "\n"  
                s3_file_name = f"{s3_folder}{ticker}_section_{section}.txt"
                s3_upload(section_text, s3_file_name)
        except Exception as e:
            print(f"Erreur lors de l'extraction de la section {section}: {e}")

    if combined_text:
        analyze_sentiment("Combined Sections", combined_text, ticker)

def s3_upload(file_content, file_name):
    try:
        s3_client.head_object(Bucket=s3_bucket_name, Key=file_name)
        print(f"Le fichier '{file_name}' existe déjà dans S3, aucune action effectuée.")
    except Exception:
        try:
            s3_client.put_object(Bucket=s3_bucket_name, Key=file_name, Body=file_content.encode('utf-8'))
            print(f"Section sauvegardée avec succès dans S3 : '{file_name}'")
        except Exception as e:
            print(f"Erreur lors de l'upload vers S3 : {e}")

def analyze_sentiment(section_name, section_text, ticker):
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = bedrock_runtime_client.invoke_model(
                modelId="anthropic.claude-3-sonnet-20240229-v1:0",
                contentType="application/json",
                accept="application/json",
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 50000,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Analyze the sentiment of the following sections from a financial report : '{section_text}', give a sentimental analysis index score from 0 to 1"
                                }
                            ]
                        }
                    ]
                })
            )
            
            result = json.loads(response['body'].read())
            if result and "content" in result:
                sentiment_analysis = result["content"][0].get("text")
                print(f"Sentiment for {section_name}: {sentiment_analysis}")
                
                # Save sentiment analysis to a text file
                sentiment_file_name = f"{ticker}_sentiment_analysis.txt"
                save_sentiment_to_file(sentiment_file_name, section_name, sentiment_analysis)
                
            else:
                print(f"Aucune analyse de sentiment disponible pour la section {section_name}")
            return 
        except Exception as e:
            if "ThrottlingException" in str(e):
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"ThrottlingException: {e}. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)  # Wait before retrying
            else:
                print(f"Erreur d'accès au modèle Bedrock pour la section {section_name}:", e)
                return  # Exit on other errors
    print(f"Max retries reached for {section_name}. Skipping sentiment analysis.")

def save_sentiment_to_file(file_name, section_name, sentiment_analysis):
    with open(file_name, "a") as f:
        f.write(f"Sentiment for {section_name}:\n{sentiment_analysis}\n\n")
    print(f"Sentiment analysis saved to {file_name}")

ticker = input("Entrez le ticker de l'entreprise (ex: NVDA) : ") 
get_latest_10k_report(ticker)
