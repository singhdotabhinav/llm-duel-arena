output "api_gateway_url" {
  description = "API Gateway endpoint URL"
  value       = aws_apigatewayv2_api.main.api_endpoint
}

output "cloudfront_url" {
  description = "CloudFront distribution URL"
  value       = aws_cloudfront_distribution.main.domain_name
}

output "dynamodb_table_name" {
  description = "DynamoDB table name"
  value       = aws_dynamodb_table.games.name
}

output "s3_bucket_name" {
  description = "S3 bucket for static assets"
  value       = aws_s3_bucket.static_assets.bucket
}

output "lambda_function_names" {
  description = "Lambda function names"
  value = {
    game = aws_lambda_function.game.function_name
    auth = aws_lambda_function.auth.function_name
    llm  = aws_lambda_function.llm.function_name
  }
}
