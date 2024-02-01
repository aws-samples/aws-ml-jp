import { Stack, StackProps, RemovalPolicy, CfnOutput } from "aws-cdk-lib";
import { Construct } from "constructs";
import { Repository } from "aws-cdk-lib/aws-ecr";
import { DockerImageAsset, Platform } from "aws-cdk-lib/aws-ecr-assets";
import { ECRDeployment, DockerImageName } from "cdk-ecr-deployment";
import { ContainerImage } from "aws-cdk-lib/aws-ecs";
import { resolve } from "path";

interface SageMakerSelfManagedImageProps extends StackProps {
    repositoryName: string;
    versionTag: string;
}

export class SagemakerSelfManagedImage extends Stack {
    public readonly imageUri: string;
    constructor(scope: Construct, id: string, props: SageMakerSelfManagedImageProps,) {
        super(scope, id, props);
        const repo = new Repository(this, `Repository`, {
            repositoryName: props.repositoryName,
            removalPolicy: RemovalPolicy.DESTROY,
            autoDeleteImages: true,
        });

        const image = new DockerImageAsset(this, "CDKDockerImage", {
            directory: resolve(__dirname, "..", "container"),
            platform: Platform.LINUX_AMD64,
        });

        this.imageUri = ContainerImage.fromEcrRepository(repo, props.versionTag,).imageName;

        new ECRDeployment(this, "DeployDockerImage2", {
            src: new DockerImageName(image.imageUri),
            dest: new DockerImageName(this.imageUri),
        });

        new CfnOutput(this, "imageUri", {
            value: this.imageUri,
        });
    }
}
