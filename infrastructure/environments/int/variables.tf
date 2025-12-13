variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "llm-duel-arena"
}

# Removed unused variables:
# - openai_api_key (not used - using Ollama/HuggingFace)
# - google_client_id (not used - using Cognito)
# - google_client_secret (not used - using Cognito)
# - domain_name (not purchased yet)
