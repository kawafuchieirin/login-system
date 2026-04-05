variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
}

variable "github_repository" {
  description = "GitHub repository in owner/repo format"
  type        = string
}

variable "ecr_repository_arn" {
  description = "ARN of the ECR repository"
  type        = string
}

variable "lambda_function_arn" {
  description = "ARN of the Lambda function"
  type        = string
}
