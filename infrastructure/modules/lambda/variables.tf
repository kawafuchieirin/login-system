variable "project_name" {
  type = string
}

variable "ecr_repo_url" {
  type = string
}

variable "environment_variables" {
  type = map(string)
}

variable "dynamodb_table_arns" {
  type = list(string)
}
