output "project_name" {
  description = "Project name used for resource naming."
  value       = var.project_name
}

output "environment" {
  description = "Single deployment environment name."
  value       = var.environment
}

output "aws_region" {
  description = "AWS region used by this Terraform root."
  value       = var.aws_region
}

output "name_prefix" {
  description = "Shared resource name prefix."
  value       = local.name_prefix
}

output "operations_bucket_name" {
  description = "Manual operations bucket used for deployment artifacts."
  value       = var.operations_bucket_name
}

output "lambda_artifact_prefix" {
  description = "Operations bucket prefix for Lambda artifacts."
  value       = var.lambda_artifact_prefix
}

output "frontend_artifact_prefix" {
  description = "Operations bucket prefix for frontend artifacts."
  value       = var.frontend_artifact_prefix
}

output "upload_bucket_name" {
  description = "Application upload bucket name."
  value       = module.upload_bucket.bucket_name
}

output "upload_bucket_arn" {
  description = "Application upload bucket ARN."
  value       = module.upload_bucket.bucket_arn
}

output "user_pool_id" {
  description = "Cognito user pool ID."
  value       = module.cognito.user_pool_id
}

output "user_pool_arn" {
  description = "Cognito user pool ARN."
  value       = module.cognito.user_pool_arn
}

output "user_pool_client_id" {
  description = "Cognito app client ID for the frontend."
  value       = module.cognito.user_pool_client_id
}

output "user_pool_domain" {
  description = "Cognito Hosted UI domain prefix."
  value       = module.cognito.user_pool_domain
}

output "user_pool_auth_domain" {
  description = "Cognito Hosted UI auth domain URL for frontend config."
  value       = module.cognito.user_pool_auth_domain
}

output "main_table_name" {
  description = "DynamoDB main table name."
  value       = module.dynamodb.table_name
}

output "main_table_arn" {
  description = "DynamoDB main table ARN."
  value       = module.dynamodb.table_arn
}

output "rest_api_lambda_name" {
  description = "REST API Lambda function name."
  value       = module.rest_api_lambda.lambda_name
}

output "rest_api_lambda_arn" {
  description = "REST API Lambda function ARN."
  value       = module.rest_api_lambda.lambda_arn
}

output "http_api_id" {
  description = "API Gateway HTTP API ID."
  value       = module.http_api.api_id
}

output "http_api_url" {
  description = "API Gateway HTTP API invoke URL for frontend config."
  value       = module.http_api.api_url
}

output "amplify_app_id" {
  description = "Amplify application ID used by frontend deploy scripts."
  value       = module.amplify.app_id
}

output "amplify_default_domain" {
  description = "Amplify default branch URL."
  value       = module.amplify.default_domain
}
