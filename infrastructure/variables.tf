variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "login-system"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-northeast-1"
}

variable "jwt_secret_key" {
  description = "JWT secret key for token signing"
  type        = string
  sensitive   = true
}

variable "github_repository" {
  description = "GitHub repository in owner/repo format"
  type        = string
}
