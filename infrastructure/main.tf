terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "dynamodb" {
  source       = "./modules/dynamodb"
  project_name = var.project_name
}

module "ecr" {
  source       = "./modules/ecr"
  project_name = var.project_name
}

module "lambda" {
  source       = "./modules/lambda"
  project_name = var.project_name
  ecr_repo_url = module.ecr.repository_url

  environment_variables = {
    USERS_TABLE_NAME                 = module.dynamodb.users_table_name
    TODOS_TABLE_NAME                 = module.dynamodb.todos_table_name
    WEBAUTHN_CREDENTIALS_TABLE_NAME  = module.dynamodb.webauthn_credentials_table_name
    AUTH_CHALLENGES_TABLE_NAME       = module.dynamodb.auth_challenges_table_name
    JWT_SECRET_KEY                   = var.jwt_secret_key
    CORS_ORIGINS                     = "*"
    WEBAUTHN_RP_ID                   = module.frontend.cloudfront_domain_name
    WEBAUTHN_RP_NAME                 = "Login System"
    WEBAUTHN_ORIGIN                  = "https://${module.frontend.cloudfront_domain_name}"
  }

  dynamodb_table_arns = [
    module.dynamodb.users_table_arn,
    module.dynamodb.todos_table_arn,
    module.dynamodb.webauthn_credentials_table_arn,
    module.dynamodb.auth_challenges_table_arn,
  ]
}

module "api_gateway" {
  source              = "./modules/api-gateway"
  project_name        = var.project_name
  lambda_function_arn = module.lambda.function_arn
  lambda_invoke_arn   = module.lambda.invoke_arn
}

module "frontend" {
  source       = "./modules/frontend"
  project_name = var.project_name
  api_endpoint = module.api_gateway.api_endpoint
}

module "cicd" {
  source              = "./modules/cicd"
  project_name        = var.project_name
  github_repository   = var.github_repository
  ecr_repository_arn  = module.ecr.repository_arn
  lambda_function_arn = module.lambda.function_arn
}
