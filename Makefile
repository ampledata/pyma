# Makefile for pymultimonaprs.
#
# Source:: https://github.com/ampledata/pymultimonaprs
# Author:: Greg Albrecht W2GMD <gba@gregalbrecht.com>
# Copyright:: Copyright 2015 OnBeep, Inc.
# License:: GNU General Public License, Version 3
#


.DEFAULT_GOAL := all


all: install_requirements develop

develop:
	python setup.py develop

install_requirements:
	pip install -r requirements.txt

install:
	python setup.py install

uninstall:
	pip uninstall -y pymultimonaprs

clean:
	@rm -rf *.egg* build dist *.py[oc] */*.py[co] cover doctest_pypi.cfg \
		nosetests.xml pylint.log output.xml flake8.log tests.log \
		test-result.xml htmlcov fab.log .coverage

publish:
	python setup.py register sdist upload

nosetests:
	python setup.py nosetests

pep8: install_requirements
	flake8 --max-complexity 12 --exit-zero pymultimonaprs/*.py tests/*.py

lint: install_requirements
	pylint --msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}" \
		-r n pymultimonaprs/*.py tests/*.py || exit 0

test: lint pep8 nosetests
