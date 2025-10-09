.PHONY: help build test run docker-build docker-run docker-compose-up docker-compose-down k8s-deploy k8s-delete clean lint

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
VENV := venv
DOCKER_IMAGE := finopsguard
DOCKER_TAG := latest
K8S_NAMESPACE := finopsguard

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development
venv: ## Create Python virtual environment
	$(PYTHON) -m venv $(VENV)
	@echo "Virtual environment created. Activate with: source $(VENV)/bin/activate"

install: ## Install Python dependencies
	pip install -r requirements.txt

install-dev: install ## Install development dependencies
	pip install pytest pytest-asyncio httpx black flake8 mypy

test: ## Run all tests
	PYTHONPATH=src pytest tests/ -v

test-unit: ## Run unit tests only
	PYTHONPATH=src pytest tests/unit/ -v

test-integration: ## Run integration tests only
	PYTHONPATH=src pytest tests/integration/ -v

test-coverage: ## Run tests with coverage report
	PYTHONPATH=src pytest tests/ --cov=finopsguard --cov-report=html --cov-report=term

lint: ## Run linters
	flake8 src/finopsguard tests/
	mypy src/finopsguard

format: ## Format code with black
	black src/finopsguard tests/

run: ## Run development server
	PYTHONPATH=src $(PYTHON) -m finopsguard.main

# Docker
docker-build: ## Build Docker image
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

docker-run: ## Run Docker container
	docker run --rm -p 8080:8080 $(DOCKER_IMAGE):$(DOCKER_TAG)

docker-push: ## Push Docker image to registry
	docker push $(DOCKER_IMAGE):$(DOCKER_TAG)

docker-shell: ## Open shell in Docker container
	docker run --rm -it $(DOCKER_IMAGE):$(DOCKER_TAG) /bin/bash

# Docker Compose
docker-compose-up: ## Start services with docker-compose
	docker-compose up -d

docker-compose-up-database: ## Start services with database
	docker-compose --profile database up -d

docker-compose-up-monitoring: ## Start services with monitoring
	docker-compose --profile monitoring up -d

docker-compose-up-all: ## Start all services (database, caching, monitoring)
	docker-compose --profile database --profile caching --profile monitoring up -d

docker-compose-down: ## Stop docker-compose services
	docker-compose down

docker-compose-down-all: ## Stop all services including volumes
	docker-compose --profile database --profile caching --profile monitoring down -v

docker-compose-logs: ## View docker-compose logs
	docker-compose logs -f finopsguard

docker-compose-ps: ## List docker-compose services
	docker-compose ps

docker-compose-restart: ## Restart docker-compose services
	docker-compose restart

# Kubernetes
k8s-build-push: docker-build ## Build and push image for Kubernetes
	docker tag $(DOCKER_IMAGE):$(DOCKER_TAG) $(DOCKER_IMAGE):$(DOCKER_TAG)
	docker push $(DOCKER_IMAGE):$(DOCKER_TAG)

k8s-deploy: ## Deploy to Kubernetes
	kubectl apply -f deploy/kubernetes/namespace.yaml
	kubectl apply -f deploy/kubernetes/configmap.yaml
	kubectl apply -f deploy/kubernetes/secret.yaml
	kubectl apply -f deploy/kubernetes/deployment.yaml
	kubectl apply -f deploy/kubernetes/service.yaml
	kubectl apply -f deploy/kubernetes/hpa.yaml
	kubectl apply -f deploy/kubernetes/pdb.yaml

k8s-deploy-ingress: ## Deploy Kubernetes ingress
	kubectl apply -f deploy/kubernetes/ingress.yaml

k8s-deploy-monitoring: ## Deploy Kubernetes ServiceMonitor
	kubectl apply -f deploy/kubernetes/servicemonitor.yaml

k8s-deploy-all: k8s-deploy k8s-deploy-ingress k8s-deploy-monitoring ## Deploy all Kubernetes resources

k8s-delete: ## Delete Kubernetes deployment
	kubectl delete -f deploy/kubernetes/ --ignore-not-found=true

k8s-status: ## Check Kubernetes deployment status
	kubectl get all -n $(K8S_NAMESPACE)

k8s-logs: ## View Kubernetes logs
	kubectl logs -n $(K8S_NAMESPACE) -l app=finopsguard -f

k8s-describe: ## Describe Kubernetes pods
	kubectl describe pods -n $(K8S_NAMESPACE) -l app=finopsguard

k8s-port-forward: ## Port forward to Kubernetes service
	kubectl port-forward -n $(K8S_NAMESPACE) svc/finopsguard 8080:8080

k8s-shell: ## Open shell in Kubernetes pod
	kubectl exec -it -n $(K8S_NAMESPACE) $$(kubectl get pods -n $(K8S_NAMESPACE) -l app=finopsguard -o jsonpath='{.items[0].metadata.name}') -- /bin/bash

k8s-restart: ## Restart Kubernetes deployment
	kubectl rollout restart deployment/finopsguard -n $(K8S_NAMESPACE)

k8s-scale: ## Scale Kubernetes deployment (use REPLICAS=N)
	kubectl scale deployment/finopsguard -n $(K8S_NAMESPACE) --replicas=$(REPLICAS)

# Kustomize
k8s-kustomize-build: ## Build Kubernetes manifests with Kustomize
	kubectl kustomize deploy/kubernetes/

k8s-kustomize-deploy: ## Deploy with Kustomize
	kubectl apply -k deploy/kubernetes/

k8s-kustomize-delete: ## Delete with Kustomize
	kubectl delete -k deploy/kubernetes/

# Database
db-init: ## Initialize database
	./scripts/db-manage.sh init

db-migrate: ## Generate new migration
	./scripts/db-manage.sh migrate

db-upgrade: ## Upgrade database to latest version
	./scripts/db-manage.sh upgrade

db-downgrade: ## Downgrade database to previous version
	./scripts/db-manage.sh downgrade

db-status: ## Show migration status
	./scripts/db-manage.sh status

db-shell: ## Open PostgreSQL shell
	./scripts/db-manage.sh shell

db-backup: ## Backup database
	./scripts/db-manage.sh backup

db-reset: ## Reset database (WARNING: deletes all data)
	./scripts/db-manage.sh reset

# Utilities
clean: ## Clean up generated files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ .coverage 2>/dev/null || true

clean-docker: ## Clean up Docker images and containers
	docker-compose down -v
	docker rmi $(DOCKER_IMAGE):$(DOCKER_TAG) 2>/dev/null || true

health-check: ## Check service health
	@curl -s http://localhost:8080/healthz && echo "✓ Service is healthy" || echo "✗ Service is not healthy"

api-docs: ## Open API documentation
	@open http://localhost:8080/docs || xdg-open http://localhost:8080/docs

metrics: ## View Prometheus metrics
	@curl -s http://localhost:8080/metrics | head -20

# CI/CD
ci-test: ## Run tests in CI environment
	PYTHONPATH=src pytest tests/ -v --tb=short

ci-build: docker-build ## Build for CI/CD pipeline

ci-deploy: k8s-deploy ## Deploy in CI/CD pipeline

# Release
release: clean test docker-build docker-push ## Prepare release (clean, test, build, push)
	@echo "Release $(DOCKER_TAG) completed!"

# Info
version: ## Show version information
	@echo "FinOpsGuard v0.2.0"
	@echo "Python: $$($(PYTHON) --version)"
	@echo "Docker: $$(docker --version)"
	@echo "kubectl: $$(kubectl version --client --short 2>/dev/null || echo 'not installed')"
	@echo "docker-compose: $$(docker-compose --version)"

