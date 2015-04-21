.PHONY: clean-all

clean:
	find . -name \*.pyc -delete
	find . -name '*.bak' -delete

install:
	scripts/install.sh

clean-all: clean
	rm -rf .venv

venv:
	virtualenv .venv
	pip install -r requirements.txt
