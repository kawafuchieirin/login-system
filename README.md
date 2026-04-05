# login-system


## この構成での最終像
アプリ機能
ユーザー登録
パスワードログイン
ログアウト
自分の TODO 一覧
TODO 作成
TODO 完了切替
TODO 削除
後で Passkey を追加
AWS 構成
API Gateway が公開エンドポイント
Lambda が FastAPI を実行
DynamoDB がデータ保存
ECR がコンテナ保存
DynamoDB のテーブル設計

学習用なら、まずは 3テーブル がわかりやすいです。

1. users

ユーザー情報

pk: USER#{user_id}
email
password_hash
created_at
2. todos

TODO 情報

pk: USER#{user_id}
sk: TODO#{todo_id}
title
completed
created_at

この形にすると、1ユーザーの TODO 一覧取得がやりやすいです。DynamoDB では主キーでアイテムを識別します。

3. webauthn_credentials

Passkey 用

pk: USER#{user_id}
sk: CRED#{credential_id}
credential_id
public_key
sign_count
created_at
challenge の保存先

Passkey を後で追加するので、challenge 保存用テーブルも用意しておくと安全です。

4. auth_challenges
pk: CHALLENGE#{challenge_id}
user_id
challenge
type (register / authenticate)
expires_at

DynamoDB は TTL を使って期限切れアイテムを自動削除できます。TTL の削除は有効期限ちょうどではなく、通常「数日以内」に非同期で行われます。
