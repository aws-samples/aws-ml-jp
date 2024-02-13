#!/usr/bin/env node
import 'source-map-support/register';
import { App, Tags } from "aws-cdk-lib";
import { SagemakerSelfManagedImage } from "../lib/sagemaker-self-managed-image";
import { SagemakerJupyterLabCdkStack } from "../lib/sagemaker-jupyter-lab-byoc-stack";

const app = new App();

const repositoryName: string = app.node.tryGetContext("repositoryName");
const versionTag: string = app.node.tryGetContext("versionTag");
const domainId: string = app.node.tryGetContext("domainId");
const imageName: string = app.node.tryGetContext("imageName");
const imageDisplayName: string = app.node.tryGetContext("imageDisplayName");

const sagemakerSelfManagedImage = new SagemakerSelfManagedImage(app, `SagemakerSelfManagedImage`, {
    repositoryName: repositoryName,
    versionTag: versionTag,
});

const sagemakerJupyterLabCdkStack = new SagemakerJupyterLabCdkStack(app, "SagemakerJupyterLabCdkStack",{
    imageUri: sagemakerSelfManagedImage.imageUri,
    domainId: domainId,
    imageName: imageName,
    imageDisplayName: imageDisplayName,
});
sagemakerJupyterLabCdkStack.addDependency(sagemakerSelfManagedImage);

Tags.of(app).add("stack", "SagemakerJupyterLabCdkStack");
