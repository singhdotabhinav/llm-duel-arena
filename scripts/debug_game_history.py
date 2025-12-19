#!/usr/bin/env python3
"""
Debug script to check game history issues
Run this to diagnose why games aren't showing up in My Games
"""

import os
import sys
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Get settings without importing services that have circular dependencies
aws_region = os.getenv("AWS_REGION", "us-east-1")
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
dynamodb_table_name = os.getenv("DYNAMODB_TABLE_NAME", "llm-duel-arena-users")
active_games_table_name = "LLM-Duel-ActiveGames"

# Initialize boto3 directly to avoid circular imports
if aws_access_key_id and aws_secret_access_key:
    dynamodb = boto3.resource(
        "dynamodb",
        region_name=aws_region,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )
else:
    dynamodb = boto3.resource("dynamodb", region_name=aws_region)

users_table = dynamodb.Table(dynamodb_table_name)
active_games_table = dynamodb.Table(active_games_table_name)

def check_tables():
    """Check if tables exist and are accessible"""
    print("=" * 60)
    print("DYNAMODB TABLES CHECK")
    print("=" * 60)
    
    # Check users table
    print(f"\n1. Users Table: {dynamodb_table_name}")
    try:
        table_desc = users_table.meta.client.describe_table(TableName=dynamodb_table_name)
        print(f"   ✅ Table exists and is accessible")
        print(f"   Status: {table_desc['Table']['TableStatus']}")
        print(f"   Item Count: {table_desc['Table'].get('ItemCount', 'N/A')}")
    except ClientError as e:
        print(f"   ❌ Error accessing table: {e}")
    
    # Check active games table
    print(f"\n2. Active Games Table: {active_games_table_name}")
    try:
        table_desc = active_games_table.meta.client.describe_table(TableName=active_games_table_name)
        print(f"   ✅ Table exists and is accessible")
        print(f"   Status: {table_desc['Table']['TableStatus']}")
        print(f"   Item Count: {table_desc['Table'].get('ItemCount', 'N/A')}")
    except ClientError as e:
        print(f"   ❌ Error accessing table: {e}")

def check_user_data(email: str):
    """Check user data in DynamoDB"""
    print("\n" + "=" * 60)
    print(f"USER DATA CHECK: {email}")
    print("=" * 60)
    
    try:
        response = users_table.get_item(Key={"email": email})
        user_data = response.get("Item")
    except ClientError as e:
        print(f"❌ Error getting user data: {e}")
        return
    
    if not user_data:
        print(f"❌ No user data found for {email}")
        print(f"\nPossible issues:")
        print(f"  1. User hasn't logged in yet (user record not created)")
        print(f"  2. Wrong table name (check DYNAMODB_TABLE_NAME env var)")
        print(f"  3. Wrong email address")
        print(f"\nCurrent table name: {dynamodb_table_name}")
        return
    
    print(f"✅ User data found!")
    print(f"\nUser data keys: {list(user_data.keys())}")
    print(f"Total games played: {user_data.get('total_games_played', 0)}")
    print(f"Last login: {user_data.get('last_login', 'N/A')}")
    
    game_list = user_data.get('game_list', {})
    print(f"\nGame list:")
    if not game_list:
        print(f"   ⚠️  No games in game_list (empty map)")
        print(f"\nPossible issues:")
        print(f"  1. Games haven't completed yet (only completed games are saved)")
        print(f"  2. Games completed but user_id wasn't set")
        print(f"  3. save_game_to_db() wasn't called when games finished")
    else:
        print(f"   ✅ Found {len(game_list)} games")
        for i, (game_id, game_data) in enumerate(list(game_list.items())[:5], 1):
            print(f"\n   Game {i}:")
            print(f"     ID: {game_id[:12]}...")
            print(f"     Type: {game_data.get('game_type') or game_data.get('game', 'unknown')}")
            print(f"     Models: {game_data.get('white_model')} vs {game_data.get('black_model')}")
            print(f"     Moves: {game_data.get('total_moves', 0)}")
            print(f"     Completed: {game_data.get('completed_at', 'N/A')}")
        if len(game_list) > 5:
            print(f"   ... and {len(game_list) - 5} more games")

def check_active_games():
    """Check active games in DynamoDB"""
    print("\n" + "=" * 60)
    print("ACTIVE GAMES CHECK")
    print("=" * 60)
    
    try:
        # Scan for active games (limit to 10)
        response = active_games_table.scan(Limit=10)
        items = response.get('Items', [])
        
        print(f"\nFound {len(items)} active games (showing up to 10)")
        
        for i, item in enumerate(items, 1):
            print(f"\n   Game {i}:")
            print(f"     ID: {item.get('game_id', 'N/A')[:12]}...")
            print(f"     Type: {item.get('game_type', 'unknown')}")
            print(f"     Over: {item.get('over', False)}")
            print(f"     User ID: {item.get('user_id', 'None')}")
            print(f"     Models: {item.get('white_model')} vs {item.get('black_model')}")
            print(f"     Moves: {len(item.get('moves', []))}")
            
            if item.get('over') and not item.get('user_id'):
                print(f"     ⚠️  WARNING: Game is over but has no user_id!")
    except ClientError as e:
        print(f"❌ Error scanning active games: {e}")

def main():
    print("\n" + "=" * 60)
    print("LLM DUEL ARENA - GAME HISTORY DEBUG")
    print("=" * 60)
    
    # Check environment
    print(f"\nEnvironment Configuration:")
    print(f"  AWS Region: {aws_region}")
    print(f"  DynamoDB Table Name: {dynamodb_table_name}")
    print(f"  Active Games Table: {active_games_table_name}")
    
    # Check tables
    check_tables()
    
    # Check active games
    check_active_games()
    
    # Check user data (if email provided)
    if len(sys.argv) > 1:
        email = sys.argv[1]
        check_user_data(email)
    else:
        print("\n" + "=" * 60)
        print("USER DATA CHECK SKIPPED")
        print("=" * 60)
        print("\nTo check a specific user's data, run:")
        print(f"  python {sys.argv[0]} <user-email>")
        print("\nExample:")
        print(f"  python {sys.argv[0]} user@example.com")

if __name__ == "__main__":
    main()

