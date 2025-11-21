resource "aws_lambda_function" "game" {
  filename      = "${path.module}/../../deployments/game.zip"
  function_name = "${var.project_name}-game-${var.environment}"
  role          = aws_iam_role.lambda_role.arn
  handler       = "game_handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 30
  memory_size   = 512

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.games.name
      ENVIRONMENT    = var.environment
    }
  }

  tags = {
    Name = "${var.project_name}-game-${var.environment}"
  }
}

resource "aws_lambda_function" "auth" {
  filename      = "${path.module}/../../deployments/auth.zip"
  function_name = "${var.project_name}-auth-${var.environment}"
  role          = aws_iam_role.lambda_role.arn
  handler       = "auth_handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 15
  memory_size   = 256

  environment {
    variables = {
      DYNAMODB_TABLE              = aws_dynamodb_table.users.name
      ENVIRONMENT                 = var.environment
      GOOGLE_CLIENT_ID_SECRET_ARN = aws_secretsmanager_secret.google_oauth.arn
    }
  }

  tags = {
    Name = "${var.project_name}-auth-${var.environment}"
  }
}

resource "aws_lambda_function" "llm" {
  filename      = "${path.module}/../../deployments/llm.zip"
  function_name = "${var.project_name}-llm-${var.environment}"
  role          = aws_iam_role.lambda_role.arn
  handler       = "llm_handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 60
  memory_size   = 1024

  environment {
    variables = {
      OPENAI_API_KEY_SECRET_ARN = aws_secretsmanager_secret.openai_api_key.arn
      ENVIRONMENT               = var.environment
    }
  }

  tags = {
    Name = "${var.project_name}-llm-${var.environment}"
  }
}

resource "aws_lambda_function_url" "game" {
  function_name      = aws_lambda_function.game.function_name
  authorization_type = "NONE"

  cors {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE"]
    allow_headers = ["*"]
  }
}

resource "aws_lambda_function_url" "auth" {
  function_name      = aws_lambda_function.auth.function_name
  authorization_type = "NONE"

  cors {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST"]
    allow_headers = ["*"]
  }
}

resource "aws_lambda_function_url" "llm" {
  function_name      = aws_lambda_function.llm.function_name
  authorization_type = "AWS_IAM"

  cors {
    allow_origins = ["*"]
    allow_methods = ["POST"]
    allow_headers = ["*"]
  }
}
