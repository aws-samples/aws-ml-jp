provider "aws" {
  region = "us-east-1"
  default_tags {
    tags = {
      ProjectName = var.project_name
      Environment = var.environment
    }
  }
}

# ------------------------------------------------------------------------------------------
# ------------------------------------Common resources--------------------------------------
# ------------------------------------------------------------------------------------------
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

# IAM policy for access shared bucket
data "aws_iam_policy_document" "bucket_shared_access" {
  statement {
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:AbortMultipartUpload"
    ]
    resources = ["arn:aws:s3:::${var.project_name}-${var.environment}-bucket-shared",
    "arn:aws:s3:::${var.project_name}-${var.environment}-bucket-shared/*"]
    effect = "Allow"
  }
}

# IAM Policy - Sagemaker S3 access
resource "aws_iam_policy" "allow_backet_shared_access" {
  name   = "allow-bucket-shared-access"
  policy = data.aws_iam_policy_document.bucket_shared_access.json
}

# SageMaker Domain 用の default execution Role
resource "aws_iam_role" "sagemaker_execution_role_default" {
  name               = "sagemaker-execution-role-default"
  assume_role_policy = data.aws_iam_policy_document.sagemaker_assume_role.json
}

# IAM policy attach - Sagemaker権限の付与
resource "aws_iam_policy_attachment" "sagemaker_execution_default_role_full_access" {
  name       = "sagemaker-execution-default-role-full-access"
  roles      = [aws_iam_role.sagemaker_execution_role_default.name]
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"

  depends_on = [aws_iam_role.sagemaker_execution_role_default]
}

data "aws_iam_policy_document" "sagemaker_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["sagemaker.amazonaws.com"]
    }
  }
}

# IAM policy document for access shared CodeCommit
data "aws_iam_policy_document" "codecommit_access" {
  statement {
    actions   = ["codecommit:*"]
    resources = ["arn:aws:codecommit:::${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:${var.project_name}-${var.environment}-repo*"]
    effect    = "Allow"
  }
}

# IAM policy for access shared CodeCommit
resource "aws_iam_policy" "allow_codecommit_access" {
  name   = "allow-access-codecommit-repository"
  policy = data.aws_iam_policy_document.codecommit_access.json
}

# VPC
module "vpc_for_sagemaker" {
  source = "terraform-aws-modules/vpc/aws"

  name            = "${var.project_name}-${var.environment}-vpc-sagemaker"
  cidr            = "10.0.0.0/16"
  azs             = ["us-east-1a", "us-east-1c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  enable_nat_gateway     = true
  single_nat_gateway     = false
  one_nat_gateway_per_az = false
  enable_dns_support     = true
  enable_dns_hostnames   = true

  tags = {
    Name = "vpc_for_sagemaker"
  }
}

# CodeCommit
resource "aws_codecommit_repository" "repository" {
  repository_name = "${var.project_name}-${var.environment}-repo"
}

# S3 Bucket - 共通　　
resource "aws_s3_bucket" "bucket_shared" {
  bucket = "${var.project_name}-${var.environment}-bucket-shared"
}

# S3 access policy - 共通
resource "aws_s3_bucket_public_access_block" "bucket_shared_public_access_block" {
  bucket = "${var.project_name}-${var.environment}-bucket-shared"

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Encryption - 共通
resource "aws_s3_bucket_server_side_encryption_configuration" "bucket_shared_encryption" {
  bucket = aws_s3_bucket.bucket_shared.bucket

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

# S3 Policy - 共通
resource "aws_s3_bucket_policy" "bucket_shared_policy" {
  bucket = aws_s3_bucket.bucket_shared.bucket

  policy = jsonencode({
    Version = "2012-10-17"
    Id      = "BUCKET-POLICY"
    Statement = [
      {
        "Sid" : "AllowSSLRequestsOnly",
        "Action" : "s3:*",
        "Effect" : "Deny",
        "Resource" : [
          "arn:aws:s3:::${var.project_name}-${var.environment}-bucket-shared",
          "arn:aws:s3:::${var.project_name}-${var.environment}-bucket-shared/*"
        ],
        "Condition" : {
          "Bool" : {
            "aws:SecureTransport" : "false"
          }
        },
        "Principal" : "*"
      }
    ]
  })

  depends_on = [aws_s3_bucket.bucket_shared]
}

# Studio Domain
resource "aws_sagemaker_domain" "domain" {
  domain_name = var.project_name
  auth_mode   = "IAM"
  vpc_id      = module.vpc_for_sagemaker.vpc_id
  subnet_ids  = [module.vpc_for_sagemaker.private_subnets[0]]

  default_user_settings {
    execution_role = aws_iam_role.sagemaker_execution_role_default.arn
  }
}

# ------------------------------------------------------------------------------------------
# ------------------------------------per user resources------------------------------------
# ------------------------------------------------------------------------------------------
# IAM User
module "user" {
  source            = "../modules/iam/user"
  for_each          = toset(var.user_list)
  aws_iam_username  = "${var.project_name}-${each.value}"
  aws_iam_grouppath = "/users/"

}

# IAM Userマネジメントコンソールログイン用プロファイル
resource "aws_iam_user_login_profile" "iam_login_profile" {
  for_each                = toset(var.user_list)
  user                    = "${var.project_name}-${each.value}"
  pgp_key                 = filebase64("../cert/terraform.public.gpg")
  password_reset_required = true
  password_length         = "20"
  depends_on              = [module.user]
}

# IAM policy - 個人バケットアクセス用
resource "aws_iam_policy" "allow_access_bucket_own" {
  for_each = toset(var.user_list)
  name     = "allow-access-bucket-own-${each.value}"
  policy   = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "s3:*"
      ],
      "Effect": "Allow",
      "Resource": ["arn:aws:s3:::${var.project_name}-${var.environment}-bucket-${each.value}",
    "arn:aws:s3:::${var.project_name}-${var.environment}-bucket-${each.value}/*"]
    }
  ]
}
EOF
}

# IAM policy - 個人UserProfile用
resource "aws_iam_policy" "user_access_only_own_profile" {
  for_each = toset(var.user_list)
  name     = "user-access-only-own-profile-${each.value}"
  policy   = <<EOF
{
"Version": "2012-10-17",
"Statement": [
    {
    "Action": [
        "license-manager:ListReceivedLicenses"
         ],
    "Effect": "Allow",
    "Resource": ["*"]
    },
    {
    "Action": [
        "sagemaker:CreatePresignedDomainUrl"
    ],
    "Effect": "Allow",
    "Resource": ["arn:aws:sagemaker:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:user-profile/${aws_sagemaker_domain.domain.id}/sagemaker-user-${each.value}"]
    },
    {
    "Action": [
        "sagemaker:CreatePresignedDomainUrl"
    ],
    "Effect": "Deny",
    "NotResource": ["arn:aws:sagemaker:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:user-profile/${aws_sagemaker_domain.domain.id}/sagemaker-user-${each.value}"]
    }
]
}
EOF
}


# S3 Bucket - 個人用
resource "aws_s3_bucket" "bucket_users" {
  for_each = toset(var.user_list)
  bucket   = "${var.project_name}-${var.environment}-bucket-${each.value}"

  tags = {
    Name = "${var.project_name}-${var.environment}-bucket-${each.value}"
  }
}

# S3 access policy - 個人用
resource "aws_s3_bucket_public_access_block" "bucket_users_public_access_block" {
  for_each = toset(var.user_list)
  bucket   = "${var.project_name}-${var.environment}-bucket-${each.value}"

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Encryption - 個人用
resource "aws_s3_bucket_server_side_encryption_configuration" "bucket_users_encryption" {
  for_each = toset(var.user_list)
  bucket   = "${var.project_name}-${var.environment}-bucket-${each.value}"

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

# S3 Policy - 個人用
resource "aws_s3_bucket_policy" "bucket_users_policy" {
  for_each = toset(var.user_list)
  bucket   = "${var.project_name}-${var.environment}-bucket-${each.value}"

  policy = jsonencode({
    Version = "2012-10-17"
    Id      = "BUCKET-POLICY"
    Statement = [
      {
        "Sid" : "AllowSSLRequestsOnly",
        "Action" : "s3:*",
        "Effect" : "Deny",
        "Resource" : [
          "arn:aws:s3:::${var.project_name}-${var.environment}-bucket-${each.value}",
          "arn:aws:s3:::${var.project_name}-${var.environment}-bucket-${each.value}/*"
        ],
        "Condition" : {
          "Bool" : {
            "aws:SecureTransport" : "false"
          }
        },
        "Principal" : "*"
      }
    ]
  })

  depends_on = [aws_s3_bucket.bucket_users]
}

# IAM role - 個人UserProfile用
resource "aws_iam_role" "sagemaker_execution_role_indivisual" {
  for_each           = toset(var.user_list)
  name               = "sagemaker-execution-role-${each.value}"
  assume_role_policy = data.aws_iam_policy_document.sagemaker_assume_role.json
}

# IAM policy attach - 個人UserProfile用に共通バケットアクセス用Policyのattache
resource "aws_iam_policy_attachment" "sagemaker_access_shared_bucket" {
  name       = "sagemaker-bucket-shared-access"
  for_each   = toset(var.user_list)
  roles      = ["sagemaker-execution-role-${each.value}"]
  policy_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/allow-bucket-shared-access"

  depends_on = [aws_iam_role.sagemaker_execution_role_indivisual, aws_iam_policy.allow_backet_shared_access]
}

# IAM policy attach - 個人UserProfile用に共通リポジトリ用Policyのattache
resource "aws_iam_policy_attachment" "sagemaker_access_shared_repository" {
  name       = "sagemaker-codecommit-shared-repository-access"
  for_each   = toset(var.user_list)
  roles      = ["sagemaker-execution-role-${each.value}"]
  policy_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/allow-access-codecommit-repository"
  depends_on = [aws_iam_role.sagemaker_execution_role_indivisual, aws_iam_policy.allow_codecommit_access]
}

# IAM policy attach - 個人UserProfile用に個人バケットアクセス用Policyのattache
resource "aws_iam_policy_attachment" "sagemaker_access_own_bucket" {
  name       = "sagemaker-bucket-own-access"
  for_each   = toset(var.user_list)
  roles      = ["sagemaker-execution-role-${each.value}"]
  policy_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/allow-access-bucket-own-${each.value}"

  depends_on = [aws_iam_role.sagemaker_execution_role_indivisual, aws_iam_policy.allow_access_bucket_own]
}

# IAM policy attach - 個人Userに共通バケットアクセス用Policyのattache
resource "aws_iam_policy_attachment" "user_access_shared_bucket" {
  name       = "user-bucket-shared-access"
  for_each   = toset(var.user_list)
  users      = ["${var.project_name}-${each.value}"]
  policy_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/allow-bucket-shared-access"

  depends_on = [module.user, aws_iam_policy.allow_backet_shared_access]
}

# IAM policy attach - 個人Userに共通リポジトリ用Policyのattache
resource "aws_iam_policy_attachment" "user_access_shared_repository" {
  name       = "user-codecommit-shared-repository-access"
  for_each   = toset(var.user_list)
  users      = ["${var.project_name}-${each.value}"]
  policy_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/allow-access-codecommit-repository"
  depends_on = [module.user, aws_iam_policy.allow_codecommit_access]
}

# IAM policy attach - 個人Userに個人バケットアクセス用Policyのattache
resource "aws_iam_policy_attachment" "user_access_own_bucket" {
  name       = "user-bucket-own-access"
  for_each   = toset(var.user_list)
  users      = ["${var.project_name}-${each.value}"]
  policy_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/allow-access-bucket-own-${each.value}"

  depends_on = [module.user, aws_iam_policy.allow_access_bucket_own]
}

# IAM policy attach - 個人User用に個人UserProfile用policyのattache
resource "aws_iam_policy_attachment" "access_own_profile" {
  name       = "access-own-profile"
  for_each   = toset(var.user_list)
  users      = ["${var.project_name}-${each.value}"]
  policy_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/user-access-only-own-profile-${each.value}"

  depends_on = [aws_iam_policy.user_access_only_own_profile, module.user]
}

# IAM policy attach - パスワード変更権限の付与
resource "aws_iam_policy_attachment" "change_password_policy_attach" {
  name       = "change-password-policy-attach"
  for_each   = toset(var.user_list)
  users      = ["${var.project_name}-${each.value}"]
  policy_arn = "arn:aws:iam::aws:policy/IAMUserChangePassword"

  depends_on = [module.user]
}

# IAM policy attach - Sagemaker権限の付与
resource "aws_iam_policy_attachment" "user_sagemaker_full_access" {
  name       = "user-sagemaker-full-access"
  for_each   = toset(var.user_list)
  users      = ["${var.project_name}-${each.value}"]
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"

  depends_on = [module.user]
}

# IAM policy attach - Sagemaker権限の付与
resource "aws_iam_policy_attachment" "sagemaker_execution_role_full_access" {
  name       = "sagemaker-execution-role-full-access"
  for_each   = toset(var.user_list)
  roles      = ["sagemaker-execution-role-${each.value}"]
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"

  depends_on = [aws_iam_role.sagemaker_execution_role_indivisual]
}

# User Profile
resource "aws_sagemaker_user_profile" "sagemaker_studio_user" {
  domain_id         = aws_sagemaker_domain.domain.id
  for_each          = toset(var.user_list)
  user_profile_name = "sagemaker-user-${each.value}"
  user_settings {
    execution_role = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/sagemaker-execution-role-${each.value}"
  }
}
