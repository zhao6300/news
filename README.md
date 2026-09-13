# News Intelligence Platform

A phased build for a modular AI information platform covering news, technology, models, reviews, and related categories.

## What is here

- `src/app.py` — browser routes and HTML rendering.
- `src/auth.py` — account-model login flow.
- `src/connectors.py` — extension protocol for new information sources.
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

Set `PLATFORM_DB` to a writable SQLite file to preserve article state across restarts. Without the variable, the starter uses in-memory seeded data.

Override the placeholder account with `PLATFORM_ACCOUNT_EMAIL` and `PLATFORM_ACCOUNT_PASSWORD`. If either variable is missing, the platform fails to start rather than silently using a partial account.

## Web experience

The platform provides a clean home view, extension-linked navigation, category listings, article detail pages, a login screen, and a health endpoint. The built-in demo account accepts `member@example.com` and `demo-password` for early development only.

## How to inspect

```bash
make test
make run
```

## Built-in extensions

The platform exposes `AI`, `Technology`, `Models`, and `Reviews` as first-class extension categories so new sources can be added without changing downstream services.

## Web endpoints

- `/` — home dashboard with all extension entries.
- `/extensions/{slug}` — seeded extension listing.
- `/category/{slug}` — category catalog with pagination.
- `/article/{id}` — article detail page.
- `/search?q=` — keyword-based article search.
- `/login` — login form and session creation.
- `/logout` — session revocation.
- `/health` — process status check.

Pagination supports `?page=` and `?page_size=1..50`.

## Known next steps

1. Add source scheduling and ingestion diagnostics.
2. Add category filters, article result counts, and richer search.
