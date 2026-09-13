PYTEST_FLAGS := -q

export
PYTHONPATH := src

.PHONY: run test

run:
	python src/main.py

test:
	python -m pytest tests $(PYTEST_FLAGS)
