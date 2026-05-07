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

variable "user_pool_name" {
  description = "Cognito user pool name."
  type        = string
}

variable "callback_urls" {
  description = "Allowed OAuth callback URLs for the SPA app client."
  type        = list(string)

  validation {
    condition     = length(var.callback_urls) > 0
    error_message = "callback_urls must include at least one URL."
  }
}

variable "logout_urls" {
  description = "Allowed logout URLs for the SPA app client."
  type        = list(string)

  validation {
    condition     = length(var.logout_urls) > 0
    error_message = "logout_urls must include at least one URL."
  }
}
