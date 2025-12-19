resource "aws_dynamodb_table" "games" {
  name         = "${var.project_name}-games-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "game_id"
  range_key    = "move_id"

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

  attribute {
    name = "created_at"
    type = "S"
  }

  global_secondary_index {
    name            = "user-games-index"
    hash_key        = "user_id"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = false
  }

  tags = {
    Name = "${var.project_name}-games-${var.environment}"
  }
}

resource "aws_dynamodb_table" "users" {
  name         = "${var.project_name}-users-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "email"

  attribute {
    name = "email"
    type = "S"
  }

  attribute {
    name = "user_id"
    type = "S"
  }

  global_secondary_index {
    name            = "user-id-index"
    hash_key        = "user_id"
    projection_type = "ALL"
  }

  tags = {
    Name = "${var.project_name}-users-${var.environment}"
  }
}
