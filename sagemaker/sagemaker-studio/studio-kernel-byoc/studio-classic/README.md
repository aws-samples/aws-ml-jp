# SageMaker Studio と SageMaker Training Jobs の環境統一
SageMaker Studio Notebooks で ML のトレーニングコードを開発し、SageMaker Training Jobs でトレーニングを行おうとしたとき、環境差異があると一回で回らない場合がある。  
Studio Notebooks も SageMaker Training Jobs もコンテナで動くため、同じコンテナを使えば環境差異をなくすことができる。  

ここでは python3.10-buster をベースイメージに、モジュールのインストールの例として `numpy` と、Studio で動かすための ipykernel の設定と、Training Jobs を動かすためのモジュール(`sagemaker-training`)をインストールしたコンテナイメージをビルドし、Studio と Training Jobs で使えるようにする方法を紹介する。

## 開始方法

SageMaker Notebooks(≠Studio) で、[1_ready.ipynb](1_ready.ipynb) を実行する。  
ただし SageMaker Notebooks には AmazonSageMakerFullAccess がアタッチされたロールが設定されていることを前提とする。  
SageMaker Notebooks 以外でも動かすことができるが、その際はロールなどの設定を適宜修正する必要がある。  
[1_ready.ipynb](1_ready.ipynb) では docker コマンドを利用するため、SageMaker Studio の環境からでは利用できない。  
[1_ready.ipynb](1_ready.ipynb) が完了したら [2_studio.ipynb](2_studio.ipynb) を SageMaker Studio で開く。
