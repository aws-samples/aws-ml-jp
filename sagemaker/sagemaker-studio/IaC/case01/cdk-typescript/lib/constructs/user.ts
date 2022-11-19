import * as cdk from 'aws-cdk-lib'
import { Construct } from 'constructs'
import * as iam from 'aws-cdk-lib/aws-iam'
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager'
import * as sagemaker from 'aws-cdk-lib/aws-sagemaker'
import * as s3 from 'aws-cdk-lib/aws-s3'

export interface UserProps {
  name: string
  domainId: string
  policy: iam.ManagedPolicy
  removalPolicy: cdk.RemovalPolicy
}

export class User extends Construct {
  public readonly user: iam.User
  public readonly role: iam.Role
  public readonly userProfile: sagemaker.CfnUserProfile
  public readonly bucket: s3.Bucket

  constructor(scope: Construct, id: string, props: UserProps) {
    super(scope, id)

    const { accountId, region } = new cdk.ScopedAws(this)

    // IAM User 用のパスワードを Secrets Manager で生成
    const secret = new secretsmanager.Secret(this, 'Secret')

    // Secrets Manager の名前を出力する
    new cdk.CfnOutput(this, 'SecretName', {
      value: secret.secretName,
    })

    // IAM ユーザー
    this.user = new iam.User(this, 'User', {
      userName: props.name,
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonSageMakerFullAccess'),
        iam.ManagedPolicy.fromAwsManagedPolicyName('IAMUserChangePassword'),
        props.policy,
      ],
      password: secret.secretValue,
      passwordResetRequired: true,
    })

    // ユーザー専用の execution Role
    this.role = new iam.Role(this, 'Role', {
      assumedBy: new iam.ServicePrincipal('sagemaker.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonSageMakerFullAccess'),
        props.policy,
      ],
    })

    // SageMaker User Profile
    this.userProfile = new sagemaker.CfnUserProfile(this, 'UserProfile', {
      domainId: props.domainId,
      userProfileName: props.name,
      userSettings: {
        executionRole: this.role.roleArn,
      },
    })

    // 自分以外の UserProfile へのアクセスを禁止
    const denyOtherUserProfile = new iam.PolicyStatement({
      effect: iam.Effect.DENY,
      actions: [
        'sagemaker:CreatePresignedDomainUrl',
        'sagemaker:DescribeUserProfile',
      ],
      notResources: [this.userProfile.attrUserProfileArn],
    })

    // User Profile 設定画面でライセンスマネージャーを見られるようにしてエラーを防ぐ
    const allowListRecievedLicenses = new iam.PolicyStatement({
      effect: iam.Effect.DENY,
      actions: ['license-manager:ListReceivedLicenses'],
      resources: ['*'],
    })

    // 作成したポリシーを IAM User にアタッチする
    this.user.attachInlinePolicy(
      new iam.Policy(this, 'UserPolicy', {
        statements: [denyOtherUserProfile, allowListRecievedLicenses],
      })
    )
    // 個人バケット
    this.bucket = new s3.Bucket(this, 'Bucket', {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      enforceSSL: true,
      removalPolicy: props.removalPolicy,
    })

    // 持ち主は読み書きできる
    this.bucket.grantReadWrite(this.user)
    this.bucket.grantReadWrite(this.role)
  }
}
