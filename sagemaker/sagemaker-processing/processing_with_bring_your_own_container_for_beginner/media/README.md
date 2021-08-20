# Amazon SageMaker Processing を独自コンテナで動かすハンズオン

## 概要
本ハンズオンは Amazon SageMaker Processing を独自コンテナで動かすハンズオンです。

Amazon SageMaker Processing には Scikit-learn や Apache Spark が利用可能な 組み込みコンテナを予め用意していますが、
組み込みコンテナだけでは不足する時のために、自身で Docker イメージを用意しして Amazon SageMaker Processing を動かすための仕組みも用意しており、
その独自の Docker イメージを準備して、動かすことが体験できるハンズオンです。

## 構成

このハンズオンは二段階の構成を取ってます。

1. [0_data_preparation.ipynb](./0_data_preparation.ipynb)
    このノートブックは SageMaker があまり関係ありませんが、[mnist のデータ](http://yann.lecun.com/exdb/mnist/)を画像化(png)し、zip 圧縮したものを Amazon S3 に保存する処理が入っています。次のノートブックを実行するためのデータ準備処理のみが記載されています。
2. [1_preprocess.ipynb](./1_preprocess.ipynb)
    Amazon SageMaker Processing を実際に動かすノートブックです。実行する処理は、先のノートブックで Amazon S3 に保存したデータを、zip 解凍し、輝度のヒストグラム平坦化の前処理を行ったあと、numpy ファイル( `.npyファイル`)に保存する処理を行います。これらの処理を行うために、画像を扱うために scikit-image をインストールした Docker イメージをビルドし、 Amazon Elastic Container Registry にプッシュし、 Amazon SageMaker Processing でビルドした Docker Image を用いた処理を行います。