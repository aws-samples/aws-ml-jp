import * as cdk from 'aws-cdk-lib'
import { Construct } from 'constructs'
import * as iam from 'aws-cdk-lib/aws-iam'
import { Effect } from 'aws-cdk-lib/aws-iam'
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager'
import * as sagemaker from 'aws-cdk-lib/aws-sagemaker'
import * as s3 from 'aws-cdk-lib/aws-s3'
import * as ec2 from 'aws-cdk-lib/aws-ec2'

export interface UserProps {
  name: string
  domainId: string
  stdioCommonPolicy: iam.ManagedPolicy
  vpc: ec2.Vpc
  removalPolicy: cdk.RemovalPolicy
}

export class User extends Construct {
  public readonly user: iam.User
  public readonly stdioRole: iam.Role
  public readonly userProfile: sagemaker.CfnUserProfile
  public readonly bucket: s3.Bucket

  constructor(scope: Construct, id: string, props: UserProps) {
    super(scope, id)

    const { accountId, region } = new cdk.ScopedAws(this)

    // IAM User 用のパスワードを Secrets Manager で生成
    const secret = new secretsmanager.Secret(this, 'UserSecret')

    new cdk.CfnOutput(this, 'UserSecretName', {
      value: secret.secretName,
    })

    // EC2 用のパスワードを Secrets Manager で生成
    const ec2Secret = new secretsmanager.Secret(this, 'Ec2Secret')

    new cdk.CfnOutput(this, 'Ec2SecretName', {
      value: ec2Secret.secretName,
    })

    // EC2 インスタンスに設定するタグ
    const nameTagValue = `ec2-individual-${props.name}`

    // 各人用の Sagemaker Studio の User Profile にアタッチするロール
    this.stdioRole = new iam.Role(this, 'Role', {
      assumedBy: new iam.ServicePrincipal('sagemaker.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonSageMakerFullAccess'),
        props.stdioCommonPolicy,
      ],
    })

    this.stdioRole.addManagedPolicy(props.stdioCommonPolicy)

    // Sagemaker Studio 内から 署名付き URL 発行を禁じる
    //（他人の user_profile で署名付きURL発行防止目的だが、そもそも署名付き URL を発行することがないため）
    const denyPresignedPolicy = new iam.ManagedPolicy(
      this,
      'DenyPresignedPolicy'
    )

    denyPresignedPolicy.addStatements(
      new iam.PolicyStatement({
        effect: iam.Effect.DENY,
        actions: ['sagemaker:CreatePresignedDomainUrl'],
        resources: ['*'],
      })
    )

    // SageMaker User Profile
    const userProfile = new sagemaker.CfnUserProfile(this, 'UserProfile', {
      domainId: props.domainId,
      userProfileName: props.name,
      userSettings: {
        executionRole: this.stdioRole.roleArn,
      },
    })

    // インスタンス用 Role
    const instanceRole = new iam.Role(this, `InstanceRole`, {
      assumedBy: new iam.ServicePrincipal('ec2.amazonaws.com'),
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName(
          'AmazonSSMManagedInstanceCore'
        ),
      ],
    })

    const instancePolicy = new iam.ManagedPolicy(this, 'InstancePolicy')
    instancePolicy.addStatements(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ['sagemaker:CreatePresignedDomainUrl'],
        resources: [userProfile.attrUserProfileArn],
      })
    )

    instancePolicy.addStatements(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ['secretsmanager:GetSecretValue'],
        resources: [ec2Secret.secretArn],
      })
    )

    instanceRole.addManagedPolicy(instancePolicy)

    // EC2 インスタンス
    const instance = new ec2.Instance(this, 'Instance', {
      vpc: props.vpc,
      vpcSubnets: props.vpc.selectSubnets({
        subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
      }),
      instanceType: ec2.InstanceType.of(
        ec2.InstanceClass.T3,
        ec2.InstanceSize.LARGE
      ),
      machineImage: new ec2.WindowsImage(
        ec2.WindowsVersion.WINDOWS_SERVER_2022_ENGLISH_FULL_BASE
      ),
      blockDevices:[
        {
          deviceName: "/dev/sda1",
          volume: ec2.BlockDeviceVolume.ebs(30, {
            encrypted: true
          })
        }
      ],

      role: instanceRole,
      userData: ec2.UserData.custom(
        `
<powershell>
$password = (Get-SECSecretValue -SecretId ${ec2Secret.secretArn} -Region ${region}).SecretString
New-LocalUser -Name user-1 -Password (ConvertTo-SecureString $password -AsPlainText -Force)
Add-LocalGroupMember -Group "Remote Desktop Users" -Member user-1
Add-LocalGroupMember -Group Administrators -Member user-1
Write-Output '$url = New-SMPresignedDomainUrl -DomainId ${props.domainId} -ExpiresInSecond 30 -UserProfileName ${userProfile.userProfileName} -Region ${region}' | Set-Content -Encoding Default 'C:\\GetPresignedUrl.ps1'
Write-Output 'start microsoft-edge:$url' | Add-Content -Encoding Default 'C:\\GetPresignedUrl.ps1' 
</powershell>
<persist>true</persist>
`
      ),
      requireImdsv2: true,
    })

    cdk.Tags.of(instance).add('Name', nameTagValue)

    // IAM ユーザー
    this.user = new iam.User(this, 'User', {
      userName: props.name,
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('IAMUserChangePassword'),
        props.stdioCommonPolicy,
      ],
      password: secret.secretValue,
      passwordResetRequired: true,
    })

    // IAM ユーザーにアタッチする Fleet Manager を使うためのポリシー
    const startSessionPolicyJson = {
      Version: '2012-10-17',
      Statement: [
        {
          Sid: 'EC2GetPasswordData',
          Effect: 'Allow',
          Action: ['ec2:GetPasswordData'],
          Resource: `arn:aws:ec2:${region}:${accountId}:instance/${instance.instanceId}`,
        },
        {
          Sid: 'EC2DescribeInstances',
          Effect: 'Allow',
          Action: ['ec2:DescribeInstances'],
          Resource: '*',
        },

        {
          Sid: 'SSM',
          Effect: 'Allow',
          Action: [
            'ssm:DescribeInstanceProperties',
            'ssm:GetCommandInvocation',
            'ssm:GetInventorySchema',
          ],
          Resource: '*',
        },
        {
          Sid: 'SSMStartSession',
          Effect: 'Allow',
          Action: ['ssm:StartSession'],
          Resource: ['arn:aws:ssm:*::document/AWS-StartPortForwardingSession'],
          Condition: {
            BoolIfExists: {
              'ssm:SessionDocumentAccessCheck': 'true',
            },
          },
        },
        {
          Sid: 'AccessTaggedInstances',
          Effect: 'Allow',
          Action: ['ssm:StartSession'],
          Resource: [
            `arn:aws:ec2:*:${accountId}:instance/*`,
            `arn:aws:ssm:*:${accountId}:managed-instance/*`,
          ],
          Condition: {
            StringLike: {
              'ssm:resourceTag/Name': [nameTagValue],
            },
          },
        },
        {
          Sid: 'GuiConnect',
          Effect: 'Allow',
          Action: [
            'ssm-guiconnect:CancelConnection',
            'ssm-guiconnect:GetConnection',
            'ssm-guiconnect:StartConnection',
          ],
          Resource: '*',
        },
      ],
    }

    const startSessionPolicyDocument = iam.PolicyDocument.fromJson(
      startSessionPolicyJson
    )
    const startSessionManagedPolicy = new iam.ManagedPolicy(
      this,
      'StartSessionManagedPolicy',
      {
        document: startSessionPolicyDocument,
      }
    )
    startSessionManagedPolicy.attachToUser(this.user)

    // 個人バケット
    this.bucket = new s3.Bucket(this, 'Bucket', {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      enforceSSL: true,
      removalPolicy: props.removalPolicy,
    })

    // 持ち主は読み書きできる
    this.bucket.grantReadWrite(this.stdioRole)
  }
}
