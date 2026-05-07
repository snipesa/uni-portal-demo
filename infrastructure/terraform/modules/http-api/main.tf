locals {
  route_keys = toset([
    "POST /uploads/request",
    "POST /uploads/confirm",
    "GET /submissions",
    "GET /submissions/{submissionId}",
    "GET /submissions/{submissionId}/details",
    "POST /submissions/{submissionId}/status",
    "POST /submissions/{submissionId}/versions/request",
    "POST /submissions/{submissionId}/versions/confirm",
    "POST /comments",
    "POST /grades",
    "GET /admin/users",
    "POST /admin/groups/add",
    "POST /admin/groups/remove",
    "GET /downloads/{submissionId}/{versionNumber}",
    "GET /courses",
    "POST /courses",
    "GET /courses/{courseId}/terms/{termId}",
    "GET /courses/{courseId}/terms/{termId}/assignments",
    "POST /courses/{courseId}/terms/{termId}/assignments",
    "POST /courses/{courseId}/terms/{termId}/enrollments",
    "DELETE /courses/{courseId}/terms/{termId}/enrollments",
    "POST /courses/{courseId}/terms/{termId}/staff",
    "DELETE /courses/{courseId}/terms/{termId}/staff",
  ])
}

resource "aws_apigatewayv2_api" "http_api" {
  name          = "${var.project_name}-${var.environment}-http-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "DELETE", "OPTIONS"]
    allow_headers = [
      "Authorization",
      "Content-Type",
      "X-Amz-Date",
      "X-Api-Key",
      "X-Amz-Security-Token",
    ]
    max_age = 3000
  }
}

resource "aws_apigatewayv2_authorizer" "cognito_jwt" {
  api_id           = aws_apigatewayv2_api.http_api.id
  name             = "${var.project_name}-${var.environment}-cognito-jwt-authorizer"
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]

  jwt_configuration {
    issuer   = "https://cognito-idp.${split("_", var.user_pool_id)[0]}.amazonaws.com/${var.user_pool_id}"
    audience = [var.user_pool_client_id]
  }
}

resource "aws_apigatewayv2_integration" "rest_lambda" {
  api_id                 = aws_apigatewayv2_api.http_api.id
  integration_type       = "AWS_PROXY"
  integration_method     = "POST"
  integration_uri        = var.lambda_arn
  payload_format_version = "2.0"
  timeout_milliseconds   = 29000
}

resource "aws_apigatewayv2_route" "protected" {
  for_each = local.route_keys

  api_id             = aws_apigatewayv2_api.http_api.id
  route_key          = each.value
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito_jwt.id
  target             = "integrations/${aws_apigatewayv2_integration.rest_lambda.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.http_api.id
  name        = "$default"
  auto_deploy = true

  default_route_settings {
    detailed_metrics_enabled = true
  }
}

resource "aws_lambda_permission" "rest_api_lambda_invoke" {
  statement_id  = "AllowExecutionFromHttpApi"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_arn
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.http_api.execution_arn}/*/*"
}
