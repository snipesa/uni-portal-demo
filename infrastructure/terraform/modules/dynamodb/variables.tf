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

variable "table_name" {
  description = "DynamoDB main table name."
  type        = string
}
