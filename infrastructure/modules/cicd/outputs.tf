output "pipeline_arn" {
  value = aws_codepipeline.main.arn
}

output "codebuild_project_name" {
  value = aws_codebuild_project.deploy.name
}

output "github_connection_arn" {
  value       = aws_codestarconnections_connection.github.arn
  description = "CodeStar Connection ARN. Must be manually approved in AWS Console after terraform apply."
}
