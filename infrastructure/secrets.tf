# Secrets Manager for OpenAI API key
resource "aws_secretsmanager_secret" "openai_api_key" {
  name        = "${var.project_name}/openai-api-key/${var.environment}"
  description = "OpenAI API key for LLM service"

  tags = {
    Name = "${var.project_name}-openai-secret-${var.environment}"
  }
}

resource "aws_secretsmanager_secret_version" "openai_api_key" {
  secret_id = aws_secretsmanager_secret.openai_api_key.id
  secret_string = jsonencode({
    api_key = var.openai_api_key
  })
}

# Secrets Manager for Google OAuth
resource "aws_secretsmanager_secret" "google_oauth" {
  name        = "${var.project_name}/google-oauth/${var.environment}"
  description = "Google OAuth credentials"

  tags = {
    Name = "${var.project_name}-google-oauth-secret-${var.environment}"
  }
}

resource "aws_secretsmanager_secret_version" "google_oauth" {
  secret_id = aws_secretsmanager_secret.google_oauth.id
  secret_string = jsonencode({
    client_id     = var.google_client_id
    client_secret = var.google_client_secret
  })
}

