from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_s3 as s3,
    aws_ec2 as ec2,
    aws_sagemaker as sagemaker,
    aws_codecommit as codecommit,
    RemovalPolicy,
)
from constructs import Construct
from chococones import User


class ChococonesStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        # SageMaker Domain 名
        DOMAIN_NAME = "chococones"

        # CodeCommit リポジトリ名
        REPOSITORY_NAME = DOMAIN_NAME

        # Domain 用の VPC
        vpc = ec2.Vpc(self, "vpc", max_azs=2)

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

        # Studio Domain
        domain = sagemaker.CfnDomain(
            self,
            "domain",
            auth_mode="IAM",
            default_user_settings={
                "executionRole": default_role.role_arn,
            },
            domain_name=DOMAIN_NAME,
            vpc_id=vpc.vpc_id,
            # VPC　の private subnets を使用
            subnet_ids=[subnet.subnet_id for subnet in vpc.private_subnets],
        )

        domain.apply_removal_policy(removal_policy)

        # 全員の IAM User・IAM Role につける共用 Policy
        policy = iam.ManagedPolicy(self, "SharedPolicy")

        # 共用 CodeCommit リポジトリへの読み書き許可
        policy.add_statements(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["codecommit:*"],
                resources=[repository.repository_arn],
            )
        )

        # 以下に使用する人分、User インスタンスを列挙する
        users = [
            User(
                self,
                "Tsugo",
                name="tsugo",
                policy=policy,
                domain=domain,
            ),
            User(
                self,
                "Kudo",
                name="kudo",
                policy=policy,
                domain=domain,
            ),
        ]

        for user in users:
            # 共用バケットへの読み書き権限
            shared_bucket.grant_read_write(user.user)
            shared_bucket.grant_read_write(user.role)

            # 他のユーザーのバケットへの読み込み権限
            for bucket_owner in users:
                bucket_owner.bucket.grant_read(user.user)
                bucket_owner.bucket.grant_read(user.role)
