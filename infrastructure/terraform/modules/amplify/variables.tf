variable "project_name" {
  description = "Project name used for resource naming."
  type        = string
}

variable "environment" {
  description = "Deployment environment name."
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
