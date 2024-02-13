# Stable Studio on AWS

[Stable Studio](https://github.com/Stability-AI/StableStudio/tree/main) と [Stable Diffusion Web UI](https://github.com/AUTOMATIC1111/stable-diffusion-webui) をバックエンドとして AWS 上にデプロイするサンプルコードです。

次の 2 つの CloudFormation テンプレートがあります:

| Launch Stack | Cfn Template | Description |
| ------------ | ------------ | ----------- |
| [![](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://us-east-1.console.aws.amazon.com/cloudformation/home#/stacks/create/review?stackName=stable-studio&templateURL=https://aws-ml-jp.s3.ap-northeast-1.amazonaws.com/tasks/generative-ai/text-to-image/stable-studio/stable-studio-webui.yaml) | [stable-studio-webui.yaml](stable-studio-webui.yaml) | Stable Studio がインストールされたインスタンスを一つデプロイ（検証用途向け） |
| [![](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://us-east-1.console.aws.amazon.com/cloudformation/home#/stacks/create/review?stackName=stable-studio&templateURL=https://aws-ml-jp.s3.ap-northeast-1.amazonaws.com/tasks/generative-ai/text-to-image/stable-studio/stable-studio-webui-alb.yaml) | [stable-studio-webui-alb.yaml](stable-studio-webui-alb.yaml) | Stable Studio のバックエンドを ALB + ASG でデプロイ。カスタムドメインによる HTTPS 化に対応。静的サイト + バックエンド の本番むけ構成 |

* [g4dn.xlarge](https://aws.amazon.com/jp/ec2/instance-types/g4/) の場合、0.526 USD / hour となります。
* ALB + g4dn.xlarge 2 台の場合、1.07 USD / hour となります。

## インストール (シングルインスタンス)

1. Stable Studio を EC2 インスタンスにデプロイする
   1. [![](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://us-east-1.console.aws.amazon.com/cloudformation/home#/stacks/create/review?stackName=stable-studio&templateURL=https://aws-ml-jp.s3.ap-northeast-1.amazonaws.com/tasks/generative-ai/text-to-image/stable-studio/stable-studio-webui.yaml)
2. Stable Studio のセットアップを完了します (このステップは、アプリを使用するすべてのユーザーに必要です)
   1. ブラウザで `<public ip address>:3000` を開きます。
   2. 右上のアイコンをクリックして設定を開き、ホストURL に `http://<public ip address>:7861`
   3. 生成ページに戻り、`Advanced`を開き、オプションから`model`と`sampler`を設定する。
   4. `Dream` をクリックして画像が生成されることを確認します。


## インストール (静的サイト + バックエンド構成)

1. Amplify ホスティングを使用して Stable Studio を静的サイトとしてデプロイする
   1. [Stable Studio](https://github.com/Stability-AI/StableStudio) をフォークする。
   2. [Amplify Console](https://us-east-1.console.aws.amazon.com/amplify)を開きます。
   3. `New App` > `Host Web App` > `GitHub`を選択し、GitHubとの統合を完了する。
   4. フォークしたリポジトリを選択し、次へ進む。
   5. `Build Setting` を以下のように置き換えてデプロイする。
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
2. Stable Diffusion Web UI を使ってバックエンドをデプロイする。
   1. [![](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://us-east-1.console.aws.amazon.com/cloudformation/home#/stacks/create/review?stackName=stable-studio&templateURL=https://aws-ml-jp.s3.ap-northeast-1.amazonaws.com/tasks/generative-ai/text-to-image/stable-studio/stable-studio-webui-alb.yaml)
   2. パラメータ StableStudioURL に、デプロイした amplify アプリの URL を設定します。(例: `https://main.***.amplifyapp.com`) 
3. Stable Studio のセットアップを完了します (このステップは、アプリを使用するすべてのユーザーに必要です)
   1. ブラウザでStable Studioを開く (例 `https://main.***.amplifyapp.com`)
   2. 右上のアイコンをクリックして設定を開き、ホストURLをデプロイされた Stable Diffusion Web UI のエンドポイントに設定します。(i.e. `http://111.222.333.444:7861`)
   3. 生成ページに戻り、`Advanced`を開き、オプションから`model`と`sampler`を設定する。
   4. `Dream` をクリックして画像が生成されることを確認します。

## トラブルシューティング

- サーバにアクセスできない
  - VPC Reachability Analyzerで到達可能性を確認する
  - ポート 3000 や 7860 が VPN でブロックされている場合があります。その場合は、VPNをオフにしてください。
  - ログを見る
    - 1.コンソールから SSM Session Manager でインスタンスにログインするか、`aws ssm start-session --region <region> --target <instance_id>` コマンドを実行する。
    　　-　前提条件：[セッションマネージャープラグイン](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html)のインストール及びインスタンスの IAM Role への [SSM 権限](https://docs.aws.amazon.com/ja_jp/systems-manager/latest/userguide/getting-started-add-permissions-to-existing-profile.html)の付与（[デフォルトのホスト管理設定](https://docs.aws.amazon.com/ja_jp/systems-manager/latest/userguide/managed-instances-default-host-management.html)が設定されていれば不要）。
    - 2. `tail /var/log/cloud-init-output.log` でユーザーデータの実行ログを見る。
    - 3. Stable Diffusion Web UI のログを `tail /home/ubuntu/sd-webui-log.txt` で表示する。
- インスタンス起動時の容量不足
  - [AMI](https://aws.amazon.com/releasenotes/aws-deep-learning-ami-gpu-pytorch-2-0-ubuntu-20-04/)をサポートする別のインスタンスタイプか、別のリージョンを試してください。
- `Dream` をクリックしても画像が生成されない。
  - Stable Diffusion Web UI エンドポイントに直接アクセスして、API エンドポイントが動作していることを確認してください。
  - 設定ページで API Endpoint が正しく設定されているか確認する。
  - モデルやサンプラーが正しく設定されているか確認する。

## 含まれるソフトウェアのライセンスに関するお知らせ

このプロジェクトは、以下のソフトウェアを使用しています。

- [AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui): GNU Affero General Public License v3.0
- [Stability-AI/StableStudio](https://github.com/Stability-AI/StableStudio/tree/main): MIT License

お好みのモデルを選択することもできますが、stable-diffusion-webui はデフォルトで以下のモデルをダウンロードします。

- [runwayml/stable-diffusion-v1-5](https://huggingface.co/runwayml/stable-diffusion-v1-5): [creativeml-openrail-m License](https://huggingface.co/spaces/CompVis/stable-diffusion-license)
