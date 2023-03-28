from aws_cdk import (
    aws_iam as iam,
    aws_s3 as s3,
    aws_ec2 as ec2,
    aws_sagemaker as sagemaker,
    aws_secretsmanager as secretsmanager,
    CfnOutput,
    RemovalPolicy,
)
import aws_cdk as cdk
from constructs import Construct


class User(Construct):
    def __init__(
        self,
        construct: Construct,
        construct_id: str,
        name: str,
        studio_common_policy,
        domain,
        vpc,
        account_id,
        region,
    ):
        super().__init__(construct, construct_id)

        # IAM User 用のパスワードを Secrets Manager で生成
        secret = secretsmanager.Secret(self, "Secret")

        # Secrets Manager の名前を出力する
        CfnOutput(self, "Password", value=secret.secret_name)

        # EC2 へのログイン用パスワードを Secrets Manager で生成
        ec2_secret = secretsmanager.Secret(self, "EC2Secret")

        # Secrets Manager の名前を出力する
        CfnOutput(self, "EC2Password", value=ec2_secret.secret_name)

        # EC2 インスタンスに設定するタグ
        NAME_TAG_VALUE = f"ec2-individual-{name}"

        # 各人用の sagemaker studio の user profile にアタッチするロール
        self.studio_role = iam.Role(
            self,
            "Role",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSageMakerFullAccess"
                ),
                studio_common_policy,
            ],
        )

        self.studio_role.add_managed_policy(studio_common_policy)

        # sagemaker studio 内から 署名付き URL 発行を禁じる
        # （他人の user_profile で署名付きURL発行防止目的だが、そもそも署名付き URL を発行することがないため）
        deny_presigned_policy = iam.ManagedPolicy(self, "DenyPresignedPolicy")

        deny_presigned_policy.add_statements(
            iam.PolicyStatement(
                effect=iam.Effect.DENY,
                actions=["sagemaker:CreatePresignedDomainUrl"],
                resources=["*"],
            )
        )

        self.studio_role.add_managed_policy(deny_presigned_policy)

        # SageMaker User Profile
        user_profile = sagemaker.CfnUserProfile(
            self,
            "UserProfile",
            domain_id=domain.attr_domain_id,
            user_profile_name=name,
            user_settings={
                "executionRole": self.studio_role.role_arn,
            },
        )

        # インスタンス用 Role
        instance_role = iam.Role(
            self,
            "InstanceRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSSMManagedInstanceCore"
                )
            ],
        )

        instance_policy = iam.ManagedPolicy(self, "InstancePolicy")
        instance_policy.add_statements(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["sagemaker:CreatePresignedDomainUrl"],
                resources=[
                    user_profile.attr_user_profile_arn,
                ],
            )
        )

        instance_policy.add_statements(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["secretsmanager:GetSecretValue"],
                resources=[ec2_secret.secret_arn],
            )
        )

        instance_role.add_managed_policy(instance_policy)

        # EC2 インスタンス
        instance = ec2.Instance(
            self,
            "Instance",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.T3,
                ec2.InstanceSize.LARGE,
            ),
            machine_image=ec2.WindowsImage(
                ec2.WindowsVersion.WINDOWS_SERVER_2022_ENGLISH_FULL_BASE
            ),
            block_devices=[
                ec2.BlockDevice(
                    device_name="/dev/sda1",
                    volume=ec2.BlockDeviceVolume.ebs(30, encrypted=True),
                ),
            ],
            role=instance_role,
            user_data=ec2.UserData.custom(
                f"""
<powershell>
$password = (Get-SECSecretValue -SecretId {ec2_secret.secret_arn} -Region {region}).SecretString
New-LocalUser -Name user-1 -Password (ConvertTo-SecureString $password  -AsPlainText -Force)
Add-LocalGroupMember -Group "Remote Desktop Users" -Member user-1
Add-LocalGroupMember -Group Administrators -Member user-1
Write-Output '$url = New-SMPresignedDomainUrl -DomainId {domain.attr_domain_id} -ExpiresInSecond 30 -UserProfileName {user_profile.user_profile_name} -Region {region}' | Set-Content -Encoding Default 'C:\\GetPresignedUrl.ps1'
Write-Output 'start microsoft-edge:$url' | Add-Content -Encoding Default 'C:\\GetPresignedUrl.ps1'
</powershell>
<persist>true</persist>
            """
            ),
            require_imdsv2=True,
        )

        cdk.Tags.of(instance).add("Name", NAME_TAG_VALUE)

        # IAM ユーザー
        self.user = iam.User(
            self,
            "User",
            user_name=name,
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("IAMUserChangePassword"),
            ],
            password=secret.secret_value,
            password_reset_required=True,
        )
        # IAM ユーザーにアタッチする Fleet Manager を使うためのポリシー
        START_SESSION_POLICY_JSON = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "EC2GetPasswordData",
                    "Effect": "Allow",
                    "Action": ["ec2:GetPasswordData"],
                    "Resource": f"arn:aws:ec2:{region}:{account_id}:instance/{instance.instance_id}",
                },
                {
                    "Sid": "EC2DescribeInstances",
                    "Effect": "Allow",
                    "Action": ["ec2:DescribeInstances"],
                    "Resource": "*",
                },
                {
                    "Sid": "SSM",
                    "Effect": "Allow",
                    "Action": [
                        "ssm:DescribeInstanceProperties",
                        "ssm:GetCommandInvocation",
                        "ssm:GetInventorySchema",
                    ],
                    "Resource": "*",
                },
                {
                    "Sid": "SSMStartSession",
                    "Effect": "Allow",
                    "Action": ["ssm:StartSession"],
                    "Resource": [
                        "arn:aws:ssm:*::document/AWS-StartPortForwardingSession"
                    ],
                    "Condition": {
                        "BoolIfExists": {
                            "ssm:SessionDocumentAccessCheck": "true",
                        }
                    },
                },
                {
                    "Sid": "AccessTaggedInstances",
                    "Effect": "Allow",
                    "Action": ["ssm:StartSession"],
                    "Resource": [
                        f"arn:aws:ec2:*:{account_id}:instance/*",
                        f"arn:aws:ssm:*:{account_id}:managed-instance/*",
                    ],
                    "Condition": {
                        "StringLike": {
                            "ssm:resourceTag/Name": [NAME_TAG_VALUE],
                        }
                    },
                },
                {
                    "Sid": "GuiConnect",
                    "Effect": "Allow",
                    "Action": [
                        "ssm-guiconnect:CancelConnection",
                        "ssm-guiconnect:GetConnection",
                        "ssm-guiconnect:StartConnection",
                    ],
                    "Resource": "*",
                },
            ],
        }

        start_session_policy_document = iam.PolicyDocument.from_json(
            START_SESSION_POLICY_JSON
        )

        start_session_managed_policy = iam.ManagedPolicy(
            self,
            "StartSessionManagedPolicy",
            document=start_session_policy_document,
        )
        start_session_managed_policy.attach_to_user(self.user)

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
        self.bucket.grant_read_write(self.studio_role)
