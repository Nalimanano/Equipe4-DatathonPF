import json
import time
import boto3

bedrock_runtime_client = boto3.client('bedrock-runtime', region_name='us-west-2')  


s3_bucket_name = "10kreportspf" 
s3_folder = "10k_reports/"
s3_client = boto3.client('s3', region_name='us-west-2') 


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
    sections = ["1", "1A", "1B", "2", "3", "4", "5", "6", "7", "7A", "8", "9", "9A", "9B", "10", "11", "12", "13", "14", "15"]    
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
        print(f"Tous les fichiers pour le ticker '{ticker}' existent déjà. Résumer le document.")
        combined_text = "\n".join(existing_sections_text.values())
        summarize_document("Combined Sections", combined_text)
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
        summarize_document("Combined Sections", combined_text)

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

def summarize_document(section_name, section_text):
    max_retries = 5
    for attempt in range(max_retries):
        try:
            response = bedrock_runtime_client.invoke_model(
                modelId="anthropic.claude-3-sonnet-20240229-v1:0",
                contentType="application/json",
                accept="application/json",
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 500,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Please summarize the following sections from a financial report: '{section_text}'"
                                }
                            ]
                        }
                    ]
                })
            )
            
            result = json.loads(response['body'].read())
            if result and "content" in result:
                summary = result["content"][0].get("text")
                print(f"Résumé pour {section_name}: {summary}")
            else:
                print(f"Aucun résumé disponible pour la section {section_name}")
            return 
        except Exception as e:
            if "ThrottlingException" in str(e):
                wait_time = 2 ** attempt
                print(f"ThrottlingException: {e}. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"Erreur d'accès au modèle Bedrock pour la section {section_name}:", e)
                return
    print(f"Max retries reached for {section_name}. Skipping résumé.")


ticker = input("Entrez le ticker de l'entreprise (ex: NVDA) : ")
get_latest_10k_report(ticker) 
