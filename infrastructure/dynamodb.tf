# DynamoDB table for games
resource "aws_dynamodb_table" "games" {
  name           = "${var.project_name}-games-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST" # Cost-effective: pay only for what you use
  hash_key       = "game_id"
  range_key      = "move_id"

  attribute {
    name = "game_id"
    type = "S"
  }

  attribute {
    name = "move_id"
    type = "S"
  }

  attribute {
    name = "user_id"
    type = "S"
  }

  # Global Secondary Index for querying by user
  global_secondary_index {
    name            = "user-games-index"
    hash_key        = "user_id"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  # Enable TTL for automatic cleanup (optional)
  ttl {
    attribute_name = "ttl"
    enabled        = false # Set to true if you want auto-delete old games
  }

  tags = {
    Name = "${var.project_name}-games-${var.environment}"
  }
}

# DynamoDB table for users
resource "aws_dynamodb_table" "users" {
  name         = "${var.project_name}-users-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "user_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "email"
    type = "S"
  }

  # Global Secondary Index for querying by email
  global_secondary_index {
    name            = "email-index"
    hash_key        = "email"
    projection_type = "ALL"
  }

  tags = {
    Name = "${var.project_name}-users-${var.environment}"
  }
}

