import { Stack, StackProps, custom_resources } from "aws-cdk-lib";
import { AwsCustomResource } from "aws-cdk-lib/custom-resources";
import { Construct } from "constructs";
import * as iam from "aws-cdk-lib/aws-iam";
import * as sagemaker from "aws-cdk-lib/aws-sagemaker";

interface SagemakerJupyterLabCdkStackProps extends StackProps {
    imageUri: string;
    domainId: string;
    imageName: string;
    imageDisplayName: string;
}

export class SagemakerJupyterLabCdkStack extends Stack {
    constructor(scope: Construct, id: string, props: SagemakerJupyterLabCdkStackProps,) {
        super(scope, id, props);
        
        const sagemakerRole = new iam.Role(this, "SagemakerRole", {
            assumedBy: new iam.ServicePrincipal("sagemaker.amazonaws.com"),
            managedPolicies: [
                iam.ManagedPolicy.fromAwsManagedPolicyName("AmazonSageMakerFullAccess"),
            ],
        });


        const customResourceRole = new iam.Role(this, "CustomResourceRole", {
            assumedBy: new iam.ServicePrincipal("lambda.amazonaws.com"),
            managedPolicies: [
                iam.ManagedPolicy.fromAwsManagedPolicyName("AWSLambda_FullAccess"),
            ],
            inlinePolicies: {
                'sm-domain-action' : new iam.PolicyDocument({
                    statements: [
                        new iam.PolicyStatement({
                            effect: iam.Effect.ALLOW,
                            actions: [
                                'sagemaker:UpdateDomain',
                                'sagemaker:CreateAppImageConfig',
                                'sagemaker:deleteAppImageConfig',
                            ],
                            resources: [
                                '*'
                            ]
                        })
                    ]
                })
            }
        });

        const cfnImage = new sagemaker.CfnImage(this, `CfnImage`, {
            imageName: props.imageName,
            imageRoleArn: sagemakerRole.roleArn,
            imageDisplayName: props.imageDisplayName,
        });

        const cfnImageVersion = new sagemaker.CfnImageVersion(this, "CfnImageVersion",{
            baseImage: props.imageUri,
            imageName: cfnImage.imageName,
        });
        cfnImageVersion.addDependency(cfnImage);

        // custom resource で app image config
        new AwsCustomResource(this, `AppImageConfig${id}`, {
            onCreate: {
                service: "SageMaker",
                action: "CreateAppImageConfig",
                parameters: {
                    AppImageConfigName: `AppImageConfig${id}`,
                    JupyterLabAppImageConfig: {},
                },
                physicalResourceId: custom_resources.PhysicalResourceId.of(`AppImageConfig${id}`,),
            },
            onDelete: {
                service: "SageMaker",
                action: "DeleteAppImageConfig",
                parameters: {AppImageConfigName: `AppImageConfig${id}`},
                physicalResourceId: custom_resources.PhysicalResourceId.of(`AppImageConfig${id}`),
            },
            role: customResourceRole,
        });

        // custom resource で update_domain
        new AwsCustomResource(this, `Domain${id}`, {
            onCreate: {
                service: "SageMaker",
                action: "UpdateDomain",
                parameters: {
                    DomainId: props.domainId,
                    DefaultUserSettings: {
                        JupyterLabAppSettings: {
                            CustomImages: [
                                {
                                    ImageName: cfnImage.imageName.toString(),
                                    ImageVersionNumber: 1,
                                    AppImageConfigName: `AppImageConfig${id}`,
                                },
                            ],
                        },
                    },
                },
            physicalResourceId: custom_resources.PhysicalResourceId.of(`Domain${id}`,),
            },
            onDelete: {
                service: "SageMaker",
                action: "UpdateDomain",
                parameters: {
                    DomainId: props.domainId,
                    DefaultUserSettings: {
                        JupyterLabAppSettings: {
                            CustomImages: [],
                    },
                },
                },
                physicalResourceId: custom_resources.PhysicalResourceId.of(`Domain${id}`,),
            },
            onUpdate: {
                service: "SageMaker",
                action: "UpdateDomain",
                parameters: {
                    DomainId: props.domainId,
                    DefaultUserSettings: {
                        JupyterLabAppSettings: {
                            CustomImages: [
                                {
                                    ImageName: cfnImage.imageName.toString(),
                                    ImageVersionNumber: 1,
                                    AppImageConfigName: `AppImageConfig${id}`,
                                },
                            ],
                        },
                    },
                },
                physicalResourceId: custom_resources.PhysicalResourceId.of(`Domain${id}`,),
            },
            role: customResourceRole,
        });
    }
}
