terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

module "llm_duel_arena" {
  source = "../../modules/core"

  aws_region  = var.aws_region
  environment = var.environment
  project_name = var.project_name
  # Removed unused variables: openai_api_key, google_client_id, google_client_secret, domain_name
}

output "api_gateway_url" {
  value = module.llm_duel_arena.api_gateway_url
}

output "cloudfront_url" {
  value = module.llm_duel_arena.cloudfront_url
}

output "dynamodb_table_name" {
  value = module.llm_duel_arena.dynamodb_table_name
}

output "s3_bucket_name" {
  value = module.llm_duel_arena.s3_bucket_name
}
