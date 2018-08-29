# Makefile for PYMMA
#
# Source:: https://github.com/ampledata/pymma
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

install: remember
	python setup.py install

uninstall:
	pip uninstall -y pymma

reinstall: uninstall install

remember:
	@echo "Don't forget to 'make install_requirements'"

clean:
	@rm -rf *.egg* build dist *.py[oc] */*.py[co] cover doctest_pypi.cfg \
		nosetests.xml pylint.log output.xml flake8.log tests.log \
		test-result.xml htmlcov fab.log .coverage

publish:
	python setup.py register sdist upload

nosetests: remember
	python setup.py nosetests

pep8: remember
	flake8 --max-complexity 12 --exit-zero pymma/*.py tests/*.py

flake8: pep8

lint: remember
	pylint --msg-template="{path}:{line}: [{msg_id}({symbol}), {obj}] {msg}" \
		-r n pymma/*.py tests/*.py || exit 0

pylint: lint

test: lint pep8 mypy nosetests

mypy:
	mypy --strict .

checkmetadata:
	python setup.py check -s --metadata --restructuredtext
