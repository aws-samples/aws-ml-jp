# Stable Diffusion Web UI on AWS

これは、EC2 インスタンス上で [AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui) の最新バージョンを起動するためのサンプルの CloudFormation テンプレートです。いくつかのバリエーションでは、モデルのトレーニングに [bmaltais/kohya_ss](https://github.com/bmaltais/kohya_ss)、GUI ベースのファイル操作に [filebrowser/filebrowser](https://github.com/filebrowser/filebrowser) が含まれています。

次の4つの CloudFormation テンプレートがあります:

- [sd-webui.yaml](sd-webui.yaml): パブリックにアクセス可能 (一部の機能はセキュリティ上の理由から無効化されています)
- [sd-webui-private.yaml](sd-webui-private.yaml): SSM セッションマネージャーポートフォワーディングを介してプライベートにアクセス可能。[filebrowser/filebrowser](https://github.com/filebrowser/filebrowser) を使用してファイルにアクセスできます。
- [sd-webui-kohya-private.yaml](sd-webui-kohya-private.yaml): [bmaltais/kohya_ss](https://github.com/bmaltais/kohya_ss) がインストールされた状態で、SSM セッションマネージャーポートフォワーディングを介してプライベートにアクセス可能。[filebrowser/filebrowser](https://github.com/filebrowser/filebrowser) を使用してファイルにアクセスできます。
- [sd-webui-kohya-private-s3.yaml](sd-webui-kohya-private-s3.yaml): [bmaltais/kohya_ss](https://github.com/bmaltais/kohya_ss) がインストールされた状態で、SSM セッションマネージャーポートフォワーディングを介してプライベートにアクセス可能。ファイルをクラウド上に保持するために S3 がマウントされます。[filebrowser/filebrowser](https://github.com/filebrowser/filebrowser) を使用してファイルにアクセスできます。

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

- サーバーにアクセスできない
  - VPC リーチャビリティアナライザで到達性をチェックしてください
  - ポート 7860 がブロックされている場合は、VPN をオフにしてください。
  - ログを確認してください
    - 1. コンソールからまたは次のコマンドを使用して、スタックのイベントを確認します : `aws cloudformation describe-stack-events --region <region> --stack-name sd-webui-stack`
    - 2. EC2 インスタンス上のログを確認します : `sudo cat /var/log/cloud-init-output.log`
    - 3. `/home/ubuntu/stable-diffusion-webui` にある各ログファイルを確認します。
  - セキュリティグループとネットワーク ACL を確認してください。
- コンソールにアクセスできない
  - ポートフォワーディングが正しく設定されていることを確認してください。
  - ローカルマシンのファイアウォール設定を確認してください。
- ファイルブラウザにアクセスできない
  - ポート 8080 が開かれていることを確認してください。
  - Filebrowser のログを確認してください : `sudo cat /home/ubuntu/filebrowser/filebrowser.log`
  - ユーザー名とパスワードが正しいことを確認してください。
  - `/home/ubuntu/filebrowser/filebrowser.json` で設定を確認します。
- Kohya SS にアクセスできない
  - ポート 7861 が開かれていることを確認してください。
  - Kohya SS のログを確認してください : `sudo cat /home/ubuntu/kohya_ss/kohya_ss.log`
- Stable Diffusion Web UI から拡張機能をインストールできない（エラー : AssertionError: extension access disabled because of command line flags）
  - [ セキュリティ上の理由から、パブリックエンドポイントを使用している場合は、UI から拡張機能をインストールできません ](https://github.com/AUTOMATIC1111/stable-diffusion-webui/issues/7153)。
- トレーニング時に CUDA のメモリ不足が発生する
  - Stable Diffusion Web UI を停止すると、一部の GPU メモリが節約される場合があります。`nvidia-smi` で GPU メモリを消費しているプロセスの PID を確認し、`kill -9 <pid>` で停止させることができます。
  - または、より大きなインスタンスでクラウドフォーメーションテンプレートを起動することができます。
- Kohya-ss の「トレーニング」をクリックしても何も起こらない
  - Kohya-ss には UI のフィードバックがありません。ログは `kohya-log.txt` を確認してください。Filebrowser からアクセスするか、`tail` コマンドでログを表示できます。

## 含まれるソフトウェアのライセンスに関するお知らせ

このプロジェクトの CloudFormation テンプレートは、以下のソフトウェアを使用しています。

- [AUTOMATIC1111/stable-diffusion-webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui): GNU Affero General Public License v3.0
- [bmaltais/kohya_ss](https://github.com/bmaltais/kohya_ss): Apache License 2.0
- [filebrowser/filebrowser](https://github.com/filebrowser/filebrowser): Apache License 2.0

お好みのモデルを選択することもできますが、stable-diffusion-webui はデフォルトで以下のモデルをダウンロードします。

- [runwayml/stable-diffusion-v1-5](https://huggingface.co/runwayml/stable-diffusion-v1-5): [creativeml-openrail-m License](https://huggingface.co/spaces/CompVis/stable-diffusion-license)
