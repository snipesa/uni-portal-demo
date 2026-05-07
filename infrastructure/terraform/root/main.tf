locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }

  resource_names = {
    amplify_app     = "${local.name_prefix}-amplify-app"
    http_api        = "${local.name_prefix}-http-api"
    main_table      = "${local.name_prefix}-MainTable"
    rest_api_lambda = "${local.name_prefix}-rest-api-lambda"
    upload_bucket   = "${local.name_prefix}-upload-bucket"
    user_pool       = "${local.name_prefix}-user-pool"
  }
}

module "upload_bucket" {
  source = "../modules/upload-bucket"

  bucket_name  = local.resource_names.upload_bucket
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
  user_pool_name = local.resource_names.user_pool
}

module "dynamodb" {
  source = "../modules/dynamodb"

  environment  = var.environment
  name_prefix  = local.name_prefix
  project_name = var.project_name
  table_name   = local.resource_names.main_table
}

module "rest_api_lambda" {
  source = "../modules/rest-api-lambda"

  environment            = var.environment
  lambda_artifact_prefix = var.lambda_artifact_prefix
  function_name          = local.resource_names.rest_api_lambda
  main_table_name        = module.dynamodb.table_name
  name_prefix            = local.name_prefix
  operations_bucket_name = var.operations_bucket_name
  project_name           = var.project_name
  upload_bucket_name     = module.upload_bucket.bucket_name
  user_pool_id           = module.cognito.user_pool_id
}

module "http_api" {
  source = "../modules/http-api"

  api_name            = local.resource_names.http_api
  environment         = var.environment
  lambda_arn          = module.rest_api_lambda.lambda_arn
  lambda_name         = module.rest_api_lambda.lambda_name
  name_prefix         = local.name_prefix
  project_name        = var.project_name
  user_pool_client_id = module.cognito.user_pool_client_id
  user_pool_id        = module.cognito.user_pool_id
}

module "amplify" {
  source = "../modules/amplify"

  app_name                 = local.resource_names.amplify_app
  environment              = var.environment
  frontend_artifact_prefix = var.frontend_artifact_prefix
  name_prefix              = local.name_prefix
  operations_bucket_name   = var.operations_bucket_name
  project_name             = var.project_name
}
