.PHONY: help install dev test lint format clean
.PHONY: backend-install backend-dev backend-test backend-lint backend-format
.PHONY: frontend-install frontend-dev frontend-test frontend-lint frontend-format frontend-build
.PHONY: infra-init infra-plan infra-apply infra-destroy
.PHONY: docker-up docker-down local e2e

# Variables
PROJECT_NAME := login-system
AWS_REGION := ap-northeast-1

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-25s\033[0m %s\n", $$1, $$2}'

# =====================
# Full Project Commands
# =====================

install: backend-install frontend-install ## Install all dependencies

dev: ## Run all development servers (requires multiple terminals)
	@echo "Run the following commands in separate terminals:"
	@echo "  make backend-dev"
	@echo "  make frontend-dev"

test: backend-test frontend-test ## Run all tests

lint: backend-lint frontend-lint ## Run all linters

format: backend-format frontend-format ## Format all code

clean: backend-clean frontend-clean ## Clean all build artifacts

# =====================
# Backend Commands
# =====================

backend-install: ## Install backend dependencies
	cd backend && poetry install

backend-dev: ## Run backend development server
	cd backend && DYNAMODB_ENDPOINT_URL=http://localhost:8000 \
		USERS_TABLE_NAME=login-system-users \
		TODOS_TABLE_NAME=login-system-todos \
		JWT_SECRET_KEY=dev-secret-key-change-in-production \
		CORS_ORIGINS=http://localhost:5173 \
		DEBUG=true \
		poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8080

backend-test: ## Run backend tests
	cd backend && poetry run pytest tests/ -v

backend-lint: ## Run backend linter
	cd backend && poetry run ruff check .
	cd backend && poetry run mypy . --ignore-missing-imports

backend-format: ## Format backend code
	cd backend && poetry run ruff check . --fix
	cd backend && poetry run ruff format .

backend-clean: ## Clean backend build artifacts
	cd backend && rm -rf .pytest_cache .mypy_cache .ruff_cache __pycache__ .coverage htmlcov
	find backend -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# =====================
# Frontend Commands
# =====================

frontend-install: ## Install frontend dependencies
	cd frontend && npm install

frontend-dev: ## Run frontend development server
	cd frontend && npm run dev

frontend-test: ## Run frontend tests
	cd frontend && npm run test -- --run

frontend-lint: ## Run frontend linter
	cd frontend && npm run lint

frontend-format: ## Format frontend code
	cd frontend && npm run format

frontend-build: ## Build frontend for production
	cd frontend && npm run build

frontend-clean: ## Clean frontend build artifacts
	cd frontend && rm -rf dist node_modules/.cache

# =====================
# E2E Test Commands
# =====================

e2e: ## Run E2E tests
	cd frontend && npx playwright test

# =====================
# Docker Commands
# =====================

docker-up: ## Start DynamoDB Local with Docker Compose
	docker compose up -d

docker-down: ## Stop all services
	docker compose down

local: docker-up ## Start local stack
	@echo ""
	@echo "DynamoDB Local を起動しました。以下のコマンドを別ターミナルで実行してください:"
	@echo ""
	@echo "  make backend-dev"
	@echo "  make frontend-dev"
	@echo ""
	@echo "Backend  → http://localhost:8080"
	@echo "Frontend → http://localhost:5173"
	@echo "DynamoDB Admin → http://localhost:8001"
	@echo ""

docker-clean: ## Remove all Docker containers and volumes
	docker compose down -v --rmi local 2>/dev/null || true

# =====================
# Infrastructure Commands
# =====================

infra-init: ## Initialize Terraform
	cd infrastructure && terraform init

infra-plan: ## Plan Terraform changes
	cd infrastructure && terraform plan

infra-apply: ## Apply Terraform changes
	cd infrastructure && terraform apply

infra-destroy: ## Destroy Terraform resources
	cd infrastructure && terraform destroy

infra-fmt: ## Format Terraform files
	cd infrastructure && terraform fmt -recursive

# =====================
# Deploy Commands
# =====================

ECR_URL := $(shell cd infrastructure && terraform output -raw ecr_repository_url 2>/dev/null)

deploy-image: ## Build and push Docker image to ECR
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(ECR_URL)
	cd backend && docker build --platform linux/amd64 -t $(ECR_URL):latest .
	docker push $(ECR_URL):latest

deploy-lambda: deploy-image ## Deploy backend to Lambda (build + push + update)
	aws lambda update-function-code --function-name $(PROJECT_NAME)-api --image-uri $(ECR_URL):latest

deploy-frontend: ## Build and deploy frontend to S3 + CloudFront
	cd frontend && VITE_API_URL="" npm run build
	aws s3 sync frontend/dist/ s3://$$(cd infrastructure && terraform output -raw frontend_bucket)/ --delete
	aws cloudfront create-invalidation --distribution-id $$(cd infrastructure && terraform output -raw cloudfront_distribution_id) --paths "/*"

deploy-first: ## First-time deploy: push image then terraform apply
	@echo "=== Step 1: Terraform apply (ECR + DynamoDB のみ、Lambda はエラーになる場合あり) ==="
	cd infrastructure && terraform apply -target=module.ecr -target=module.dynamodb -auto-approve
	@echo ""
	@echo "=== Step 2: Docker イメージを ECR に push ==="
	$(MAKE) deploy-image
	@echo ""
	@echo "=== Step 3: 全リソースを作成 ==="
	cd infrastructure && terraform apply

# =====================
# CI Commands
# =====================

ci: lint test ## Run CI checks locally
