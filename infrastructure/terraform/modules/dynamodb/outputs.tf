output "table_name" {
  description = "DynamoDB main table name."
  value       = aws_dynamodb_table.main.name
}

output "table_arn" {
  description = "DynamoDB main table ARN."
  value       = aws_dynamodb_table.main.arn
}
