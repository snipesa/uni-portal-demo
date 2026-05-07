output "bucket_name" {
  description = "Application upload bucket name."
  value       = aws_s3_bucket.upload.id
}

output "bucket_arn" {
  description = "Application upload bucket ARN."
  value       = aws_s3_bucket.upload.arn
}
