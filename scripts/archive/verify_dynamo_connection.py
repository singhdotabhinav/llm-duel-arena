import os
import boto3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def verify_connection():
    table_name = os.getenv("DYNAMODB_TABLE_NAME")
    region = os.getenv("AWS_REGION", "us-east-1")
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

    print(f"Checking connection to table '{table_name}' in region '{region}'...")
    
    if not aws_access_key or not aws_secret_key:
        print("❌ Error: AWS credentials not found in environment variables.")
        return

    try:
        dynamodb = boto3.resource(
            'dynamodb',
            region_name=region,
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key
        )
        table = dynamodb.Table(table_name)
        
        # Check if table exists by accessing a property
        print(f"Table status: {table.table_status}")
        print("✅ Successfully connected to DynamoDB!")
        
    except Exception as e:
        print(f"❌ Failed to connect: {e}")

if __name__ == "__main__":
    verify_connection()
