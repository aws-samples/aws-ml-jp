from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_s3 as s3,
    aws_ec2 as ec2,
    aws_sagemaker as sagemaker,
    aws_codecommit as codecommit,
    aws_codeartifact as codeartifact,
    RemovalPolicy,
)
import aws_cdk as cdk
from constructs import Construct
from chococones import User


class ChococonesStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        # SageMaker Domain 名
        DOMAIN_NAME = "chococones"

        # CodeArtifact Domain 名
        CODE_ARTIFACT_DOMAIN_NAME = DOMAIN_NAME

        # CodeCommit リポジトリ名
        REPOSITORY_NAME = DOMAIN_NAME

        # CodeArtifact リポジトリ名
        CODE_ARTIFACT_REPOSITORY_NAME = DOMAIN_NAME

        SCOPED_AWS = cdk.ScopedAws(self)
        ACCOUNT_ID = SCOPED_AWS.account_id
        REGION = SCOPED_AWS.region

        # Domain 用の VPC
        vpc = ec2.Vpc(
            self,
            "vpc",
            max_azs=2,
            nat_gateways=0,
            subnet_configuration=[
                {
                    "name": "isolated-subnet",
                    "subnetType": ec2.SubnetType.PRIVATE_ISOLATED,
                    "cidrMask": 24,
                },
            ],
        )

        # エンドポイントを設定
        ec2.InterfaceVpcEndpoint(
            self,
            "SsmVpcEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SSM,
            private_dns_enabled=True,
            vpc=vpc,
            subnets={"subnet_type": ec2.SubnetType.PRIVATE_ISOLATED},
        )

        ec2.InterfaceVpcEndpoint(
            self,
            "SsmMessagesVpcEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SSM_MESSAGES,
            private_dns_enabled=True,
            vpc=vpc,
            subnets={"subnet_type": ec2.SubnetType.PRIVATE_ISOLATED},
        )

        ec2.InterfaceVpcEndpoint(
            self,
            "Ec2VpcEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.EC2,
            private_dns_enabled=True,
            vpc=vpc,
            subnets={"subnet_type": ec2.SubnetType.PRIVATE_ISOLATED},
        )

        ec2.InterfaceVpcEndpoint(
            self,
            "EC2MessagesVpcEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.EC2_MESSAGES,
            private_dns_enabled=True,
            vpc=vpc,
            subnets={"subnet_type": ec2.SubnetType.PRIVATE_ISOLATED},
        )

        ec2.InterfaceVpcEndpoint(
            self,
            "EcrVpcEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.ECR,
            private_dns_enabled=True,
            vpc=vpc,
            subnets={"subnet_type": ec2.SubnetType.PRIVATE_ISOLATED},
        )

        ec2.InterfaceVpcEndpoint(
            self,
            "EcrDockerVpcEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER,
            private_dns_enabled=True,
            vpc=vpc,
            subnets={"subnet_type": ec2.SubnetType.PRIVATE_ISOLATED},
        )

        ec2.InterfaceVpcEndpoint(
            self,
            "KmsVpcEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.KMS,
            private_dns_enabled=True,
            vpc=vpc,
            subnets={"subnet_type": ec2.SubnetType.PRIVATE_ISOLATED},
        )

        ec2.InterfaceVpcEndpoint(
            self,
            "CodeArtifactApiVpcEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.CODEARTIFACT_API,
            private_dns_enabled=True,
            vpc=vpc,
            subnets={"subnet_type": ec2.SubnetType.PRIVATE_ISOLATED},
        )

        ec2.InterfaceVpcEndpoint(
            self,
            "CodeArtifactRepositoriesVpcEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.CODEARTIFACT_REPOSITORIES,
            private_dns_enabled=True,
            vpc=vpc,
            subnets={"subnet_type": ec2.SubnetType.PRIVATE_ISOLATED},
        )

        ec2.InterfaceVpcEndpoint(
            self,
            "CodeCommitVpcEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.CODECOMMIT,
            private_dns_enabled=True,
            vpc=vpc,
            subnets={"subnet_type": ec2.SubnetType.PRIVATE_ISOLATED},
        )

        ec2.InterfaceVpcEndpoint(
            self,
            "CodeCommitGitVpcEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.CODECOMMIT_GIT,
            private_dns_enabled=True,
            vpc=vpc,
            subnets={"subnet_type": ec2.SubnetType.PRIVATE_ISOLATED},
        )

        ec2.InterfaceVpcEndpoint(
            self,
            "SmApiVpcEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SAGEMAKER_API,
            private_dns_enabled=True,
            vpc=vpc,
            subnets={"subnet_type": ec2.SubnetType.PRIVATE_ISOLATED},
        )

        ec2.InterfaceVpcEndpoint(
            self,
            "SmStdioApiVpcEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SAGEMAKER_STUDIO,
            private_dns_enabled=True,
            vpc=vpc,
            subnets={"subnet_type": ec2.SubnetType.PRIVATE_ISOLATED},
        )

        ec2.InterfaceVpcEndpoint(
            self,
            "SmNotebookRuntimeApiVpcEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SAGEMAKER_NOTEBOOK,
            private_dns_enabled=True,
            vpc=vpc,
            subnets={"subnet_type": ec2.SubnetType.PRIVATE_ISOLATED},
        )

        ec2.InterfaceVpcEndpoint(
            self,
            "SmRuntimeApiVpcEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SAGEMAKER_RUNTIME,
            private_dns_enabled=True,
            vpc=vpc,
            subnets={"subnet_type": ec2.SubnetType.PRIVATE_ISOLATED},
        )

        ec2.InterfaceVpcEndpoint(
            self,
            "SecretsManagerApiVpcEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
            private_dns_enabled=True,
            vpc=vpc,
            subnets={"subnet_type": ec2.SubnetType.PRIVATE_ISOLATED},
        )

        vpc.add_gateway_endpoint(
            "S3GatewayEndpoint",
            service=ec2.GatewayVpcEndpointAwsService.S3,
            subnets=[
                {"subnet_type": ec2.SubnetType.PRIVATE_ISOLATED},
            ],
        )

        # S3 と Domain に設定する Removal Policy
        removal_policy = RemovalPolicy.DESTROY

        # 共用 Bucket
        shared_bucket = s3.Bucket(
            self,
            "shared_bucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            removal_policy=removal_policy,
        )

        # 共用リポジトリ
        repository = codecommit.Repository(
            self,
            "Repository",
            repository_name=REPOSITORY_NAME,
        )

        # 共用 CodeArtifact
        code_artifact_domain = codeartifact.CfnDomain(
            self,
            "codeartifactDomain",
            domain_name=CODE_ARTIFACT_DOMAIN_NAME,
        )

        code_artifact_repository = codeartifact.CfnRepository(
            self,
            "codeartifactRepository",
            domain_name=code_artifact_domain.domain_name,
            repository_name=CODE_ARTIFACT_REPOSITORY_NAME,
            external_connections=["public:pypi"],
        )

        code_artifact_repository.add_dependency(code_artifact_domain)

        # SageMaker Domain 用の default execution Role
        default_role = iam.Role(
            self,
            "DefaultRole",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSageMakerFullAccess"
                ),
            ],
        )

        domain_security_group = ec2.SecurityGroup(
            self,
            "DomainSecurityGroup",
            vpc=vpc,
            allow_all_outbound=True,
        )
        domain_security_group.add_ingress_rule(
            ec2.Peer.ipv4("10.0.0.0/16"),
            ec2.Port.tcp_range(8192,65535)
        )

        # Studio Domain
        domain = sagemaker.CfnDomain(
            self,
            "domain",
            auth_mode="IAM",
            default_user_settings=sagemaker.CfnDomain.UserSettingsProperty(
                execution_role=default_role.role_arn,
                security_groups=[domain_security_group.security_group_id],
            ),
            domain_name=DOMAIN_NAME,
            vpc_id=vpc.vpc_id,
            # VPC の private subnets を使用
            subnet_ids=[subnet.subnet_id for subnet in vpc.isolated_subnets],
            # Studio からインターネットに出さない設定
            app_network_access_type="VpcOnly",
        )

        domain.apply_removal_policy(removal_policy)

        # 全員の SageMaker Studio Profile につける共用 Policy
        studio_common_policy = iam.ManagedPolicy(self, "StudioCommonPolicy")

        # 共用 CodeArtifact リポジトリへのアクセス許可
        studio_common_policy.add_statements(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
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
                ],
                resources=[
                    code_artifact_domain.attr_arn,
                    code_artifact_repository.attr_arn,
                ],
            )
        )

        studio_common_policy.add_statements(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["sts:GetServiceBearerToken"],
                resources=["*"],
                conditions={
                    "StringEquals": {"sts:AWSServiceName": "codeartifact.amazonaws.com"}
                },
            )
        )

        # 以下に使用する人分、User インスタンスを列挙する
        users = [
            User(
                self,
                "Tsugo",
                name="tsugo",
                studio_common_policy=studio_common_policy,
                domain=domain,
                vpc=vpc,
                account_id=ACCOUNT_ID,
                region=REGION,
            ),
            User(
                self,
                "Kudo",
                name="kudo",
                studio_common_policy=studio_common_policy,
                domain=domain,
                vpc=vpc,
                account_id=ACCOUNT_ID,
                region=REGION,
            ),
        ]

        for user in users:
            # 共用バケットへの読み書き権限
            shared_bucket.grant_read_write(user.studio_role)

            # 共用 CodeCommit リポジトリへのアクセス許可
            repository.grant_pull_push(user.studio_role)

            # 他のユーザーのバケットへの読み込み権限
            for bucket_owner in users:
                bucket_owner.bucket.grant_read(user.studio_role)
