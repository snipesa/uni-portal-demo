resource "aws_iam_role" "amplify_service_role" {
  name = "${var.project_name}-${var.environment}-amplify-service-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "amplify.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "amplify_s3_artifact_access" {
  name = "AmplifyS3ArtifactAccess"
  role = aws_iam_role.amplify_service_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ReadFrontendBuilds"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
        ]
        Resource = "arn:aws:s3:::${var.operations_bucket_name}/${var.frontend_artifact_prefix}/*"
      }
    ]
  })
}

resource "aws_amplify_app" "this" {
  name                 = "${var.project_name}-${var.environment}"
  platform             = "WEB"
  iam_service_role_arn = aws_iam_role.amplify_service_role.arn

  custom_rule {
    source = "</^[^.]+$|\\.(?!(css|gif|ico|jpg|js|png|txt|svg|woff|woff2|ttf|map|json)$)([^.]+$)/>"
    target = "/index.html"
    status = "200"
  }
}

resource "aws_amplify_branch" "environment" {
  app_id                  = aws_amplify_app.this.id
  branch_name             = var.environment
  enable_auto_build       = false
  enable_performance_mode = false
}
