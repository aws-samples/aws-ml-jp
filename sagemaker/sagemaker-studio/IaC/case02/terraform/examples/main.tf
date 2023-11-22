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
    actions   = ["codecommit:GitPull", "codecommit:GitPush"]
    resources = ["arn:aws:codecommit:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:${var.project_name}-${var.environment}-repo"]
    effect    = "Allow"
  }
}

# IAM policy for access shared CodeCommit
resource "aws_iam_policy" "allow_codecommit_access" {
  name   = "allow-access-codecommit-repository"
  policy = data.aws_iam_policy_document.codecommit_access.json
}

# IAM policy document for access shared CodeArtifact
data "aws_iam_policy_document" "codecartifact_access" {
  statement {
    actions=[
        "codeartifact:DescribeDomain",
        "codeartifact:DescribeRepository",
        "codeartifact:GetAuthorizationToken",
        "codeartifact:GetRepositoryEndpoint",
        "codeartifact:GetRepositoryPermissionsPolicy",
        "codeartifact:ListPackages",
        "codeartifact:ListRepositories",
        "codeartifact:ListTagsForResource",
        "codeartifact:ReadFromRepository",
    ]
    resources = [aws_codeartifact_domain.codeartifact_domain.arn, aws_codeartifact_repository.codeartifact_repository.arn]
    effect    = "Allow"
  }
  statement {
    actions   = ["sts:GetServiceBearerToken"]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "sts:AWSServiceName"
      values   = ["codeartifact.amazonaws.com"]
    }
    effect = "Allow"
  }
}

# IAM policy for access shared CodeArtifact
resource "aws_iam_policy" "allow_codeartifact_access" {
  name   = "allow-access-codeartifact-repository"
  policy = data.aws_iam_policy_document.codecartifact_access.json
}

# VPC
module "vpc_for_sagemaker" {
  source = "terraform-aws-modules/vpc/aws"

  name            = "${var.project_name}-${var.environment}-vpc"
  cidr            = "10.0.0.0/16"
  azs             = ["${var.aws_region}a", "${var.aws_region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]

  enable_nat_gateway     = false
  single_nat_gateway     = false
  one_nat_gateway_per_az = false
  enable_dns_support     = true
  enable_dns_hostnames   = true

  tags = {
    Name = "${var.project_name}-${var.environment}-vpc"
  }
}


# Security Group for VPC endpoint
resource "aws_security_group" "allow_local_https" {
  name        = "allow_local_https"
  description = "Allow HTTPS inbound traffic"
  vpc_id      = module.vpc_for_sagemaker.vpc_id

  ingress {
    description = "TLS from VPC"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [module.vpc_for_sagemaker.vpc_cidr_block]
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name = "allow_local_https"
  }
}

resource "aws_vpc_endpoint" "s3_endpoint" {
  vpc_id            = module.vpc_for_sagemaker.vpc_id
  service_name      = "com.amazonaws.${data.aws_region.current.name}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = module.vpc_for_sagemaker.private_route_table_ids
  policy            = <<POLICY
    {
        "Statement": [
            {
                "Action": "*",
                "Effect": "Allow",
                "Resource": "*",
                "Principal": "*"
            }
        ]
    }
    POLICY
}

# VPCエンドポイント
module "endpoints" {
  source = "terraform-aws-modules/vpc/aws//modules/vpc-endpoints"

  vpc_id             = module.vpc_for_sagemaker.vpc_id
  security_group_ids = [aws_security_group.allow_local_https.id]

  endpoints = {

    ssm = {
      service             = "ssm"
      private_dns_enabled = true
      subnet_ids          = module.vpc_for_sagemaker.private_subnets
      security_group_ids  = [aws_security_group.allow_local_https.id]
    },
    ssmmessages = {
      service             = "ssmmessages"
      private_dns_enabled = true
      subnet_ids          = module.vpc_for_sagemaker.private_subnets
    },
    ec2 = {
      service             = "ec2"
      private_dns_enabled = true
      subnet_ids          = module.vpc_for_sagemaker.private_subnets
      security_group_ids  = [aws_security_group.allow_local_https.id]
    },
    ec2messages = {
      service             = "ec2messages"
      private_dns_enabled = true
      subnet_ids          = module.vpc_for_sagemaker.private_subnets
    },
    ecr_api = {
      service             = "ecr.api"
      private_dns_enabled = true
      subnet_ids          = module.vpc_for_sagemaker.private_subnets
      policy              = data.aws_iam_policy_document.generic_endpoint_policy.json
    },
    ecr_dkr = {
      service             = "ecr.dkr"
      private_dns_enabled = true
      subnet_ids          = module.vpc_for_sagemaker.private_subnets
      policy              = data.aws_iam_policy_document.generic_endpoint_policy.json
    },
    kms = {
      service             = "kms"
      private_dns_enabled = true
      subnet_ids          = module.vpc_for_sagemaker.private_subnets
      security_group_ids  = [aws_security_group.allow_local_https.id]
    },
    codeartifact_api = {
      service             = "codeartifact.api"
      private_dns_enabled = true
      subnet_ids          = module.vpc_for_sagemaker.private_subnets
    },
    codeartifact_repositories = {
      service             = "codeartifact.repositories"
      private_dns_enabled = true
      subnet_ids          = module.vpc_for_sagemaker.private_subnets
    },
    codecommit = {
      service             = "codecommit"
      private_dns_enabled = true
      subnet_ids          = module.vpc_for_sagemaker.private_subnets
      security_group_ids  = [aws_security_group.allow_local_https.id]
    },
    git-codecommit = {
      service             = "git-codecommit"
      private_dns_enabled = true
      subnet_ids          = module.vpc_for_sagemaker.private_subnets
      security_group_ids  = [aws_security_group.allow_local_https.id]
    },
    sagemaker_api = {
      service             = "sagemaker.api"
      private_dns_enabled = true
      subnet_ids          = module.vpc_for_sagemaker.private_subnets
    },
    sagemaker_runtime = {
      service             = "sagemaker.runtime"
      private_dns_enabled = true
      subnet_ids          = module.vpc_for_sagemaker.private_subnets
      policy              = data.aws_iam_policy_document.generic_endpoint_policy.json
    }

    secretsmanager = {
      service             = "secretsmanager"
      private_dns_enabled = true
      subnet_ids          = module.vpc_for_sagemaker.private_subnets
  } }
}

resource "aws_vpc_endpoint" "sagemaker_studio" {
  vpc_id              = module.vpc_for_sagemaker.vpc_id
  service_name        = "aws.sagemaker.${var.aws_region}.studio"
  vpc_endpoint_type   = "Interface"
  security_group_ids  = [aws_security_group.allow_local_https.id]
  private_dns_enabled = true
}
resource "aws_vpc_endpoint_subnet_association" "sagemaker_studio_1" {
  vpc_endpoint_id = aws_vpc_endpoint.sagemaker_studio.id
  subnet_id       = module.vpc_for_sagemaker.private_subnets[0]
}

resource "aws_vpc_endpoint_subnet_association" "sagemaker_studio_2" {
  vpc_endpoint_id = aws_vpc_endpoint.sagemaker_studio.id
  subnet_id       = module.vpc_for_sagemaker.private_subnets[1]
}


# Security Group for VPC endpoint
resource "aws_security_group" "lambda" {
  name        = "password rotation lambda"
  description = "Lambda security group sample"
  vpc_id      = module.vpc_for_sagemaker.vpc_id
  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name = "lambda"
  }
}


resource "aws_iam_role" "iam_for_lambda" {
  name = "iam_for_lambda"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "iam_role_policy_attachment_lambda_vpc_access_execution" {
  role       = aws_iam_role.iam_for_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# IAM policy - rotate用Lambda Secretの操作権限
resource "aws_iam_policy" "manage_secret" {
  name   = "manage-secret-for-lambda"
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "secretsmanager:*"
      ],
      "Effect": "Allow",
      "Resource": ["arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:*"]
    },
    {
      "Action": [
        "secretsmanager:GetRandomPassword"
      ],
      "Effect": "Allow",
      "Resource": ["*"]
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "iam_role_policy_attachment_lambda_manage_secret" {
  role       = aws_iam_role.iam_for_lambda.name
  policy_arn = aws_iam_policy.manage_secret.arn
}

resource "aws_lambda_permission" "allow_secretsmanager" {
  statement_id  = "AllowExecutionFromSecretsManager"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.password_rotate_lambda.function_name
  principal     = "secretsmanager.amazonaws.com"
  source_arn = "arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:${var.project_name}-ec2-login-password-*"
}


resource "aws_lambda_function" "password_rotate_lambda" {
  filename      = "rotate.py.zip"
  function_name = "password_rotate_lambda_function"
  role          = aws_iam_role.iam_for_lambda.arn
  handler       = "rotate.lambda_handler"
  runtime       = "python3.9"
  timeout       = 300
  vpc_config {
    subnet_ids         = [module.vpc_for_sagemaker.private_subnets[0]]
    security_group_ids = ["${aws_security_group.lambda.id}"]
  }
  depends_on = [
    aws_iam_role_policy_attachment.lambda_logs,
    aws_cloudwatch_log_group.password_rotate
  ]
  environment {
    variables = {
      SECRETS_MANAGER_ENDPOINT = "https://secretsmanager.${data.aws_region.current.name}.amazonaws.com"
      EXCLUDE_CHARACTERS       = "/@\"'\\"
    }
  }

}

resource "aws_secretsmanager_secret_rotation" "ec2_login_password_secret_rotation" {
  for_each            = toset(var.user_list)
  secret_id           = "${var.project_name}-ec2-login-password-${each.value}"
  rotation_lambda_arn = aws_lambda_function.password_rotate_lambda.arn
  rotation_rules {
    automatically_after_days = 30
  }

  depends_on = [
    aws_lambda_function.password_rotate_lambda
  ]
}

resource "aws_cloudwatch_log_group" "password_rotate" {
  name              = "/aws/lambda/password_rotate_lambda_function"
  retention_in_days = 30
}

resource "aws_iam_policy" "lambda_logging" {
  name        = "lambda_logging"
  path        = "/"
  description = "IAM policy for logging from a lambda"

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*",
      "Effect": "Allow"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.iam_for_lambda.name
  policy_arn = aws_iam_policy.lambda_logging.arn
}


data "aws_iam_policy_document" "generic_endpoint_policy" {
  statement {
    effect    = "Deny"
    actions   = ["*"]
    resources = ["*"]

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    condition {
      test     = "StringNotEquals"
      variable = "aws:SourceVpc"

      values = [module.vpc_for_sagemaker.vpc_id]
    }
  }
}

# CodeCommit
resource "aws_codecommit_repository" "repository" {
  repository_name = "${var.project_name}-${var.environment}-repo"
}

# CodeArtifact
resource "aws_codeartifact_domain" "codeartifact_domain" {
  domain = var.project_name
}

resource "aws_codeartifact_repository" "codeartifact_repository" {
  repository = var.project_name
  domain     = aws_codeartifact_domain.codeartifact_domain.domain
  external_connections {
    external_connection_name = "public:pypi"
  }
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

# Security Group for Sagemaker Studio Domain
resource "aws_security_group" "sagemaker_studio_outbound" {
  name        = "sagemaker_studio_outbound"
  description = "Sagemaker Studio Doamain sample"
  vpc_id      = module.vpc_for_sagemaker.vpc_id
  ingress {
    description      = "tcp access from KernelGateway"
    from_port        = 8192
    to_port          = 65535
    protocol         = "tcp"
    cidr_blocks      = ["10.0.0.0/16"]
  }
  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name = "sagemaker_studio_outbound"
  }
}


# Studio Domain
resource "aws_sagemaker_domain" "domain" {
  domain_name             = var.project_name
  auth_mode               = "IAM"
  vpc_id                  = module.vpc_for_sagemaker.vpc_id
  subnet_ids              = [module.vpc_for_sagemaker.private_subnets[0]]
  app_network_access_type = "VpcOnly"
  default_user_settings {
    execution_role  = aws_iam_role.sagemaker_execution_role_default.arn
    security_groups = [aws_security_group.sagemaker_studio_outbound.id]
  }
}


# Security Group for EC2
resource "aws_security_group" "private_ec2" {
  name        = "private_ec2"
  description = "EC2 security group sample"
  vpc_id      = module.vpc_for_sagemaker.vpc_id
  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name = "private_ec2"
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
resource "aws_iam_policy_attachment" "sagemaker_access_shared_repository_codecommit" {
  name       = "sagemaker-codecommit-shared-repository-access"
  for_each   = toset(var.user_list)
  roles      = ["sagemaker-execution-role-${each.value}"]
  policy_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/allow-access-codecommit-repository"
  depends_on = [aws_iam_role.sagemaker_execution_role_indivisual, aws_iam_policy.allow_codecommit_access]
}

# IAM policy attach - 個人UserProfile用に共通リポジトリ用Policyのattache
resource "aws_iam_policy_attachment" "sagemaker_access_shared_repository_codeartifact" {
  name       = "sagemaker-codeartifact-shared-repository-access"
  for_each   = toset(var.user_list)
  roles      = ["sagemaker-execution-role-${each.value}"]
  policy_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/allow-access-codeartifact-repository"
  depends_on = [aws_iam_role.sagemaker_execution_role_indivisual, aws_iam_policy.allow_codeartifact_access]
}

# IAM policy attach - 個人UserProfile用に個人バケットアクセス用Policyのattache
resource "aws_iam_policy_attachment" "sagemaker_access_own_bucket" {
  name       = "sagemaker-bucket-own-access"
  for_each   = toset(var.user_list)
  roles      = ["sagemaker-execution-role-${each.value}"]
  policy_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/allow-access-bucket-own-${each.value}"

  depends_on = [aws_iam_role.sagemaker_execution_role_indivisual, aws_iam_policy.allow_access_bucket_own]
}

# IAM policy attach - 個人UserProfile用に他人のpresigned urlを発行できないPolicyのattache
resource "aws_iam_policy_attachment" "sagemaker_access_own_presignedurl" {
  name       = "sagemaker-bucket-own-access"
  for_each   = toset(var.user_list)
  roles      = ["sagemaker-execution-role-${each.value}"]
  policy_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/user-access-only-own-profile-${each.value}"

  depends_on = [aws_iam_role.sagemaker_execution_role_indivisual, aws_iam_policy.allow_access_bucket_own, aws_iam_policy.user_access_only_own_profile]
}

# IAM policy attach - 個人用EC2に個人UserProfile用policyのattache
resource "aws_iam_policy_attachment" "access_own_profile" {
  name       = "access-own-profile"
  for_each   = toset(var.user_list)
  roles      = ["ec2-role-${each.value}"]
  policy_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/user-access-only-own-profile-${each.value}"

  depends_on = [aws_iam_role.ec2_role_indivisual, aws_iam_policy.user_access_only_own_profile]
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

# IAM role - 個人EC2用
resource "aws_iam_role" "ec2_role_indivisual" {
  for_each           = toset(var.user_list)
  name               = "ec2-role-${each.value}"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json
}

data "aws_iam_policy_document" "ec2_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

# IAM policy - SecretsManagerの値を取得
resource "aws_iam_policy" "ec2_get_secret" {
  for_each = toset(var.user_list)
  name     = "allow-get-${var.project_name}-ec2-login-password-${each.value}"
  policy   = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Effect": "Allow",
      "Resource": ["arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:${var.project_name}-ec2-login-password-${each.value}-??????"]
    }
  ]
}
EOF
}

resource "aws_iam_instance_profile" "ec2_isntanceprofile_indivisual" {
  for_each = toset(var.user_list)
  name     = "ec2-instanceprofile-${each.value}"
  role     = "ec2-role-${each.value}"
}

# windows server の最新版AMIを取得
data "aws_ssm_parameter" "windows_latest_ami" {
  name = "/aws/service/ami-windows-latest/Windows_Server-2022-English-Full-Base"
}

# Secret
resource "aws_secretsmanager_secret" "ec2_login_password" {
  for_each = toset(var.user_list)
  name     = "${var.project_name}-ec2-login-password-${each.value}"
}

resource "aws_secretsmanager_secret_version" "secret_version" {
  for_each      = toset(var.user_list)
  secret_id     = "${var.project_name}-ec2-login-password-${each.value}"
  secret_string = jsonencode("dummypassword")

  lifecycle {
    ignore_changes = [
      secret_string
    ]
  }
  depends_on = [
    aws_secretsmanager_secret.ec2_login_password
  ]
}


# EC2
resource "aws_instance" "ec2-indivisual" {
  for_each               = toset(var.user_list)
  ami                    = data.aws_ssm_parameter.windows_latest_ami.value
  instance_type          = "m5.xlarge"
  iam_instance_profile   = "ec2-instanceprofile-${each.value}"
  subnet_id              = module.vpc_for_sagemaker.private_subnets[0]
  vpc_security_group_ids = [aws_security_group.private_ec2.id]
  user_data              = <<EOF
<powershell>
$password = (Get-SECSecretValue -SecretId ${var.project_name}-ec2-login-password-${each.value}).SecretString
New-LocalUser -Name user-1 -Password (ConvertTo-SecureString $password -AsPlainText -Force)
Add-LocalGroupMember -Group "Remote Desktop Users" -Member user-1
Add-LocalGroupMember -Group Administrators -Member user-1
Write-Output '$url = New-SMPresignedDomainUrl -DomainId ${aws_sagemaker_domain.domain.id} -ExpiresInSecond 30 -UserProfileName sagemaker-user-${each.value} -Region us-east-1' | Set-Content -Encoding Default 'C:\GetPresignedUrl.ps1'
Write-Output 'start microsoft-edge:$url' | Add-Content -Encoding Default 'C:\GetPresignedUrl.ps1' 
</powershell>
<persist>true</persist>
EOF
  tags = {
    Name = "ec2-indivisual-${each.value}"
  }

  metadata_options {
    http_endpoint = "enabled"
    http_tokens = "required"
  }

  depends_on = [
    aws_secretsmanager_secret.ec2_login_password,
    aws_secretsmanager_secret_rotation.ec2_login_password_secret_rotation,
    aws_iam_policy_attachment.ec2_get_secret,
    aws_secretsmanager_secret_rotation.ec2_login_password_secret_rotation,
    aws_ebs_encryption_by_default.ebs_encrypt
  ]

}

resource "aws_ebs_encryption_by_default" "ebs_encrypt" {
  enabled = true
}

# IAM Role SSM利用権限
resource "aws_iam_policy_attachment" "access_session_manager" {
  name       = "access-own-profile"
  for_each   = toset(var.user_list)
  roles      = ["ec2-role-${each.value}"]
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"

  depends_on = [aws_iam_role.ec2_role_indivisual]
}

resource "aws_iam_policy_attachment" "ec2_get_secret" {
  name       = "get-login-password"
  for_each   = toset(var.user_list)
  roles      = ["ec2-role-${each.value}"]
  policy_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/allow-get-${var.project_name}-ec2-login-password-${each.value}"

  depends_on = [aws_iam_role.ec2_role_indivisual]
}

# IAM policy - 個人StartSession用
resource "aws_iam_policy" "user_access_only_own_instance" {
  for_each = toset(var.user_list)
  name     = "user-access-only-own-ec2-${each.value}"
  policy   = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "EC2GetPasswordData",
            "Effect": "Allow",
            "Action": [
                "ec2:GetPasswordData"
            ],
            "Resource": "*",
            "Condition": {
                "StringEquals": {
                    "ec2:ResourceTag/Name": "ec2-indivisual-${each.value}"
                }
              }
        },
        {
            "Sid": "EC2DescribeInstances",
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeInstances"
            ],
            "Resource": "*"
        },
        {
            "Sid": "SSM",
            "Effect": "Allow",
            "Action": [
                "ssm:DescribeInstanceProperties",
                "ssm:GetCommandInvocation",
                "ssm:GetInventorySchema"
            ],
            "Resource": "*"
        },
        {
            "Sid": "SSMStartSession",
            "Effect": "Allow",
            "Action": [
                "ssm:StartSession"
            ],
            "Resource": [
                "arn:aws:ssm:*::document/AWS-StartPortForwardingSession"
            ],
            "Condition": {
                "BoolIfExists": {
                    "ssm:SessionDocumentAccessCheck": "true"
                }
            }
        },
        {
            "Sid": "AccessTaggedInstances",
            "Effect": "Allow",
            "Action": [
                "ssm:StartSession"
            ],
            "Resource": [
                "arn:aws:ec2:*:${data.aws_caller_identity.current.account_id}:instance/*",
                "arn:aws:ssm:*:${data.aws_caller_identity.current.account_id}:managed-instance/*"
            ],
            "Condition": {
                "StringLike": {
                    "ssm:resourceTag/Name": [
                        "ec2-indivisual-${each.value}"
                    ]
                }
            }
        },
        {
            "Sid": "GuiConnect",
            "Effect": "Allow",
            "Action": [
                "ssm-guiconnect:CancelConnection",
                "ssm-guiconnect:GetConnection",
                "ssm-guiconnect:StartConnection"
            ],
            "Resource": "*"
        }
    ]
}
EOF
}

# IAM policy attach - EC2接続権限
resource "aws_iam_policy_attachment" "access_own_instance" {
  name       = "readonly-policy-attach"
  for_each   = toset(var.user_list)
  users      = ["${var.project_name}-${each.value}"]
  policy_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/user-access-only-own-ec2-${each.value}"

  depends_on = [aws_iam_policy.user_access_only_own_instance]
}