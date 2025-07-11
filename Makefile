.PHONY: test test-python test-javascript lint format clean

test: test-python test-javascript

test-python:
	pytest --cov=ha_mqtt_pi_smbus --cov-report=term-missing

test-javascript:
	npm test

lint:
	black --check .
	flake8 .

format:
	black .

clean:
	rm -rf coverage coverage-js lcov-report .pytest_cache

