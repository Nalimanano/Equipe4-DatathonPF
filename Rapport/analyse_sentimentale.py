import warnings
warnings.filterwarnings('ignore')
import json
import datetime
import os
import boto3
import uuid
import random
import pandas as pd
import time
from datasets import Dataset
import jsonlines
from datetime import datetime


session = boto3.session.Session()
region = session.region_name
sts_client = boto3.client('sts')
account_id = sts_client.get_caller_identity()["Account"]
s3_suffix = f"{region}-{account_id}"
bucket_name = f"bedrock-haiku-customization-{s3_suffix}"
s3_client = boto3.client('s3')
bedrock = boto3.client(service_name="bedrock")
bedrock_runtime = boto3.client(service_name="bedrock-runtime")
iam = boto3.client('iam', region_name=region)

# Generate a unique role name and access policy
suffix = str(uuid.uuid4())
role_name = "BedrockRole-" + suffix
s3_bedrock_finetuning_access_policy = "BedrockPolicy-" + suffix
customization_role = f"arn:aws:iam::{account_id}:role/{role_name}"

for model in bedrock.list_foundation_models(
    byCustomizationType="FINE_TUNING")["modelSummaries"]:
    for key, value in model.items():
        print(key, ":", value)
    print("-----\n")

# Create IAM role and policy documents
ROLE_DOC = f"""{{
    "Version": "2012-10-17",
    "Statement": [
        {{
            "Effect": "Allow",
            "Principal": {{
                "Service": "bedrock.amazonaws.com"
            }},
            "Action": "sts:AssumeRole",
            "Condition": {{
                "StringEquals": {{
                    "aws:SourceAccount": "{account_id}"
                }},
                "ArnEquals": {{
                    "aws:SourceArn": "arn:aws:bedrock:{region}:{account_id}:model-customization-job/*"
                }}
            }}
        }}
    ]
}}"""

ACCESS_POLICY_DOC = f"""{{
    "Version": "2012-10-17",
    "Statement": [
        {{
            "Effect": "Allow",
            "Action": [
                "s3:AbortMultipartUpload",
                "s3:DeleteObject",
                "s3:PutObject",
                "s3:GetObject",
                "s3:GetBucketAcl",
                "s3:GetBucketNotification",
                "s3:ListBucket",
                "s3:PutBucketNotification"
            ],
            "Resource": [
                "arn:aws:s3:::{bucket_name}",
                "arn:aws:s3:::{bucket_name}/*"
            ]
        }}
    ]
}}"""

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return super().default(obj)

# Create IAM Role
response = iam.create_role(
    RoleName=role_name,
    AssumeRolePolicyDocument=ROLE_DOC,
    Description="Role for Bedrock to access S3 for haiku finetuning",
)

role_arn = response["Role"]["Arn"]

# Create IAM Policy
response = iam.create_policy(
    PolicyName=s3_bedrock_finetuning_access_policy,
    PolicyDocument=ACCESS_POLICY_DOC,
)

policy_arn = response["Policy"]["Arn"]
iam.attach_role_policy(
    RoleName=role_name,
    PolicyArn=policy_arn,
)

# Load dataset
data = pd.read_csv("data_financial_sentiment.csv")

# Split the dataset
train_data = data.sample(frac=0.8, random_state=42)  # 80% for training
test_data = data.drop(train_data.index)               # Remaining 20% for testing
validation_data = test_data.sample(frac=0.5, random_state=42)  # 10% of total for validation
test_data = test_data.drop(validation_data.index)               # Remaining 10% for testing

# Create datasets
dataset = {
    'train': Dataset.from_pandas(train_data),
    'validation': Dataset.from_pandas(validation_data),
    'test': Dataset.from_pandas(test_data),
}

system_string = "Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request."
instruction = "instruction:\n\nAnalyze the sentiment of the following sentence.\n\ninput:\n"

# Prepare data points
def prepare_data_points(data_subset):
    data_points = []
    for dp in data_subset:
        temp_dict = {
            "system": system_string,
            "messages": [
                {"role": "user", "content": instruction + dp['Sentence']},
                {"role": "assistant", "content": dp['Sentiment']}
            ]
        }
        data_points.append(temp_dict)
    return data_points

datapoints_train = prepare_data_points(dataset['train'])
datapoints_valid = prepare_data_points(dataset['validation'])
datapoints_test = prepare_data_points(dataset['test'])

def dp_transform(data_points, num_dps, max_dp_length):
    """
    Filters and selects a subset of data points based on specified maximum length and desired number of data points.
    """ 
    lines = []
    for dp in data_points:
        if len(dp['system'] + dp['messages'][0]['content'] + dp['messages'][1]['content']) <= max_dp_length:
            lines.append(dp)
    random.shuffle(lines)
    return lines[:num_dps]

# Define paths and ensure directory exists
dataset_folder = "haiku-fine-tuning-datasets-finstatement-sentiment"
train_file_name = "train-fss-1K.jsonl"
validation_file_name = "validation-fss-100.jsonl"
test_file_name = "test-fss-10.jsonl"
abs_path = os.path.abspath(dataset_folder)

# Create the dataset folder if it doesn't exist
if not os.path.exists(abs_path):
    os.makedirs(abs_path)

# Function to convert dataset to JSONL format
def jsonl_converter(dataset, file_path):
    with jsonlines.open(file_path, 'w') as writer:
        for line in dataset:
            writer.write(line)

# Generate and save datasets
train = dp_transform(datapoints_train, 1000, 20000)
validation = dp_transform(datapoints_valid, 100, 20000)
test = dp_transform(datapoints_test, 10, 20000)

# Write datasets to JSONL files
jsonl_converter(train, os.path.join(abs_path, train_file_name))
jsonl_converter(validation, os.path.join(abs_path, validation_file_name))
jsonl_converter(test, os.path.join(abs_path, test_file_name))

# Upload files to S3 with error handling
def upload_to_s3(file_path, bucket, s3_key):
    try:
        s3_client.upload_file(file_path, bucket, s3_key)
        print(f"Successfully uploaded {file_path} to s3://{bucket}/{s3_key}")
    except Exception as e:
        print(f"Error uploading {file_path} to S3: {e}")

# Uploading datasets to S3
upload_to_s3(os.path.join(abs_path, train_file_name), bucket_name, f'haiku-fine-tuning-datasets/train/{train_file_name}')
upload_to_s3(os.path.join(abs_path, validation_file_name), bucket_name, f'haiku-fine-tuning-datasets/validation/{validation_file_name}')
upload_to_s3(os.path.join(abs_path, test_file_name), bucket_name, f'haiku-fine-tuning-datasets/test/{test_file_name}')

# Print S3 URIs
s3_train_uri = f's3://{bucket_name}/haiku-fine-tuning-datasets/train/{train_file_name}'
s3_validation_uri = f's3://{bucket_name}/haiku-fine-tuning-datasets/validation/{validation_file_name}'
s3_test_uri = f's3://{bucket_name}/haiku-fine-tuning-datasets/test/{test_file_name}'

print("S3 URIs:")
print(f"Train: {s3_train_uri}")
print(f"Validation: {s3_validation_uri}")
print(f"Test: {s3_test_uri}")

print("\n" + "="*100)
print("Starting Fine-Tuning Process...")

base_model_id = "anthropic.claude-3-haiku-20240307-v1:0:200k"
test_file_name = "test-fss-10.jsonl"
data_folder = "haiku-fine-tuning-datasets"

ts = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
customization_job_name = f"model-finetune-job-{ts}"
custom_model_name = f"finetuned-model-{ts}"
customization_role = role_arn
customization_type = "FINE_TUNING"

hyper_parameters = {
        "epochCount": "2",
        "batchSize": "32",
        "learningRateMultiplier": "1",
        "earlyStoppingThreshold": "0.001",
        "earlyStoppingPatience": "2"
    }

s3_bucket_config=f's3://{bucket_name}/outputs/output-{custom_model_name}'
training_data_config = {"s3Uri": s3_train_uri}
validation_data_config = {
        "validators": [{
            "s3Uri": s3_validation_uri
        }]
    }

output_data_config = {"s3Uri": s3_bucket_config}

training_job_response = bedrock.create_model_customization_job(
    customizationType=customization_type,
    jobName=customization_job_name,
    customModelName=custom_model_name,
    roleArn=customization_role,
    baseModelIdentifier=base_model_id,
    hyperParameters=hyper_parameters,
    trainingDataConfig=training_data_config,
    validationDataConfig=validation_data_config,
    outputDataConfig=output_data_config
)
training_job_response

fine_tune_job = bedrock.get_model_customization_job(jobIdentifier=customization_job_name)["status"]
print(fine_tune_job)

while fine_tune_job == "InProgress":
    time.sleep(60)
    fine_tune_job = bedrock.get_model_customization_job(jobIdentifier=customization_job_name)["status"]
    print (fine_tune_job)
    time.sleep(60)
fine_tune_job = bedrock.get_model_customization_job(jobIdentifier=customization_job_name)
print.pp(fine_tune_job)
output_job_name = "model-customization-job-"+fine_tune_job['jobArn'].split('/')[-1]
output_job_name

