.PHONY: test test-python test-javascript lint format clean lint-json lint-python lint-js lint-yaml format-python format-js

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

