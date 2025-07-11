.PHONY: test test-python test-javascript lint format

#test: test-python test-javascript

test-python:
	pytest --cov=ha_mqtt_pi_smbus --cov-report=term-missing

test-javascript:
	npm test

