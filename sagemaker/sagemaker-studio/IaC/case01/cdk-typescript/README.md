# 開発用メモ

## TypeScript版

### 最初のデプロイまで
```
$ cd sagemaker-studio-ts
$ npm install
$ cdk bootstrap
$ cdk deploy
```

### Commit 前にコードフォーマットをかけるやつ
```
$ npm run format
```

### 仮パスワードの取得
CDK Deploy すると Outputs に SecretName が出てくるので控える
```
Outputs:
SagemakerStudioTsStack.KudoSecretName3DFC938D = KudoSecretE3E97241-yzycMG4fcQ4p
SagemakerStudioTsStack.TsugoSecretName7A5FCA12 = TsugoSecret31EAF625-0VcqdpwE8Q6F
Stack ARN:
arn:aws:cloudformation:ap-northeast-1:171368914135:stack/SagemakerStudioTsStack/ed1b9160-1466-11ed-b110-06d0805be2ab

✨  Total time: 31.54s
```

SecretNameを指定して仮パスワードを取得
```
$ aws secretsmanager get-secret-value --secret-id KudoSecretE3E97241-yzycMG4fcQ4p | jq -r .SecretString
```
