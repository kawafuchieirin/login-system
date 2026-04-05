# パスキー（WebAuthn）実装解説

## 概要

W3C の WebAuthn 仕様に基づくパスキー認証を、パスワード認証に加えて実装。
ユーザーは Touch ID / Face ID / セキュリティキーなどでログインできる。

## アーキテクチャ

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────────┐     ┌──────────────┐
│  ブラウザ    │────▶│  CloudFront      │────▶│  Lambda (FastAPI)   │────▶│  DynamoDB    │
│             │     │                  │     │                     │     │              │
│ SimpleWebAuthn    │  /api/v1/passkey/ │     │  py_webauthn 2.7   │     │ credentials  │
│ Browser     │◀────│                  │◀────│                     │◀────│ challenges   │
└─────────────┘     └──────────────────┘     └─────────────────────┘     └──────────────┘
```

## 技術スタック

| レイヤー | ライブラリ | 役割 |
|---------|-----------|------|
| バックエンド | `webauthn` (py_webauthn 2.7.1) | チャレンジ生成、レスポンス検証、公開鍵管理 |
| フロントエンド | `@simplewebauthn/browser` | ブラウザ WebAuthn API のラッパー |
| データベース | DynamoDB | 認証情報（公開鍵）とチャレンジの保存 |

---

## DynamoDB テーブル設計

### webauthn_credentials テーブル

パスキーの公開鍵情報を保存。ユーザーは複数のパスキーを登録可能。

| 属性 | 型 | 説明 |
|------|-----|------|
| pk | `USER#{user_id}` | パーティションキー |
| sk | `CRED#{credential_id}` | ソートキー |
| credential_id | String | Base64URL エンコードされた Credential ID |
| public_key | String | Base64URL エンコードされた公開鍵 |
| sign_count | Number | 署名カウンター（リプレイ攻撃防止） |
| user_id | String | ユーザー ID |
| created_at | String (ISO 8601) | 作成日時 |

### auth_challenges テーブル

認証チャレンジを一時保存。TTL で 5 分後に自動削除。

| 属性 | 型 | 説明 |
|------|-----|------|
| pk | `CHALLENGE#{challenge_id}` | パーティションキー |
| user_id | String | ユーザー ID（または anonymous-{uuid}） |
| challenge | String | Base64URL エンコードされたチャレンジ値 |
| type | String | `register` または `authenticate` |
| expires_at | Number (Unix epoch) | TTL（5分後） |

---

## API エンドポイント

### パスキー登録（認証必須）

#### 1. `POST /api/v1/passkey/register/options`

登録オプション（チャレンジ）を生成。`py_webauthn.generate_registration_options()` を使用。

**処理フロー:**
1. JWT からユーザー ID を取得
2. 既存のパスキーを取得し `excludeCredentials` に設定（重複登録防止）
3. チャレンジを生成し DynamoDB に保存（TTL 5分）
4. `PublicKeyCredentialCreationOptions` を JSON で返却

**レスポンス例:**
```json
{
  "rp": { "name": "Login System", "id": "d3vkegfr7g7kls.cloudfront.net" },
  "user": { "id": "base64url...", "name": "user@example.com", "displayName": "user@example.com" },
  "challenge": "base64url...",
  "pubKeyCredParams": [{ "type": "public-key", "alg": -7 }, ...],
  "excludeCredentials": [],
  "authenticatorSelection": { "residentKey": "preferred", "userVerification": "preferred" }
}
```

#### 2. `POST /api/v1/passkey/register/verify`

ブラウザから返された Credential を検証し、公開鍵を保存。

**処理フロー:**
1. DynamoDB からチャレンジを取得・削除（ワンタイム使用）
2. `py_webauthn.verify_registration_response()` で検証
   - チャレンジ一致、RP ID 一致、Origin 一致を確認
3. 検証成功時、公開鍵と Credential ID を `webauthn_credentials` テーブルに保存

### パスキー認証（認証不要）

#### 3. `POST /api/v1/passkey/authenticate/options`

認証オプション（チャレンジ）を生成。

**処理フロー:**
1. email が指定された場合、該当ユーザーの Credential を `allowCredentials` に設定
2. email が未指定の場合、`allowCredentials` を空にして Discoverable Credential（Resident Key）を使用
3. チャレンジを DynamoDB に保存
4. `_challenge_user_id` をレスポンスに含めて返却（フロントエンドが verify 時に送り返す）

#### 4. `POST /api/v1/passkey/authenticate/verify`

ブラウザの署名を検証し、JWT を発行。

**処理フロー:**
1. `_challenge_user_id` からチャレンジを取得・削除
2. Credential ID から公開鍵を DynamoDB で検索
3. `py_webauthn.verify_authentication_response()` で署名検証
   - チャレンジ一致、RP ID 一致、Origin 一致、公開鍵で署名検証
4. 署名カウンターを更新（リプレイ攻撃防止）
5. 検証成功時、JWT を発行して返却

### パスキー管理（認証必須）

#### 5. `GET /api/v1/passkey/credentials` — 一覧取得
#### 6. `DELETE /api/v1/passkey/credentials/{credential_id}` — 削除

---

## フロントエンド実装

### パスキー登録（PasskeySettings コンポーネント）

TODO ページ下部に表示。ログイン済みユーザーがパスキーを追加・管理する。

```
パスキーを追加（ボタン）
  ↓
passkeyApi.getRegistrationOptions()     ← サーバーからオプション取得
  ↓
startRegistration({ optionsJSON })      ← ブラウザの WebAuthn API を呼び出し
  ↓                                       （Touch ID / Face ID ダイアログ表示）
passkeyApi.verifyRegistration(credential) ← サーバーで検証・保存
```

### パスキー認証（LoginPage）

ログインページに「パスキーでログイン」ボタンを追加。`browserSupportsWebAuthn()` で対応ブラウザのみ表示。

```
パスキーでログイン（ボタン）
  ↓
passkeyApi.getAuthenticationOptions(email?)  ← サーバーからオプション取得
  ↓
startAuthentication({ optionsJSON })         ← ブラウザの WebAuthn API を呼び出し
  ↓                                            （Touch ID / Face ID ダイアログ表示）
passkeyApi.verifyAuthentication(credential)  ← サーバーで署名検証
  ↓
JWT を受け取り localStorage に保存            ← ログイン完了
```

### チャレンジ ID の受け渡し

サーバーはチャレンジをユーザー ID に紐づけて DynamoDB に保存する。
認証フロー（未ログイン）ではユーザー特定が困難なため、`_challenge_user_id` をレスポンスに含めてフロントエンドに渡し、verify リクエスト時に送り返させることでチャレンジを特定する。

---

## セキュリティ設計

### チャレンジ管理
- **ワンタイム使用**: チャレンジは検証後に即削除（リプレイ攻撃防止）
- **TTL 5分**: DynamoDB の TTL で期限切れチャレンジを自動削除
- **有効期限チェック**: TTL 削除前でもアプリ側で `expires_at` を検証

### 署名カウンター
- 認証成功時に `sign_count` を更新
- 次回認証時に前回より大きいことを検証（クローンデバイス検出）

### RP ID / Origin 検証
- `WEBAUTHN_RP_ID`: CloudFront ドメイン（`d3vkegfr7g7kls.cloudfront.net`）
- `WEBAUTHN_ORIGIN`: `https://` 付きの完全な Origin URL
- 環境変数で管理し、本番 / ローカルで切り替え可能

### Discoverable Credential
- `residentKey: "preferred"` を設定し、対応デバイスではパスキーをデバイスに保存
- ログイン時に email 未入力でもパスキー認証が可能（ブラウザがアカウント選択 UI を表示）

---

## ファイル構成

```
backend/
├── routers/passkey.py              # API エンドポイント定義
├── services/passkey_service.py     # WebAuthn ビジネスロジック
├── models/passkey.py               # Pydantic リクエスト/レスポンスモデル
├── clients/dynamodb.py             # Settings に WebAuthn 設定追加
└── tests/test_passkey.py           # テスト（8ケース）

frontend/src/
├── services/api.ts                 # passkeyApi 追加
├── contexts/AuthContext.tsx        # loginWithPasskey() 追加
├── contexts/authContextValue.ts    # AuthContextType に loginWithPasskey 追加
├── components/PasskeySettings.tsx  # パスキー登録・一覧・削除 UI
├── pages/LoginPage.tsx             # 「パスキーでログイン」ボタン追加
├── pages/TodoPage.tsx              # PasskeySettings 組み込み
└── types/index.ts                  # PasskeyCredential 型追加

infrastructure/modules/dynamodb/
├── main.tf                         # webauthn_credentials, auth_challenges テーブル追加
└── outputs.tf                      # テーブル名・ARN の output 追加
```

---

## 環境変数

| 変数名 | 用途 | 例 |
|--------|------|-----|
| `WEBAUTHN_RP_ID` | Relying Party ID（ドメイン名） | `d3vkegfr7g7kls.cloudfront.net` |
| `WEBAUTHN_RP_NAME` | 表示名 | `Login System` |
| `WEBAUTHN_ORIGIN` | 許可する Origin | `https://d3vkegfr7g7kls.cloudfront.net` |
| `WEBAUTHN_CREDENTIALS_TABLE_NAME` | DynamoDB テーブル名 | `login-system-webauthn-credentials` |
| `AUTH_CHALLENGES_TABLE_NAME` | DynamoDB テーブル名 | `login-system-auth-challenges` |
