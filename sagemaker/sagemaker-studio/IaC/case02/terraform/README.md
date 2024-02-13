## Terraform版　実行手順

### git clone & cd
```
git clone https://github.com/aws-samples/aws-ml-jp.git
cd aws-ml-jp/sagemaker/sagemaker-studio/IaC/case02/terraform
```

### 鍵保管用のディレクトリ作成
```
mkdir ./cert
```

### gpgインストール
```
brew install gpg
```
### 鍵生成
```
gpg --gen-key
```
※本名には"terraform"と入力してください。メールアドレスは適当で良いです。

### 鍵のエクスポート
```
gpg -o ./cert/terraform.public.gpg  --export terraform
gpg -o ./cert/terraform.private.gpg --export-secret-key terraform
```

### Terrafrorm インストール
```
brew install terraform
```

### Terraform実行準備
```
cd examples
terraform init
```

### Lambda 関数の zip アーカイブ
```
zip rotate.py.zip rotate.py
```

### Terraform実行
```
terraform apply -var='project_name=<任意のプロジェクト名>' -auto-approve
```

### 暗号化されたパスワードの複合化
```
export GPG_TTY=$(tty) 
echo <出力された対象ユーザーの暗号化パスワード> | base64 -d | gpg -r terraform
```
