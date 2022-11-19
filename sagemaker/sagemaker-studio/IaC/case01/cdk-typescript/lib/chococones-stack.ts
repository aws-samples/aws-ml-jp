import * as cdk from 'aws-cdk-lib'
import { Construct } from 'constructs'
import * as ec2 from 'aws-cdk-lib/aws-ec2'
import * as s3 from 'aws-cdk-lib/aws-s3'
import * as codecommit from 'aws-cdk-lib/aws-codecommit'
import * as iam from 'aws-cdk-lib/aws-iam'
import * as sagemaker from 'aws-cdk-lib/aws-sagemaker'
import { User } from './constructs/user'

export class ChococonesStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props)

    // SageMaker Domain 名
    const domainName = 'chococones'

    // CodeCommit リポジトリ名
    const repositoryName = domainName

    // Domain 用の VPC
    const vpc = new ec2.Vpc(this, 'Vpc', { maxAzs: 2 })

    // S3 と Domain に設定する Removal Policy
    const removalPolicy = cdk.RemovalPolicy.DESTROY

    // 共用 Bucket
    const sharedBucket = new s3.Bucket(this, 'SharedBucket', {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      enforceSSL: true,
      removalPolicy,
    })

    // 共用リポジトリ
    const repository = new codecommit.Repository(this, 'Repository', {
      repositoryName,
    })

    // SageMaker Domain 用の default execution Role
    const defaultRole = new iam.Role(this, 'DefaultRole', {
      assumedBy: new iam.ServicePrincipal('sagemaker.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonSageMakerFullAccess'),
      ],
    })

    // Studio Domain
    const domain = new sagemaker.CfnDomain(this, 'Domain', {
      authMode: 'IAM',
      defaultUserSettings: {
        executionRole: defaultRole.roleArn,
      },
      domainName,
      vpcId: vpc.vpcId,
      // VPC　の private subnets を使用
      subnetIds: vpc.privateSubnets.map((subnet) => subnet.subnetId),
    })

    domain.applyRemovalPolicy(removalPolicy)

    // 全員の IAM User・IAM Role につける共用 Policy
    const policy = new iam.ManagedPolicy(this, 'SharedPolicy')

    // 共用 CodeCommit リポジトリへの読み書き許可
    policy.addStatements(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ['codecommit:*'],
        resources: [repository.repositoryArn],
      })
    )

    const users: User[] = [
      // ユーザーの作成
      new User(this, 'Tsugo', {
        name: 'tsugo',
        domainId: domain.attrDomainId,
        policy,
        removalPolicy,
      }),

      new User(this, 'Kudo', {
        name: 'kudo',
        domainId: domain.attrDomainId,
        policy,
        removalPolicy,
      }),
    ]

    users.forEach((user) => {
      // 共用バケットへの読み書き権限
      sharedBucket.grantReadWrite(user.user)
      sharedBucket.grantReadWrite(user.role)

      users.forEach((bucketOwner) => {
        // 他のユーザーのバケットへの読み込み権限
        bucketOwner.bucket.grantRead(user.user)
        bucketOwner.bucket.grantRead(user.role)
      })
    })
  }
}
