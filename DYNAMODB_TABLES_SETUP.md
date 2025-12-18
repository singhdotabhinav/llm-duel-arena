# DynamoDB Tables Setup Guide

This document lists all DynamoDB tables that need to be created manually for the LLM Duel Arena application.

## Required Tables

### 1. **LLM-Duel-ActiveGames**
**Purpose**: Stores active/in-progress game states

**Primary Key**:
- `game_id` (String, Partition Key - HASH)

**Billing Mode**: `PAY_PER_REQUEST` (On-Demand)

**Attributes Stored**:
- `game_id` (String) - Primary Key
- `game_type` (String) - Type of game (chess, tic_tac_toe, etc.)
- `state` (String) - Game board state (FEN for chess, board string for others)
- `turn` (String) - Current turn (white/black)
- `over` (Boolean) - Whether game is finished
- `result` (Map) - Game result dictionary
- `white_model` (String) - Model playing as white
- `black_model` (String) - Model playing as black
- `white_tokens` (Number) - Tokens used by white model
- `black_tokens` (Number) - Tokens used by black model
- `user_id` (String) - User who created the game (email)
- `moves` (List) - Array of move records

**AWS CLI Creation Command**:
```bash
aws dynamodb create-table \
  --table-name LLM-Duel-ActiveGames \
  --attribute-definitions AttributeName=game_id,AttributeType=S \
  --key-schema AttributeName=game_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

**Terraform/Console Settings**:
- Table Name: `LLM-Duel-ActiveGames`
- Partition Key: `game_id` (String)
- Billing Mode: On-Demand (PAY_PER_REQUEST)
- No Sort Key required
- No Global Secondary Indexes required

---

### 2. **llm-duel-arena-users-int** (or value from `DYNAMODB_TABLE_NAME` env var)
**Note**: If using Terraform, the table name will be `${project_name}-users-${environment}`, which typically results in `llm-duel-arena-users-int` for the int environment.
**Purpose**: Stores user accounts and completed game history

**Primary Key**:
- `email` (String, Partition Key - HASH)

**Billing Mode**: `PAY_PER_REQUEST` (On-Demand) or `PROVISIONED` (5 RCU/5 WCU)

**Attributes Stored**:
- `email` (String) - Primary Key (user's email address)
- `total_games_played` (Number) - Total number of games played
- `last_login` (String) - ISO timestamp of last login
- `game_list` (Map) - Map of game_id → game_data
  - Each game entry contains:
    - `game_id` (String)
    - `game_type` (String)
    - `game` (String) - Backward compatibility field
    - `white_model` (String)
    - `black_model` (String)
    - `p1` (String) - Backward compatibility field
    - `p2` (String) - Backward compatibility field
    - `result` (String) - Winner/result string
    - `result_dict` (Map) - Full result dictionary
    - `total_moves` (Number)
    - `completed_at` (String) - ISO timestamp
    - `white_tokens` (Number)
    - `black_tokens` (Number)

**AWS CLI Creation Command**:
```bash
aws dynamodb create-table \
  --table-name llm-duel-arena-users \
  --attribute-definitions AttributeName=email,AttributeType=S \
  --key-schema AttributeName=email,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

**Terraform/Console Settings**:
- Table Name: `llm-duel-arena-users` (or your custom name from `DYNAMODB_TABLE_NAME`)
- Partition Key: `email` (String)
- Billing Mode: On-Demand (PAY_PER_REQUEST) recommended, or Provisioned (5/5)
- No Sort Key required
- No Global Secondary Indexes required

---

### 3. **LLM-Duel-Sessions** (Optional - only if `USE_DYNAMODB_SESSIONS=true`)
**Purpose**: Stores user session data with TTL support

**Primary Key**:
- `session_id` (String, Partition Key - HASH)

**TTL Attribute**:
- `ttl` (Number) - Unix timestamp for automatic expiration

**Billing Mode**: `PAY_PER_REQUEST` (On-Demand)

**Attributes Stored**:
- `session_id` (String) - Primary Key
- `user_data` (String) - JSON string of user data
- `created_at` (String) - ISO timestamp
- `ttl` (Number) - Unix timestamp for expiration (DynamoDB TTL)

**AWS CLI Creation Command**:
```bash
# Step 1: Create the table first
aws dynamodb create-table \
  --table-name LLM-Duel-Sessions \
  --attribute-definitions AttributeName=session_id,AttributeType=S \
  --key-schema AttributeName=session_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1

# Step 2: Wait for table to be active, then enable TTL
aws dynamodb update-time-to-live \
  --table-name LLM-Duel-Sessions \
  --time-to-live-specification Enabled=true,AttributeName=ttl \
  --region us-east-1
```

**Alternative: Using JSON format for TTL (single command)**:
```bash
aws dynamodb create-table \
  --table-name LLM-Duel-Sessions \
  --attribute-definitions AttributeName=session_id,AttributeType=S \
  --key-schema AttributeName=session_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1

# Then enable TTL separately (required - TTL cannot be set during table creation)
aws dynamodb update-time-to-live \
  --table-name LLM-Duel-Sessions \
  --time-to-live-specification '{"Enabled":true,"AttributeName":"ttl"}' \
  --region us-east-1
```

**Terraform/Console Settings**:
- Table Name: `LLM-Duel-Sessions`
- Partition Key: `session_id` (String)
- Billing Mode: On-Demand (PAY_PER_REQUEST)
- TTL Enabled: Yes
- TTL Attribute: `ttl`
- No Sort Key required
- No Global Secondary Indexes required

**Note**: This table is only needed if you set `USE_DYNAMODB_SESSIONS=true` in your environment variables. Otherwise, sessions are stored in-memory (local development) or using cookies.

---

## Quick Setup Script

You can use this Python script to create all tables:

```python
import boto3
from botocore.exceptions import ClientError

def create_tables(region='us-east-1'):
    dynamodb = boto3.resource('dynamodb', region_name=region)
    
    tables = [
        {
            'name': 'LLM-Duel-ActiveGames',
            'key': 'game_id',
            'ttl': None
        },
        {
            'name': 'llm-duel-arena-users',
            'key': 'email',
            'ttl': None
        },
        {
            'name': 'LLM-Duel-Sessions',
            'key': 'session_id',
            'ttl': 'ttl'
        }
    ]
    
    for table_config in tables:
        try:
            table = dynamodb.create_table(
                TableName=table_config['name'],
                KeySchema=[
                    {'AttributeName': table_config['key'], 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': table_config['key'], 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            
            if table_config['ttl']:
                # Enable TTL after table creation
                table.wait_until_exists()
                table.meta.client.update_time_to_live(
                    TableName=table_config['name'],
                    TimeToLiveSpecification={
                        'Enabled': True,
                        'AttributeName': table_config['ttl']
                    }
                )
            
            print(f"✅ Created table: {table_config['name']}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"⚠️  Table {table_config['name']} already exists")
            else:
                print(f"❌ Error creating {table_config['name']}: {e}")

if __name__ == '__main__':
    create_tables()
```

---

## Environment Variables Reference

Make sure these are set in your `.env` file:

```bash
# Required
DYNAMODB_TABLE_NAME=llm-duel-arena-users  # Users table name
AWS_REGION=us-east-1

# Optional (only if using DynamoDB for sessions)
SESSION_TABLE_NAME=LLM-Duel-Sessions
USE_DYNAMODB_SESSIONS=false  # Set to true to use DynamoDB sessions (recommended for AWS Lambda)
```

### When to Use DynamoDB Sessions

**Use DynamoDB Sessions (`USE_DYNAMODB_SESSIONS=true`) when:**
- Deploying to AWS Lambda (serverless)
- Need sessions to persist across Lambda cold starts
- Running multiple Lambda instances (sessions shared across instances)
- Want automatic session expiration via DynamoDB TTL

**Use Cookie-Based Sessions (`USE_DYNAMODB_SESSIONS=false`) when:**
- Running locally for development
- Using a single server instance
- Don't have DynamoDB access configured

---

## Verification

After creating tables, verify they exist:

```bash
aws dynamodb list-tables --region us-east-1
```

You should see:
- `LLM-Duel-ActiveGames`
- `llm-duel-arena-users` (or your custom name)
- `LLM-Duel-Sessions` (if using DynamoDB sessions)

