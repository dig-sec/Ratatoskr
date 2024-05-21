# Makefile for Ratatoskr FastAPI Project
VENV := .venv
VENV_ACTIVATE := . $(VENV)/bin/activate

# --- Environment Setup ---
.PHONY: venv
venv: $(VENV)/bin/activate

$(VENV)/bin/activate: requirements.txt
	test -d $(VENV) || python3 -m venv $(VENV)
	$(VENV_ACTIVATE) && pip install -U pip wheel setuptools
	$(VENV_ACTIVATE) && pip install -r requirements.txt
	touch $(VENV)/bin/activate

# --- Installation ---
.PHONY: install
install: venv
	$(VENV_ACTIVATE) && pip install -e .[dev]

# --- Linting and Formatting ---
.PHONY: lint
lint: venv
	$(VENV_ACTIVATE) && ruff check ratatoskr  # Check the ratatoskr directory
	$(VENV_ACTIVATE) && mypy ratatoskr --ignore-missing-imports

.PHONY: format
format: venv
	$(VENV_ACTIVATE) && black ratatoskr
	$(VENV_ACTIVATE) && isort ratatoskr

# --- Testing ---
.PHONY: test
test: venv
	$(VENV_ACTIVATE) && pytest 

# --- Running the Server ---
.PHONY: run
run: venv
	$(VENV_ACTIVATE) && uvicorn ratatoskr.main:app --reload

# --- Cleaning Up ---
.PHONY: clean
clean:
	rm -rf $(VENV)
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete