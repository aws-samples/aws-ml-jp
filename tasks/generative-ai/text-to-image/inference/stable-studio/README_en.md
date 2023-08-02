# Stable Studio on AWS

Sample code to deploy [Stable Studio](https://github.com/Stability-AI/StableStudio/tree/main) with [Stable Diffusion Web UI](https://github.com/AUTOMATIC1111/stable-diffusion-webui) as backend on AWS.

There are two cloudformation templates

| Launch Stack | Cfn Template | Description |
| ------------ | ------------ | ----------- |
| [![](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://us-east-1.console.aws.amazon.com/cloudformation/home#/stacks/create/review?stackName=stable-studio&templateURL=https://aws-ml-jp.s3.ap-northeast-1.amazonaws.com/tasks/generative-ai/text-to-image/stable-studio/stable-studio-webui.yaml) | [stable-studio-webui.yaml](stable-studio-webui.yaml) | Deploy Stable Studio on single EC2 instance for testing |
| [![](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://us-east-1.console.aws.amazon.com/cloudformation/home#/stacks/create/review?stackName=stable-studio&templateURL=https://aws-ml-jp.s3.ap-northeast-1.amazonaws.com/tasks/generative-ai/text-to-image/stable-studio/stable-studio-webui-alb.yaml) | [stable-studio-webui-alb.yaml](stable-studio-webui-alb.yaml) | Deploy backend of Stable Studio using ALB + ASG with HTTPS using custom domain. Production setting with Static Site + Backend |

## Installation (Single Instance)

1. Deploy Stable Studio on Single EC2 Instance
   1. [![](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=sd-webui&templateURL=https://aws-ml-jp.s3.ap-northeast-1.amazonaws.com/tasks/generative-ai/text-to-image/stable-studio/stable-studio-webui.yaml)
2. Setup Stable Studio (This step is required for all user using the app)
    1. Open `<public ip address>:3000` on browser
    2. Open setting from icon on top right, and enter `http://<public ip address>:7861` for host url.
    3. Go back to generation page, open `Advanced` and select `model` and `sampler` option.
    4. Click `Dream` to generate image.

## Installation (Static Site + Backend)

1. Deploy Stable Studio as Static Site using Amplify Hosting
   1. Fork [Stable Studio](https://github.com/Stability-AI/StableStudio)
   2. Open [Amplify Console](https://us-east-1.console.aws.amazon.com/amplify)
   3. Select `New App` > `Host Web App` > `GitHub` and complete GitHub integration.
   4. Select forked repository and go to next.
   5. Replace `Build Setting` with following and deploy.
```
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - yarn install
    build:
      commands:
        - npx cross-env VITE_USE_WEBUI_PLUGIN=true yarn build
  artifacts:
    # IMPORTANT - Please verify your build output directory
    baseDirectory: /packages/stablestudio-ui/dist/
    files:
      - '**/*'
  cache:
    paths:
      - node_modules/**/*
```
2. Deploy backend using Stable Diffusion Web UI.
   1. [![](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=sd-webui&templateURL=https://aws-ml-jp.s3.ap-northeast-1.amazonaws.com/tasks/generative-ai/text-to-image/stable-studio/stable-studio-webui.yaml)
   2. Set parameter StableStudioURL to url of deployed amplify app. (i.e.`https://main.***.amplifyapp.com`) 
3. Finish setup of Stable Studio (This step is required for all user using the app)
   1. Open Stable Studio on browser (i.e. `https://main.***.amplifyapp.com`)
   2. Go to setting by clicking icon on top right and set host url to endpoint of deployed Stable Diffusion Web UI. (i.e. `http://111.222.333.444:7861`)
   3. Go back to generate page, open `Advanced` and set `model` and `sampler` from options.
   4. Click Dream to test image is generated.

## Troubleshoot

- Cannot access Stable Diffusion Web UI server
  - Check reachability with VPC Reachability Analyzer
  - Turn off VPN in case the port is blocked.
  - See logs
    - 1. Get in to the instance with SSM Session Manager from console or with command `aws ssm start-session --region <region> --target <instance_id>`
        - Prerequisite: Install [Session Manger Plugin](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html) and attach IAM role with [SSM Permission](https://docs.aws.amazon.com/systems-manager/latest/userguide/getting-started-add-permissions-to-existing-profile.html) to the instance.（Not required if [default host management configuration](https://docs.aws.amazon.com/systems-manager/latest/userguide/managed-instances-default-host-management.html) is enabled）。
    - 2. View log of running userdata with `tail /var/log/cloud-init-output.log`
    - 3. View log of Stable Diffusion Web UI with `tail /home/ubuntu/sd-webui-log.txt`
- Insufficient Capacity when launching instance
  - Try another instance type supporting [AMI](https://aws.amazon.com/releasenotes/aws-deep-learning-ami-gpu-pytorch-2-0-ubuntu-20-04/) or another region.
- Image not generated when clicking `Dream`.
  - Check api endpoint is running by directly accessing Stable Diffusion Web UI endpoint.
  - Check api endpoint is set correctly by checking setting page.
  - Check model and sampler is set correctly.

## Notice of License for included Software

Cloudformation templates in this project  uses following software.

- [AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui): GNU Affero General Public License v3.0
- [Stability-AI/StableStudio](https://github.com/Stability-AI/StableStudio/tree/main): MIT License

Although you may choose the model you like, stable-diffusion-webui downloads following model by default.

- [runwayml/stable-diffusion-v1-5](https://huggingface.co/runwayml/stable-diffusion-v1-5): [creativeml-openrail-m License](https://huggingface.co/spaces/CompVis/stable-diffusion-license)

