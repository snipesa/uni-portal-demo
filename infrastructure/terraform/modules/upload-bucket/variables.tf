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

variable "bucket_name" {
  description = "Application upload bucket name."
  type        = string
}
