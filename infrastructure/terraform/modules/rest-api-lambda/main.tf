locals {
  function_name = "${var.project_name}-${var.environment}-rest-api"
}

data "aws_ssm_parameter" "lambda_code_s3_key" {
  name = "/${var.project_name}/${var.environment}/rest-lambda-zip"
}

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "rest_api_lambda" {
  name               = "${var.project_name}-${var.environment}-RestApiLambdaRole"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_cloudwatch_log_group" "rest_api_lambda" {
  name              = "/aws/lambda/${local.function_name}"
  retention_in_days = 14
}

data "aws_iam_policy_document" "lambda_base_logs" {
  statement {
    effect = "Allow"

    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = [
      aws_cloudwatch_log_group.rest_api_lambda.arn,
      "${aws_cloudwatch_log_group.rest_api_lambda.arn}:*",
    ]
  }
}

resource "aws_iam_role_policy" "lambda_base_logs" {
  name   = "LambdaBaseLogs"
  role   = aws_iam_role.rest_api_lambda.id
  policy = data.aws_iam_policy_document.lambda_base_logs.json
}

data "aws_iam_policy_document" "s3_presigned_put_and_get" {
  statement {
    effect = "Allow"

    actions = [
      "s3:PutObject",
      "s3:GetObject",
    ]

    resources = ["${var.upload_bucket_arn}/*"]
  }
}

resource "aws_iam_role_policy" "s3_presigned_put_and_get" {
  name   = "S3PresignedPutAndGet"
  role   = aws_iam_role.rest_api_lambda.id
  policy = data.aws_iam_policy_document.s3_presigned_put_and_get.json
}

data "aws_iam_policy_document" "dynamodb_full_crud" {
  statement {
    effect = "Allow"

    actions = [
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:GetItem",
      "dynamodb:BatchGetItem",
      "dynamodb:Query",
      "dynamodb:DeleteItem",
      "dynamodb:BatchWriteItem",
      "dynamodb:TransactWriteItems",
    ]

    resources = [
      var.main_table_arn,
      "${var.main_table_arn}/index/*",
    ]
  }
}

resource "aws_iam_role_policy" "dynamodb_full_crud" {
  name   = "DynamoDBFullCRUD"
  role   = aws_iam_role.rest_api_lambda.id
  policy = data.aws_iam_policy_document.dynamodb_full_crud.json
}

data "aws_iam_policy_document" "cognito_user_lookup" {
  statement {
    effect = "Allow"

    actions = [
      "cognito-idp:ListUsers",
      "cognito-idp:AdminListGroupsForUser",
      "cognito-idp:AdminAddUserToGroup",
      "cognito-idp:AdminRemoveUserFromGroup",
    ]

    resources = [var.user_pool_arn]
  }
}

resource "aws_iam_role_policy" "cognito_user_lookup" {
  name   = "CognitoUserLookup"
  role   = aws_iam_role.rest_api_lambda.id
  policy = data.aws_iam_policy_document.cognito_user_lookup.json
}

resource "aws_lambda_function" "rest_api" {
  function_name = local.function_name
  role          = aws_iam_role.rest_api_lambda.arn
  runtime       = "python3.12"
  handler       = "lambda_function.lambda_handler"
  memory_size   = 256
  timeout       = 29

  s3_bucket = var.lambda_code_bucket_name
  s3_key    = data.aws_ssm_parameter.lambda_code_s3_key.value

  environment {
    variables = {
      UPLOAD_BUCKET_NAME           = var.upload_bucket_name
      MAIN_TABLE_NAME              = var.main_table_name
      USER_POOL_ID                 = var.user_pool_id
      PRESIGNED_URL_EXPIRY_SECONDS = "900"
      ENVIRONMENT                  = var.environment
      LOG_LEVEL                    = "INFO"
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.rest_api_lambda,
    aws_iam_role_policy.cognito_user_lookup,
    aws_iam_role_policy.dynamodb_full_crud,
    aws_iam_role_policy.lambda_base_logs,
    aws_iam_role_policy.s3_presigned_put_and_get,
  ]
}
