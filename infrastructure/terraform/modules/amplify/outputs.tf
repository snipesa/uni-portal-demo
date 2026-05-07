output "app_id" {
  description = "Amplify app ID."
  value       = aws_amplify_app.this.id
}

output "default_domain" {
  description = "Amplify default branch URL."
  value       = "https://${aws_amplify_branch.environment.branch_name}.${aws_amplify_app.this.default_domain}"
}

output "app_name" {
  description = "Amplify app name."
  value       = aws_amplify_app.this.name
}
