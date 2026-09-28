# YOHAKU TOKYO — developer entry points. See README.md.
SHELL := /bin/bash
.DEFAULT_GOAL := help

ROOT      := $(abspath .)
WEB       := $(ROOT)/apps/web
PIPELINE  := $(ROOT)/pipeline
NODE_VER  := v24.21.0

# Prefer a project-local Node (installed by `make node`) when present.
ifneq ($(wildcard $(ROOT)/.tools/node/bin/node),)
export PATH := $(ROOT)/.tools/node/bin:$(PATH)
endif

.PHONY: help node setup discover data dev test test-py test-web lint build clean check-tools

help: ## Show targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*## "}{printf "  \033[1m%-10s\033[0m %s\n",$$1,$$2}'

check-tools:
	@command -v uv >/dev/null || { echo "uv が見つかりません: https://docs.astral.sh/uv/"; exit 1; }
	@command -v node >/dev/null || { echo "node が見つかりません。'make node' でプロジェクト内に導入できます"; exit 1; }

node: ## Download Node.js $(NODE_VER) into .tools/ (Linux x64, no root needed)
	@mkdir -p .tools
	curl -fsSL https://nodejs.org/dist/$(NODE_VER)/node-$(NODE_VER)-linux-x64.tar.xz -o .tools/node.tar.xz
	tar xf .tools/node.tar.xz -C .tools && rm .tools/node.tar.xz
	rm -rf .tools/node && mv .tools/node-$(NODE_VER)-linux-x64 .tools/node
	@.tools/node/bin/node -v

setup: check-tools ## Install Python and Node dependencies
	cd $(PIPELINE) && uv sync
	cd $(WEB) && npm ci

FEATURE ?=
discover: ## Search the open data catalog -> data/manifests/datasets.json (FEATURE=park to limit)
	cd $(PIPELINE) && uv run station-pipeline discover $(if $(FEATURE),--feature $(FEATURE))

data: ## Fetch + normalize accepted datasets, then build stations.json (scores: fixture for now)
	cd $(PIPELINE) && uv run station-pipeline stations
	cd $(PIPELINE) && uv run station-pipeline ingest
	cd $(PIPELINE) && uv run station-pipeline aggregate
	cd $(PIPELINE) && uv run station-pipeline ridership
	cd $(PIPELINE) && uv run station-pipeline build-fixture
	cd $(PIPELINE) && uv run station-pipeline export-web

dev: ## Start the Next.js dev server (http://localhost:3000)
	cd $(WEB) && npm run dev

test: test-py test-web ## Run all tests

test-py:
	cd $(PIPELINE) && uv run pytest

test-web:
	cd $(WEB) && npm test

lint: ## Lint and typecheck both sides
	cd $(PIPELINE) && uv run ruff check . && uv run ruff format --check .
	cd $(WEB) && npm run lint && npm run typecheck

build: ## Production build of the web app
	cd $(WEB) && npm run build

clean: ## Remove build artifacts
	rm -rf $(WEB)/.next $(PIPELINE)/.pytest_cache $(PIPELINE)/.ruff_cache
