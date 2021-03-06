# Makefile
# Copyright (c) 2018-2019 Pablo Acosta-Serafini
# See LICENSE for details

PKG_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
REPO_DIR ?= $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
SOURCE_DIR ?= $(dir $(abspath $(lastword $(MAKEFILE_LIST))))/pre_commit_hooks
EXTRA_DIR ?= $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
### Custom pylint plugins configuration
PYLINT_PLUGINS_DIR := $(shell if [ -d $(EXTRA_DIR)/pylint_plugins ]; then echo "$(EXTRA_DIR)/pylint_plugins"; fi)
PYLINT_PLUGINS_LIST := $(shell if [ -d $(EXTRA_DIR)/pylint_plugins ]; then cd $(EXTRA_DIR)/pylint_plugins && ls -m *.py | sed 's|.*/||g' | sed 's|, |,|g' | sed 's|\.py||g'; fi)
PYLINT_CLI_APPEND := $(shell if [ -d $(EXTRA_DIR)/pylint_plugins ]; then echo "--load-plugins=$(PYLINT_PLUGINS_LIST)"; fi)
PYLINT_CMD := pylint \
	--rcfile=$(EXTRA_DIR)/.pylintrc \
	$(PYLINT_CLI_APPEND) \
	--output-format=colorized \
	--reports=no \
	--score=no
###

asort:
	@echo "Sorting Aspell whitelist"
	@$(PKG_DIR)/bin/sort-whitelist.sh $(PKG_DIR)/data/whitelist.en.pws

bdist:
	@echo "Creating binary distribution"
	@$(PKG_DIR)/bin/make-pkg.sh

black:
	black \
		$(REPO_DIR) \
		$(SOURCE_DIR)/ \

clean: FORCE
	@echo "Cleaning package"
	@find $(PKG_DIR) -name '*.pyc' -delete
	@find $(PKG_DIR) -name '__pycache__' -delete
	@find $(PKG_DIR) -name '.coverage*' -delete
	@find $(PKG_DIR) -name '*.tmp' -delete
	@find $(PKG_DIR) -name '*.pkl' -delete
	@find $(PKG_DIR) -name '*.error' -delete
	@rm -rf $(PKG_DIR)/build
	@rm -rf	$(PKG_DIR)/dist
	@rm -rf $(PKG_DIR)/.eggs
	@rm -rf $(PKG_DIR)/.cache
	@rm -rf $(PKG_DIR)/tests/support/_build
	@rm -rf $(PKG_DIR)/.tox

default:
	@echo "No default action"

FORCE:

lint:
	@echo "Running Pylint on package files"
	@echo "Directory $(REPO_DIR)"
	@PYTHONPATH="$(PYTHONPATH):$(PYLINT_PLUGINS_DIR)" \
		$(PYLINT_CMD) $(REPO_DIR)/*.py
	@echo "Directory $(SOURCE_DIR)"
	@PYTHONPATH="$(PYTHONPATH):$(PYLINT_PLUGINS_DIR)" \
		$(PYLINT_CMD) $(SOURCE_DIR)/*.py
