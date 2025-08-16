SERVICE_NAME=tph280
USER=$(shell id -un)

# Build python virtual environment ###################################
.PHONY: venv clean-venv 

VENV_DIR = .venv
PYTHON = python3

# Target to create the virtual environment
$(VENV_DIR)/bin/activate:
	@echo "Creating virtual environment in $(VENV_DIR)..."
	$(PYTHON) -m venv $(VENV_DIR)
	@echo "Virtual environment created."

# Target to ensure the virtual environment exists
venv: $(VENV_DIR)/bin/activate

# Target to install dependencies
install: venv
	@echo "Installing dependencies..."
	$(VENV_DIR)/bin/pip install -r requirements.txt
	$(VENV_DIR)/bin/pip install -r requirements-dev.txt
	@echo "Dependencies installed."

# Target to clean the virtual environment
clean-venv:
	@echo "Cleaning virtual environment..."
	rm -rf $(VENV_DIR)
	@echo "Virtual environment cleaned."

# install example service ############################################
.PHONY: service-uninstall service-install service-start service-stop service-logs

SERVICE_FILE=/etc/systemd/system/$(SERVICE_NAME).service
SERVICE_LOG_DIR=/var/log/$(SERVICE_NAME)
SERVICE_STOP=\
	@if systemctl is-active --quiet $(SERVICE_NAME).service; then \
		sudo systemctl stop $(SERVICE_NAME).service; \
	fi
SERVICE_DISABLE=\
	@systemctl is-enabled $(SERVICE_NAME).service > /dev/null 2>&1; \
	if [ $$? -eq 0 ]; then \
		sudo systemctl disable $(SERVICE_NAME).service; \
	fi
SERVICE_START=\
	sudo systemctl start pi_bme280.service
SERVICE_ENABLE=\
	sudo systemctl enable $(SERVICE_NAME).service
SERVICE_LOGS=\
	sudo journalctl -u $(SERVICE_NAME)

service-start:
	$(SERVICE_START)

service-stop:
	$(SERVICE_STOP)

service-logs:
	$(SERVICE_LOGS) | cat
	@if test -f /var/log/$(SERVICE_NAME)/output.log; then \
		echo '------------ output.log ------------------------' ;\
		cat /var/log/$(SERVICE_NAME)/output.log; \
	fi
	@if test -f /var/log/$(SERVICE_NAME)/error.log; then \
		echo '------------ error.log ------------------------'; \
		cat /var/log/$(SERVICE_NAME)/error.log; \
	fi

service-logs-follow:
	$(SERVICE_LOGS) -f

service-uninstall: service-stop
	$(SERVICE_STOP)
	$(SERVICE_DISABLE)
	@if test -f $(SERVICE_FILE); then \
		sudo rm $(SERVICE_FILE); \
	fi
	@if test -d $(SERVICE_LOG_DIR); then \
		sudo rm -rf $(SERVICE_LOG_DIR); \
	fi
	sudo systemctl daemon-reload
	sudo systemctl daemon-reexec
	@if test -f /etc/systemd/$(SERVICE_NAME).service; then \
		sudo rm /etc/systemd/system/$(SERVICE_NAME).service; \
	fi

service-install: service-clean
	sudo sh -c "sed -e 's!CURDIR!$(CURDIR)!g' -e 's/USER/$(USER)/g' -e 's/SERVICE/$(SERVICE_NAME)/g' example/pi_bme280/pi_bme280.service > /etc/systemd/system/$(SERVICE_NAME).service"
	sudo mkdir $(SERVICE_LOG_DIR)
	sudo chown root:root $(SERVICE_LOG_DIR)
	sudo chmod 755 $(SERVICE_LOG_DIR)
	sudo systemctl daemon-reexec
	sudo systemctl daemon-reload
	$(SERVICE_ENABLE)
	$(SERVICE_START)

# setuptools - manage versioning #####################################
VERSION := $(shell python3 -m setuptools_scm)
TAG := v$(VERSION)

.PHONY: version tag release suggest-next

# Print current version of package
version:
	@echo "Current version: $(VERSION)"

# Add version tag to git
tag:
	@if echo "$(VERSION)" | grep -q dev; then \
		echo "✖ Refusing to tag a dev version ($(VERSION))"; \
		exit 1; \
	fi
	@echo "✔ Tagging version $(TAG)"
	git tag v$(VERSION)
	git push origin v$(VERSION)

# Release a new version package
release: version tag
	@echo "Release v$(VERSION) pushed."

# Suggest the next version of package
suggest-next:
	@echo "Suggested next tag: v$$(python3 -m setuptools_scm | awk -F. '{printf "%d.%d.%d\n", $$1, $$2, $$3+1}')"

# Build and test #####################################################
.PHONY: test test-python test-javascript lint format clean lint-json lint-python lint-js lint-yaml format-python format-js build

# Build
build:
	$(PYTHON) -m build

# Run all tests
test: test-python test-javascript

# Python tests
test-python:
	pytest --cov=ha_mqtt_pi_smbus --cov-report=term-missing

# JavaScript tests
test-javascript:
	npm test

# Lint everything
lint: lint-python lint-js lint-json lint-yaml

# Python lint
lint-python:
	black --check .
	flake8 .

# JS lint
lint-json:
	find . -name "*.json" -not -path "./node_modules/*" -not -path "./venv/*" -print0 | \
		xargs -0 -I {} sh -c 'echo "Checking {}"; jq empty {}'

# YAML lint	
lint-yaml:
	find . \( -name "*.yml" -o -name "*.yaml" \) -not -path "./node_modules/*" -not -path "./venv/*" | \
		xargs yamllint	

# Format everything
format: format-python format-js

# Python format
format-python:
	black .

# JS format
format-js:
	npm run format

# Clean build artifacts & caches
clean:
	rm -rf coverage coverage-js lcov-report .pytest_cache

