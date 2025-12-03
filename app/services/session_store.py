"""
DynamoDB-backed session store for AWS Lambda deployment
Provides persistent session storage with automatic expiration
"""

import json
import time
import logging
import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

import boto3
from botocore.exceptions import ClientError

from ..core.config import settings

logger = logging.getLogger(__name__)


class DynamoDBSessionStore:
    """
    DynamoDB-backed session store with TTL support
    Cheaper than Redis for low-medium traffic applications
    """
    
    def __init__(self, table_name: str = None):
        """
        Initialize DynamoDB session store
        
        Args:
            table_name: Name of DynamoDB table for sessions
        """
        self.table_name = table_name or settings.session_table_name
        
        # Initialize DynamoDB client
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            self.dynamodb = boto3.resource(
                'dynamodb',
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key
            )
        else:
            # Use default credentials (IAM role in Lambda)
            self.dynamodb = boto3.resource('dynamodb', region_name=settings.aws_region)
        
        self.table = self.dynamodb.Table(self.table_name)
        logger.info(f"DynamoDB session store initialized with table: {self.table_name}")
    
    def create_session(self, user_data: Dict[str, Any], ttl_seconds: int = 3600) -> str:
        """
        Create a new session
        
        Args:
            user_data: User data to store in session
            ttl_seconds: Session TTL in seconds (default 1 hour)
        
        Returns:
            session_id: Generated session ID
        """
        session_id = secrets.token_urlsafe(32)
        ttl = int(time.time()) + ttl_seconds
        
        try:
            self.table.put_item(
                Item={
                    'session_id': session_id,
                    'user_data': json.dumps(user_data),
                    'created_at': datetime.utcnow().isoformat(),
                    'ttl': ttl  # DynamoDB will auto-delete after this timestamp
                }
            )
            logger.info(f"Created session {session_id[:8]}... with TTL {ttl}")
            return session_id
        
        except ClientError as e:
            logger.error(f"Failed to create session: {e}")
            raise
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session data
        
        Args:
            session_id: Session ID to retrieve
        
        Returns:
            User data dict or None if session not found/expired
        """
        try:
            response = self.table.get_item(Key={'session_id': session_id})
            
            if 'Item' not in response:
                logger.debug(f"Session {session_id[:8]}... not found")
                return None
            
            item = response['Item']
            
            # Check if session has expired (belt-and-suspenders with DynamoDB TTL)
            if int(time.time()) > item.get('ttl', 0):
                logger.debug(f"Session {session_id[:8]}... expired")
                self.delete_session(session_id)  # Clean up
                return None
            
            user_data = json.loads(item['user_data'])
            logger.debug(f"Retrieved session {session_id[:8]}...")
            return user_data
        
        except ClientError as e:
            logger.error(f"Failed to get session: {e}")
            return None
    
    def update_session(self, session_id: str, user_data: Dict[str, Any]) -> bool:
        """
        Update session data
        
        Args:
            session_id: Session ID to update
            user_data: New user data
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.table.update_item(
                Key={'session_id': session_id},
                UpdateExpression='SET user_data = :data',
                ExpressionAttributeValues={
                    ':data': json.dumps(user_data)
                }
            )
            logger.debug(f"Updated session {session_id[:8]}...")
            return True
        
        except ClientError as e:
            logger.error(f"Failed to update session: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session
        
        Args:
            session_id: Session ID to delete
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.table.delete_item(Key={'session_id': session_id})
            logger.info(f"Deleted session {session_id[:8]}...")
            return True
        
        except ClientError as e:
            logger.error(f"Failed to delete session: {e}")
            return False
    
    def extend_session(self, session_id: str, ttl_seconds: int = 3600) -> bool:
        """
        Extend session TTL
        
        Args:
            session_id: Session ID to extend
            ttl_seconds: New TTL in seconds from now
        
        Returns:
            True if successful, False otherwise
        """
        new_ttl = int(time.time()) + ttl_seconds
        
        try:
            self.table.update_item(
                Key={'session_id': session_id},
                UpdateExpression='SET ttl = :ttl',
                ExpressionAttributeValues={
                    ':ttl': new_ttl
                }
            )
            logger.debug(f"Extended session {session_id[:8]}... to TTL {new_ttl}")
            return True
        
        except ClientError as e:
            logger.error(f"Failed to extend session: {e}")
            return False


class InMemorySessionStore:
    """
    In-memory session store for local development
    Falls back to this when DynamoDB is not available/configured
    """
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        logger.info("In-memory session store initialized (local development mode)")
    
    def create_session(self, user_data: Dict[str, Any], ttl_seconds: int = 3600) -> str:
        session_id = secrets.token_urlsafe(32)
        self.sessions[session_id] = {
            'user_data': user_data,
            'expires_at': time.time() + ttl_seconds
        }
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # Check expiration
        if time.time() > session['expires_at']:
            del self.sessions[session_id]
            return None
        
        return session['user_data']
    
    def update_session(self, session_id: str, user_data: Dict[str, Any]) -> bool:
        if session_id not in self.sessions:
            return False
        
        self.sessions[session_id]['user_data'] = user_data
        return True
    
    def delete_session(self, session_id: str) -> bool:
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def extend_session(self, session_id: str, ttl_seconds: int = 3600) -> bool:
        if session_id not in self.sessions:
            return False
        
        self.sessions[session_id]['expires_at'] = time.time() + ttl_seconds
        return True


# Global session store instance
# Use DynamoDB in AWS, in-memory for local development
def get_session_store():
    """
    Get the appropriate session store based on deployment mode
    """
    if settings.use_dynamodb_sessions and not settings.is_local:
        return DynamoDBSessionStore()
    else:
        return InMemorySessionStore()


# Singleton instance
session_store = get_session_store()
