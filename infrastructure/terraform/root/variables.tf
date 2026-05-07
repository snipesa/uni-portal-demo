variable "project_name" {
  description = "Project name prefix used for Terraform-managed application resources."
  type        = string
  default     = "cytora-uni-portal"
  nullable    = false
}

variable "environment" {
  description = "Single deployment environment name. Defaults to prod for the migration root."
  type        = string
  default     = "prod"
  nullable    = false
}

variable "aws_region" {
  description = "AWS region for all application resources."
  type        = string
  default     = "us-east-1"
  nullable    = false
}

variable "operations_bucket_name" {
  description = "Name of the manually created operations bucket for Lambda and frontend artifacts."
  type        = string
  nullable    = false
}

variable "lambda_artifact_prefix" {
  description = "Prefix in the operations bucket where Lambda deployment artifacts are stored."
  type        = string
  default     = "lambda-artifacts"
  nullable    = false
}

variable "frontend_artifact_prefix" {
  description = "Prefix in the operations bucket where frontend deployment artifacts are stored."
  type        = string
  default     = "frontend-builds"
  nullable    = false
}

variable "frontend_callback_url" {
  description = "Frontend URL registered as the Cognito Hosted UI callback URL."
  type        = string
  default     = "http://localhost:3000"
  nullable    = false
}

variable "frontend_logout_url" {
  description = "Frontend URL registered as the Cognito Hosted UI logout URL. Defaults to frontend_callback_url when unset."
  type        = string
  default     = null
}

variable "additional_cognito_callback_urls" {
  description = "Additional Cognito Hosted UI callback URLs, such as Postman OAuth testing."
  type        = list(string)
  default     = ["https://oauth.pstmn.io/v1/callback"]
  nullable    = false
}
