.PHONY: agent

help: ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================
# Commande pour lancer l'agent
# ============================================

agent:
	python -m scripts.agent

fastmcp:
	python -m scripts.run_mcp

fastapi:
	python -m scripts.run_api

bpedb:
	python -m scripts.data_bpe_insert

build:
	docker build -f docker/Dockerfile -t projet-immo-chatbot:latest .

build-mcp:
	docker build -f docker/Dockerfile.mcp -t projet-immo-chatbot-mcp:latest .

run:
	docker rm -f immo-api || true
	docker run --env-file .env -d -p 8000:8000 --dns 8.8.8.8 --name immo-api projet-immo-chatbot:latest

run-mcp:
	docker rm -f immo-mcp || true
	docker run --env-file .env -d -p 8100:8100 --dns 8.8.8.8 --name immo-mcp projet-immo-chatbot-mcp:latest

stop:
	docker stop immo-api

test:
	coverage run -m pytest

coverage-report:
	coverage report -m