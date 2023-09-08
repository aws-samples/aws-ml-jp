# AWS NEURON JP


[AWS Trainium](https://aws.amazon.com/jp/machine-learning/trainium/)、[AWS Inferentia](https://aws.amazon.com/jp/machine-learning/inferentia/) は、AWSが設計した機械学習アクセラレータで、クラウドで低コストでコスト効率の高い機械学習トレーニング、推論を可能にします。



![Neuron Overview](./neuron-aws-ml-chip.png)


## Amazon EC2 Inf1 インスタンス

[Amazon EC２ Inf1](https://aws.amazon.com/jp/ec2/instance-types/inf1/) インスタンスは 2019年12月にローンチした初代 AWS Inferentia を搭載したインスタンスです。これまで [Money Forward 様](https://aws.amazon.com/jp/builders-flash/202209/create-large-scale-inference-environment/)、[ByteDance 様](https://aws.amazon.com/jp/blogs/news/bytedance-saves-up-to-60-on-inference-costs-while-reducing-latency-and-increasing-throughput-using-aws-inferentia/) をはじめとした多くの AWS のお客様に活用頂いているだけではなく、[Amazon Alexa](https://aws.amazon.com/jp/blogs/news/majority-of-alexa-now-running-on-faster-more-cost-effective-amazon-ec2-inf1-instances/)、[Amazon Search](https://aws.amazon.com/jp/blogs/news/how-amazon-search-reduced-ml-inference-costs-by-85-with-aws-inferentia/)、[Amazon Robotics](https://aws.amazon.com/jp/solutions/case-studies/amazon-robotics-case-study/) といった Amazon、AWS が提供しているサービスを支えるインフラとしても活用されています。



## Amazon EC2 Trn1 インスタンス
[Amazon EC２ Trn1](https://aws.amazon.com/jp/ec2/instance-types/trn1/) インスタンスは、大規模言語モデル（LLM）などの生成系 AI モデルのトレーニングに特化した AWS Trainium を搭載したインスタンスです。Trn1 インスタンスは、他の同等の Amazon EC2 のインスタンスと比較して、トレーニングにかかるコストを最大 50% 削減します。 AWS Trainium では第二世代となる [NeuronCore-v2](https://awsdocs-neuron.readthedocs-hosted.com/en/latest/general/arch/neuron-hardware/neuron-core-v2.html) を搭載しています。


## Amazon EC2 Inf2 インスタンス
[Amazon EC２ Inf2](https://aws.amazon.com/jp/ec2/instance-types/inf2/) インスタンスは、第 2 世代の AWS Inferentia アクセラレータである AWS Inferentia2 を搭載しています。Inf1 インスタンスと比較し、最大 3 倍のコンピューティングパフォーマンス、最大 4 倍のアクセラレーターメモリ、最大 4 倍のスループット、10 分の 1 以下の低レイテンシーを実現します。
AWS Trainium と同じ世代となる NeuronCore-v2 を搭載、推論だけではなく、小規模モデルのファインチューニングも実行可能です。


## AWS Neuron
[AWS Neuron](https://aws.amazon.com/jp/machine-learning/neuron/) は　AWS Trainium、AWS Inferentia 上に機械学習ワークロードを実装する支援をするための SDK です。PyTorch や TensorFlow などのフレームワークとネイティブに統合されるため、既存のコードやワークフローを引き続き利用可能です。
機械学習 (ML) フレームワークやライブラリ、モデルアーキテクチャ、ハードウェア最適化など、現在の Neuron のサポートについては、[AWS Neuron ドキュメント](https://awsdocs-neuron.readthedocs-hosted.com/) をご覧ください。


## :books: 日本語コンテンツ

* [日本語 BERT Base Model Fine-tuning & Deployment on Inferentia2/Trainium](./bertj_finetuning_classification/)
  * 日本語BERTモデルを用いてファインチューニングと推論を同一インスタンス上で通して実行
  * inf2.xlarge もしくは trn1.2xlarge上で実行可能（より大きいサイズのインスタンスでも実行可能）
* [ViT Model Fine-tuning & Deployment on Inferentia2/Trainium](./ViT_finetuning_classification/)
  * Vision Transformer (ViT) モデルを beans データセットを使ってファインチューニングから推論まで同一インスタンス上で通して実行
  * inf2.xlarge もしくは trn1.2xlarge上で実行可能（より大きいサイズのインスタンスでも実行可能）

## :books: グローバルコンテンツ

* https://awsdocs-neuron.readthedocs-hosted.com/en/latest/general/arch/model-architecture-fit.html
  * AWS Trainium、AWS Inferentia が対応しているモデル、得意不得意なモデルに関してはこちらのドキュメントをご参照下さい。
* https://github.com/aws-neuron/aws-neuron-samples/
  * This repository contains samples for AWS Neuron, the software development kit (SDK) that enables machine learning (ML) inference and training workloads on the AWS ML accelerator chips Inferentia and Trainium.
* https://github.com/aws-samples/ml-specialized-hardware
  * In this tutorial you'll learn how to use AWS Trainium and AWS Inferentia with Amazon SageMaker and Hugging Face Optimum Neuron, to optimize your ML workloads
* https://github.com/huggingface/optimum-neuron
  * 🤗 Optimum Neuron is the interface between the 🤗 Transformers library and AWS Accelerators including AWS Trainium and AWS Inferentia. It provides a set of tools enabling easy model loading, training and inference on single- and multi-Accelerator settings for different downstream tasks.


## 📝 注目コンテンツ

* Llama2 7B (学習)
  * [Llama2 pretraining job using neuronx-nemo-megatron](https://github.com/aws-neuron/aws-neuron-parallelcluster-samples/blob/master/examples/jobs/neuronx-nemo-megatron-llamav2-job.md)
* Llama2 7B/13B (推論 - テキスト生成)
  * [Llama2 autoregressive sampling using transformers-neuronx](https://github.com/aws-neuron/aws-neuron-samples/blob/master/torch-neuronx/transformers-neuronx/inference/meta-llama-2-13b-sampling.ipynb)
* Stable Diffusion (推論 - 画像生成)
  * AWSブログ: [AWS Inferentia2 で Stable Diffusion のパフォーマンスを最大化し、推論コストを削減する](https://aws.amazon.com/jp/blogs/news/create-high-quality-images-with-stable-diffusion-models-and-deploy-them-cost-efficiently-with-amazon-sagemaker/)
  * [HuggingFace Stable Diffusion 1.5 (512x512)](https://github.com/aws-neuron/aws-neuron-samples/blob/master/torch-neuronx/inference/hf_pretrained_sd15_512_inference.ipynb)
  * [HuggingFace Stable Diffusion 2.1 (512x512)](https://github.com/aws-neuron/aws-neuron-samples/blob/master/torch-neuronx/inference/hf_pretrained_sd2_512_inference.ipynb)
  * [HuggingFace Stable Diffusion 2.1 (768x768)](https://github.com/aws-neuron/aws-neuron-samples/blob/master/torch-neuronx/inference/hf_pretrained_sd2_768_inference.ipynb)
  * [HuggingFace Stable Diffusion XL 1.0 (1024x1024)](https://github.com/aws-neuron/aws-neuron-samples/blob/master/torch-neuronx/inference/hf_pretrained_sdxl_1024_inference.ipynb)
