output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = module.api_gateway.api_endpoint
}

output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = module.ecr.repository_url
}

output "cloudfront_url" {
  description = "CloudFront distribution URL"
  value       = "https://${module.frontend.cloudfront_domain_name}"
}

output "frontend_bucket" {
  description = "S3 bucket for frontend assets"
  value       = module.frontend.s3_bucket_name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = module.frontend.cloudfront_distribution_id
}
