# bedrock-beginners-handson

このリポジトリでは、Amazon Bedrock を初めて触る方向けに、Amazon Bedrock をお試しいただけるような Notebook コンテンツを提供します。
以下の 3 つのコンテンツを提供予定です。
なお、Amazon Bedrock を利用する際にはモデルの有効化手続きが必要になります。[Amazon Bedrock をセットアップする](https://docs.aws.amazon.com/ja_jp/bedrock/latest/userguide/setting-up.html)の手順をもとにセットアップをお願いします。

## Chapter1: 基盤モデルの基本的な呼び出し 
[![Jupyter Notebook](https://img.shields.io/badge/jupyter-%23FA0F00.svg?style=for-the-badge&logo=jupyter&logoColor=white)](bedrock/bedrock-beginners-handson/chapter1_introduction.ipynb)  
このチャプターでは、Python SDK を用いて Amazon Bedrock 上の基盤モデルを呼び出す方法をご紹介します。

## Chapter2: プロンプトエンジニアリング (作成中)
このチャプターでは実際に基盤モデルを使って、会社の宣伝メールやスローガンを生成するような仕組みを作ります。

## Chapter3: RAG 入門 (作成中)
このチャプターでは、検索拡張生成(Retrieval Augmented Generation) の仕組みや実装方法をご紹介します。

# 始めるにあたっての準備

このハンズオンでは SageMaker Notebook Instance での実行を前提とします。  
ノートブックインスタンスに対して、Bedrock の呼び出しを許可するため、次のような Bedrock Full Access 権限を実行ロールに付与してください。

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Statement1",
      "Effect": "Allow",
      "Action": "bedrock:*",
      "Resource": "*"
    }
  ]
}
```
