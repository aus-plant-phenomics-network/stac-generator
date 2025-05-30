SHELL := /bin/bash
# =============================================================================
# Variables
# =============================================================================

.DEFAULT_GOAL:=help
.ONESHELL:
USING_PDM		=	$(shell grep "tool.pdm" pyproject.toml && echo "yes")
ENV_PREFIX		=  .venv/bin/
VENV_EXISTS		=	$(shell python3 -c "if __import__('pathlib').Path('.venv/bin/activate').exists(): print('yes')")
PDM_OPTS 		?=
PDM 			?= 	pdm $(PDM_OPTS)

.EXPORT_ALL_VARIABLES:


.PHONY: help
help: 		   										## Display this help text for Makefile
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

.PHONY: upgrade
upgrade:       										## Upgrade all dependencies to the latest stable versions
	@echo "=> Updating all dependencies"
	@if [ "$(USING_PDM)" ]; then $(PDM) update; fi
	@echo "=> Dependencies Updated"
	@$(PDM) run pre-commit autoupdate
	@echo "=> Updated Pre-commit"

# =============================================================================
# Developer Utils
# =============================================================================
.PHONY: install-pdm
install-pdm: 										## Install latest version of PDM
	@curl -sSLO https://pdm.fming.dev/install-pdm.py && \
	curl -sSL https://pdm.fming.dev/install-pdm.py.sha256 | shasum -a 256 -c - && \
	python3 install-pdm.py && \
	rm install-pdm.py

.PHONY: install
install: clean										## Install the project, dependencies, and pre-commit for local development
	@if ! $(PDM) --version > /dev/null; then echo '=> Installing PDM'; $(MAKE) install-pdm; fi
	@if [ "$(VENV_EXISTS)" ]; then echo "=> Removing existing virtual environment"; fi
	if [ "$(VENV_EXISTS)" ]; then $(MAKE) destroy; fi
	if [ "$(VENV_EXISTS)" ]; then $(MAKE) clean; fi
	@if [ "$(USING_PDM)" ]; then $(PDM) config --local venv.in_project true && python3 -m venv --copies .venv && . $(ENV_PREFIX)/activate && $(ENV_PREFIX)/pip install --quiet -U wheel setuptools cython mypy pip; fi
	@if [ "$(USING_PDM)" ]; then $(PDM) install -dG:all; fi
	@echo "=> Install complete! Note: If you want to re-install re-run 'make install'"

.PHONY: clean
clean: 												## Cleanup temporary build artifacts
	@echo "=> Cleaning working directory"
	@rm -rf .pytest_cache .ruff_cache .hypothesis build/ -rf dist/ .eggs/
	@find . -name '*.egg-info' -exec rm -rf {} +
	@find . -name '*.egg' -exec rm -f {} +
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +
	@find . -name '*~' -exec rm -f {} +
	@find . -name '__pycache__' -exec rm -rf {} +
	@find . -name '.ipynb_checkpoints' -exec rm -rf {} +
	@find . -name '*.sqlite3' -exec rm -rf {} +
	@rm -rf .coverage coverage.xml coverage.json htmlcov/ .pytest_cache tests/.pytest_cache tests/**/.pytest_cache .mypy_cache
	$(MAKE) docs-clean

.PHONY: destroy
destroy: 											## Destroy the virtual environment
	@rm -rf .venv

.PHONY: refresh-lockfiles
refresh-lockfiles:                                 ## Sync lockfiles with requirements files.
	pdm update --update-reuse --group :all

.PHONY: lock
lock:                                             ## Rebuild lockfiles from scratch, updating all dependencies
	pdm update --update-eager --group :all

# =============================================================================
# Tests, Linting, Coverage
# =============================================================================
.PHONY: mypy
mypy:                                               ## Run mypy
	@echo "=> Running mypy"
	@$(PDM) run dmypy run
	@echo "=> mypy complete"

.PHONY: mypy-nocache
mypy-nocache:                                       ## Run Mypy without cache
	@echo "=> Running mypy without a cache"
	@$(PDM) run dmypy run -- --cache-dir=/dev/null
	@echo "=> mypy complete"

.PHONY: type-check
type-check: mypy		                            ## Run all type checking

.PHONY: pre-commit
pre-commit: 										## Runs pre-commit hooks; includes ruff formatting and linting, codespell
	@echo "=> Running pre-commit process"
	@$(PDM) run pre-commit run --all-files
	@echo "=> Pre-commit complete"

.PHONY: lint
lint: pre-commit type-check 						## Run all linting

.PHONY: coverage
coverage:  											## Run the tests and generate coverage report
	@echo "=> Running tests with coverage"
	@$(PDM) run pytest tests --cov stac_generator --cov-report html

.PHONY: test
test:  												## Run the tests
	@echo "=> Running test cases"
	@$(PDM) run pytest tests
	@echo "=> Tests complete"


.PHONY: check-all
check-all: lint test-all coverage                   ## Run all linting, tests, and coverage checks


.PHONY: docs
docs: 												## Serve mkdocs locally
	@$(PDM) run mkdocs serve

.PHONY: docs-deploy
docs-deploy:										## Deploy to docs to github pages
	@$(PDM) run mkdocs gh-deploy

.PHONY: test-example
test-example:
	@$(PDM) run stac_generator serialise tests/files/integration_tests/composite/config/composite_config.json --id collection --dst example/generated/cli -v


.PHONY: test-module-collection
test-module-collection:
	@$(PDM) run python script/generate_collection.py

.PHONY: test-module-config
test-module-config:
	@$(PDM) run python script/generate_config.py
	echo "Finish generating config at example/configs/composite_config.json"

.PHONY: test-generated-config
test-generated-config:
	@$(PDM) run stac_generator serialise example/configs/composite_config.json --id collection --dst example/generated/config -v

.PHONY: generate-test-fixtures
generate-test-fixtures:
	@$(PDM) run stac_generator serialise tests/files/integration_tests/composite/config/composite_config.json --id collection --dst tests/files/integration_tests/composite/generated
	@$(PDM) run stac_generator serialise tests/files/integration_tests/point/config/point_config.json --id collection --dst tests/files/integration_tests/point/generated
	@$(PDM) run stac_generator serialise tests/files/integration_tests/raster/config/raster_config.json --id collection --dst tests/files/integration_tests/raster/generated
	@$(PDM) run stac_generator serialise tests/files/integration_tests/vector/config/vector_config.json --id collection --dst tests/files/integration_tests/vector/generated
