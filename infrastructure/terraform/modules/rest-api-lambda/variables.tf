variable "project_name" {
  description = "Project name used for resource naming."
  type        = string
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
}

variable "name_prefix" {
  description = "Shared resource name prefix."
  type        = string
}

variable "function_name" {
  description = "REST API Lambda function name."
  type        = string
}

variable "operations_bucket_name" {
  description = "Manual operations bucket containing Lambda artifacts."
  type        = string
}

variable "lambda_artifact_prefix" {
  description = "Operations bucket prefix for Lambda artifacts."
  type        = string
}

variable "upload_bucket_name" {
  description = "Application upload bucket name passed to Lambda."
  type        = string
}

variable "main_table_name" {
  description = "DynamoDB main table name passed to Lambda."
  type        = string
}

variable "user_pool_id" {
  description = "Cognito user pool ID passed to Lambda."
  type        = string
}
