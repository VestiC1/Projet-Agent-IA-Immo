.PHONY: agent

help: ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ============================================
# Commande pour lancer l'agent
# ============================================

agent:
	python -m scripts.agent

fastapi:
	python -m scripts.run_api

bpedb:
	python -m scripts.data_bpe_insert