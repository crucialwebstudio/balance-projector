#
# Makefile for balance_projector
#
# https://stackoverflow.com/questions/24736146/how-to-use-virtualenv-in-makefile
#

.DEFAULT_GOAL := help
.PHONY: help init update clean

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

init: ## Create venv and install dependencies
	@python3 -m venv venv
	@source venv/bin/activate; pip3 install --editable . .[dev];

update: ## Update the pip package
	@source venv/bin/activate; pip3 install --upgrade .

clean: ## Clean python cache files
	@find . -type f -name "*.py[co]" -delete
	@find . -type d -name "__pycache__" -delete
