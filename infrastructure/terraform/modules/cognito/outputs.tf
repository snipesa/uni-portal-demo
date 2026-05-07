output "user_pool_id" {
  description = "Cognito user pool ID."
  value       = aws_cognito_user_pool.this.id
}

output "user_pool_arn" {
  description = "Cognito user pool ARN."
  value       = aws_cognito_user_pool.this.arn
}

output "user_pool_client_id" {
  description = "Cognito app client ID."
  value       = aws_cognito_user_pool_client.spa.id
}

output "user_pool_domain" {
  description = "Cognito Hosted UI domain prefix."
  value       = aws_cognito_user_pool_domain.hosted_ui.domain
}

output "user_pool_auth_domain" {
  description = "Cognito Hosted UI auth domain URL."
  value       = "https://${aws_cognito_user_pool_domain.hosted_ui.domain}.auth.${data.aws_region.current.name}.amazoncognito.com"
}

output "user_pool_name" {
  description = "Cognito user pool name."
  value       = var.user_pool_name
}
