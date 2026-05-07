output "api_id" {
  description = "API Gateway HTTP API ID."
  value       = aws_apigatewayv2_api.http_api.id
}

output "api_url" {
  description = "API Gateway HTTP API invoke URL."
  value       = aws_apigatewayv2_api.http_api.api_endpoint
}

output "api_name" {
  description = "API Gateway HTTP API name."
  value       = aws_apigatewayv2_api.http_api.name
}
