PYTEST_FLAGS := -q

.PHONY: run test

run:
	python src/main.py

test:
	python -m pytest tests $(PYTEST_FLAGS)
