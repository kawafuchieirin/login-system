# AWS デプロイ手順

## 前提条件

- AWS CLI がインストール・設定済み（`aws configure`）
- Terraform >= 1.0 がインストール済み
- Docker がインストール・起動済み
- Poetry がインストール済み

---

## 1. 初回セットアップ

### 1-1. Terraform 変数の設定

```bash
cd infrastructure
cp terraform.tfvars.example terraform.tfvars
```

`terraform.tfvars` を編集：

```hcl
project_name      = "login-system"
aws_region        = "ap-northeast-1"
jwt_secret_key    = "ランダムな文字列を設定"    # openssl rand -base64 32 で生成
github_repository = "kawafuchieirin/login-system"
```

### 1-2. インフラ構築（Terraform）

```bash
cd infrastructure
terraform init
terraform plan    # 変更内容を確認
terraform apply   # リソースを作成
```

作成されるリソース：
- DynamoDB テーブル（users, todos）
- ECR リポジトリ
- Lambda 関数
- API Gateway（HTTP API）
- CodePipeline + CodeBuild（CI/CD）
- CodeStar Connection（GitHub 接続）

### 1-3. CodeStar Connection の手動承認

`terraform apply` 後、GitHub 接続を承認する必要があります。

1. [AWS コンソール > Developer Tools > Settings > Connections](https://ap-northeast-1.console.aws.amazon.com/codesuite/settings/connections) を開く
2. `login-system-github` の接続をクリック
3. 「保留中」ステータスの接続で「接続を更新」をクリック
4. GitHub アカウントでの OAuth 認証を完了

---

## 2. バックエンドの手動デプロイ

初回、または CI/CD を使わず手動でデプロイする場合の手順です。

### 2-1. ECR リポジトリ URL の取得

```bash
# Terraform output から取得
cd infrastructure
ECR_URL=$(terraform output -raw ecr_repository_url)
echo $ECR_URL
```

### 2-2. ECR ログイン

```bash
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=ap-northeast-1

aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
```

### 2-3. Docker イメージのビルド・プッシュ

```bash
cd backend

# ビルド
docker build -t $ECR_URL:latest .

# プッシュ
docker push $ECR_URL:latest
```

### 2-4. Lambda 関数の更新

```bash
aws lambda update-function-code \
  --function-name login-system-api \
  --image-uri $ECR_URL:latest
```

### 2-5. デプロイ確認

```bash
# API エンドポイントを取得
cd infrastructure
API_URL=$(terraform output -raw api_endpoint)

# ヘルスチェック
curl $API_URL/health
# → {"status":"healthy"}
```

---

## 3. CI/CD による自動デプロイ

CodeStar Connection の承認が完了していれば、`main` ブランチへの push で自動デプロイされます。

### フロー

```
main に push
  → CodePipeline が起動
    → CodeBuild が実行
      → Docker build (backend/)
      → ECR push (:sha8 + :latest)
      → Lambda update-function-code
```

### パイプラインの確認

```bash
# CodePipeline の状態を確認
aws codepipeline get-pipeline-state --name login-system-pipeline \
  --query 'stageStates[*].{Stage:stageName,Status:latestExecution.status}' \
  --output table

# CodeBuild のログを確認
aws codebuild list-builds-for-project --project-name login-system-deploy \
  --query 'ids[0]' --output text | \
  xargs aws codebuild batch-get-builds --ids --query 'builds[0].logs.deepLink' --output text
```

---

## 4. インフラの更新

```bash
cd infrastructure
terraform plan    # 差分を確認
terraform apply   # 適用
```

> **注意**: Lambda の `image_uri` は `lifecycle { ignore_changes }` で管理外にしているため、`terraform apply` と CodeBuild の `update-function-code` は競合しません。

---

## 5. インフラの削除

```bash
cd infrastructure
terraform destroy
```

> **注意**: ECR リポジトリは `force_delete = true` のため、イメージごと削除されます。

---

## トラブルシューティング

### Lambda がタイムアウトする

- Lambda のタイムアウトは 30 秒に設定されています
- CloudWatch Logs でエラーを確認：
  ```bash
  aws logs tail /aws/lambda/login-system-api --follow
  ```

### CodePipeline が失敗する

- CodeStar Connection が「利用可能」状態か確認
- CodeBuild のログを確認：
  ```bash
  aws codebuild list-builds-for-project --project-name login-system-deploy --max-items 1
  ```

### ECR ログインが失敗する

- AWS CLI の認証情報が有効か確認：`aws sts get-caller-identity`
- Docker が起動しているか確認：`docker info`
