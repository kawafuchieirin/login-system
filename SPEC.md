# login-system 設計書

## システムアーキテクチャ

### AWS 構成

```
┌──────────┐     ┌─────────────┐     ┌─────────────────────┐     ┌──────────┐
│ ブラウザ  │────▶│ CloudFront  │────▶│   S3 (React SPA)    │     │          │
│          │     │             │     └─────────────────────┘     │ DynamoDB │
│          │────▶│ API Gateway │────▶│ Lambda (FastAPI+Mangum) │──▶│          │
└──────────┘     └─────────────┘     └─────────────────────────┘  └──────────┘
                                              │
                                         ┌────┴────┐
                                         │   ECR   │
                                         └─────────┘
```

### ローカル開発構成

```
┌──────────────┐     ┌────────────────────────┐     ┌─────────────────┐
│ ブラウザ     │────▶│ Vite Dev Server (:5173) │     │ DynamoDB Local  │
│              │     └────────────────────────┘     │  (Docker :8000) │
│              │────▶│ uvicorn (:8000)         │────▶│                 │
└──────────────┘     └─────────────────────────┘    │ DynamoDB Admin  │
                                                     │  (Docker :8001) │
                                                     └─────────────────┘
```

- Docker Compose で DynamoDB Local + Admin UI を起動
- バックエンドは `uvicorn` で直接起動（ホットリロード対応）
- フロントエンドは Vite dev server で起動

---

## API エンドポイント設計

### 認証 API

#### `POST /api/v1/auth/register` — ユーザー登録

認証不要

```json
// Request
{
  "email": "user@example.com",
  "password": "securepassword123"
}

// Response 201
{
  "user_id": "uuid",
  "email": "user@example.com",
  "created_at": "2026-04-05T00:00:00Z"
}

// Error 409
{
  "detail": "Email already registered"
}
```

#### `POST /api/v1/auth/login` — ログイン

認証不要

```json
// Request
{
  "email": "user@example.com",
  "password": "securepassword123"
}

// Response 200
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}

// Error 401
{
  "detail": "Invalid email or password"
}
```

#### `POST /api/v1/auth/logout` — ログアウト

認証必要（`Authorization: Bearer <token>`）

```json
// Response 200
{
  "message": "Successfully logged out"
}
```

#### `GET /api/v1/auth/me` — 現在のユーザー情報取得

認証必要

```json
// Response 200
{
  "user_id": "uuid",
  "email": "user@example.com",
  "created_at": "2026-04-05T00:00:00Z"
}
```

### TODO API

#### `GET /api/v1/todos` — TODO 一覧取得

認証必要

```json
// Response 200
{
  "todos": [
    {
      "todo_id": "uuid",
      "title": "買い物に行く",
      "completed": false,
      "created_at": "2026-04-05T00:00:00Z"
    }
  ]
}
```

#### `POST /api/v1/todos` — TODO 作成

認証必要

```json
// Request
{
  "title": "買い物に行く"
}

// Response 201
{
  "todo_id": "uuid",
  "title": "買い物に行く",
  "completed": false,
  "created_at": "2026-04-05T00:00:00Z"
}
```

#### `PATCH /api/v1/todos/{todo_id}` — TODO 更新

認証必要

```json
// Request
{
  "title": "スーパーで買い物",    // optional
  "completed": true              // optional
}

// Response 200
{
  "todo_id": "uuid",
  "title": "スーパーで買い物",
  "completed": true,
  "created_at": "2026-04-05T00:00:00Z"
}

// Error 404
{
  "detail": "Todo not found"
}
```

#### `DELETE /api/v1/todos/{todo_id}` — TODO 削除

認証必要

```json
// Response 204 (No Content)

// Error 404
{
  "detail": "Todo not found"
}
```

### ヘルスチェック

#### `GET /health` — ヘルスチェック

認証不要

```json
// Response 200
{
  "status": "healthy"
}
```

---

## DynamoDB テーブル設計

### Phase 1: パスワード認証 + TODO

#### users テーブル

| 属性 | 型 | 説明 |
|------|-----|------|
| PK | `USER#{user_id}` | パーティションキー |
| email | String | メールアドレス（一意） |
| password_hash | String | bcrypt ハッシュ |
| created_at | String (ISO 8601) | 作成日時 |

**GSI: `email-index`**
- パーティションキー: `email`
- 用途: ログイン時のメールアドレス検索

#### todos テーブル

| 属性 | 型 | 説明 |
|------|-----|------|
| PK | `USER#{user_id}` | パーティションキー |
| SK | `TODO#{todo_id}` | ソートキー |
| title | String | TODO タイトル |
| completed | Boolean | 完了フラグ |
| created_at | String (ISO 8601) | 作成日時 |

### Phase 2: Passkey 対応（将来）

#### webauthn_credentials テーブル

| 属性 | 型 | 説明 |
|------|-----|------|
| PK | `USER#{user_id}` | パーティションキー |
| SK | `CRED#{credential_id}` | ソートキー |
| credential_id | String | WebAuthn Credential ID |
| public_key | Binary | 公開鍵 |
| sign_count | Number | 署名カウンター |
| created_at | String (ISO 8601) | 作成日時 |

#### auth_challenges テーブル

| 属性 | 型 | 説明 |
|------|-----|------|
| PK | `CHALLENGE#{challenge_id}` | パーティションキー |
| user_id | String | ユーザーID |
| challenge | String | チャレンジ値 |
| type | String | `register` / `authenticate` |
| expires_at | Number (Unix epoch) | TTL による自動削除 |

---

## 認証フロー

### パスワード認証

```
[登録]
  Client → POST /auth/register (email, password)
  Server → bcrypt でパスワードハッシュ化 → DynamoDB に保存
  Server → 201 (user_id, email)

[ログイン]
  Client → POST /auth/login (email, password)
  Server → email-index で検索 → bcrypt.verify でパスワード検証
  Server → JWT (HS256) を発行 → 200 (access_token)

[認証済みリクエスト]
  Client → Authorization: Bearer <token>
  Server → FastAPI Depends(get_current_user) で JWT を検証
  Server → user_id を抽出してリクエスト処理
```

### JWT 設定

| 項目 | 値 |
|------|-----|
| アルゴリズム | HS256 |
| 有効期限 | 24時間 |
| シークレットキー | 環境変数 `JWT_SECRET_KEY` |
| ペイロード | `{ "sub": user_id, "exp": expiration }` |

### セキュリティ要件

- パスワードは bcrypt でハッシュ化して保存（平文保存禁止）
- JWT シークレットキーは環境変数で管理（ハードコード禁止）
- パスワードは最低8文字
- メールアドレスの重複チェック

---

## フロントエンド設計

### ルーティング

| パス | コンポーネント | 認証 | 説明 |
|------|--------------|------|------|
| `/login` | LoginPage | 不要 | ログイン画面 |
| `/register` | RegisterPage | 不要 | ユーザー登録画面 |
| `/` | TodoPage | 必要 | TODO 一覧（メイン画面） |

### 状態管理

- **AuthContext**: 認証状態（token, user）をアプリ全体で共有
- **useAuth**: ログイン / 登録 / ログアウト操作
- **useTodos**: TODO CRUD 操作
- **ProtectedRoute**: 未認証ユーザーを `/login` にリダイレクト

### API クライアント

- axios インスタンスに `Authorization` ヘッダーを自動付与
- 401 レスポンス時に自動ログアウト（interceptor）

---

## ディレクトリ構成

```
login-system/
├── CLAUDE.md
├── SPEC.md
├── README.md
├── Makefile
├── docker-compose.yml
├── .gitignore
│
├── backend/
│   ├── pyproject.toml          # Poetry 設定（依存・ruff・mypy）
│   ├── main.py                 # FastAPI アプリ + Mangum handler
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py             # 認証エンドポイント
│   │   └── todos.py            # TODO エンドポイント
│   ├── models/
│   │   ├── __init__.py
│   │   ├── auth.py             # AuthRequest, AuthResponse, Token
│   │   └── todo.py             # TodoCreate, TodoUpdate, TodoResponse
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py     # JWT 発行・検証, パスワードハッシュ
│   │   └── todo_service.py     # TODO CRUD ロジック
│   ├── clients/
│   │   ├── __init__.py
│   │   └── dynamodb.py         # DynamoDB クライアント + Settings
│   ├── dependencies.py         # get_current_user 等の共通依存
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py         # pytest fixtures (moto mock)
│       ├── test_auth.py
│       └── test_todos.py
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── index.html
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── RegisterPage.tsx
│   │   │   └── TodoPage.tsx
│   │   ├── components/
│   │   │   ├── ProtectedRoute.tsx
│   │   │   ├── TodoItem.tsx
│   │   │   └── TodoForm.tsx
│   │   ├── contexts/
│   │   │   └── AuthContext.tsx
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   └── useTodos.ts
│   │   ├── services/
│   │   │   └── api.ts          # axios インスタンス + API 関数
│   │   └── types/
│   │       └── index.ts        # 型定義
│   └── tests/
│       └── e2e/
│           └── todo.spec.ts    # Playwright E2E テスト
│
└── infrastructure/
    ├── main.tf
    ├── variables.tf
    ├── outputs.tf
    ├── terraform.tfvars.example
    └── modules/
        ├── dynamodb/
        │   ├── main.tf
        │   ├── variables.tf
        │   └── outputs.tf
        ├── lambda/
        │   ├── main.tf
        │   ├── variables.tf
        │   └── outputs.tf
        ├── api-gateway/
        │   ├── main.tf
        │   ├── variables.tf
        │   └── outputs.tf
        └── ecr/
            ├── main.tf
            ├── variables.tf
            └── outputs.tf
```

### personal-growth-tracker との構成比較

| 項目 | personal-growth-tracker | login-system |
|------|------------------------|-------------|
| API 構成 | マイクロサービス（4 API） | 単一 FastAPI アプリ |
| ルーター | `api_handler.py` | `routers/auth.py`, `routers/todos.py` |
| DynamoDB | `client.py` + Settings | `clients/dynamodb.py` + Settings |
| Lambda | API ごとに Mangum | 単一 `main.py` で Mangum |
| Docker Compose | DynamoDB Local + Admin | 同様の構成 |

---

## 主要依存パッケージ

### Backend (Python)

| パッケージ | 用途 |
|-----------|------|
| fastapi | Web フレームワーク |
| mangum | Lambda アダプター |
| uvicorn | ASGI サーバー（ローカル開発） |
| boto3 | AWS SDK (DynamoDB) |
| python-jose[cryptography] | JWT 生成・検証 |
| passlib[bcrypt] | パスワードハッシュ |
| pydantic-settings | 設定管理 |
| ruff | リンター + フォーマッター |
| mypy | 型チェック |
| pytest | テスト |
| moto | AWS モック（テスト用） |
| httpx | TestClient 用 |

### Frontend (TypeScript)

| パッケージ | 用途 |
|-----------|------|
| react | UI ライブラリ |
| react-dom | DOM レンダリング |
| react-router-dom | ルーティング |
| axios | HTTP クライアント |
| vite | ビルドツール |
| typescript | 型チェック |
| vitest | ユニットテスト |
| @playwright/test | E2E テスト |
| eslint | リンター |
| prettier | フォーマッター |

---

## 環境変数

| 変数名 | 用途 | デフォルト値 |
|--------|------|-------------|
| `JWT_SECRET_KEY` | JWT 署名キー | （必須、デフォルトなし） |
| `DYNAMODB_ENDPOINT_URL` | DynamoDB エンドポイント | `http://localhost:8000`（ローカル） |
| `USERS_TABLE_NAME` | users テーブル名 | `login-system-users` |
| `TODOS_TABLE_NAME` | todos テーブル名 | `login-system-todos` |
| `CORS_ORIGINS` | 許可オリジン | `http://localhost:5173` |
| `DEBUG` | デバッグモード | `false` |

---

## CI/CD

### パイプライン構成

```
[GitHub push/PR]
  │
  ├─ GitHub Actions (CI) ─── .github/workflows/ci.yml
  │    ├─ Backend:  ruff lint/format + mypy + pytest
  │    ├─ Frontend: eslint + tsc --noEmit + vite build
  │    └─ Terraform: fmt -check + init -backend=false + validate
  │
  └─ AWS CodePipeline (CD) ─── main push のみ
       ├─ Source: CodeStar Connection (GitHub v2)
       └─ Build:  CodeBuild (buildspec.yml)
            ├─ Docker build (backend/)
            ├─ ECR push (:sha8 + :latest)
            └─ Lambda update-function-code
```

### CI ジョブ一覧（GitHub Actions）

| ジョブ | トリガー | 内容 |
|--------|---------|------|
| changes | push(main) / PR(main) | `dorny/paths-filter` で変更検知 |
| backend | backend/** 変更時 | ruff check, ruff format --check, mypy, pytest |
| frontend | frontend/** 変更時 | eslint, tsc --noEmit, vite build |
| terraform | infrastructure/** 変更時 | terraform fmt -check, init, validate |

### CD 構成（AWS CodePipeline + CodeBuild）

| リソース | 説明 |
|---------|------|
| CodeStar Connection | GitHub v2 接続（apply 後に AWS コンソールで手動承認が必要） |
| S3 バケット | CodePipeline アーティファクト保管 |
| CodeBuild プロジェクト | Docker ビルド + ECR push + Lambda 更新 |
| CodePipeline | Source → Build の 2 ステージ |

### 注意事項

- Lambda の `lifecycle { ignore_changes = [image_uri] }` により、CodeBuild の `update-function-code` と terraform apply は競合しない
- CodeStar Connection は `terraform apply` 後に **AWS コンソールで手動承認**（GitHub OAuth）が必要
- フロントエンドの CD（S3 + CloudFront）はスコープ外（インフラモジュール未構築のため）

---

## 実装フェーズ

### Phase 1: プロジェクト骨格

- [ ] `pyproject.toml`（Poetry + ruff + mypy 設定）
- [ ] `package.json`（React + Vite 設定）
- [ ] `Makefile`（開発コマンド統一）
- [ ] `docker-compose.yml`（DynamoDB Local + Admin）
- [ ] `.gitignore`
- [ ] `pre-commit` 設定

### Phase 2: バックエンド認証

- [ ] FastAPI アプリ骨格（`main.py`）
- [ ] DynamoDB クライアント（`clients/dynamodb.py`）
- [ ] 認証サービス（`services/auth_service.py`）
- [ ] 認証ルーター（`routers/auth.py`）
- [ ] JWT 依存関係（`dependencies.py`）
- [ ] テスト（`tests/test_auth.py`）

### Phase 3: バックエンド TODO CRUD

- [ ] TODO サービス（`services/todo_service.py`）
- [ ] TODO ルーター（`routers/todos.py`）
- [ ] テスト（`tests/test_todos.py`）

### Phase 4: フロントエンド

- [ ] Vite + React プロジェクト初期化
- [ ] AuthContext + useAuth
- [ ] LoginPage / RegisterPage
- [ ] ProtectedRoute
- [ ] TodoPage + useTodos
- [ ] E2E テスト

### Phase 5: インフラ（Terraform）

- [ ] DynamoDB モジュール（users, todos テーブル + GSI）
- [ ] ECR モジュール
- [ ] Lambda モジュール
- [ ] API Gateway モジュール
- [ ] CloudFront + S3（フロントエンド配信）
