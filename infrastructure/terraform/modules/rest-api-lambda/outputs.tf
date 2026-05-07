output "lambda_name" {
  description = "REST API Lambda function name."
  value       = aws_lambda_function.rest_api.function_name
}

output "lambda_arn" {
  description = "REST API Lambda function ARN."
  value       = aws_lambda_function.rest_api.arn
}
