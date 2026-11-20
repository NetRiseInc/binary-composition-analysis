PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
SRC := action.py auth.py tests/

.PHONY: help install lint format format-check test check release

help:
	@echo "Targets:"
	@echo "  make install       Install runtime + test dependencies"
	@echo "  make lint          Ruff lint"
	@echo "  make format        Ruff format (apply)"
	@echo "  make format-check  Ruff format check (CI)"
	@echo "  make test          Pytest"
	@echo "  make check         Lint + format-check + test (same as CI)"
	@echo "  make release       Interactive release (detect current, suggest next, confirm)"
	@echo "                     Or: VERSION=vX.Y.Z UPDATE_MAJOR=1 make release"

install:
	$(PIP) install -r requirements.txt
	$(PIP) install ruff pytest

lint:
	ruff check $(SRC)

format:
	ruff format $(SRC)

format-check:
	ruff format --check $(SRC)

test:
	pytest -q

check: lint format-check test

# Run after latest release commit is on origin/main.
# Interactive: make release
# Scripted:    VERSION=v1.0.8 UPDATE_MAJOR=1 make release
release:
	VERSION="$(VERSION)" UPDATE_MAJOR="$(UPDATE_MAJOR)" SKIP_CHECK="$(SKIP_CHECK)" \
		bash scripts/release.sh
