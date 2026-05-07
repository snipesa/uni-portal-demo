locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

module "upload_bucket" {
  source = "../modules/upload-bucket"

  bucket_name  = "${local.name_prefix}-upload-bucket"
  environment  = var.environment
  name_prefix  = local.name_prefix
  project_name = var.project_name
}

module "cognito" {
  source = "../modules/cognito"

  callback_urls  = distinct(concat([var.frontend_callback_url], var.additional_cognito_callback_urls))
  environment    = var.environment
  logout_urls    = [coalesce(var.frontend_logout_url, var.frontend_callback_url)]
  name_prefix    = local.name_prefix
  project_name   = var.project_name
  user_pool_name = "${local.name_prefix}-user-pool"
}

module "dynamodb" {
  source = "../modules/dynamodb"

  environment  = var.environment
  name_prefix  = local.name_prefix
  project_name = var.project_name
  table_name   = "${local.name_prefix}-MainTable"
}

module "rest_api_lambda" {
  source = "../modules/rest-api-lambda"

  environment             = var.environment
  lambda_code_bucket_name = var.operations_bucket_name
  main_table_arn          = module.dynamodb.table_arn
  main_table_name         = module.dynamodb.table_name
  project_name            = var.project_name
  upload_bucket_arn       = module.upload_bucket.bucket_arn
  upload_bucket_name      = module.upload_bucket.bucket_name
  user_pool_arn           = module.cognito.user_pool_arn
  user_pool_id            = module.cognito.user_pool_id
}

module "http_api" {
  source = "../modules/http-api"

  environment         = var.environment
  lambda_arn          = module.rest_api_lambda.lambda_arn
  project_name        = var.project_name
  user_pool_client_id = module.cognito.user_pool_client_id
  user_pool_id        = module.cognito.user_pool_id
}

module "amplify" {
  source = "../modules/amplify"

  app_name                 = "${local.name_prefix}-amplify-app"
  environment              = var.environment
  frontend_artifact_prefix = var.frontend_artifact_prefix
  name_prefix              = local.name_prefix
  operations_bucket_name   = var.operations_bucket_name
  project_name             = var.project_name
}
