# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

認証付きTODOアプリ。パスワードログイン + 将来的にPasskey対応予定。

## 技術スタック

- **Backend**: Python + FastAPI（Mangum経由でLambda対応）
- **Frontend**: React + TypeScript + Vite
- **Database**: DynamoDB
- **Infrastructure**: AWS（Lambda, API Gateway, DynamoDB, ECR）

## DynamoDB テーブル設計

4テーブル構成。単一テーブル設計ではなく、テーブル分離方式。

| テーブル | PK | SK | 用途 |
|---------|----|----|------|
| users | `USER#{user_id}` | - | ユーザー情報（email, password_hash） |
| todos | `USER#{user_id}` | `TODO#{todo_id}` | TODO情報（title, completed） |
| webauthn_credentials | `USER#{user_id}` | `CRED#{credential_id}` | Passkey認証情報 |
| auth_challenges | `CHALLENGE#{challenge_id}` | - | 認証チャレンジ（TTLで自動削除） |

## 設計書

詳細な設計は [SPEC.md](./SPEC.md) を参照。API 仕様・テーブル設計・認証フロー・ディレクトリ構成・実装フェーズを記載。

## アプリ機能

- ユーザー登録 / パスワードログイン / ログアウト
- TODO CRUD（一覧・作成・完了切替・削除）
- Passkey認証（後日追加予定）

## 開発コマンド

```bash
make install          # 全依存関係インストール
make docker-up        # DynamoDB Local 起動
make backend-dev      # バックエンド起動 (localhost:8080)
make frontend-dev     # フロントエンド起動 (localhost:5173)
make backend-test     # バックエンドテスト
make lint             # 全リンター実行
make local            # DynamoDB起動 + 起動手順表示
```

## CI/CD

- **CI**: GitHub Actions（`.github/workflows/ci.yml`）— push/PR で backend, frontend, terraform を検査
- **CD**: AWS CodePipeline + CodeBuild（`buildspec.yml`）— main push で Docker ビルド → ECR push → Lambda 更新
- **Terraform モジュール**: `infrastructure/modules/cicd/` — CodeStar Connection, CodeBuild, CodePipeline, IAM
- CodeStar Connection は `terraform apply` 後に AWS コンソールで手動承認が必要
