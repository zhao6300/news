PYTEST_FLAGS := -q

export
PYTHONPATH := src,$(CURDIR)/frontend:$(CURDIR)

.PHONY: run unit integration test

run:
	python frontend/core/main.py

TEST_FILES := $(wildcard tests/test_*.py)
INTEGRATION_TEST_FILES := tests/test_separated_frontend.py tests/test_web_api.py tests/test_search_page.py tests/test_persistence_roundtrip.py tests/test_front_main.py
UNIT_TEST_FILES := $(filter-out $(INTEGRATION_TEST_FILES),$(TEST_FILES))

unit:
	python -m pytest $(UNIT_TEST_FILES) $(PYTEST_FLAGS)

integration:
	python -m pytest $(INTEGRATION_TEST_FILES) $(PYTEST_FLAGS)

test: unit integration
