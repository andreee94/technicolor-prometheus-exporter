PYTHON = python3
BROWSER = firefox
VERSION = 0.1.1
# REGISTRY = registry.andreee94.ml
REGISTRY = andreee94
IMAGE = technicolor-prometheus-exporter

test:
	${PYTHON} -m pytest
	
run:
	${PYTHON} src/main.py

clean: clean-pyc clean-test

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/

lint:
	flake8 tests

coverage:
	coverage run --source setup.py test
	coverage report -m
	coverage html
	$(BROWSER) htmlcov/index.html

docker-build:
	docker build -t ${REGISTRY}/${IMAGE}:${VERSION} .

docker-push:
	docker push ${REGISTRY}/${IMAGE}:${VERSION}

# run as: make TECHNICOLOR_PASSWORD=<password> run
docker-run:
	docker run -it --rm -p 9182:9182 -e TECHNICOLOR_PASSWORD=$(TECHNICOLOR_PASSWORD) ${REGISTRY}/${IMAGE}:${VERSION}