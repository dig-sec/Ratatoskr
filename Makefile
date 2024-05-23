# Makefile for Ratatoskr Project

VENV := .venv
VENV_ACTIVATE := . $(VENV)/bin/activate
PLAYWRIGHT := $(VENV)/bin/playwright

# Virtual environment setup 
.PHONY: venv
venv: $(VENV)/bin/activate

$(VENV)/bin/activate: requirements.txt
	test -d $(VENV) || python3 -m venv $(VENV)
	$(VENV_ACTIVATE) && pip install -U pip wheel setuptools
	$(VENV_ACTIVATE) && pip install -r requirements.txt
	$(VENV_ACTIVATE) && python -m spacy download en_core_web_sm
	touch $(VENV)/bin/activate

# Playwright setup
.PHONY: playwright
playwright: $(PLAYWRIGHT)

$(PLAYWRIGHT): venv
	$(VENV_ACTIVATE) && pip install playwright
	$(VENV_ACTIVATE) && playwright install
	touch $(PLAYWRIGHT)

# Project-specific commands
.PHONY: install
install: venv playwright
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

