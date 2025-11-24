import boto3
from botocore.exceptions import ClientError
from datetime import datetime
import uuid
import logging
from typing import Dict, Any, Optional, List
from ..core.config import settings

logger = logging.getLogger(__name__)

class DynamoDBService:
    def __init__(self):
        self.table_name = settings.dynamodb_table_name
        self.region = settings.aws_region
        
        # Initialize boto3 client
        # It will automatically use environment variables or AWS profile
        try:
            if settings.aws_access_key_id and settings.aws_secret_access_key:
                self.dynamodb = boto3.resource(
                    'dynamodb',
                    region_name=self.region,
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key
                )
            else:
                session_kwargs = {'region_name': self.region}
                if settings.aws_profile:
                    session_kwargs['profile_name'] = settings.aws_profile
                
                session = boto3.Session(**session_kwargs)
                self.dynamodb = session.resource('dynamodb')
                
            self.table = self.dynamodb.Table(self.table_name)
            logger.info(f"DynamoDB Service initialized for table: {self.table_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize DynamoDB Service: {e}")
            self.table = None

    def get_user(self, email: str) -> Optional[Dict[str, Any]]:
        """Retrieve user data by email"""
        if not self.table:
            logger.warning("DynamoDB table not initialized")
            return None
            
        try:
            response = self.table.get_item(Key={'email': email})
            return response.get('Item')
        except ClientError as e:
            logger.error(f"Error getting user {email}: {e}")
            return None

    def update_user_login(self, email: str) -> bool:
        """
        Update user's last login timestamp.
        Creates the user if they don't exist.
        """
        if not self.table:
            return False
            
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        try:
            # Try to update existing user first
            self.table.update_item(
                Key={'email': email},
                UpdateExpression="SET last_login = :t",
                ExpressionAttributeValues={':t': timestamp},
                ConditionExpression="attribute_exists(email)"
            )
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                # User doesn't exist, create new user
                try:
                    self.table.put_item(
                        Item={
                            'email': email,
                            'total_games_played': 0,
                            'game_list': {},
                            'last_login': timestamp
                        }
                    )
                    logger.info(f"Created new user in DynamoDB: {email}")
                    return True
                except ClientError as put_error:
                    logger.error(f"Error creating user {email}: {put_error}")
                    return False
            else:
                logger.error(f"Error updating login for {email}: {e}")
                return False

    def add_game_result(self, email: str, game_id: str, game_data: Dict[str, Any]) -> bool:
        """
        Add a game result to the user's history.
        Increments total_games_played and adds to game_list map.
        """
        if not self.table:
            return False
            
        try:
            # Ensure game_id is a string
            game_uuid = str(game_id)
            
            # Prepare the update expression
            # We use a map for game_list where key is the game_uuid
            update_expr = "SET game_list.#gid = :g, total_games_played = total_games_played + :inc"
            expr_names = {'#gid': game_uuid}
            expr_values = {
                ':g': game_data,
                ':inc': 1
            }
            
            self.table.update_item(
                Key={'email': email},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_names,
                ExpressionAttributeValues=expr_values
            )
            logger.info(f"Added game {game_uuid} to user {email}")
            return True
        except ClientError as e:
            logger.error(f"Error adding game result for {email}: {e}")
            return False

# Global instance
dynamodb_service = DynamoDBService()
