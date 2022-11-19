from aws_cdk import (
    aws_iam as iam,
    aws_s3 as s3,
    aws_sagemaker as sagemaker,
    aws_secretsmanager as secretsmanager,
    CfnOutput,
    RemovalPolicy,
)
from constructs import Construct


class User(Construct):
    def __init__(
        self, construct: Construct, construct_id: str, name: str, policy, domain
    ):
        super().__init__(construct, construct_id)

        # IAM User 用のパスワードを Secrets Manager で生成
        self.secret = secretsmanager.Secret(self, "Secret")

        # Secrets Manager の名前を出力する
        CfnOutput(self, "Password", value=self.secret.secret_name)

        # IAM ユーザー
        self.user = iam.User(
            self,
            "User",
            user_name=name,
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSageMakerFullAccess"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name("IAMUserChangePassword"),
                policy,
            ],
            password=self.secret.secret_value,
            password_reset_required=True,
        )

        # ユーザー専用の execution Role
        self.role = iam.Role(
            self,
            "Role",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSageMakerFullAccess"
                ),
                policy,
            ],
        )

        # SageMaker User Profile
        self.user_profile = sagemaker.CfnUserProfile(
            self,
            "UserProfile",
            domain_id=domain.attr_domain_id,
            user_profile_name=name,
            user_settings={
                "executionRole": self.role.role_arn,
            },
        )

        # 自分以外の UserProfile へのアクセスを禁止
        self.deny_other_user_profile = iam.PolicyStatement(
            effect=iam.Effect.DENY,
            actions=[
                "sagemaker:CreatePresignedDomainUrl",
                "sagemaker:DescribeUserProfile",
            ],
            not_resources=[self.user_profile.attr_user_profile_arn],
        )

        # User Profile 設定画面でライセンスマネージャーを見られるようにしてエラーを防ぐ
        self.allow_list_recieved_licenses = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["license-manager:ListReceivedLicenses"],
            resources=["*"],
        )

        # 作成したポリシーを IAM User にアタッチする
        self.user.attach_inline_policy(
            iam.Policy(
                self,
                "CustomPolicy",
                statements=[
                    self.deny_other_user_profile,
                    self.allow_list_recieved_licenses,
                ],
            )
        )

        # 個人バケット
        self.bucket = s3.Bucket(
            self,
            "Bucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # 持ち主は読み書きできる
        self.bucket.grant_read_write(self.user)
        self.bucket.grant_read_write(self.role)
