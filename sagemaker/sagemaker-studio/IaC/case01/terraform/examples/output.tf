output "vpc_id" {
  description = "The ID of the VPC"
  value       = try(module.vpc_for_sagemaker.vpc_id, "")
}

output "vpc_arn" {
  description = "The ARN of the VPC"
  value       = try(module.vpc_for_sagemaker.vpc_arn, "")
}

output "vpc_cidr_block" {
  description = "The CIDR block of the VPC"
  value       = try(module.vpc_for_sagemaker.vpc_cidr_block, "")
}

output "aws_iam_user_password" {
  value = { for p in aws_iam_user_login_profile.iam_login_profile : p.user => p.encrypted_password }
}