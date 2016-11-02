# Makefile for PYMA
#
# Source:: https://github.com/ampledata/pyma
# Author:: Greg Albrecht W2GMD <oss@undef.net>
# Copyright:: Copyright 2016 Dominik Heidler
# License:: GNU General Public License, Version 3
#


.DEFAULT_GOAL := all


all: develop

develop: remember
	python setup.py develop

install_requirements:
	pip install -r requirements.txt

install:
	python setup.py install

uninstall:
	pip uninstall -y pyma

clean:
	@rm -rf *.egg* build dist *.py[oc] */*.py[co] cover doctest_pypi.cfg \
		nosetests.xml pylint.log output.xml flake8.log tests.log \
		test-result.xml htmlcov fab.log .coverage

publish:
	python setup.py register sdist upload

nosetests: remember
	python setup.py nosetests

pep8: remember
	flake8 --max-complexity 12 --exit-zero pyma/*.py tests/*.py

lint: remember
	pylint --msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}" \
		-r n pyma/*.py tests/*.py || exit 0

test: lint pep8 nosetests

remember:
	@echo "Don't forget to 'make install_requirements'"
