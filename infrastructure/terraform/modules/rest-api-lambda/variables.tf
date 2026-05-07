variable "project_name" {
  description = "Project name used for resource naming."
  type        = string
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
}

variable "lambda_code_bucket_name" {
  description = "S3 bucket that holds the Lambda deployment zip."
  type        = string
}

variable "upload_bucket_name" {
  description = "Application upload bucket name passed to Lambda."
  type        = string
}

variable "upload_bucket_arn" {
  description = "Application upload bucket ARN used by the Lambda IAM policy."
  type        = string
}

variable "main_table_name" {
  description = "DynamoDB main table name passed to Lambda."
  type        = string
}

variable "main_table_arn" {
  description = "DynamoDB main table ARN used by the Lambda IAM policy."
  type        = string
}

variable "user_pool_id" {
  description = "Cognito user pool ID passed to Lambda."
  type        = string
}

variable "user_pool_arn" {
  description = "Cognito user pool ARN used by the Lambda IAM policy."
  type        = string
}
