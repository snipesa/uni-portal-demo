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

variable "app_name" {
  description = "Amplify app name."
  type        = string
}

variable "operations_bucket_name" {
  description = "Manual operations bucket containing frontend artifacts."
  type        = string
}

variable "frontend_artifact_prefix" {
  description = "Operations bucket prefix for frontend artifacts."
  type        = string
}
