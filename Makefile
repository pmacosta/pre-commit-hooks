# Makefile
# Copyright (c) 2018-2019 Pablo Acosta-Serafini
# See LICENSE for details

PKG_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
REPO_DIR ?= $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
SOURCE_DIR ?= $(dir $(abspath $(lastword $(MAKEFILE_LIST))))/pre_commit_hooks
EXTRA_DIR ?= $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PYLINT_CMD := pylint --rcfile=$(EXTRA_DIR)/.pylintrc -f colorized -r no

asort:
	@echo "Sorting Aspell whitelist"
	@$(PKG_DIR)/bin/sort-whitelist.sh $(PKG_DIR)/data/whitelist.en.pws

bdist:
	@echo "Creating binary distribution"
	@$(PKG_DIR)/bin/make-pkg.sh

black:
	black \
		$(REPO_DIR) \
		$(SOURCE_DIR)/shellcheck.py \
		$(EXTRA_DIR)/tests \
		$(EXTRA_DIR)/tests/support

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

default:
	@echo "No default action"

FORCE:

lint:
	@echo "Running Pylint on package files"
	@$(PYLINT_CMD) $(REPO_DIR)/*.py
	@$(PYLINT_CMD) $(SOURCE_DIR)/*.py
	@$(PYLINT_CMD) $(EXTRA_DIR)/tests/*.py
	@$(PYLINT_CMD) $(EXTRA_DIR)/tests/support/*.py
sdist:
	@echo "Creating source distribution"
	@cd $(PKG_DIR) && python setup.py sdist --formats=gztar,zip
	@$(PKG_DIR)/bin/list-authors.sh

sterile: clean
	@echo "Removing tox directory"
	@rm -rf $(PKG_DIR)/.tox

test: FORCE
	@$(PKG_DIR)/bin/rtest.sh $(ARGS)