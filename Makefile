# Some simple testing tasks (sorry, UNIX only).

PYTHON=venv/bin/python3
PSERVE=venv/bin/gunicorn --paste
PIP=venv/bin/pip
EI=venv/bin/easy_install
NOSE=venv/bin/nosetests
FLAKE=venv/bin/flake8
APIDOC=node_modules/.bin/apidoc
APIDOC_BUILD_DIR=doc/
FLAGS=


env:
	python3 -m venv venv
	${PIP} install -r requirements-dev.txt
	$(PYTHON) ./setup.py develop

dev:
	$(PIP) install coverage requests
	${PIP} install -r requirements-dev.txt
	$(PYTHON) ./setup.py develop
	npm install apidoc

install:
	$(PYTHON) ./setup.py install

run:
	$(PSERVE) ./etc/local.ini

flake:
	$(FLAKE) notifier tests

test: flake
	$(NOSE) -s $(FLAGS)

vtest:
	$(NOSE) -s -v $(FLAGS)

testloop:
	while sleep 1; do $(NOSE) -s $(FLAGS); done

cov cover coverage:
	$(NOSE) -s --with-cover --cover-html --cover-html-dir ./coverage $(FLAGS)
	echo "open file://`pwd`/coverage/index.html"

apidoc:
	$(APIDOC) -o $(APIDOC_BUILD_DIR) -i notifier

clean:
	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -f `find . -type f -name '*~' `
	rm -f `find . -type f -name '.*~' `
	rm -f `find . -type f -name '@*' `
	rm -f `find . -type f -name '#*#' `
	rm -f `find . -type f -name '*.orig' `
	rm -f `find . -type f -name '*.rej' `
	rm -f .coverage
	rm -rf coverage
	rm -rf build
	rm -rf $(APIDOC_BUILD_DIR)


.PHONY: all build env linux run pep test vtest testloop cov clean
