terraform {
  backend "s3" {
    bucket         = "llm-duel-arena-terraform-state"
    key            = "int/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "llm-duel-arena-terraform-locks"
    encrypt        = true
  }
}
