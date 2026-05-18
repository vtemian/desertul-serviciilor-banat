.PHONY: venv install pipeline test serve

venv:
	python3.11 -m venv .venv
	.venv/bin/pip install --upgrade pip

install: venv
	.venv/bin/pip install -e ".[dev]"
	.venv/bin/playwright install chromium

pipeline:
	.venv/bin/python -m pipeline.run_all

test:
	.venv/bin/pytest

serve:
	cd web && python3 -m http.server 8080
