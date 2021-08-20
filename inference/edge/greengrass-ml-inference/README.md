# greengrass-ml-inference
* 本コンテンツは AWS IoT Greengrass(v2) 上で動く ML 推論アプリを開発、デプロイするハンズオンです。
* EC2 を 4 台、それぞれ開発機、ステージング機、本番機 2 台をエッジデバイスとして扱います。
* ML モデルの作成は [build_mnist_dcgan_and_classifier.ipynb](./build_mnist_dcgan_and_classifier.ipynb) で行っていますが、モデル自体はこのリポジトリにすでに含まれているため改めて動かす必要はありません。
* [greengrass_ml_inference.ipynb](greengrass_ml_inference.ipynb)ですべて動作が完結するように記載しているため、詳細は[greengrass_ml_inference.ipynb](greengrass_ml_inference.ipynb)をご参照ください。
* notebook を実行する環境には下記ポリシーがアタッチされていることを前提としています。
  * AmazonEC2FullAccess
  * AmazonSSMFullAccess
  * AmazonS3FullAccess
  * IAMFullAccess
  * AWSGreengrassFullAccess
  * AWSIoTFullAccess
  * AmazonEC2ContainerRegistryFullAccess