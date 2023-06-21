# Stable Diffusion Web UI on AWS

This is a sample cloudformation template to launch latest version of [AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui) on EC2 instance. Some variant includes [bmaltais/kohya_ss](https://github.com/bmaltais/kohya_ss) for training model and [filebrowser/filebrowser](https://github.com/filebrowser/filebrowser) for GUI based file manipulation.

There are four cloudformation templates:

- [sd-webui.yaml](sd-webui.yaml): publicly accessible (some features are disabled for security reason)
- [sd-webui-private.yaml](sd-webui-private.yaml): privately accessible through SSM Session Manager Port Forwarding. File can be accessed using [filebrowser/filebrowser](https://github.com/filebrowser/filebrowser).
- [sd-webui-kohya-private.yaml](sd-webui-kohya-private.yaml): privately accessible through SSM Session Manager Port Forwarding with [bmaltais/kohya_ss](https://github.com/bmaltais/kohya_ss) installed as well. File can be accessed using [filebrowser/filebrowser](https://github.com/filebrowser/filebrowser).
- [sd-webui-kohya-private-s3.yaml](sd-webui-kohya-private-s3.yaml): privately accessible through SSM Session Manager Port Forwarding with [bmaltais/kohya_ss](https://github.com/bmaltais/kohya_ss) installed as well. S3 is mounted for keeping file on cloud. File can be accessed using [filebrowser/filebrowser](https://github.com/filebrowser/filebrowser).

## Getting Started

### Deploy as Public Endpoint

1. Launch template from console or with command `aws cloudformation create-stack --stack-name sd-webui-stack --template-body file://sd-webui.yaml --region us-east-1 --parameters ParameterKey=SubnetId,ParameterValue=<SubnetId> ParameterKey=VpcId,ParameterValue=<VpcId>`
2. It takes 10 min ~ to launch application.
3. Open `<public ip address>:7860`

### Deploy as Private Endpoint

Prerequisite:
- Install session manager plugin following [document](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html) if not installed yet

1. Launch template from console or with command `aws cloudformation create-stack --stack-name sd-webui-stack --template-body file://sd-webui-private.yaml --region us-east-1 --parameters ParameterKey=SubnetId,ParameterValue=<SubnetId>`
2. It takes 10 min ~ to launch application.
3. Run Port Forwarding with `./port-forwarding.sh <instance_id> <region> 7860 8080`
4. Open `localhost:7860` for Stable Diffusion Web UI. Open `localhost:8080` for file browser.

For more control over SSM Session Manager, please check out the [document](https://docs.aws.amazon.com/systems-manager/latest/userguide/getting-started-restrict-access-examples.html) to limit access of specific user to specific instance.

### Deploy Private Endpoint with Kohya SS

1. Launch template from console or with command `aws cloudformation create-stack --stack-name sd-webui-stack --template-body file://sd-webui-kohya-private.yaml --region us-east-1 --parameters ParameterKey=SubnetId,ParameterValue=<SubnetId>`
2. Run Port Forwarding with `./port-forwarding.sh <instance_id> <region> 7860 7861 8080`
3. Open `localhost:7860` for Stable Diffusion Web UI. Open `localhost:7861` for Kohya-ss. Open `localhost:8080` for file browser.

### Deploy Private Endpoint with Kohya SS and S3 Mounted

1. Launch template from console or with command `aws cloudformation create-stack --stack-name sd-webui-stack --template-body file://sd-webui-kohya-private-s3.yaml --region us-east-1 --parameters ParameterKey=EC2InstanceProfileName,ParameterValue=<InstanceProfile> ParameterKey=S3BucketName,ParameterValue=<Bucket> ParameterKey=SubnetId,ParameterValue=<SubnetId>`
2. Run Port Forwarding with `./port-forwarding.sh <instance_id> <region> 7860 7861 8080`
3. Open `localhost:7860` for Stable Diffusion Web UI. Open `localhost:7861` for Kohya-ss. Open `localhost:8080` for file browser.

### Use Filebrowser for file manipulation

1. Access port 8080
2. Enter default user/password: admin/admin
3. `/home/ubuntu` is mapped to `files` by default. (ex. `/files/s3` = `/home/ubuntu/s3`)

### Use Kohya to tune model

1. Access port 7861
2. Upload Images using Filebrowser
3. Generate CLIP for images from Utilities tab.
4. Start Training. Check `kohya-log.txt` for training logs.
5. Download weight / move weight to `~/stable-diffusion-webui/models/Lora` to use it.
6. For detailed instruction, see [bmaltais/kohya_ss](https://github.com/bmaltais/kohya_ss)

### Stop Instance

You can stop instance when you do not use it. The application will automatically launch when EC2 instance restarts.

You may use following commands to start/stop instance.

- `aws ec2 stop-instances --region <region> --instance-ids <instance-id>`
- `aws ec2 start-instances --region <region> --instance-ids <instance-id>`

### Add Extensions to Stable Diffusion Web UI

You can either add extension from UI or command line.

When using command line with SSM Session Manager,

1. Access server: `aws ssm start-session --region <region> --target <instance_id>`
2. `ssm-user` is the default user when using SSM Session Manager. You can change user with `sudo su ubuntu` for example.

## Troubleshoot

- Cannot access server
  - Check reachability with VPC Reachability Analyzer
  - Turn off VPN in case the port 7860 is blocked.
  - See logs
    - 1. Get in to the instance with SSM Session Manager from console or with command `aws ssm start-session --region <region> --target <instance_id>`
    - 2. View log of running userdata with `tail /var/log/cloud-init-output.log`
    - 3. View log of Stable Diffusion Web UI with `tail /home/ubuntu/sd-webui-log.txt`
    - 4. View log of Kohya SS with `tail /home/ubuntu/kohya-log.txt`
- Cannot access server with SSM Session Manager
  - Follow [SSM Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-getting-started.html) guide to enable Session Manager
  - It will be easier to opt for region level setting from [Fleet Manager](https://us-east-1.console.aws.amazon.com/systems-manager/managed-instances/dhmc-configuration?region=us-east-1)
- Cannot install extension from UI (Error: AssertionError: extension access disabled because of command line flags)
  - [You cannot install extension from UI when using public endpoint from security reason](https://github.com/AUTOMATIC1111/stable-diffusion-webui/issues/7153).
- CUDA out of memory for training.
  - Stopping Stable Diffusion Web UI may save some GPU memory. Fine pid consuming GPU memory with `nvidia-smi` and stop it with `kill -9 <pid>`
  - Alternatively, you may launch cloudformation template on larger instance.
- Nothing happens after clicking train / caption on kohya_ss.
  - There is no UI feedback for kohya_ss. See `kohya-log.txt` for logs. Access it from filebrowser or tail it.
- Insufficient Capacity when launching instance
  - Try another instance type supporting [AMI](https://aws.amazon.com/releasenotes/aws-deep-learning-ami-gpu-pytorch-2-0-ubuntu-20-04/) or another region.


## Notice of License for included Software

Cloudformation templates in this project  uses following software.

- [AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui): GNU Affero General Public License v3.0
- [bmaltais/kohya_ss](https://github.com/bmaltais/kohya_ss): Apache License 2.0
- [filebrowser/filebrowser](https://github.com/filebrowser/filebrowser): Apache License 2.0

Although you may choose the model you like, stable-diffusion-webui downloads following model by default.

- [runwayml/stable-diffusion-v1-5](https://huggingface.co/runwayml/stable-diffusion-v1-5): [creativeml-openrail-m License](https://huggingface.co/spaces/CompVis/stable-diffusion-license)
