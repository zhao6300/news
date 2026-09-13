# News Intelligence Platform

A phased build for a modular AI information platform covering news, technology, models, reviews, and related categories.

## What is here

- `src/app.py` — browser routes and HTML rendering.
- `src/auth.py` — account-model login flow.
- `src/connectors.py` — extension protocol, connector registry, and ingestion diagnostics.
- `src/extensions/builtin.py` — seeded content for the initial platform schema.
- `src/services.py` — service-layer access to extensions.
- `src/sessions.py` — login session store.
- `src/storage.py` — replaceable repository layer and simple pagination.
- `tests/` — focused unit and HTTP integration tests.

## Requirements

- Python 3.11+
- Make

## Commands

```bash
make test
make run
```

For faster verification, run the focused layers separately with `make unit` and `make integration`.

Set `PLATFORM_DB` to a writable SQLite file to preserve article state across restarts. Without the variable, the starter uses in-memory seeded data.

Override the placeholder account with `PLATFORM_ACCOUNT_EMAIL` and `PLATFORM_ACCOUNT_PASSWORD`. If either variable is missing, the platform fails to start rather than silently using a partial account.

## Web experience

The platform provides a consistent top bar with visible sign-in or logout status, global keyword search, category shortcuts with result counts, published dates, source attribution on cards, readable article cards, a login screen, and a health endpoint. The built-in demo account accepts `member@example.com` and `demo-password` for early development only.

## How to inspect

```bash
make test
make run
```

## Built-in extensions

The platform exposes `AI`, `News`, `Technology`, `Models`, and `Reviews` as first-class extension categories so new sources can be added without changing downstream services.

Custom sources can implement the `fetch` protocol, be wrapped in the connector registry, and appear in the startup ingestion report without changing the Web routes.

RSS sources can be enabled with `PLATFORM_FEEDS`. Each record requires `slug`, `source`, `category`, and `url`; the `url` points to an RSS document. When this variable is absent, the platform only uses the built-in seed collectors.

## Web endpoints

- `/` — home dashboard with all extension entries.
- `/extensions/{slug}` — source-specific listing with article count and category links.
- `/category/{slug}` — category catalog with pagination.
- `/article/{id}` — article detail page.
- `/search?q=` — keyword-based article search and optional category filter.
- `/login` — login form and session creation.
- `/logout` — session revocation.
- `/health` — process status check.
- `/api/ingestion` — startup source diagnostics, including item counts and source errors.

Pagination supports `?page=` and `?page_size=1..50`; search accepts an optional `category` slug such as `models`.

## Known next steps

1. Add more external source formats and per-source collection policies.

Article ingestion now runs through the connector scheduler, deduplicates by article ID, and writes into the repository layer used by category pages.
