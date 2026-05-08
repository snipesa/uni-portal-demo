data "aws_region" "current" {}

resource "aws_cognito_user_pool" "this" {
  name = var.user_pool_name

  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]
  mfa_configuration        = "OFF"
  deletion_protection      = "INACTIVE"

  username_configuration {
    case_sensitive = false
  }

  admin_create_user_config {
    allow_admin_create_user_only = false
  }

  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_numbers   = true
    require_symbols   = false
    require_uppercase = true
  }

  lifecycle {
    prevent_destroy = false
  }
}

resource "aws_cognito_user_pool_domain" "hosted_ui" {
  domain       = "${var.name_prefix}-auth"
  user_pool_id = aws_cognito_user_pool.this.id
}

resource "aws_cognito_user_pool_client" "spa" {
  name         = "${var.name_prefix}-SpaClient"
  user_pool_id = aws_cognito_user_pool.this.id

  generate_secret                      = false
  explicit_auth_flows                  = ["ALLOW_USER_SRP_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"]
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["email", "openid", "profile"]
  callback_urls                        = var.callback_urls
  logout_urls                          = var.logout_urls
  supported_identity_providers         = ["COGNITO"]
  prevent_user_existence_errors        = "ENABLED"

  access_token_validity  = 60
  id_token_validity      = 60
  refresh_token_validity = 30

  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "days"
  }
}

resource "aws_cognito_user_group" "admin" {
  name         = "Admin"
  description  = "Platform administrators - can manage portal role assignment in Cognito"
  precedence   = 0
  user_pool_id = aws_cognito_user_pool.this.id
}

resource "aws_cognito_user_group" "staff" {
  name         = "Staff"
  description  = "Staff users - course-specific Instructor vs TA access is stored in DynamoDB"
  precedence   = 1
  user_pool_id = aws_cognito_user_pool.this.id
}

resource "aws_cognito_user_group" "students" {
  name         = "Students"
  description  = "Student users - can submit assignments and view their own grades"
  precedence   = 2
  user_pool_id = aws_cognito_user_pool.this.id
}
