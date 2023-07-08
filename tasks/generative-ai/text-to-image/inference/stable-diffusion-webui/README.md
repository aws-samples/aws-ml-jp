# Stable Diffusion Web UI on AWS

これは、EC2 インスタンス上で [AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui) の最新バージョンを起動するためのサンプルの CloudFormation テンプレートです。いくつかのバリエーションでは、モデルのトレーニングに [bmaltais/kohya_ss](https://github.com/bmaltais/kohya_ss)、GUI ベースのファイル操作に [filebrowser/filebrowser](https://github.com/filebrowser/filebrowser) が含まれています。

次の4つの CloudFormation テンプレートがあります:

| Launch Stack | Cfn Template | Description |
| ------------ | ------------ | ----------- |
| [![](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://us-east-1.console.aws.amazon.com/cloudformation/home#/stacks/create/review?stackName=sd-webui&templateURL=https://aws-ml-jp.s3.ap-northeast-1.amazonaws.com/tasks/generative-ai/text-to-image/stable-diffusion-webui/sd-webui.yaml) | [sd-webui.yaml](sd-webui.yaml) | パブリックにアクセス可能 (一部の機能はセキュリティ上の理由から無効化されています) |
| [![](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://us-east-1.console.aws.amazon.com/cloudformation/home#/stacks/create/review?stackName=sd-webui&templateURL=https://aws-ml-jp.s3.ap-northeast-1.amazonaws.com/tasks/generative-ai/text-to-image/stable-diffusion-webui/sd-webui-private.yaml) | [sd-webui-private.yaml](sd-webui-private.yaml) | SSM セッションマネージャーポートフォワーディングを介してプライベートにアクセス可能。[filebrowser/filebrowser](https://github.com/filebrowser/filebrowser) を使用してファイルにアクセスできます。|
| [![](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://us-east-1.console.aws.amazon.com/cloudformation/home#/stacks/create/review?stackName=sd-webui&templateURL=https://aws-ml-jp.s3.ap-northeast-1.amazonaws.com/tasks/generative-ai/text-to-image/stable-diffusion-webui/sd-webui-kohya-private.yaml) | [sd-webui-kohya-private.yaml](sd-webui-kohya-private.yaml) | [bmaltais/kohya_ss](https://github.com/bmaltais/kohya_ss) がインストールされた状態で、SSM セッションマネージャーポートフォワーディングを介してプライベートにアクセス可能。[filebrowser/filebrowser](https://github.com/filebrowser/filebrowser) を使用してファイルにアクセスできます。 |
| [![](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://us-east-1.console.aws.amazon.com/cloudformation/home#/stacks/create/review?stackName=sd-webui&templateURL=https://aws-ml-jp.s3.ap-northeast-1.amazonaws.com/tasks/generative-ai/text-to-image/stable-diffusion-webui/sd-webui-kohya-private-s3.yaml) | [sd-webui-kohya-private-s3.yaml](sd-webui-kohya-private-s3.yaml) | [bmaltais/kohya_ss](https://github.com/bmaltais/kohya_ss) がインストールされた状態で、SSM セッションマネージャーポートフォワーディングを介してプライベートにアクセス可能。ファイルをクラウド上に保持するために S3 がマウントされます。[filebrowser/filebrowser](https://github.com/filebrowser/filebrowser) を使用してファイルにアクセスできます。 |

※ [Cloud Formation](https://aws.amazon.com/jp/cloudformation/) とは、アプリケーションに関連する様々な AWS のリソースを一度に構築できる仕組みです。AWSで環境を構築した際、リソースの消し忘れで課金がされてしまったことはないでしょうか? Cloud Formation を使用すると必要なリソースをまとめて作成しまとめて消すことができます。

本ページの Cloud Formation は、基本的に EC2 インスタンスを立ててそこにアプリケーションを配置し、外部からアクセスできるようにします。 EC2インスタンスを立てる場所を決めるために、 VPC とサブネットの指定が必要です。作成方法やそもそも意味がわからない方は、 [[初心者向け]VPC作成からEC2インスタンス起動までを構成図見ながらやってみる（その1）](https://dev.classmethod.jp/articles/creation_vpc_ec2_for_beginner_1/) の解説が丁寧であるため参照してください。

EC2 インスタンスとして GPU が搭載された G 系のインスタンスを使用します。ただ、デフォルトでは立ち上げられる数が制限されており Cloud Formation の実行がエラーになることがあります。そのため、事前に [引き上げのリクエスト](https://docs.aws.amazon.com/ja_jp/AWSEC2/latest/UserGuide/ec2-resource-limits.html) を参照し制限を引き上げてください。設定値はインスタンスの数ではなく vCPU の数になっており、 `sd-webui` で使用する `g4dn.xlarge` の vCPU 数は 4 です。そのため最低4、さらに `2xlarge` を使用する場合は 8 と`xlarge` の前の数をかけて数を申請してください。なお、vCPUの数は次世代の `g5.xlarge` でも 4 です。申請の承認に数十分程度かかるので、[Running On-Demand G and VT instances](https://us-east-1.console.aws.amazon.com/servicequotas/home/services/ec2/quotas/L-DB2E81BA) からまず申請だけしておくのを推奨します。"On-Demand" とある通り、スポットインスタンスを使う場合の申請と別れています。

![](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png) のボタンを押すと、 Cloud Formation が実行できます。エラーになってしまった場合は、AWS コンソール上で Cloud Formation > Stacks と選択しエラーになったスタックを削除してください。削除した後、制限が足りないなどの原因を解消した後再度ボタンを押し実行してみてください。

起動ができた後の料金について記載しておきます。 [g4dn.xlarge](https://aws.amazon.com/jp/ec2/instance-types/g4/) の場合、0.526 USD / hour = 約75円/hour となります。最新の価格はリンク先の価格表で確認してください。なお、1日4時間までであれば無料で GPU インスタンスが利用できる [SageMaker Studio Lab でのStable Diffusion Web UI の実装](https://github.com/camenduru/stable-diffusion-webui-sagemaker) もあります。1日4時間以上利用する/安定的に運用するケースではこちらの CloudFormation Template をお使いください。

## はじめに

### パブリックエンドポイントとしてデプロイする

1. コンソールからテンプレートを起動するか、次のコマンドを使用します : `aws cloudformation create-stack --stack-name sd-webui-stack --template-body file://sd-webui.yaml --region us-east-1 --parameters ParameterKey=SubnetId,ParameterValue=<SubnetId> ParameterKey=VpcId,ParameterValue=<VpcId>`
2. アプリケーションの起動には 10 分程度かかります。
3. `<public ip address>:7860` を開きます。

### プライベートエンドポイントとしてデプロイする

前提条件:
- インストールされていない場合は、[ドキュメント ](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html) に従ってセッションマネージャープラグインをインストールします。

1. コンソールからテンプレートを起動するか、次のコマンドを使用します : `aws cloudformation create-stack --stack-name sd-webui-stack --template-body file://sd-webui-private.yaml --region us-east-1 --parameters ParameterKey=SubnetId,ParameterValue=<SubnetId>`
2. アプリケーションの起動には 10 分程度かかります。
3. `./port-forwarding.sh <instance_id> <region> 7860 8080` を使用してポートフォワーディングを実行します。
4. 安定した拡散 Web UI には `localhost:7860` を開きます。ファイルブラウザには `localhost:8080` を開きます。

SSM セッションマネージャーの詳細な制御については、[ドキュメント ](https://docs.aws.amazon.com/systems-manager/latest/userguide/getting-started-restrict-access-examples.html) を参照して、特定のユーザーの特定のインスタンスへのアクセスを制限してください。

### Kohya SS を使用したプライベートエンドポイントのデプロイ

1. コンソールからテンプレートを起動するか、次のコマンドを使用します : `aws cloudformation create-stack --stack-name sd-webui-stack --template-body file://sd-webui-kohya-private.yaml --region us-east-1 --parameters ParameterKey=SubnetId,ParameterValue=<SubnetId>`
2. `./port-forwarding.sh <instance_id> <region> 7860 7861 8080` を使用してポートフォワーディングを実行します。
3. Stable Diffusion Web UI には `localhost:7860` を開きます。Kohya-ss には `localhost:7861` を開きます。ファイルブラウザには `localhost:8080` を開きます。

### Kohya SS と S3 マウントを使用したプライベートエンドポイントのデプロイ

1. コンソールからテンプレートを起動するか、次のコマンドを使用します : `aws cloudformation create-stack --stack-name sd-webui-stack --template-body file://sd-webui-kohya-private-s3.yaml --region us-east-1 --parameters ParameterKey=EC2InstanceProfileName,ParameterValue=<InstanceProfile> ParameterKey=S3BucketName,ParameterValue=<Bucket> ParameterKey=SubnetId,ParameterValue=<SubnetId>`
2. `./port-forwarding.sh <instance_id> <region> 7860 7861 8080` を使用してポートフォワーディングを実行します。
3. Stable Diffusion Web UI には `localhost:7860` を開きます。Kohya-ss には `localhost:7861` を開きます。ファイルブラウザには `localhost:8080` を開きます。

### ファイル操作のための Filebrowser の使用

1. ポート 8080 にアクセスします。
2. デフォルトのユーザー名とパスワード `admin/admin` を入力します。
3. `/home/ubuntu` はデフォルトで `files` にマップされています（例 : `/files/s3` = `/home/ubuntu/s3`）。

### モデルの調整のための Kohya の使用

1. ポート 7861 にアクセスします。
2. Filebrowser を使用して画像をアップロードします。
3. ユーティリティタブから画像のための CLIP を生成します。
4. トレーニングを開始します。トレーニングログには `kohya-log.txt` をチェックしてください。
5. モデルファイルをダウンロードし、`~/stable-diffusion-webui/models/Lora` に移動して使用します。
6. 詳細な手順については、[bmaltais/kohya_ss](https://github.com/bmaltais/kohya_ss) を参照してください。

### インスタンスの停止

使用しない場合は、インスタンスを停止することができます。EC2 インスタンスが再起動すると、アプリケーションが自動的に起動されます。

以下のコマンドを使用してインスタンスを起動/停止できます。

- `aws ec2 stop-instances --region <region> --instance-ids <instance-id>`
- `aws ec2 start-instances --region <region> --instance-ids <instance-id>`

### Stable Diffusion Web UI への拡張機能の追加

拡張機能を追加するには、UI またはコマンドラインのいずれかを使用できます。

SSM セッションマネージャーを使用してコマンドラインで操作する場合:

1. サーバーにアクセスします : `aws ssm start-session --region <region> --target <instance_id>`
2. `ssm-user` は、SSM セッションマネージャーを使用する場合のデフォルトのユーザーです。例えば、`sudo su ubuntu` でユーザーを変更できます。
3. 手動で拡張機能をインストールします。

## トラブルシューティング

- サーバにアクセスできない
  - VPC Reachability Analyzerで到達可能性を確認する
  - ポート7860がブロックされている場合は、VPNをオフにしてください。
  - ログを見る
    - 1.コンソールから SSM Session Manager でインスタンスにログインするか、`aws ssm start-session --region <region> --target <instance_id>` コマンドを実行する。
    - 2. `tail /var/log/cloud-init-output.log` でユーザーデータの実行ログを見る。
    - 3. Stable Diffusion Web UI のログを `tail /home/ubuntu/sd-webui-log.txt` で表示する。
    - 4. Kohya SS のログを `tail /home/ubuntu/kohya-log.txt` で表示する。
- SSMセッションマネージャでサーバにアクセスできない
  - [SSMセッションマネージャ](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-getting-started.html)のガイドに従って、セッションマネージャを有効にしてください。
  - リージョンレベルの設定は [Fleet Manager](https://us-east-1.console.aws.amazon.com/systems-manager/managed-instances/dhmc-configuration?region=us-east-1)から選ぶと簡単です。
- UI から拡張機能をインストールできない (Error: AssertionError: extension access disabled because of command line flags）
  - [セキュリティ上の理由でパブリックエンドポイントを使用している場合、UIから拡張機能をインストールできません](https://github.com/AUTOMATIC1111/stable-diffusion-webui/issues/7153)。
- トレーニング時の CUDA out of memory。
  - Stable Diffusion Web UIを停止すると、GPUメモリが節約される場合があります。`nvidia-smi` でGPUメモリを消費しているpidを確認し、`kill -9 <pid>` で停止してください。
  - あるいは、より大きなインスタンスでcloudformationテンプレートを起動することもできます。
- kohya_ss の train / caption をクリックしても何も起こらない。
  - kohya_ssのUIフィードバックはありません。ログは `kohya-log.txt` を参照してください。ファイルブラウザからアクセスしてください。
- インスタンス起動時の容量不足
  - [AMI](https://aws.amazon.com/releasenotes/aws-deep-learning-ami-gpu-pytorch-2-0-ubuntu-20-04/)をサポートする別のインスタンスタイプか、別のリージョンを試してください。

## 含まれるソフトウェアのライセンスに関するお知らせ

このプロジェクトの CloudFormation テンプレートは、以下のソフトウェアを使用しています。

- [AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui): GNU Affero General Public License v3.0
- [bmaltais/kohya_ss](https://github.com/bmaltais/kohya_ss): Apache License 2.0
- [filebrowser/filebrowser](https://github.com/filebrowser/filebrowser): Apache License 2.0

お好みのモデルを選択することもできますが、stable-diffusion-webui はデフォルトで以下のモデルをダウンロードします。

- [runwayml/stable-diffusion-v1-5](https://huggingface.co/runwayml/stable-diffusion-v1-5): [creativeml-openrail-m License](https://huggingface.co/spaces/CompVis/stable-diffusion-license)
