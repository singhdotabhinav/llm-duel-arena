import os
import boto3
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

def create_table():
    table_name = os.getenv("DYNAMODB_TABLE_NAME", "llm-duel-arena-users")
    region = os.getenv("AWS_REGION", "eu-north-1")
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

    print(f"Creating table '{table_name}' in region '{region}'...")

    if not aws_access_key or not aws_secret_key:
        print("❌ Error: AWS credentials not found.")
        return

    dynamodb = boto3.resource(
        'dynamodb',
        region_name=region,
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key
    )

    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {
                    'AttributeName': 'email',
                    'KeyType': 'HASH'  # Partition key
                }
            ],
            AttributeDefinitions=[
                {
                    'AttributeName': 'email',
                    'AttributeType': 'S'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        print(f"Table status: {table.table_status}")
        print("Waiting for table to be active...")
        
        table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
        print(f"✅ Table '{table_name}' created successfully and is ACTIVE.")
        
    except Exception as e:
        if "ResourceInUseException" in str(e):
             print(f"✅ Table '{table_name}' already exists in '{region}'.")
        else:
            print(f"❌ Failed to create table: {e}")

if __name__ == "__main__":
    create_table()
