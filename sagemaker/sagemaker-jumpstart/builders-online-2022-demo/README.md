# builders-online-202201-demo
Amazon SageMaker GroundTruth で画像に対する物体検出用のラベリングジョブと、  
Amazon SageMaker JumpStart で SSD MobileNet v1 を用いた Fine-Tune による物体検出モデルの開発と推論を行うコンテンツです。  

[SageMaker Studio](https://aws.amazon.com/jp/sagemaker/studio/)を[セットアップ](https://catalog.us-east-1.prod.workshops.aws/v2/workshops/63069e26-921c-4ce1-9cc7-dd882ff62575/ja-JP/prerequisites/option2)(12. 「Open Studio」をクリックし、…までを実行)の上、SageMaker Studio にこのリポジトリをcloneした上、[./takenoko_to_kinoko.ipynb](./takenoko_to_kinoko.ipynb) を開いてください。  

学習には ml.g4dn.xlarge という GPU インスタンスの使用を推奨しています。アカウントの初期状態だと使用できないので、[リンク](https://docs.aws.amazon.com/ja_jp/general/latest/gr/aws_service_limits.html)の  
> AWS サポートセンターのページを開き、必要に応じてサインインし、[Create case] を選択します。[Service Limit increase](サービス制限の緩和) を選択します。フォームに入力して送信します。  

から SageMaker Training Instance の ml.g4dn.xlarge を 1 台使えるように申請してください。
