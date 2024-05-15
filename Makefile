# Makefile for Ratatoskr Project

VENV := .venv
VENV_ACTIVATE := . $(VENV)/bin/activate

# Virtual environment setup 
.PHONY: venv
venv: $(VENV)/bin/activate

$(VENV)/bin/activate: requirements.txt
	test -d $(VENV) || python3 -m venv $(VENV)
	$(VENV_ACTIVATE) && pip install -U pip wheel setuptools
	$(VENV_ACTIVATE) && pip install -r requirements.txt
	$(VENV_ACTIVATE) && python -m spacy download en_core_web_sm
	touch $(VENV)/bin/activate

# Project-specific commands
.PHONY: install
install: venv
	$(VENV_ACTIVATE) && python -m pip install -e .

.PHONY: lint
lint: venv
	$(VENV_ACTIVATE) && ruff check . && mypy ratatoskr

.PHONY: format
format: venv
	$(VENV_ACTIVATE) && black . && isort .

.PHONY: test
test: venv
	$(VENV_ACTIVATE) && pytest tests/

.PHONY: run
run: venv
	$(VENV_ACTIVATE) && $(VENV)/bin/python src/main.py

.PHONY: clean
clean:
	rm -rf $(VENV)
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete

.PHONY: docs
docs: venv
	$(VENV_ACTIVATE) && mkdocs serve  # Install mkdocs if needed
