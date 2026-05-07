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

variable "api_name" {
  description = "API Gateway HTTP API name."
  type        = string
}

variable "lambda_name" {
  description = "REST API Lambda function name for invoke permission."
  type        = string
}

variable "lambda_arn" {
  description = "REST API Lambda function ARN for API integration."
  type        = string
}

variable "user_pool_id" {
  description = "Cognito user pool ID for the JWT authorizer."
  type        = string
}

variable "user_pool_client_id" {
  description = "Cognito user pool client ID for the JWT authorizer audience."
  type        = string
}
