# Makefile for ecommerce-nau-extensions

# ==============================================================================
# VARIABLES

# current directory relative to the Makefile file
ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

# By default use the devstack ecommerce folder
# but you can use other folder, you just have to change this environment variable like:
#   ECOMMERCE_SOURCE_PATH=/nau make test
#   make ECOMMERCE_SOURCE_PATH=/nau test
ECOMMERCE_SOURCE_PATH ?= /edx/app/ecommerce/ecommerce
SRC_FOLDER_RELATIVE_PATH ?= nau_extensions
SRC_FOLDER_FULL_PATH=$(ROOT_DIR)/$(SRC_FOLDER_RELATIVE_PATH)
LOCALES=--locale en --locale pt_PT

# ==============================================================================
# RULES

default: help

help:
	@echo "Please use \`make <target>' where <target> is one of"
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
.PHONY: help

_prerequire:
	@if [ ! -d "${ECOMMERCE_SOURCE_PATH}" ]; then { echo "Ecommerce directory doesn't exist.\n  ECOMMERCE_SOURCE_PATH=${ECOMMERCE_SOURCE_PATH}\nPlease check if that directory exist or change the default value using:\n  ECOMMERCE_SOURCE_PATH=~/<different path>/ecommerce make <target>" ; exit 1; } fi
.PHONY: _prerequire

test: | _prerequire ## Run all the tests, to run a specific test run: make test `pwd`/nau_extensions/tests/test_XPTO.py
	@args="$(filter-out $@,$(MAKECMDGOALS))" && \
	arg_2="$${args:-${1}}" && \
	arg_3="$${arg_2:=$(SRC_FOLDER_FULL_PATH)}" && \
	cd ${ECOMMERCE_SOURCE_PATH} && \
	DJANGO_SETTINGS_MODULE=nau_extensions.settings.test coverage run --source="$(ROOT_DIR)" -m pytest $${arg_3}
.PHONY: test

clean: ## remove all the unneeded artifacts
	-rm -rf .tox
	-rm -rf *.egg-info
	-find . -name '__pycache__' -prune -exec rm -rf "{}" \;
	-find . -name '*.pyc' -delete
	-rm -f MANIFEST
	-rm -rf .coverage .coverage.* htmlcov
.PHONY: clean

# It will use the `.isort.cfg` from ecommerce
lint_isort: _prerequire
	@echo "Run isort"
	@cd ${ECOMMERCE_SOURCE_PATH} && \
	isort --check-only --diff $(SRC_FOLDER_FULL_PATH)
.PHONY: lint_isort

# It will use the `.isort.cfg` from ecommerce
run_isort: _prerequire  ## Run the isort to sort the python imports
	@cd ${ECOMMERCE_SOURCE_PATH} && \
	isort $(SRC_FOLDER_FULL_PATH)
.PHONY: run_isort

# It will use the `setup.cfg` from ecommerce
lint_pycodestyle: _prerequire
	@echo "Run pycodestyle"
	@cd ${ECOMMERCE_SOURCE_PATH} && \
	pycodestyle --config=setup.cfg $(SRC_FOLDER_FULL_PATH)
.PHONY: lint_pycodestyle

# It will use the `pylintrc` from ecommerce
lint_pylint: _prerequire
	@echo "Run pylint"
	@cd ${ECOMMERCE_SOURCE_PATH} && \
	pylint -j 0 --rcfile=pylintrc --verbose --init-hook='import sys; sys.path.append("${ECOMMERCE_SOURCE_PATH}")' $(SRC_FOLDER_FULL_PATH)
.PHONY: lint_pylint

# Can't run pylint from ecommerce externally, the pylint plugins aren't being loaded.
lint: | lint_isort lint_pycodestyle # lint_pylint ## Run Python linting
.PHONY: lint

extract_translations:  ## Extract translations from source code
	@DJANGO_SETTINGS_MODULE="" django-admin makemessages $(LOCALES) -d django
.PHONY: extract_translations

compile_translations:  ## Compiles the extracted translations
	@DJANGO_SETTINGS_MODULE="" django-admin compilemessages
.PHONY: compile_translations

detect_changed_source_translations:
	@test $$(git diff --exit-code -G "^(msgid|msgstr)" | wc -l) -eq 0 || ( echo "Detected a changed source translations!" ; exit 1 )
.PHONY: detect_changed_source_translations

translations: | extract_translations compile_translations ## Extract and compile translations
.PHONY: translations
