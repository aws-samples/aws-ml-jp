## Object Detection with Detectron2 on Amazon SageMaker

### Overview

In this repository, we use [Amazon SageMaker](https://aws.amazon.com/sagemaker/) to build, train and deploy [Faster-RCNN](https://arxiv.org/abs/1506.01497) and [RetinaNet](https://arxiv.org/abs/1708.02002) models using [Detectron2](https://github.com/facebookresearch/detectron2).
Detectron2 is an open-source project released by Facebook AI Research and build on top of PyTorch deep learning framework. Detectron2 makes easy to build, train and deploy state of the art object detection algorithms. Moreover, Detecron2’s design makes easy to implement cutting-edge research projects without having to fork the entire codebase.Detectron2 also provides a [Model Zoo](https://github.com/facebookresearch/detectron2/blob/master/MODEL_ZOO.md) which is a collection of pre-trained detection models we can use to accelerate our endeavour.

This repository shows how to do the following:

* Build Detectron2 Docker images and push them to [Amazon ECR](https://aws.amazon.com/ecr/) to run training and inference jobs on Amazon SageMaker.
* Register a dataset in Detectron2 catalog from annotations in augmented manifest files. Augmented manifest file is the output format of [Amazon SageMaker Ground Truth](https://aws.amazon.com/sagemaker/groundtruth/) annotation jobs.
* Run a SageMaker Training job to finetune pre-trained model weights on a custom dataset.
* Configure SageMaker Hyperparameter Optimization jobs to finetune hyper-parameters.
* Run a SageMaker Batch Transform job to predict bouding boxes in a large chunk of images.

### Get Started

Create a SageMaker notebook instance with an EBS volume equal or bigger than 30 GB and add the following lines to **start notebook** section of your life cycle configuration:

```
service docker stop
sudo mv /var/lib/docker /home/ec2-user/SageMaker/docker
sudo ln -s /home/ec2-user/SageMaker/docker /var/lib/docker
service docker start
```

This ensures that docker builds images to a folder that is mounted on EBS. Once the instance is running, open Jupyter lab, launch a terminal and clone this repository:

```
cd SageMaker
git clone https://github.com/aws-samples/amazon-sagemaker-pytorch-detectron2.git
cd amazon-sagemaker-pytorch-detectron2
```
Open the [notebook](d2_custom_sku110k.ipynb). Follow the instruction in the notebook and use `conda_pytorch_p36` as kernel to execute code cells.

You can also test the content in this repository on an EC2 that is running the [AWS Deep Learning AMI](https://docs.aws.amazon.com/dlami/latest/devguide/what-is-dlami.html).
### Instructions

You will use a Detectron2 object detection model to recognize objects in densely packed scenes. You will use the SKU-110k dataset for this task. Be aware that the authors of the dataset provided it solely for academic and non-commercial purposes. Please refer to the following [paper](https://arxiv.org/abs/1904.00853) for further details on the dataset:

```
@inproceedings{goldman2019dense,
 author    = {Eran Goldman and Roei Herzig and Aviv Eisenschtat and Jacob Goldberger and Tal Hassner},
 title     = {Precise Detection in Densely Packed Scenes},
 booktitle = {Proc. Conf. Comput. Vision Pattern Recognition (CVPR)},
 year      = {2019}
}
```

If you want details on the code used for [training](container_training/sku-110k) and [prediction](container_serving), please refer to code documentation in the respective source directories.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

