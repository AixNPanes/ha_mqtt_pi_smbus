VERSION := $(shell python3 -m setuptools_scm)
TAG := v$(VERSION)

.PHONY: test test-python test-javascript lint format clean lint-json lint-python lint-js lint-yaml format-python format-js build version tag release suggest-next

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

# Build
build:
	python -m build

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

