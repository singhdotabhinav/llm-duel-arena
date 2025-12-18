#!/usr/bin/env python3
"""
Backfill script to save completed games from ActiveGames table to user history
This fixes games that completed but weren't saved to user's game_list
"""

import os
import sys
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Get settings
aws_region = os.getenv("AWS_REGION", "us-east-1")
aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
dynamodb_table_name = os.getenv("DYNAMODB_TABLE_NAME", "llm-duel-arena-users")
active_games_table_name = "LLM-Duel-ActiveGames"

# Initialize boto3
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

# Also check the alternative table name (in case user data is in different table)
alt_users_table_name = "llm-duel-arena-users" if dynamodb_table_name != "llm-duel-arena-users" else "llm-duel-arena-users-int"
alt_users_table = dynamodb.Table(alt_users_table_name)


def save_game_to_user_history(email: str, game_id: str, game_data: dict, table=None):
    """Save a game to user's history in DynamoDB"""
    if table is None:
        table = users_table
    
    try:
        # First check if user exists
        try:
            response = table.get_item(Key={"email": email})
            if "Item" not in response:
                print(f"  ⚠️  User {email} not found in table {table.table_name}")
                return False
        except ClientError as e:
            print(f"  ❌ Error checking user existence: {e}")
            return False
        
        game_uuid = str(game_id)
        
        # Prepare update expression
        update_expr = "SET game_list.#gid = :g, total_games_played = total_games_played + :inc"
        expr_names = {"#gid": game_uuid}
        expr_values = {":g": game_data, ":inc": 1}
        
        # Try to add new game and increment counter
        try:
            table.update_item(
                Key={"email": email},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_names,
                ExpressionAttributeValues=expr_values,
                ConditionExpression="attribute_not_exists(game_list.#gid)",
            )
            print(f"  ✅ Saved game {game_id[:12]}... to user history")
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                # Game already exists, just update
                print(f"  ⚠️  Game {game_id[:12]}... already in history, updating...")
                table.update_item(
                    Key={"email": email},
                    UpdateExpression="SET game_list.#gid = :g",
                    ExpressionAttributeNames=expr_names,
                    ExpressionAttributeValues={":g": game_data},
                )
                return True
            elif e.response["Error"]["Code"] == "ValidationException":
                # game_list doesn't exist, initialize it
                print(f"  ⚠️  Initializing game_list for user...")
                table.update_item(
                    Key={"email": email},
                    UpdateExpression="SET game_list = :empty_map, total_games_played = if_not_exists(total_games_played, :zero)",
                    ExpressionAttributeValues={":empty_map": {}, ":zero": 0},
                    ConditionExpression="attribute_not_exists(game_list)",
                )
                # Retry
                table.update_item(
                    Key={"email": email},
                    UpdateExpression=update_expr,
                    ExpressionAttributeNames=expr_names,
                    ExpressionAttributeValues=expr_values,
                    ConditionExpression="attribute_not_exists(game_list.#gid)",
                )
                print(f"  ✅ Saved game {game_id[:12]}... to user history (after init)")
                return True
            else:
                raise e
    except ClientError as e:
        print(f"  ❌ Error saving game: {e}")
        return False


def backfill_completed_games():
    """Find all completed games and save them to user history"""
    print("=" * 60)
    print("BACKFILL COMPLETED GAMES")
    print("=" * 60)
    
    try:
        # Scan for completed games
        print("\nScanning for completed games...")
        response = active_games_table.scan(
            FilterExpression="#over = :over",
            ExpressionAttributeNames={"#over": "over"},
            ExpressionAttributeValues={":over": True}
        )
        items = response.get('Items', [])
        
        print(f"Found {len(items)} completed games\n")
        
        saved_count = 0
        skipped_count = 0
        
        for item in items:
            game_id = item.get('game_id')
            user_id = item.get('user_id')
            
            if not user_id:
                print(f"⚠️  Game {game_id[:12]}... has no user_id, skipping")
                skipped_count += 1
                continue
            
            print(f"Processing game {game_id[:12]}...")
            print(f"  User: {user_id}")
            print(f"  Type: {item.get('game_type')}")
            print(f"  Models: {item.get('white_model')} vs {item.get('black_model')}")
            
            # Prepare game data
            result = item.get('result', {})
            result_str = result.get("winner") or result.get("result") or "draw"
            
            game_data = {
                "game_id": game_id,
                "game_type": item.get('game_type'),
                "game": item.get('game_type'),  # Backward compatibility
                "p1": item.get('white_model') or "Unknown",
                "p2": item.get('black_model') or "Unknown",
                "result": result_str,
                "result_dict": result,
                "white_model": item.get('white_model'),
                "black_model": item.get('black_model'),
                "white_tokens": item.get('white_tokens', 0),
                "black_tokens": item.get('black_tokens', 0),
                "total_moves": len(item.get('moves', [])),
                "completed_at": datetime.utcnow().isoformat() + "Z",
            }
            
            # Try saving to primary table first
            success = save_game_to_user_history(user_id, game_id, game_data, table=users_table)
            
            # If failed and tables are different, try alternative table
            if not success and dynamodb_table_name != alt_users_table_name:
                print(f"  Trying alternative table: {alt_users_table_name}")
                success = save_game_to_user_history(user_id, game_id, game_data, table=alt_users_table)
            
            if success:
                saved_count += 1
            else:
                skipped_count += 1
            
            print()
        
        print("=" * 60)
        print(f"SUMMARY")
        print("=" * 60)
        print(f"✅ Saved: {saved_count} games")
        print(f"⚠️  Skipped: {skipped_count} games")
        
    except ClientError as e:
        print(f"❌ Error scanning games: {e}")


if __name__ == "__main__":
    backfill_completed_games()

