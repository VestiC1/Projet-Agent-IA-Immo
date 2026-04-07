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
	docker build -t projet-immo-chatbot:latest .

run:
	docker rm -f immo-api || true
	docker run --env-file .env -d -p 8000:8000 --name immo-api projet-immo-chatbot:latest

stop:
	docker stop immo-api

test:
	coverage run -m pytest

coverage-report:
	coverage report -m