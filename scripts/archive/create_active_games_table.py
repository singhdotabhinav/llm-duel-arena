import boto3
import os
import sys
from botocore.exceptions import ClientError

# Add project root to path
sys.path.append(os.getcwd())

from app.core.config import settings

def create_active_games_table():
    region = settings.aws_region
    
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        dynamodb = boto3.resource(
            'dynamodb',
            region_name=region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key
        )
    else:
        dynamodb = boto3.resource('dynamodb', region_name=region)
        
    table_name = 'LLM-Duel-ActiveGames'

    try:
        table = dynamodb.create_table(
            TableName=table_name,
            KeySchema=[
                {'AttributeName': 'game_id', 'KeyType': 'HASH'}  # Partition key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'game_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print(f"Creating table {table_name}...")
        table.wait_until_exists()
        print(f"Table {table_name} created successfully.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"Table {table_name} already exists.")
        else:
            print(f"Error creating table: {e}")

if __name__ == '__main__':
    create_active_games_table()
