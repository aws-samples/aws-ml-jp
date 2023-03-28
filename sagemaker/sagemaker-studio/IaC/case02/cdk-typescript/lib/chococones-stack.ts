import * as cdk from 'aws-cdk-lib'
import { Construct } from 'constructs'
import * as ec2 from 'aws-cdk-lib/aws-ec2'
import * as s3 from 'aws-cdk-lib/aws-s3'
import * as codecommit from 'aws-cdk-lib/aws-codecommit'
import * as codeartifact from 'aws-cdk-lib/aws-codeartifact'
import * as iam from 'aws-cdk-lib/aws-iam'
import * as sagemaker from 'aws-cdk-lib/aws-sagemaker'
import { User } from './constructs/user'

export class ChococonesStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props)

    // SageMaker Domain 名
    const domainName = 'chococones'

    // CodeCommit リポジトリ名
    const codecommitRepositoryName = domainName

    // CodeArtifact リポジトリ名
    const codeartifactRepositoryName = domainName

    // Domain 用の VPC
    const vpc = new ec2.Vpc(this, 'Vpc', {
      maxAzs: 2,
      natGateways: 0,
      subnetConfiguration: [
        {
          name: 'isolated-subnet',
          subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
          cidrMask: 24,
        },
      ],
    })

    // エンドポイントを設定
    new ec2.InterfaceVpcEndpoint(this, `SsmVpcEndpoint`, {
      service: ec2.InterfaceVpcEndpointAwsService.SSM,
      privateDnsEnabled: true,
      vpc: vpc,
      subnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
    })

    new ec2.InterfaceVpcEndpoint(this, `SsmMessagesVpcEndpoint`, {
      service: ec2.InterfaceVpcEndpointAwsService.SSM_MESSAGES,
      privateDnsEnabled: true,
      vpc: vpc,
      subnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
    })

    new ec2.InterfaceVpcEndpoint(this, `Ec2VpcEndpoint`, {
      service: ec2.InterfaceVpcEndpointAwsService.EC2,
      privateDnsEnabled: true,
      vpc: vpc,
      subnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
    })

    new ec2.InterfaceVpcEndpoint(this, `EC2MessagesVpcEndpoint`, {
      service: ec2.InterfaceVpcEndpointAwsService.EC2_MESSAGES,
      privateDnsEnabled: true,
      vpc: vpc,
      subnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
    })

    new ec2.InterfaceVpcEndpoint(this, `EcrVpcEndpoint`, {
      service: ec2.InterfaceVpcEndpointAwsService.ECR,
      privateDnsEnabled: true,
      vpc: vpc,
      subnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
    })

    new ec2.InterfaceVpcEndpoint(this, `EcrDockerVpcEndpoint`, {
      service: ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER,
      privateDnsEnabled: true,
      vpc: vpc,
      subnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
    })

    new ec2.InterfaceVpcEndpoint(this, `KmsVpcEndpoint`, {
      service: ec2.InterfaceVpcEndpointAwsService.KMS,
      privateDnsEnabled: true,
      vpc: vpc,
      subnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
    })

    new ec2.InterfaceVpcEndpoint(this, `CodeArtifactApiVpcEndpoint`, {
      service: ec2.InterfaceVpcEndpointAwsService.CODEARTIFACT_API,
      privateDnsEnabled: true,
      vpc: vpc,
      subnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
    })

    new ec2.InterfaceVpcEndpoint(this, `CodeArtifactRepositoriesVpcEndpoint`, {
      service: ec2.InterfaceVpcEndpointAwsService.CODEARTIFACT_REPOSITORIES,
      privateDnsEnabled: true,
      vpc: vpc,
      subnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
    })

    new ec2.InterfaceVpcEndpoint(this, `CodeCommitVpcEndpoint`, {
      service: ec2.InterfaceVpcEndpointAwsService.CODECOMMIT,
      privateDnsEnabled: true,
      vpc: vpc,
      subnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
    })

    new ec2.InterfaceVpcEndpoint(this, `CodeCommitGitVpcEndpoint`, {
      service: ec2.InterfaceVpcEndpointAwsService.CODECOMMIT_GIT,
      privateDnsEnabled: true,
      vpc: vpc,
      subnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
    })

    new ec2.InterfaceVpcEndpoint(this, `SmApiVpcEndpoint`, {
      service: ec2.InterfaceVpcEndpointAwsService.SAGEMAKER_API,
      privateDnsEnabled: true,
      vpc: vpc,
      subnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
    })

    new ec2.InterfaceVpcEndpoint(this, `SmStdioApiVpcEndpoint`, {
      service: ec2.InterfaceVpcEndpointAwsService.SAGEMAKER_STUDIO,
      privateDnsEnabled: true,
      vpc: vpc,
      subnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
    })

    new ec2.InterfaceVpcEndpoint(this, `SmNotebookRuntimeApiVpcEndpoint`, {
      service: ec2.InterfaceVpcEndpointAwsService.SAGEMAKER_NOTEBOOK,
      privateDnsEnabled: true,
      vpc: vpc,
      subnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
    })

    new ec2.InterfaceVpcEndpoint(this, `SmRuntimeApiVpcEndpoint`, {
      service: ec2.InterfaceVpcEndpointAwsService.SAGEMAKER_RUNTIME,
      privateDnsEnabled: true,
      vpc: vpc,
      subnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
    })

    new ec2.InterfaceVpcEndpoint(this, 'SecretsManagerApiVpcEndpoint', {
      service: ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
      privateDnsEnabled: true,
      vpc: vpc,
      subnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
    })
    vpc.addGatewayEndpoint('S3GatewayEndpoint', {
      service: ec2.GatewayVpcEndpointAwsService.S3,
      subnets: [{ subnetType: ec2.SubnetType.PRIVATE_ISOLATED }],
    })

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
      repositoryName: codecommitRepositoryName,
    })

    const codeartifactDomain = new codeartifact.CfnDomain(
      this,
      'codeartifactDomain',
      {
        domainName: codeartifactRepositoryName,
      }
    )

    const codeartifactRepository = new codeartifact.CfnRepository(
      this,
      'codeartifactRepository',
      {
        domainName: codeartifactDomain.domainName,
        repositoryName: codeartifactRepositoryName,
        externalConnections: ['public:pypi'],
      }
    )

    codeartifactRepository.addDependency(codeartifactDomain)

    // SageMaker Domain 用の default execution Role
    const defaultRole = new iam.Role(this, 'DefaultRole', {
      assumedBy: new iam.ServicePrincipal('sagemaker.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonSageMakerFullAccess'),
      ],
    })

    const domainSecurityGroup = new ec2.SecurityGroup(
      this,
      'DomainSecurityGroup',
      {
        vpc,
        allowAllOutbound: true,
      }
    )
    // Studio Domain
    const domain = new sagemaker.CfnDomain(this, 'Domain', {
      authMode: 'IAM',
      defaultUserSettings: {
        executionRole: defaultRole.roleArn,
        securityGroups: [domainSecurityGroup.securityGroupId],
        jupyterServerAppSettings: {
          defaultResourceSpec: {
            sageMakerImageArn: `arn:aws:sagemaker:${this.region}:102112518831:image/jupyter-server-3`,
          },
        },
      },
      domainName,
      vpcId: vpc.vpcId,
      // VPC　の private subnets を使用
      subnetIds: vpc.isolatedSubnets.map((subnet) => subnet.subnetId),
      appNetworkAccessType: 'VpcOnly',
    })

    domain.applyRemovalPolicy(removalPolicy)

    // 全員の SageMaker Studio Profile につける共用 Policy
    const studioCommonPolicy = new iam.ManagedPolicy(this, 'CommonPolicy')

    // 共用 CodeArtifact リポジトリへのアクセス許可
    studioCommonPolicy.addStatements(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: [
          'codeartifact:DescribeDomain',
          'codeartifact:DescribeRepository',
          'codeartifact:GetAuthorizationToken',
          'codeartifact:GetRepositoryEndpoint',
          'codeartifact:GetRepositoryPermissionsPolicy',
          'codeartifact:ListPackages',
          'codeartifact:ListRepositories',
          'codeartifact:ListTagsForResource',
          'codeartifact:ReadFromRepository',
        ],
        resources: [codeartifactDomain.attrArn, codeartifactRepository.attrArn],
      })
    )

    studioCommonPolicy.addStatements(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ['sts:GetServiceBearerToken'],
        resources: ['*'],
        conditions: {
          StringEquals: {
            'sts:AWSServiceName': 'codeartifact.amazonaws.com',
          },
        },
      })
    )

    const users: User[] = [
      // ユーザーの作成
      new User(this, 'Tsugo', {
        name: 'tsugo',
        domainId: domain.attrDomainId,
        stdioCommonPolicy: studioCommonPolicy,
        vpc,
        removalPolicy,
      }),

      new User(this, 'Kudo', {
        name: 'kudo',
        domainId: domain.attrDomainId,
        stdioCommonPolicy: studioCommonPolicy,
        vpc,
        removalPolicy,
      }),
    ]

    users.forEach((user) => {
      // 共用バケットへの読み書き権限
      sharedBucket.grantReadWrite(user.stdioRole)

      // 共用 CodeCommit リポジトリへのアクセス許可
      repository.grantPullPush(user.stdioRole)

      users.forEach((bucketOwner) => {
        // 他のユーザーのバケットへの読み込み権限
        bucketOwner.bucket.grantRead(user.stdioRole)
      })
    })
  }
}
